import json
import secrets
from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Header, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.staff import StaffUser
from app.utils.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> StaffUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    staff_id = payload.get("sub")
    if not staff_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(StaffUser).where(StaffUser.id == int(staff_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    issued_at = payload.get("iat")
    if user.password_changed_at and issued_at is not None:
        if int(issued_at) < int(user.password_changed_at.timestamp()):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
    return user


def require_role(*roles: str) -> Callable:
    async def checker(current_user: StaffUser = Depends(get_current_user)) -> StaffUser:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return checker


def require_permission(perm: str) -> Callable:
    """owner проходит всегда; остальным нужен perm в списке
    permissions (JSON-массив строк), иначе 403."""
    async def checker(
        current_user: StaffUser = Depends(get_current_user),
    ) -> StaffUser:
        if current_user.role == "owner":
            return current_user
        try:
            perms = json.loads(current_user.permissions or "[]")
        except (ValueError, TypeError):
            perms = []
        if not isinstance(perms, list) or perm not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return checker


async def verify_bot_secret(x_bot_secret: str = Header(...)) -> None:
    if not secrets.compare_digest(x_bot_secret, settings.API_BOT_SECRET):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bot secret")


def to_naive_utc(dt: datetime | None) -> datetime | None:
    """Колонки DateTime в моделях — TIMESTAMP WITHOUT TIME ZONE. Фронт
    шлёт ISO-строки с суффиксом Z (tz-aware), asyncpg не сравнивает
    tz-aware с naive — фильтры по датам молча возвращают пусто.
    Нормализуем входящие даты в naive UTC, чтобы сравнение работало.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def get_client_ip(request: Request) -> str:
    direct_ip = request.client.host if request.client else "unknown"
    if direct_ip in settings.TRUSTED_PROXIES:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return direct_ip
