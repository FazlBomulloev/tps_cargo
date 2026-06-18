import logging
import math
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.client import Client
from app.models.issuance import IssuanceItem, IssuanceOrder
from app.models.parcel_china import ParcelChina
from app.models.parcel_dushanbe import ParcelDushanbe
from app.models.staff import StaffUser
from app.models.unresolved import UnresolvedParcel
from app.schemas.parcel import (
    MyParcelResponse,
    ParcelChinaBulk,
    ParcelChinaCreate,
    ParcelChinaResponse,
    ParcelDushanbeBulk,
    ParcelDushanbeCreate,
    ParcelDushanbeResponse,
    ParcelStatusUpdate,
    ParcelUpdate,
)
from app.services.audit_service import log_action
from app.utils.track_normalize import normalize_track
from app.api.deps import (
    get_client_ip,
    get_current_user,
    require_permission,
    require_role,
    verify_bot_secret,
)

router = APIRouter(prefix="/api/parcels", tags=["parcels"])

log = logging.getLogger(__name__)

VALID_STATUSES = {"received_dushanbe", "issued"}


def _created_at_sort_key(item: dict):
    v = item.get("created_at")
    if not v:
        return datetime.min
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            return datetime.min
    return v


# ── China ──

@router.post("/china", response_model=ParcelChinaResponse, status_code=201)
async def add_china(
    body: ParcelChinaCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_china", "owner")),
):
    track = normalize_track(body.track_id)
    if not track:
        raise HTTPException(status_code=400, detail="Invalid track code")
    existing = await db.execute(select(ParcelChina).where(ParcelChina.track_id == track))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Track already exists")
    parcel = ParcelChina(track_id=track, created_by=current_user.id)
    db.add(parcel)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Track already exists")
    await log_action(
        db, staff_id=current_user.id, action="create_parcel_china",
        entity_type="parcel", entity_id=parcel.id,
        after={"track_id": track}, ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    return parcel


@router.post("/china/bulk")
async def add_china_bulk(
    body: ParcelChinaBulk,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_china", "owner")),
):
    added = 0
    duplicates = []
    for raw in body.track_ids:
        track = normalize_track(raw)
        if not track:
            continue
        existing = await db.execute(select(ParcelChina).where(ParcelChina.track_id == track))
        if existing.scalar_one_or_none():
            duplicates.append(track)
            continue
        db.add(ParcelChina(track_id=track, created_by=current_user.id))
        added += 1
    if added:
        await log_action(
            db, staff_id=current_user.id, action="bulk_create_parcel_china",
            entity_type="parcel", after={"count": added}, ip_address=get_client_ip(request),
        )
    await db.commit()
    return {
        "total": len(body.track_ids),
        "added": added,
        "duplicates": len(duplicates),
        "duplicate_list": duplicates,
    }


@router.get("/china", response_model=dict)
async def list_china(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_china", "owner")),
):
    query = select(ParcelChina).where(ParcelChina.is_deleted == False)
    if q:
        # Поиск по трек-коду (нормализуем под формат хранения).
        term = normalize_track(q)
        if term:
            query = query.where(ParcelChina.track_id.ilike(f"%{term}%"))
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.order_by(ParcelChina.created_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    items = [ParcelChinaResponse.model_validate(p) for p in result.scalars().all()]
    return {"items": items, "total": total, "page": page, "pages": pages, "per_page": per_page}


# ── Dushanbe ──

@router.post("/dushanbe", status_code=201)
async def add_dushanbe(
    body: ParcelDushanbeCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    track = normalize_track(body.track_id)
    if not track:
        raise HTTPException(status_code=400, detail="Invalid track code")
    if body.delivery_method not in ("avia", "truck"):
        raise HTTPException(status_code=400, detail="delivery_method must be 'avia' or 'truck'")

    tps = (body.tps_code or "").strip().upper()

    if not tps:
        unresolved = UnresolvedParcel(
            track_id=track,
            raw_tps_code="",
            weight_kg=body.weight_kg,
            volume_m3=body.volume_m3,
            delivery_method=body.delivery_method,
            comment=body.comment,
            created_by=current_user.id,
        )
        db.add(unresolved)
        await db.commit()
        return {
            "status": "unresolved_no_tps",
            "message": "Посылка добавлена без TPS-кода",
        }

    result = await db.execute(
        select(Client).where(Client.tps_code == tps)
    )
    client = result.scalar_one_or_none()

    if not client:
        unresolved = UnresolvedParcel(
            track_id=track,
            raw_tps_code=tps,
            weight_kg=body.weight_kg,
            volume_m3=body.volume_m3,
            delivery_method=body.delivery_method,
            comment=body.comment,
            created_by=current_user.id,
        )
        db.add(unresolved)
        await db.commit()
        return {
            "status": "unresolved",
            "message": (
                "TPS-код не найден,"
                " сохранено как неразобранное"
            ),
        }

    existing = await db.execute(
        select(ParcelDushanbe)
        .where(ParcelDushanbe.track_id == track)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Трек уже обработан в Душанбе",
        )

    china_result = await db.execute(
        select(ParcelChina)
        .where(ParcelChina.track_id == track)
    )
    has_china = (
        china_result.scalar_one_or_none() is not None
    )

    parcel = ParcelDushanbe(
        track_id=track,
        client_id=client.id,
        weight_kg=body.weight_kg,
        volume_m3=body.volume_m3,
        delivery_method=body.delivery_method,
        comment=body.comment,
        shelf=(body.shelf or "").strip() or None,
        has_china_registration=has_china,
        created_by=current_user.id,
    )
    db.add(parcel)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Трек уже обработан в Душанбе",
        )
    await log_action(
        db,
        staff_id=current_user.id,
        action="create_parcel_dushanbe",
        entity_type="parcel",
        entity_id=parcel.id,
        after={
            "track_id": track,
            "client_id": client.id,
            "tps_code": tps,
        },
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    return {
        "status": "ok",
        "parcel_id": parcel.id,
        "client_name": client.full_name,
        "telegram_id": client.telegram_id,
    }


@router.post("/dushanbe/bulk")
async def add_dushanbe_bulk(
    body: ParcelDushanbeBulk,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(
        require_role("admin_dushanbe", "owner")
    ),
):
    if body.delivery_method not in ("avia", "truck"):
        raise HTTPException(
            status_code=400,
            detail="delivery_method must be 'avia' or 'truck'",
        )

    # Клиент резолвится один раз — TPS общий на всю партию.
    tps = (body.tps_code or "").strip().upper()
    client = None
    if tps:
        client = (await db.execute(
            select(Client).where(Client.tps_code == tps)
        )).scalar_one_or_none()

    added: list[str] = []
    unresolved_list: list[str] = []
    duplicates: list[str] = []
    seen: set[str] = set()

    for raw in body.track_ids:
        track = normalize_track(raw)
        if not track:
            continue

        # TPS пуст или клиент не найден -> неразобранное
        # (как в одиночном add_dushanbe).
        if not tps or client is None:
            db.add(UnresolvedParcel(
                track_id=track,
                raw_tps_code=tps,
                weight_kg=body.weight_kg,
                volume_m3=body.volume_m3,
                delivery_method=body.delivery_method,
                comment=body.comment,
                created_by=current_user.id,
            ))
            unresolved_list.append(track)
            continue

        # Дубликат трека: уже в этой партии или в БД.
        if track in seen:
            duplicates.append(track)
            continue
        exists = (await db.execute(
            select(ParcelDushanbe)
            .where(ParcelDushanbe.track_id == track)
        )).scalar_one_or_none()
        if exists:
            duplicates.append(track)
            continue

        has_china = (await db.execute(
            select(ParcelChina)
            .where(ParcelChina.track_id == track)
        )).scalar_one_or_none() is not None

        db.add(ParcelDushanbe(
            track_id=track,
            client_id=client.id,
            weight_kg=body.weight_kg,
            volume_m3=body.volume_m3,
            delivery_method=body.delivery_method,
            comment=body.comment,
            shelf=(body.shelf or "").strip() or None,
            has_china_registration=has_china,
            created_by=current_user.id,
        ))
        seen.add(track)
        added.append(track)

    if added or unresolved_list:
        await log_action(
            db,
            staff_id=current_user.id,
            action="bulk_create_parcel_dushanbe",
            entity_type="parcel",
            after={
                "tps_code": tps,
                "added": len(added),
                "unresolved": len(unresolved_list),
            },
            ip_address=get_client_ip(request),
        )
    await db.commit()

    log.info(
        "Групповая приёмка Душанбе (TPS=%s): "
        "добавлено=%s, неопознано=%s, дубли=%s",
        tps or "—", len(added), len(unresolved_list),
        len(duplicates),
    )
    return {
        "total": len(body.track_ids),
        "added": len(added),
        "unresolved": len(unresolved_list),
        "duplicates": len(duplicates),
        "added_list": added,
        "unresolved_list": unresolved_list,
        "duplicate_list": duplicates,
        "client_name": client.full_name if client else None,
    }


# ── Soft delete ──

@router.delete("/dushanbe/{parcel_id}")
async def delete_dushanbe(
    parcel_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(
        require_permission("parcels_delete")
    ),
):
    parcel = await db.get(ParcelDushanbe, parcel_id)
    if not parcel or parcel.is_deleted:
        raise HTTPException(
            status_code=404, detail="Посылка не найдена"
        )
    # Выданные посылки не удаляем: они уже учтены в выдаче и
    # отчётности, мягкое удаление исказило бы историю.
    if parcel.status == "issued":
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить выданную посылку",
        )
    parcel.is_deleted = True
    parcel.deleted_at = datetime.utcnow()
    parcel.deleted_by = current_user.id
    await log_action(
        db,
        staff_id=current_user.id,
        action="delete_parcel_dushanbe",
        entity_type="parcel",
        entity_id=parcel.id,
        before={"track_id": parcel.track_id},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    log.info(
        "Мягкое удаление посылки Душанбе id=%s (трек=%s) "
        "сотрудником id=%s",
        parcel.id, parcel.track_id, current_user.id,
    )
    return {"detail": "Посылка удалена", "id": parcel.id}


@router.delete("/china/{parcel_id}")
async def delete_china(
    parcel_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(
        require_permission("parcels_delete")
    ),
):
    parcel = await db.get(ParcelChina, parcel_id)
    if not parcel or parcel.is_deleted:
        raise HTTPException(
            status_code=404, detail="Посылка не найдена"
        )
    parcel.is_deleted = True
    parcel.deleted_at = datetime.utcnow()
    parcel.deleted_by = current_user.id
    await log_action(
        db,
        staff_id=current_user.id,
        action="delete_parcel_china",
        entity_type="parcel",
        entity_id=parcel.id,
        before={"track_id": parcel.track_id},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    log.info(
        "Мягкое удаление посылки Китай id=%s (трек=%s) "
        "сотрудником id=%s",
        parcel.id, parcel.track_id, current_user.id,
    )
    return {"detail": "Посылка удалена", "id": parcel.id}


# ── List / detail ──

@router.get("/all")
async def list_all_parcels(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_china", "admin_dushanbe", "owner")),
):
    # Поиск по ФИО / TPS / трек-коду. Имя/TPS ищем по клиенту,
    # трек — по нормализованному коду. norm пуст -> запрос без
    # букв/цифр трека (т.е. по имени) -> по Китаю не ищем.
    term = (q or "").strip()
    norm = normalize_track(term) if term else ""

    async def _unresolved_items(db: AsyncSession, query=None):
        if query is None:
            query = select(UnresolvedParcel).where(
                UnresolvedParcel.resolved == False,
                UnresolvedParcel.is_deleted == False,
            )
            if term:
                uconds = [
                    UnresolvedParcel.raw_tps_code.ilike(f"%{term}%")
                ]
                if norm:
                    uconds.append(
                        UnresolvedParcel.track_id.ilike(f"%{norm}%")
                    )
                query = query.where(or_(*uconds))
        result = await db.execute(query.order_by(UnresolvedParcel.created_at.desc()))
        items = []
        for p in result.scalars().all():
            items.append({
                "id": p.id, "track_id": p.track_id, "status": "unresolved",
                "weight_kg": float(p.weight_kg) if p.weight_kg else None,
                "delivery_method": p.delivery_method,
                "client_name": None, "tps_code": p.raw_tps_code,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
        return items

    async def _dushanbe_items(db: AsyncSession, query):
        if term:
            client_ids = select(Client.id).where(
                or_(
                    Client.full_name.ilike(f"%{term}%"),
                    Client.tps_code.ilike(f"%{term}%"),
                )
            )
            dconds = [ParcelDushanbe.client_id.in_(client_ids)]
            if norm:
                dconds.append(
                    ParcelDushanbe.track_id.ilike(f"%{norm}%")
                )
            query = query.where(or_(*dconds))
        result = await db.execute(
            query.options(joinedload(ParcelDushanbe.client))
            .order_by(ParcelDushanbe.created_at.desc())
        )
        items = []
        for p in result.unique().scalars().all():
            c = p.client
            items.append({
                "id": p.id, "track_id": p.track_id, "status": p.status,
                "weight_kg": float(p.weight_kg) if p.weight_kg else None,
                "delivery_method": p.delivery_method,
                "client_name": c.full_name if c else None,
                "tps_code": c.tps_code if c else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
        return items

    if status_filter == "in_china":
        if term and not norm:
            # Поиск по имени/TPS — в Китае искать нечего.
            return {"items": [], "total": 0, "page": page, "pages": 1}
        query = select(ParcelChina).where(ParcelChina.is_deleted == False)
        if term and norm:
            query = query.where(ParcelChina.track_id.ilike(f"%{norm}%"))
        total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
        pages = max(1, math.ceil(total / per_page))
        result = await db.execute(
            query.order_by(ParcelChina.created_at.desc())
            .offset((page - 1) * per_page).limit(per_page)
        )
        items = []
        for p in result.scalars().all():
            items.append({
                "id": p.id, "track_id": p.track_id, "status": "in_china",
                "weight_kg": None, "delivery_method": None,
                "client_name": None, "tps_code": None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
        return {"items": items, "total": total, "page": page, "pages": pages}

    if status_filter == "unresolved":
        all_items = await _unresolved_items(db)
        total = len(all_items)
        pages = max(1, math.ceil(total / per_page))
        start = (page - 1) * per_page
        return {"items": all_items[start:start + per_page], "total": total, "page": page, "pages": pages}

    if status_filter == "dushanbe":
        # «Физически в Душанбе»: принятые (received_dushanbe)
        # + неопознанные (resolved=false).
        all_items = await _dushanbe_items(
            db,
            select(ParcelDushanbe).where(
                ParcelDushanbe.status == "received_dushanbe",
                ParcelDushanbe.is_deleted == False,
            ),
        )
        all_items.extend(await _unresolved_items(db))
        all_items.sort(key=_created_at_sort_key, reverse=True)
        total = len(all_items)
        pages = max(1, math.ceil(total / per_page))
        start = (page - 1) * per_page
        return {"items": all_items[start:start + per_page], "total": total, "page": page, "pages": pages}

    if status_filter:
        query = select(ParcelDushanbe).where(
            ParcelDushanbe.status == status_filter,
            ParcelDushanbe.is_deleted == False,
        )
        all_items = await _dushanbe_items(db, query)
        total = len(all_items)
        pages = max(1, math.ceil(total / per_page))
        start = (page - 1) * per_page
        return {"items": all_items[start:start + per_page], "total": total, "page": page, "pages": pages}

    # No filter — combine China + Dushanbe + Unresolved
    all_items = []
    # Китай в общий список — кроме поиска по имени/TPS.
    if not (term and not norm):
        china_query = select(ParcelChina).where(
            ParcelChina.is_deleted == False
        )
        if term and norm:
            china_query = china_query.where(
                ParcelChina.track_id.ilike(f"%{norm}%")
            )
        china_result = await db.execute(
            china_query.order_by(ParcelChina.created_at.desc())
        )
        for p in china_result.scalars().all():
            all_items.append({
                "id": p.id, "track_id": p.track_id, "status": "in_china",
                "weight_kg": None, "delivery_method": None,
                "client_name": None, "tps_code": None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            })
    all_items.extend(await _dushanbe_items(
        db,
        select(ParcelDushanbe).where(
            ParcelDushanbe.is_deleted == False
        ),
    ))
    all_items.extend(await _unresolved_items(db))

    all_items.sort(key=_created_at_sort_key, reverse=True)
    total = len(all_items)
    pages = max(1, math.ceil(total / per_page))
    start = (page - 1) * per_page
    items = all_items[start:start + per_page]
    return {"items": items, "total": total, "page": page, "pages": pages}


@router.get("", response_model=dict)
async def list_parcels(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    status_filter: str | None = Query(
        None, alias="status",
    ),
    q: str | None = None,
    client_id: int | None = None,
    delivery_method: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(
        require_role("admin_dushanbe", "owner"),
    ),
):
    query = select(ParcelDushanbe).where(
        ParcelDushanbe.is_deleted == False
    )
    if q:
        # Поиск по трек-коду, ФИО или TPS-коду клиента.
        term = q.strip()
        conds = []
        norm = normalize_track(term)
        if norm:
            conds.append(
                ParcelDushanbe.track_id.ilike(f"%{norm}%")
            )
        client_ids = select(Client.id).where(
            or_(
                Client.full_name.ilike(f"%{term}%"),
                Client.tps_code.ilike(f"%{term}%"),
            )
        )
        conds.append(ParcelDushanbe.client_id.in_(client_ids))
        query = query.where(or_(*conds))
    if status_filter:
        query = query.where(
            ParcelDushanbe.status == status_filter,
        )
    if client_id:
        query = query.where(
            ParcelDushanbe.client_id == client_id,
        )
    if delivery_method:
        query = query.where(
            ParcelDushanbe.delivery_method
            == delivery_method,
        )
    if date_from:
        query = query.where(
            ParcelDushanbe.created_at >= date_from,
        )
    if date_to:
        query = query.where(
            ParcelDushanbe.created_at <= date_to,
        )

    sub = query.subquery()
    total = (await db.execute(
        select(func.count()).select_from(sub)
    )).scalar() or 0
    pages = max(1, math.ceil(total / per_page))

    sums = (await db.execute(
        select(
            func.coalesce(
                func.sum(sub.c.weight_kg), 0,
            ),
            func.coalesce(
                func.sum(sub.c.amount_due), 0,
            ),
        )
    )).one()
    total_weight, total_amount = sums

    result = await db.execute(
        query.order_by(ParcelDushanbe.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    items = [
        ParcelDushanbeResponse.model_validate(p)
        for p in result.scalars().all()
    ]
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
        "total_weight": total_weight,
        "total_amount": total_amount,
    }


@router.get("/track/{track_id}")
async def search_by_track(
    track_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    track = normalize_track(track_id)
    dushanbe = (await db.execute(
        select(ParcelDushanbe).where(
            ParcelDushanbe.track_id == track,
            ParcelDushanbe.is_deleted == False,
        )
    )).scalar_one_or_none()
    if dushanbe:
        return {"location": "dushanbe", "status": dushanbe.status, "track_id": track}
    unresolved = (await db.execute(
        select(UnresolvedParcel).where(
            UnresolvedParcel.track_id == track,
            UnresolvedParcel.resolved == False,
            UnresolvedParcel.is_deleted == False,
        )
    )).scalar_one_or_none()
    if unresolved:
        # Трек уже в Душанбе, но ещё не привязан к клиенту
        # (обрабатывается на месте).
        return {
            "location": "dushanbe",
            "status": "processing",
            "track_id": track,
        }
    china = (await db.execute(
        select(ParcelChina).where(
            ParcelChina.track_id == track,
            ParcelChina.is_deleted == False,
        )
    )).scalar_one_or_none()
    if china:
        return {"location": "china", "status": "in_china", "track_id": track}
    return {"location": None, "status": "not_found", "track_id": track}


@router.get("/my", dependencies=[Depends(verify_bot_secret)])
async def my_parcels(
    telegram_id: int,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    client = (await db.execute(
        select(Client).where(Client.telegram_id == telegram_id)
    )).scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    query = select(ParcelDushanbe).where(
        ParcelDushanbe.client_id == client.id,
        ParcelDushanbe.is_deleted == False,
    )
    if status_filter:
        query = query.where(ParcelDushanbe.status == status_filter)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.order_by(ParcelDushanbe.created_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    parcels = list(result.scalars().all())

    # Дата принятия в Китае по track_id (одним запросом).
    track_ids = [p.track_id for p in parcels]
    china_map: dict[str, datetime] = {}
    if track_ids:
        china_rows = await db.execute(
            select(ParcelChina.track_id, ParcelChina.created_at)
            .where(
                ParcelChina.track_id.in_(track_ids),
                ParcelChina.is_deleted == False,
            )
        )
        china_map = {t: c for t, c in china_rows.all()}

    # Дата выдачи для выданных посылок. Источник — issued_at
    # связанной выдачи (issuance_orders): это фактический момент
    # выдачи и он не меняется при последующих правках посылки,
    # в отличие от parcels_dushanbe.updated_at (обновляется при
    # любом изменении). updated_at используем лишь как запасной
    # вариант, если позиция выдачи не найдена.
    issued_ids = [p.id for p in parcels if p.status == "issued"]
    issued_map: dict[int, datetime] = {}
    if issued_ids:
        issued_rows = await db.execute(
            select(IssuanceItem.parcel_id, IssuanceOrder.issued_at)
            .join(
                IssuanceOrder,
                IssuanceItem.issuance_order_id == IssuanceOrder.id,
            )
            .where(IssuanceItem.parcel_id.in_(issued_ids))
        )
        for pid, issued_at in issued_rows.all():
            issued_map[pid] = issued_at

    items = []
    for p in parcels:
        issued_at = None
        if p.status == "issued":
            issued_at = issued_map.get(p.id) or p.updated_at
        items.append(MyParcelResponse(
            track_id=p.track_id,
            status=p.status,
            china_at=china_map.get(p.track_id),
            arrived_at=p.created_at,
            weight_kg=p.weight_kg,
            amount_due=p.amount_due,
            issued_at=issued_at,
            shelf=p.shelf,
        ))
    return {"items": items, "total": total, "page": page, "pages": pages, "per_page": per_page}


@router.get("/{parcel_id}", response_model=ParcelDushanbeResponse)
async def get_parcel(
    parcel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    parcel = await db.get(ParcelDushanbe, parcel_id)
    if not parcel or parcel.is_deleted:
        raise HTTPException(status_code=404, detail="Parcel not found")
    return parcel


@router.get("/{parcel_id}/issuance")
async def get_parcel_issuance(
    parcel_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    from app.models.issuance import IssuanceItem, IssuanceOrder

    item_res = await db.execute(
        select(IssuanceItem).where(IssuanceItem.parcel_id == parcel_id)
    )
    item = item_res.scalar_one_or_none()
    if not item:
        return None
    order = await db.get(IssuanceOrder, item.issuance_order_id)
    if not order:
        return None
    return {
        "order_id": order.id,
        "comment": order.comment,
        "issued_at": order.issued_at,
        "payment_status": order.payment_status,
        "payment_method": order.payment_method,
        "total_amount": float(order.total_amount or 0),
        "custom_price": float(item.custom_price) if item.custom_price is not None else None,
        "amount": float(item.amount or 0),
    }


@router.patch("/{parcel_id}/status", response_model=ParcelDushanbeResponse)
async def update_status(
    parcel_id: int,
    body: ParcelStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    if body.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    if body.status == "issued":
        raise HTTPException(
            status_code=400,
            detail="Использовать /api/issuance для выдачи",
        )
    parcel = await db.get(ParcelDushanbe, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    if parcel.status == "issued":
        raise HTTPException(
            status_code=400,
            detail="Нельзя изменить статус выданной посылки через этот эндпоинт",
        )
    before = {"status": parcel.status}
    parcel.status = body.status
    await log_action(
        db, staff_id=current_user.id, action="update_status",
        entity_type="parcel", entity_id=parcel.id,
        before=before, after={"status": body.status},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    return parcel


@router.patch("/{parcel_id}", response_model=ParcelDushanbeResponse)
async def update_parcel(
    parcel_id: int,
    body: ParcelUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    parcel = await db.get(ParcelDushanbe, parcel_id)
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    if parcel.status == "issued":
        raise HTTPException(
            status_code=400,
            detail="Нельзя изменить выданную посылку через этот эндпоинт",
        )
    update_fields = body.model_dump(exclude_unset=True)

    # Если итоговый delivery_method (новый или текущий) — truck,
    # итоговый volume_m3 (новый или текущий) обязателен и > 0.
    # Иначе amount_by_m3=0 и тариф молча падает до amount_by_kg
    # при следующей выдаче (недосчёт денег).
    final_method = update_fields.get("delivery_method", parcel.delivery_method)
    final_volume = update_fields.get("volume_m3", parcel.volume_m3)
    if final_method == "truck" and (final_volume is None or final_volume <= 0):
        raise HTTPException(
            status_code=400,
            detail="volume_m3 обязателен и должен быть > 0 для delivery_method='truck'",
        )

    before = {}
    after = {}
    for field, value in update_fields.items():
        if field == "status":
            if value not in VALID_STATUSES:
                raise HTTPException(status_code=400, detail="Invalid status")
            if value == "issued":
                raise HTTPException(
                    status_code=400,
                    detail="Использовать /api/issuance для выдачи",
                )
        before[field] = getattr(parcel, field)
        setattr(parcel, field, value)
        after[field] = value
    await log_action(
        db, staff_id=current_user.id, action="update_parcel",
        entity_type="parcel", entity_id=parcel.id,
        before=before, after=after, ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(parcel)
    return parcel
