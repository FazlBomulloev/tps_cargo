import math
from datetime import datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.client import Client
from app.models.issuance import IssuanceItem, IssuanceOrder
from app.models.parcel_dushanbe import ParcelDushanbe
from app.models.staff import StaffUser
from app.models.tariff import Tariff
from app.schemas.issuance import IssuanceCreate, IssuanceItemResponse, IssuanceResponse
from app.services.audit_service import log_action
from app.api.deps import get_client_ip, require_role, to_naive_utc

router = APIRouter(prefix="/api/issuance", tags=["issuance"])


def _sort_clause(sort_by: str, sort_order: str):
    column = {
        "id": IssuanceOrder.id,
        "issued_at": IssuanceOrder.issued_at,
        "total_amount": IssuanceOrder.total_amount,
        "total_weight": IssuanceOrder.total_weight,
    }.get(sort_by, IssuanceOrder.issued_at)
    return column.desc() if sort_order == "desc" else column.asc()


@router.post("", response_model=IssuanceResponse, status_code=201)
async def create_issuance(
    body: IssuanceCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    if body.payment_status not in ("paid", "debt"):
        raise HTTPException(status_code=400, detail="payment_status must be 'paid' or 'debt'")
    if body.payment_status == "paid" and body.payment_method not in ("cash", "transfer"):
        raise HTTPException(status_code=400, detail="payment_method must be 'cash' or 'transfer' when paid")

    total_weight = Decimal(0)
    total_amount = Decimal(0)
    items_data = []

    custom_map = body.custom_prices or {}

    # Блокируем строки посылок на время транзакции (row-level lock),
    # чтобы два параллельных запроса на одну и ту же посылку не могли
    # оба пройти проверку статуса и создать дублирующую выдачу.
    locked_parcels = (await db.execute(
        select(ParcelDushanbe)
        .where(ParcelDushanbe.id.in_(body.parcel_ids))
        .with_for_update()
    )).scalars().all()
    parcels_by_id = {p.id: p for p in locked_parcels}

    for pid in body.parcel_ids:
        parcel = parcels_by_id.get(pid)
        if not parcel or parcel.is_deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Посылка {pid} не найдена",
            )
        if parcel.status == "issued":
            raise HTTPException(
                status_code=400,
                detail=f"Посылка {pid} уже выдана",
            )

        tariff = (await db.execute(
            select(Tariff)
            .where(
                Tariff.method == parcel.delivery_method,
                Tariff.is_active == True,
            )
            .order_by(Tariff.created_at.desc())
            .limit(1)
        )).scalar_one_or_none()
        if not tariff:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Нет активного тарифа"
                    f" для {parcel.delivery_method}"
                ),
            )

        custom = custom_map.get(parcel.id)
        if custom is not None:
            try:
                amount = Decimal(custom)
            except (InvalidOperation, TypeError, ValueError):
                raise HTTPException(
                    status_code=400,
                    detail=f"Некорректная custom_price для посылки {parcel.id}",
                )
            if amount < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"custom_price для посылки {parcel.id} не может быть отрицательной",
                )
        elif parcel.delivery_method == "avia":
            amount = parcel.weight_kg * tariff.price_per_kg
        else:
            amount_by_kg = (
                parcel.weight_kg * tariff.price_per_kg
            )
            amount_by_m3 = (
                (parcel.volume_m3 or Decimal(0))
                * (tariff.price_per_m3 or Decimal(0))
            )
            amount = max(amount_by_kg, amount_by_m3)

        parcel.status = "issued"
        parcel.amount_due = amount
        # IN-25: tariff_snapshot хранит только price_per_kg (legacy).
        # tariff_snapshot_data — полный снапшот {kg, m3, currency},
        # нужен для truck (price_per_m3 теряется в старом поле).
        parcel.tariff_snapshot = tariff.price_per_kg
        parcel.tariff_snapshot_data = {
            "kg": str(tariff.price_per_kg),
            "m3": str(tariff.price_per_m3) if tariff.price_per_m3 is not None else None,
            "currency": tariff.currency,
        }

        total_weight += parcel.weight_kg
        total_amount += amount
        items_data.append({
            "parcel": parcel,
            "tariff": tariff,
            "amount": amount,
            "custom_price": custom,
        })

    order = IssuanceOrder(
        client_id=body.client_id,
        staff_id=current_user.id,
        total_weight=total_weight,
        total_amount=total_amount,
        payment_status=body.payment_status,
        payment_method=body.payment_method,
        comment=body.comment,
    )
    db.add(order)
    await db.flush()

    items = []
    for d in items_data:
        p = d["parcel"]
        item = IssuanceItem(
            issuance_order_id=order.id,
            parcel_id=p.id,
            weight_kg=p.weight_kg,
            volume_m3=p.volume_m3,
            delivery_method=p.delivery_method,
            tariff_applied=d["tariff"].price_per_kg,
            custom_price=d["custom_price"],
            amount=d["amount"],
            tariff_snapshot_data=p.tariff_snapshot_data,
        )
        db.add(item)
        items.append(item)

    await log_action(
        db,
        staff_id=current_user.id,
        action="issue_parcels",
        entity_type="issuance",
        entity_id=order.id,
        after={
            "client_id": body.client_id,
            "parcel_count": len(body.parcel_ids),
            "total_amount": str(total_amount),
            "has_custom_prices": bool(
                body.custom_prices
            ),
        },
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(order)
    for item in items:
        await db.refresh(item)

    return IssuanceResponse(
        id=order.id,
        client_id=order.client_id,
        staff_id=order.staff_id,
        total_weight=order.total_weight,
        total_amount=order.total_amount,
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        comment=order.comment,
        issued_at=order.issued_at,
        items=[
            IssuanceItemResponse.model_validate(i)
            for i in items
        ],
    )


@router.get("", response_model=dict)
async def list_issuance(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    client_id: int | None = None,
    search: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_by: str = Query("issued_at", regex="^(id|issued_at|total_amount|total_weight)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(
        require_role("admin_dushanbe", "owner"),
    ),
):
    query = select(IssuanceOrder)
    if client_id:
        query = query.where(
            IssuanceOrder.client_id == client_id,
        )
    df = to_naive_utc(date_from)
    dt_to = to_naive_utc(date_to)
    if df:
        query = query.where(IssuanceOrder.issued_at >= df)
    if dt_to:
        query = query.where(IssuanceOrder.issued_at <= dt_to)
    if search:
        s = search.strip()
        conditions = []
        if s.isdigit():
            conditions.append(
                IssuanceOrder.id == int(s),
            )
        client_ids = select(Client.id).where(
            Client.tps_code.ilike(f"%{s}%"),
        )
        conditions.append(
            IssuanceOrder.client_id.in_(client_ids),
        )
        order_ids = (
            select(IssuanceItem.issuance_order_id)
            .join(
                ParcelDushanbe,
                ParcelDushanbe.id
                == IssuanceItem.parcel_id,
            )
            .where(
                ParcelDushanbe.track_id.ilike(
                    f"%{s}%",
                ),
            )
        )
        conditions.append(
            IssuanceOrder.id.in_(order_ids),
        )
        query = query.where(or_(*conditions))

    total = (await db.execute(
        select(func.count())
        .select_from(query.subquery())
    )).scalar() or 0
    pages = max(1, math.ceil(total / per_page))
    result = await db.execute(
        query.options(
            joinedload(IssuanceOrder.client),
            joinedload(IssuanceOrder.items).joinedload(IssuanceItem.parcel),
        )
        .order_by(_sort_clause(sort_by, sort_order))
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    orders = result.unique().scalars().all()
    items_out = []
    for order in orders:
        client = order.client
        item_responses = []
        for i in order.items:
            ir = IssuanceItemResponse.model_validate(i)
            ir.track_id = i.parcel.track_id if i.parcel else None
            item_responses.append(ir)
        items_out.append(IssuanceResponse(
            id=order.id,
            client_id=order.client_id,
            client_name=client.full_name if client else None,
            tps_code=client.tps_code if client else None,
            staff_id=order.staff_id,
            total_weight=order.total_weight,
            total_amount=order.total_amount,
            payment_status=order.payment_status,
            payment_method=order.payment_method,
            comment=order.comment,
            issued_at=order.issued_at,
            items=item_responses,
        ))
    return {
        "items": items_out,
        "total": total,
        "page": page,
        "pages": pages,
        "per_page": per_page,
    }


@router.get("/{order_id}", response_model=IssuanceResponse)
async def get_issuance(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    order = (await db.execute(
        select(IssuanceOrder)
        .options(
            joinedload(IssuanceOrder.client),
            joinedload(IssuanceOrder.items).joinedload(IssuanceItem.parcel),
        )
        .where(IssuanceOrder.id == order_id)
    )).unique().scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Issuance order not found")
    client = order.client
    item_responses = []
    for i in order.items:
        ir = IssuanceItemResponse.model_validate(i)
        ir.track_id = i.parcel.track_id if i.parcel else None
        item_responses.append(ir)
    return IssuanceResponse(
        id=order.id,
        client_id=order.client_id,
        client_name=client.full_name if client else None,
        tps_code=client.tps_code if client else None,
        staff_id=order.staff_id,
        total_weight=order.total_weight,
        total_amount=order.total_amount,
        payment_status=order.payment_status,
        payment_method=order.payment_method,
        comment=order.comment,
        issued_at=order.issued_at,
        items=item_responses,
    )
