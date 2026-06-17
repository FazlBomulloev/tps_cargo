from enum import StrEnum

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.setting import Setting
from app.models.staff import StaffUser
from app.services.audit_service import log_action
from app.api.deps import get_client_ip, require_role, get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingKey(StrEnum):
    # IN-24: реально используемые ключи — tariffs/support (см.
    # src/handlers/client.py: get_setting('tariffs'), get_setting('support')).
    # Остальные зарезервированы под будущие настройки компании.
    COMPANY_NAME = "company_name"
    CURRENCY = "currency"
    CHANNEL_REQUIRED = "channel_required"
    TARIFFS = "tariffs"
    SUPPORT = "support"


class SettingValue(BaseModel):
    value: str


@router.get("")
async def list_settings(
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    result = await db.execute(select(Setting))
    return {s.key: s.value for s in result.scalars().all()}


@router.get("/{key}")
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    if key not in SettingKey.__members__.values():
        raise HTTPException(status_code=400, detail="Unknown setting key")
    s = await db.get(Setting, key)
    if not s:
        raise HTTPException(status_code=404, detail="Setting not found")
    return {"key": s.key, "value": s.value}


@router.put("/{key}")
async def update_setting(
    key: str,
    body: SettingValue,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(require_role("admin_dushanbe", "owner")),
):
    if key not in SettingKey.__members__.values():
        raise HTTPException(status_code=400, detail="Unknown setting key")
    s = await db.get(Setting, key)
    if s:
        before = {"value": s.value}
        s.value = body.value
        s.updated_by = current_user.id
        s.updated_at = func.now()
    else:
        before = None
        s = Setting(key=key, value=body.value, updated_by=current_user.id)
        db.add(s)
    await log_action(
        db, staff_id=current_user.id, action="update_setting",
        entity_type="setting", before=before, after={"key": key, "value": body.value},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    return {"key": key, "value": body.value}
