from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Date, String, cast, exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.client import Client
from app.models.expense import Expense
from app.models.issuance import IssuanceItem, IssuanceOrder
from app.models.parcel_china import ParcelChina
from app.models.parcel_dushanbe import ParcelDushanbe
from app.models.staff import StaffUser
from app.models.unresolved import UnresolvedParcel
from app.api.deps import require_role

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _resolve_range(period: str, from_date: str | None, to_date: str | None):
    now = datetime.utcnow()
    if period == "custom" and from_date:
        start = datetime.fromisoformat(from_date)
        end = datetime.fromisoformat(to_date) if to_date else now
        return start, end
    if period == "all":
        return None, None
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0), None
    days = {"7d": 7, "30d": 30, "90d": 90}.get(period, 30)
    return now - timedelta(days=days), None


def _time_filter(col, start, end):
    clauses = []
    if start is not None:
        clauses.append(col >= start)
    if end is not None:
        clauses.append(col <= end)
    return clauses


@router.get("/overview")
async def overview(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)

    # Исключаем треки, физически добравшиеся до Душанбе (опознанные или нет),
    # иначе посылка считается дважды. EXISTS — чтобы планировщик попал в индекс.
    dushanbe_track_exists = exists().where(
        ParcelDushanbe.track_id == ParcelChina.track_id,
        ParcelDushanbe.is_deleted.is_(False),
    )
    unresolved_track_exists = exists().where(
        UnresolvedParcel.track_id == ParcelChina.track_id,
        UnresolvedParcel.resolved.is_(False),
    )
    # china_count/dushanbe_count — остатки на сейчас, не за период.
    china_count = (await db.execute(
        select(func.count(ParcelChina.id)).where(
            ParcelChina.is_deleted == False,
            ~dushanbe_track_exists,
            ~unresolved_track_exists,
        )
    )).scalar() or 0

    dushanbe_count = (await db.execute(
        select(func.count(ParcelDushanbe.id)).where(
            ParcelDushanbe.status == "received_dushanbe",
            ParcelDushanbe.is_deleted == False,
        )
    )).scalar() or 0

    unresolved_count_total = (await db.execute(
        select(func.count(UnresolvedParcel.id)).where(
            UnresolvedParcel.resolved.is_(False),
        )
    )).scalar() or 0

    dushanbe_count += unresolved_count_total

    # за период — только для added_count, не для остатков.
    unresolved_count = (await db.execute(
        select(func.count(UnresolvedParcel.id)).where(
            UnresolvedParcel.resolved.is_(False),
            *_time_filter(UnresolvedParcel.created_at, start, end),
        )
    )).scalar() or 0

    issued_count = (await db.execute(
        select(func.count(ParcelDushanbe.id)).where(
            ParcelDushanbe.status == "issued",
            ParcelDushanbe.is_deleted == False,
            *_time_filter(ParcelDushanbe.updated_at, start, end),
        )
    )).scalar() or 0

    china_added = (await db.execute(
        select(func.count(ParcelChina.id)).where(
            ParcelChina.is_deleted == False,
            *_time_filter(ParcelChina.created_at, start, end),
        )
    )).scalar() or 0
    dushanbe_added = (await db.execute(
        select(func.count(ParcelDushanbe.id)).where(
            ParcelDushanbe.is_deleted == False,
            *_time_filter(ParcelDushanbe.created_at, start, end),
        )
    )).scalar() or 0
    dushanbe_added += unresolved_count
    added_count = china_added + dushanbe_added

    total_weight = (await db.execute(
        select(func.sum(ParcelDushanbe.weight_kg)).where(
            ParcelDushanbe.is_deleted == False,
            *_time_filter(ParcelDushanbe.created_at, start, end),
        )
    )).scalar() or 0

    gross_revenue = (await db.execute(
        select(func.sum(IssuanceOrder.total_amount)).where(*_time_filter(IssuanceOrder.issued_at, start, end))
    )).scalar() or 0

    # Расходы вычитаются из gross_revenue → revenue. По категории — из net_by_method.
    expense_rows = (await db.execute(
        select(
            Expense.category,
            func.coalesce(func.sum(Expense.amount), 0),
        )
        .where(
            Expense.is_deleted.is_(False),
            *_time_filter(Expense.created_at, start, end),
        )
        .group_by(Expense.category)
    )).all()
    # Decimal до конца расчётов, float только на выходе через quantize(0.01).
    expense_by_category_dec = {
        c: Decimal(str(s)) for c, s in expense_rows
    }
    total_expenses_dec = sum(
        expense_by_category_dec.values(), Decimal("0")
    )
    gross_revenue_dec = Decimal(str(gross_revenue))
    revenue_val_dec = gross_revenue_dec - total_expenses_dec

    def _q(d: Decimal) -> float:
        return float(d.quantize(Decimal("0.01")))

    expense_by_category = {
        c: _q(v) for c, v in expense_by_category_dec.items()
    }
    total_expenses = _q(total_expenses_dec)
    revenue_val = _q(revenue_val_dec)

    new_clients = (await db.execute(
        select(func.count(Client.id)).where(*_time_filter(Client.created_at, start, end))
    )).scalar() or 0

    revenue_rows = (await db.execute(
        select(
            IssuanceItem.delivery_method,
            func.coalesce(func.sum(IssuanceItem.amount), 0),
        )
        .join(
            IssuanceOrder,
            IssuanceItem.issuance_order_id == IssuanceOrder.id,
        )
        .where(*_time_filter(IssuanceOrder.issued_at, start, end))
        .group_by(IssuanceItem.delivery_method)
    )).all()
    gross_revenue_by_method_dec = {m: Decimal(str(s)) for m, s in revenue_rows}
    gross_revenue_by_method = {
        m: _q(v) for m, v in gross_revenue_by_method_dec.items()
    }
    # net = gross − расходы той же категории. Если по методу не было выдач,
    # отрицательную «выручку» не показываем — убыток уходит в expense_by_category.
    net_revenue_by_method_dec = {}
    for cat, exp_dec in expense_by_category_dec.items():
        if cat in gross_revenue_by_method_dec:
            net_revenue_by_method_dec[cat] = (
                gross_revenue_by_method_dec[cat] - exp_dec
            )
    for m, v in gross_revenue_by_method_dec.items():
        net_revenue_by_method_dec.setdefault(m, v)
    net_revenue_by_method = {m: _q(v) for m, v in net_revenue_by_method_dec.items()}
    revenue_by_method = net_revenue_by_method  # legacy alias

    weight_rows = (await db.execute(
        select(
            ParcelDushanbe.delivery_method,
            func.coalesce(func.sum(ParcelDushanbe.weight_kg), 0),
        )
        .where(
            ParcelDushanbe.is_deleted == False,
            *_time_filter(ParcelDushanbe.created_at, start, end),
        )
        .group_by(ParcelDushanbe.delivery_method)
    )).all()
    weight_by_method = {m: float(s) for m, s in weight_rows}

    return {
        "china_count": china_count,
        "dushanbe_count": dushanbe_count,
        "issued_count": issued_count,
        "added_count": added_count,
        "china_added": china_added,
        "dushanbe_added": dushanbe_added,
        "total_weight": float(total_weight),
        "revenue": revenue_val,
        "gross_revenue": _q(gross_revenue_dec),
        "total_expenses": total_expenses,
        "expense_by_category": expense_by_category,
        "new_clients": new_clients,
        "revenue_by_method": revenue_by_method,
        "gross_revenue_by_method": gross_revenue_by_method,
        "net_revenue_by_method": net_revenue_by_method,
        "weight_by_method": weight_by_method,
    }


@router.get("/parcels-by-day")
async def parcels_by_day(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)
    now = datetime.utcnow()
    if start is None:
        start = now - timedelta(days=90)
    if end is None:
        end = now

    day_label = cast(ParcelChina.created_at, Date)
    china = (await db.execute(
        select(day_label.label("day"), func.count(ParcelChina.id))
        .where(
            ParcelChina.created_at.between(start, end),
            ParcelChina.is_deleted == False,
        )
        .group_by("day").order_by("day")
    )).all()

    day_label2 = cast(ParcelDushanbe.created_at, Date)
    dushanbe = (await db.execute(
        select(day_label2.label("day"), func.count(ParcelDushanbe.id))
        .where(
            ParcelDushanbe.created_at.between(start, end),
            ParcelDushanbe.is_deleted == False,
        )
        .group_by("day").order_by("day")
    )).all()

    combined = defaultdict(int)
    for d in china:
        combined[d[0]] += d[1]
    for d in dushanbe:
        combined[d[0]] += d[1]

    return [{"date": k, "count": v} for k, v in sorted(combined.items())]


@router.get("/revenue")
async def revenue(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)

    period_label = func.substr(func.cast(IssuanceOrder.issued_at, String), 1, 10)
    query = select(period_label.label("period"), func.sum(IssuanceOrder.total_amount))
    filters = _time_filter(IssuanceOrder.issued_at, start, end)
    if filters:
        query = query.where(*filters)
    result = (await db.execute(query.group_by("period").order_by("period"))).all()
    return [{"period": r[0], "amount": float(r[1])} for r in result]


@router.get("/top-clients")
async def top_clients(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("amount"),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)

    if sort_by in ("amount", "weight"):
        order_col = func.sum(IssuanceOrder.total_amount).desc() if sort_by == "amount" else func.sum(IssuanceOrder.total_weight).desc()
        query = (
            select(
                IssuanceOrder.client_id,
                func.sum(IssuanceOrder.total_amount).label("total_amount"),
                func.sum(IssuanceOrder.total_weight).label("total_weight"),
                func.count(IssuanceOrder.id).label("order_count"),
            )
        )
        filters = _time_filter(IssuanceOrder.issued_at, start, end)
        if filters:
            query = query.where(*filters)
        result = (await db.execute(
            query.group_by(IssuanceOrder.client_id).order_by(order_col).limit(limit)
        )).all()
        client_ids = [r.client_id for r in result]
        clients_map: dict[int, Client] = {}
        if client_ids:
            rows = (await db.execute(
                select(Client).where(Client.id.in_(client_ids))
            )).scalars().all()
            clients_map = {c.id: c for c in rows}
        clients = []
        for r in result:
            c = clients_map.get(r.client_id)
            clients.append({
                "client_id": r.client_id,
                "tps_code": c.tps_code if c else "?",
                "full_name": c.full_name if c else "?",
                "total_amount": float(r.total_amount),
                "total_weight": float(r.total_weight),
                "order_count": r.order_count,
            })
        return clients

    query = (
        select(
            ParcelDushanbe.client_id,
            func.count(ParcelDushanbe.id).label("parcel_count"),
        )
        .where(ParcelDushanbe.is_deleted == False)
    )
    filters = _time_filter(ParcelDushanbe.created_at, start, end)
    if filters:
        query = query.where(*filters)
    result = (await db.execute(
        query.group_by(ParcelDushanbe.client_id)
        .order_by(func.count(ParcelDushanbe.id).desc())
        .limit(limit)
    )).all()
    client_ids = [r.client_id for r in result]
    clients_map: dict[int, Client] = {}
    if client_ids:
        rows = (await db.execute(
            select(Client).where(Client.id.in_(client_ids))
        )).scalars().all()
        clients_map = {c.id: c for c in rows}
    clients = []
    for r in result:
        c = clients_map.get(r.client_id)
        clients.append({
            "client_id": r.client_id,
            "tps_code": c.tps_code if c else "?",
            "full_name": c.full_name if c else "?",
            "parcel_count": r.parcel_count,
        })
    return clients


@router.get("/stuck-parcels")
async def stuck_parcels(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    days: int = Query(14),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    start, end = _resolve_range(period, from_date, to_date)
    cutoff = datetime.utcnow() - timedelta(days=days)

    query = (
        select(ParcelDushanbe)
        .options(joinedload(ParcelDushanbe.client))
        .where(
            ParcelDushanbe.status == "received_dushanbe",
            ParcelDushanbe.is_deleted == False,
            ParcelDushanbe.created_at <= cutoff,
        )
    )
    filters = _time_filter(ParcelDushanbe.created_at, start, end)
    if filters:
        query = query.where(*filters)
    result = (await db.execute(
        query.order_by(ParcelDushanbe.created_at.asc())
    )).unique().scalars().all()
    items = []
    for p in result:
        c = p.client
        waiting = (datetime.utcnow() - p.created_at).days
        items.append({
            "parcel_id": p.id, "track_id": p.track_id,
            "client_id": p.client_id,
            "tps_code": c.tps_code if c else "?",
            "full_name": c.full_name if c else "?",
            "phone": c.phone if c else "?",
            "waiting_days": waiting,
        })
    return items


@router.get("/staff-activity")
async def staff_activity(
    period: str = Query("30d"),
    from_date: str | None = None,
    to_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("owner", "admin_china", "admin_dushanbe")),
):
    from app.models.audit import AuditLog
    start, end = _resolve_range(period, from_date, to_date)
    query = select(
        AuditLog.staff_id,
        func.count(AuditLog.id).label("action_count"),
    ).group_by(AuditLog.staff_id).order_by(func.count(AuditLog.id).desc())
    filters = _time_filter(AuditLog.created_at, start, end)
    if filters:
        query = query.where(*filters)
    result = (await db.execute(query)).all()
    staff_ids = [r.staff_id for r in result]
    staff_map: dict[int, StaffUser] = {}
    if staff_ids:
        rows = (await db.execute(
            select(StaffUser).where(StaffUser.id.in_(staff_ids))
        )).scalars().all()
        staff_map = {s.id: s for s in rows}
    items = []
    for r in result:
        staff = staff_map.get(r.staff_id)
        items.append({
            "staff_id": r.staff_id,
            "full_name": staff.full_name if staff else "?",
            "role": staff.role if staff else "?",
            "action_count": r.action_count,
        })
    return items
