import logging
import re

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client

log = logging.getLogger(__name__)

RESERVED_NUMBERS = {7, 111, 222, 333, 444, 555, 666, 777, 888, 999}
MAX_TPS_CODE_ATTEMPTS = 5


def format_tps_code(num: int) -> str:
    if num < 1000:
        return f"TPS{num:03d}"
    return f"TPS{num}"


def parse_tps_number(code: str) -> int | None:
    m = re.fullmatch(r"TPS(\d+)", (code or "").strip().upper())
    return int(m.group(1)) if m else None


async def generate_tps_code(session: AsyncSession) -> str:
    result = await session.execute(select(Client.tps_code))
    used = {n for (code,) in result.all() if (n := parse_tps_number(code)) is not None}
    num = 1
    while num in used or num in RESERVED_NUMBERS:
        num += 1
    return format_tps_code(num)


async def create_client_with_tps_code(session: AsyncSession, build_client) -> Client:
    """Генерирует tps_code и сохраняет клиента с retry на IntegrityError.

    Две параллельные регистрации могут вычислить один и тот же
    свободный tps_code (race condition между select и insert).
    UNIQUE-индекс на clients.tps_code тогда бросит IntegrityError —
    в этом случае пересчитываем код и пробуем снова, до
    MAX_TPS_CODE_ATTEMPTS раз.

    `build_client(tps_code: str) -> Client` создаёт несохранённый
    объект Client с этим кодом.
    """
    last_error: IntegrityError | None = None
    for attempt in range(1, MAX_TPS_CODE_ATTEMPTS + 1):
        tps_code = await generate_tps_code(session)
        client = build_client(tps_code)
        session.add(client)
        try:
            await session.commit()
            return client
        except IntegrityError as exc:
            await session.rollback()
            last_error = exc
            log.warning(
                "Коллизия tps_code=%s при регистрации клиента, попытка %s/%s",
                tps_code, attempt, MAX_TPS_CODE_ATTEMPTS,
            )
    raise last_error
