import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import async_session, engine, Base
from app.models import *  # noqa: F401,F403 — register all models
from app.models.staff import StaffUser
from app.models.warehouse import Warehouse
from app.models.tariff import Tariff
from app.utils.security import hash_password

from app.api.auth import router as auth_router
from app.api.staff import router as staff_router
from app.api.clients import router as clients_router
from app.api.parcels import router as parcels_router
from app.api.unresolved import router as unresolved_router
from app.api.issuance import router as issuance_router
from app.api.warehouses import router as warehouses_router
from app.api.tariffs import router as tariffs_router
from app.api.settings import router as settings_router
from app.api.stats import router as stats_router
from app.api.audit import router as audit_router
from app.api.notifications import router as notifications_router
from app.api.expenses import router as expenses_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Cargo TPS API", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://195.133.21.15:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(staff_router)
app.include_router(clients_router)
app.include_router(parcels_router)
app.include_router(unresolved_router)
app.include_router(issuance_router)
app.include_router(warehouses_router)
app.include_router(tariffs_router)
app.include_router(settings_router)
app.include_router(stats_router)
app.include_router(audit_router)
app.include_router(notifications_router)
app.include_router(expenses_router)


@app.on_event("startup")
async def on_startup():
    Path("data").mkdir(exist_ok=True)
    Path("data/avatars").mkdir(exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _migrate_staff_columns()
    await _migrate_parcel_soft_delete_columns()
    await _migrate_parcel_shelf_column()
    await _seed_owner()
    await _seed_warehouses()
    await _seed_tariffs()
    log.info("Cargo TPS API started")


async def _migrate_staff_columns():
    from sqlalchemy import text, inspect as sa_inspect
    async with engine.begin() as conn:
        def _check_and_add(connection):
            inspector = sa_inspect(connection)
            columns = [c["name"] for c in inspector.get_columns("staff_users")]
            stmts = []
            if "avatar_url" not in columns:
                stmts.append("ALTER TABLE staff_users ADD COLUMN avatar_url VARCHAR(500)")
            if "permissions" not in columns:
                stmts.append("ALTER TABLE staff_users ADD COLUMN permissions TEXT")
            for stmt in stmts:
                connection.execute(text(stmt))
        await conn.run_sync(_check_and_add)


async def _migrate_parcel_soft_delete_columns():
    """Добавляет колонки мягкого удаления в существующие таблицы
    посылок. Base.metadata.create_all не меняет уже созданные
    таблицы, поэтому недостающие колонки добавляем вручную, как
    и для staff_users. Безопасно для живых данных (только ADD)."""
    from sqlalchemy import text, inspect as sa_inspect
    async with engine.begin() as conn:
        def _check_and_add(connection):
            inspector = sa_inspect(connection)
            # На Postgres булев DEFAULT — false, на SQLite — 0.
            is_pg = connection.dialect.name == "postgresql"
            false_lit = "false" if is_pg else "0"
            for table in ("parcels_dushanbe", "parcels_china"):
                columns = [
                    c["name"]
                    for c in inspector.get_columns(table)
                ]
                stmts = []
                if "is_deleted" not in columns:
                    stmts.append(
                        f"ALTER TABLE {table} ADD COLUMN "
                        f"is_deleted BOOLEAN NOT NULL "
                        f"DEFAULT {false_lit}"
                    )
                if "deleted_at" not in columns:
                    stmts.append(
                        f"ALTER TABLE {table} ADD COLUMN "
                        "deleted_at TIMESTAMP"
                    )
                if "deleted_by" not in columns:
                    stmts.append(
                        f"ALTER TABLE {table} ADD COLUMN "
                        "deleted_by INTEGER"
                    )
                for stmt in stmts:
                    connection.execute(text(stmt))
                    log.info("Миграция: %s", stmt)
        await conn.run_sync(_check_and_add)


async def _migrate_parcel_shelf_column():
    """Добавляет колонку «полка» (shelf) в parcels_dushanbe.
    Безопасно для живых данных (только ADD COLUMN)."""
    from sqlalchemy import text, inspect as sa_inspect
    async with engine.begin() as conn:
        def _check_and_add(connection):
            inspector = sa_inspect(connection)
            columns = [
                c["name"]
                for c in inspector.get_columns("parcels_dushanbe")
            ]
            if "shelf" not in columns:
                stmt = (
                    "ALTER TABLE parcels_dushanbe "
                    "ADD COLUMN shelf VARCHAR(20)"
                )
                connection.execute(text(stmt))
                log.info("Миграция: %s", stmt)
        await conn.run_sync(_check_and_add)


async def _seed_owner():
    async with async_session() as db:
        result = await db.execute(select(StaffUser).where(StaffUser.login == settings.OWNER_LOGIN))
        if result.scalar_one_or_none():
            return
        owner = StaffUser(
            full_name=settings.OWNER_FULL_NAME,
            login=settings.OWNER_LOGIN,
            password_hash=hash_password(settings.OWNER_PASSWORD),
            role="owner",
        )
        db.add(owner)
        await db.commit()
        log.info("Owner account created: %s", settings.OWNER_LOGIN)


async def _seed_warehouses():
    async with async_session() as db:
        result = await db.execute(select(Warehouse))
        if result.scalars().first():
            return
        warehouses = [
            Warehouse(
                name="Склад Иву", type="china", country="Китай", city="Иву",
                phone="19878638724", region="浙江省 金华市 义乌市",
                address="洪华小区26幢2单元",
            ),
            Warehouse(
                name="Склад Урумчи (Авиа)", type="china", country="Китай", city="Урумчи",
                phone="13999210571", region="新疆维吾尔自治区 乌鲁木齐市 天山区",
                address="延安路662号边疆宾馆19TPS号库房",
            ),
            Warehouse(
                name="Склад Урумчи (Авто)", type="china", country="Китай", city="Урумчи",
                phone="13999210571", region="新疆维吾尔自治区 乌鲁木齐市 天山区",
                address="延安路662号边疆宾馆19TPS号库房",
            ),
            Warehouse(
                name="Склад Душанбе", type="dushanbe", country="Таджикистан", city="Душанбе",
                phone="+992900000000", region="Душанбе",
                address="Адрес склада Душанбе",
            ),
        ]
        for w in warehouses:
            db.add(w)
        await db.commit()
        log.info("Seed warehouses created")


async def _seed_tariffs():
    async with async_session() as db:
        result = await db.execute(select(Tariff))
        if result.scalars().first():
            return
        owner = (await db.execute(
            select(StaffUser).where(StaffUser.role == "owner")
        )).scalar_one_or_none()
        if not owner:
            return
        from decimal import Decimal
        tariffs = [
            Tariff(method="avia", price_per_kg=Decimal("10.00"), created_by=owner.id),
            Tariff(method="truck", price_per_kg=Decimal("2.50"), price_per_m3=Decimal("280.00"), created_by=owner.id),
        ]
        for t in tariffs:
            db.add(t)
        await db.commit()
        log.info("Seed tariffs created")


@app.get("/")
async def root():
    return {"service": "Cargo TPS API", "version": "1.0.0"}


