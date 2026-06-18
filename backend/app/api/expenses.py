import math
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.expense import Expense
from app.models.staff import StaffUser
from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.services.audit_service import log_action
from app.api.deps import get_client_ip, require_permission, to_naive_utc

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

VALID_CATEGORIES = {"avia", "truck"}


@router.post("", response_model=ExpenseResponse, status_code=201)
async def create_expense(
    body: ExpenseCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_permission("expenses")),
):
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail="category must be 'avia' or 'truck'",
        )
    expense = Expense(
        amount=body.amount,
        category=body.category,
        comment=(body.comment or "").strip() or None,
        created_by=current_user.id,
    )
    db.add(expense)
    await db.flush()
    await log_action(
        db,
        staff_id=current_user.id,
        action="create_expense",
        entity_type="expense",
        entity_id=expense.id,
        after={
            "amount": str(expense.amount),
            "category": expense.category,
        },
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse(
        id=expense.id,
        amount=expense.amount,
        category=expense.category,
        comment=expense.comment,
        created_by=expense.created_by,
        created_by_name=current_user.full_name,
        created_at=expense.created_at,
    )


@router.get("", response_model=dict)
async def list_expenses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_permission("expenses")),
):
    query = select(Expense).where(Expense.is_deleted.is_(False))
    if category and category in VALID_CATEGORIES:
        query = query.where(Expense.category == category)
    df = to_naive_utc(date_from)
    dt_to = to_naive_utc(date_to)
    if df:
        query = query.where(Expense.created_at >= df)
    if dt_to:
        query = query.where(Expense.created_at <= dt_to)

    # Используем один subquery и ссылаемся на его колонки — иначе
    # SQLAlchemy делает CROSS JOIN с основной таблицей и сумма
    # умножается на количество строк (баг был раньше: видно 2 строки
    # на 21 TJS, total_sum показывал ~25 000 TJS).
    subq = query.subquery()
    total = (await db.execute(
        select(func.count()).select_from(subq)
    )).scalar() or 0
    pages = max(1, math.ceil(total / per_page))

    total_sum = (await db.execute(
        select(func.coalesce(func.sum(subq.c.amount), 0))
    )).scalar() or Decimal(0)

    result = await db.execute(
        query.order_by(Expense.created_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    rows = result.scalars().all()

    # Подтягиваем ФИО сотрудников одним запросом, чтобы не делать
    # N+1 по числу строк на странице.
    staff_ids = {r.created_by for r in rows}
    staff_map: dict[int, str] = {}
    if staff_ids:
        staff_rows = (await db.execute(
            select(StaffUser.id, StaffUser.full_name)
            .where(StaffUser.id.in_(staff_ids))
        )).all()
        staff_map = {sid: name for sid, name in staff_rows}

    items = [
        ExpenseResponse(
            id=r.id,
            amount=r.amount,
            category=r.category,
            comment=r.comment,
            created_by=r.created_by,
            created_by_name=staff_map.get(r.created_by),
            created_at=r.created_at,
        )
        for r in rows
    ]
    return {
        "items": items,
        "total": total,
        "pages": pages,
        "page": page,
        "per_page": per_page,
        "total_sum": float(total_sum),
    }


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_permission("expenses")),
):
    expense = await db.get(Expense, expense_id)
    if not expense or expense.is_deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    await log_action(
        db,
        staff_id=current_user.id,
        action="delete_expense",
        entity_type="expense",
        entity_id=expense.id,
        before={
            "amount": str(expense.amount),
            "category": expense.category,
        },
        ip_address=get_client_ip(request),
    )
    expense.is_deleted = True
    expense.deleted_at = func.now()
    expense.deleted_by = current_user.id
    await db.commit()
    return {"detail": "Expense deleted", "id": expense_id}
