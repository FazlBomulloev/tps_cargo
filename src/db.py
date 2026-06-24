import logging
import re
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from src.config import DATABASE_URL
from src.models import (
    Base,
    Client,
    IssuanceItem,
    IssuanceOrder,
    ParcelChina,
    ParcelDushanbe,
    Setting,
    Tariff,
    UnresolvedParcel,
    Warehouse,
)

log = logging.getLogger(__name__)

_engine_kwargs = {"echo": False}
if not DATABASE_URL.startswith("sqlite"):
    _engine_kwargs.update(
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
engine = create_async_engine(DATABASE_URL, **_engine_kwargs)
async_session = async_sessionmaker(
    engine, expire_on_commit=False,
)

RESERVED_NUMBERS = {
    7, 111, 222, 333, 444, 555, 666, 777, 888, 999,
}


class ClientStatus:
    """Канонические значения Client.status (BO-29). Используй вместо
    голых строк в новом коде; существующие места — см. TODO рядом."""
    ACTIVE = "active"
    BLOCKED = "blocked"
    DELETED = "deleted"


def _mask_db_url(url: str) -> str:
    return re.sub(r"://([^:]+):[^@]+@", r"://\1:***@", url)


def normalize_track(value: str) -> str:
    # Mirror of backend/app/utils/track_normalize.py — держать в sync вручную.
    value = str(value).upper().strip()
    return re.sub(r"[^A-Z0-9]+", "", value)


async def init_db():
    """Не создаёт таблицы (это делает backend/alembic) — только
    проверяет, что схема уже накатана, и логирует цель подключения."""
    masked = _mask_db_url(DATABASE_URL)
    async with engine.connect() as conn:
        def _check(sync_conn):
            return inspect(sync_conn).has_table("clients")
        has_clients = await conn.run_sync(_check)
        if not has_clients:
            log.error(
                "Таблицы БД не найдены. Накатите миграции "
                "(alembic upgrade head) в backend.",
            )
            raise RuntimeError("DB not initialized")
    log.info("БД подключена: %s", masked)


# ── TPS code generation ──

def _format_tps_code(num: int) -> str:
    if num < 1000:
        return f"TPS{num:03d}"
    return f"TPS{num}"


def _parse_tps_number(code: str) -> int | None:
    m = re.fullmatch(
        r"TPS(\d+)", (code or "").strip().upper(),
    )
    return int(m.group(1)) if m else None


async def _next_tps_code(s) -> str:
    result = await s.execute(select(Client.tps_code))
    used = {
        n for (code,) in result.all()
        if (n := _parse_tps_number(code)) is not None
    }
    num = 1
    while num in used or num in RESERVED_NUMBERS:
        num += 1
    return _format_tps_code(num)


# ── Clients ──

async def get_client(
    telegram_id: int,
) -> Client | None:
    async with async_session() as s:
        result = await s.execute(
            select(Client).where(
                Client.telegram_id == telegram_id
            )
        )
        return result.scalar_one_or_none()


async def get_broadcast_recipients() -> list[int]:
    """Telegram-id всех клиентов, кому можно слать рассылку.
    Исключаем deleted; blocked оставляем — Telegram сам отвергнет."""
    async with async_session() as s:
        result = await s.execute(
            select(Client.telegram_id).where(
                Client.status != ClientStatus.DELETED,
            )
        )
        return [tid for (tid,) in result.all() if tid]


async def create_client(
    telegram_id: int, full_name: str,
    phone: str, lang: str = "ru",
) -> str:
    async with async_session() as s:
        existing = (await s.execute(
            select(Client).where(
                Client.telegram_id == telegram_id
            )
        )).scalar_one_or_none()
        if existing:
            return existing.tps_code

        for _ in range(50):
            tps_code = await _next_tps_code(s)
            s.add(Client(
                telegram_id=telegram_id,
                tps_code=tps_code,
                full_name=full_name,
                phone=phone,
                lang=lang,
            ))
            try:
                await s.commit()
                return tps_code
            except IntegrityError:
                await s.rollback()
                existing = (await s.execute(
                    select(Client).where(
                        Client.telegram_id == telegram_id
                    )
                )).scalar_one_or_none()
                if existing:
                    return existing.tps_code
        raise RuntimeError(
            "Не удалось сгенерировать уникальный TPS код"
        )


async def update_client_lang(
    telegram_id: int, lang: str,
):
    async with async_session() as s:
        result = await s.execute(
            select(Client).where(
                Client.telegram_id == telegram_id
            )
        )
        client = result.scalar_one_or_none()
        if client:
            client.lang = lang
            await s.commit()


async def update_client_field(
    telegram_id: int, field: str, value: str,
):
    allowed = {"full_name", "phone"}
    if field not in allowed:
        return
    async with async_session() as s:
        result = await s.execute(
            select(Client).where(
                Client.telegram_id == telegram_id
            )
        )
        client = result.scalar_one_or_none()
        if client:
            setattr(client, field, value)
            await s.commit()


async def get_client_by_tps_code(
    tps_code: str,
) -> Client | None:
    code = tps_code.strip().upper()
    async with async_session() as s:
        result = await s.execute(
            select(Client).where(
                Client.tps_code == code
            )
        )
        return result.scalar_one_or_none()


# ── Parcels China ──

async def find_in_china(track: str) -> bool:
    code = normalize_track(track)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelChina).where(
                ParcelChina.track_id == code,
                ParcelChina.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none() is not None


# ── Parcels Dushanbe ──

async def find_in_dushanbe(
    track: str,
) -> ParcelDushanbe | None:
    code = normalize_track(track)
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.track_id == code,
                ParcelDushanbe.is_deleted.is_(False),
            )
        )
        return result.scalar_one_or_none()


# ── Unresolved (неразобранные) ──

async def find_in_unresolved(track: str) -> bool:
    """Трек есть среди неразобранных (уже в Душанбе)."""
    code = normalize_track(track)
    async with async_session() as s:
        result = await s.execute(
            select(UnresolvedParcel).where(
                UnresolvedParcel.track_id == code,
                UnresolvedParcel.resolved.is_(False),
            )
        )
        return result.scalar_one_or_none() is not None


async def get_unresolved_info(track: str) -> dict | None:
    """Детали неопознанной посылки по треку или None."""
    code = normalize_track(track)
    async with async_session() as s:
        u = (await s.execute(
            select(UnresolvedParcel).where(
                UnresolvedParcel.track_id == code,
                UnresolvedParcel.resolved.is_(False),
            )
        )).scalar_one_or_none()
        if not u:
            return None
        china_at = (await s.execute(
            select(ParcelChina.created_at).where(
                ParcelChina.track_id == code,
                ParcelChina.is_deleted.is_(False),
            )
        )).scalar_one_or_none()
        est = None
        if u.weight_kg is not None and u.delivery_method:
            tariff = (await s.execute(
                select(Tariff)
                .where(
                    Tariff.method == u.delivery_method,
                    Tariff.is_active.is_(True),
                )
                .order_by(Tariff.created_at.desc())
                .limit(1)
            )).scalar_one_or_none()
            est = _estimate_amount(u, tariff)
        return {
            "china_at": china_at,
            "arrived_at": u.created_at,
            "weight_kg": u.weight_kg,
            "amount_estimated": est,
        }


def _estimate_amount(parcel, tariff) -> Decimal | None:
    """Ориентировочная стоимость по активному тарифу
    (та же формула, что и при выдаче). None, если тарифа нет."""
    if tariff is None:
        return None
    if parcel.delivery_method == "avia":
        return parcel.weight_kg * tariff.price_per_kg
    by_kg = parcel.weight_kg * tariff.price_per_kg
    by_m3 = (
        (parcel.volume_m3 or Decimal(0))
        * (tariff.price_per_m3 or Decimal(0))
    )
    return max(by_kg, by_m3)


async def get_parcels_by_client(
    tps_code: str,
) -> list[dict]:
    """Посылки клиента с данными по этапам для «Мои посылки».

    Возвращает по каждой посылке: трек, статус, дату принятия
    в Китае, дату прибытия в Душанбе, вес, сумму к оплате и
    дату выдачи. Пустые поля = None (бот их не показывает).
    """
    code = tps_code.strip().upper()
    async with async_session() as s:
        client = (await s.execute(
            select(Client).where(
                Client.tps_code == code
            )
        )).scalar_one_or_none()
        if not client:
            return []
        parcels = list((await s.execute(
            select(ParcelDushanbe)
            .where(
                ParcelDushanbe.client_id == client.id,
                ParcelDushanbe.is_deleted.is_(False),
            )
            .order_by(ParcelDushanbe.created_at.desc())
        )).scalars().all())
        if not parcels:
            return []

        track_ids = [p.track_id for p in parcels]
        china_rows = (await s.execute(
            select(
                ParcelChina.track_id,
                ParcelChina.created_at,
            ).where(
                ParcelChina.track_id.in_(track_ids),
                ParcelChina.is_deleted.is_(False),
            )
        )).all()
        china_map = {t: c for t, c in china_rows}

        # issued_at из выдачи надёжнее updated_at (меняется на любой правке).
        issued_ids = [
            p.id for p in parcels if p.status == "issued"
        ]
        issued_map: dict[int, object] = {}
        if issued_ids:
            rows = (await s.execute(
                select(
                    IssuanceItem.parcel_id,
                    IssuanceOrder.issued_at,
                )
                .join(
                    IssuanceOrder,
                    IssuanceItem.issuance_order_id
                    == IssuanceOrder.id,
                )
                .where(
                    IssuanceItem.parcel_id.in_(issued_ids)
                )
            )).all()
            for pid, issued_at in rows:
                issued_map[pid] = issued_at

        # Последний активный тариф на метод — для оценки невыданных.
        tariff_rows = (await s.execute(
            select(Tariff)
            .where(Tariff.is_active.is_(True))
            .order_by(Tariff.created_at.desc())
        )).scalars().all()
        tariff_map: dict[str, object] = {}
        for t in tariff_rows:
            tariff_map.setdefault(t.method, t)

        items = []
        for p in parcels:
            issued_at = None
            if p.status == "issued":
                issued_at = (
                    issued_map.get(p.id) or p.updated_at
                )
            est = None
            if p.amount_due is None and p.status != "issued":
                est = _estimate_amount(
                    p, tariff_map.get(p.delivery_method)
                )
            items.append({
                "track_id": p.track_id,
                "status": p.status,
                "china_at": china_map.get(p.track_id),
                "arrived_at": p.created_at,
                "weight_kg": p.weight_kg,
                "amount_due": p.amount_due,
                "amount_estimated": est,
                "issued_at": issued_at,
                "shelf": p.shelf,
                "intake_group_id": p.intake_group_id,
            })
        return items


# ── Notifications ──

async def get_unnotified_parcels() -> list[dict]:
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.notified_at.is_(None),
                ParcelDushanbe.is_deleted.is_(False),
            )
        )
        parcels = result.scalars().all()
        items = []
        for p in parcels:
            client = (await s.execute(
                select(Client).where(
                    Client.id == p.client_id
                )
            )).scalar_one_or_none()
            if client:
                items.append({
                    "id": p.id,
                    "track_id": p.track_id,
                    "telegram_id": client.telegram_id,
                    "lang": client.lang or "ru",
                })
        return items


async def mark_notified(parcel_id: int):
    """Помечает посылку уведомлённой по primary key (а не track_id),
    чтобы не зависеть от soft-delete/уникальности трека (BO-005)."""
    async with async_session() as s:
        result = await s.execute(
            select(ParcelDushanbe).where(
                ParcelDushanbe.id == parcel_id,
                ParcelDushanbe.is_deleted.is_(False),
            )
        )
        parcel = result.scalar_one_or_none()
        if parcel:
            parcel.notified_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await s.commit()


# ── Warehouses ──

async def list_warehouses() -> list[Warehouse]:
    async with async_session() as s:
        result = await s.execute(
            select(Warehouse)
            .where(Warehouse.is_active.is_(True))
            .order_by(Warehouse.id)
        )
        return list(result.scalars().all())


async def get_warehouse(
    wid: int,
) -> Warehouse | None:
    async with async_session() as s:
        return await s.get(Warehouse, wid)


# ── Settings ──

async def get_setting(key: str) -> str | None:
    async with async_session() as s:
        result = await s.get(Setting, key)
        return result.value if result else None
