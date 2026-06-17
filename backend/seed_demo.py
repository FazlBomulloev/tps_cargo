"""Заполнение БД демо-данными.

Запуск:
    docker compose exec api python /app/seed_demo.py
или:
    docker compose run --rm api python /app/seed_demo.py

Идемпотентен по факту: если в clients > 20 — выходит и ничего не делает.
"""
import asyncio
import json
import random
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.models import (
    AuditLog,
    Client,
    Expense,
    IssuanceItem,
    IssuanceOrder,
    NotificationLog,
    ParcelChina,
    ParcelDushanbe,
    Setting,
    StaffUser,
    Tariff,
    UnresolvedParcel,
    Warehouse,
)
from app.utils.security import hash_password

random.seed(42)

# ─── Справочники ──────────────────────────────────────────────────────────────

TJ_FIRST_NAMES = [
    "Бахтиёр", "Шохрух", "Фируза", "Махмадали", "Зухра", "Рустам", "Сафия",
    "Карим", "Парвина", "Шерали", "Мижгона", "Далер", "Гулнора", "Илхом",
    "Нозия", "Фарход", "Зарина", "Анвар", "Дилшод", "Сабохат", "Махмуд",
    "Шахло", "Назрулло", "Гулчехра", "Озодбек", "Манижа", "Хасан", "Зебо",
    "Ёрмахмад", "Лола", "Камол", "Шахноза", "Рахим", "Райхона", "Бобур",
    "Нилуфар", "Шавкат", "Мадина", "Сухроб", "Анора", "Темур", "Малика",
    "Хуршед", "Зарифа", "Мансур", "Дилноза", "Самир", "Маъсума", "Алишер",
    "Шукрия", "Низом", "Нигина", "Рашид", "Мехринисо", "Музаффар", "Сабина",
    "Восеъ", "Гулрухсор", "Рамазон", "Зулфия", "Икром", "Феруза", "Хуршеда",
    "Нурмухаммад", "Олима", "Хайриддин", "Тахмина", "Зокир", "Машарифа",
    "Сайдулло", "Гулжахон", "Толиб", "Зебуниссо", "Самин", "Озода", "Гайрат",
    "Майрам", "Холмурод", "Мутрафа", "Маъруф", "Рухшона",
]

TJ_LAST_NAMES = [
    "Каримов", "Назаров", "Шарипов", "Рахимов", "Холов", "Сафаров", "Иброгимов",
    "Ахмадов", "Курбонов", "Махмадалиев", "Рустамов", "Хакимов", "Юсупов",
    "Алиев", "Камолов", "Раджабов", "Махмудов", "Низомов", "Олимов", "Бобоев",
    "Содиков", "Эргашев", "Усманов", "Гулов", "Мирзоев", "Шукуров", "Тошев",
    "Зокиров", "Файзиев", "Икромов",
]

CHINA_WAREHOUSES = [
    ("Гуанчжоу склад №1", "Гуанчжоу", "Yiwu International Trade Mart, Hall 1"),
    ("Иу транзит", "Иу", "Yiwu Futian Market District"),
    ("Шэньчжэнь Логистика", "Шэньчжэнь", "Bao'an District, Logistics Park"),
    ("Пекин Авиа", "Пекин", "Shunyi District, Cargo Terminal"),
]

DUSHANBE_WAREHOUSES = [
    ("ТПС Душанбе Центральный", "Душанбе", "ул. Нисормухаммад, 14"),
    ("ТПС Худжанд филиал", "Худжанд", "ул. Хушёр, 88"),
    ("ТПС Бохтар", "Бохтар", "ул. Айни, 12"),
]

CN_TRACK_PREFIXES = ["LP", "RU", "CN", "YT", "CR"]
CN_TRACK_SUFFIXES = ["CN", "YP", "RU"]

CHINA_GOODS = [
    "Электроника", "Одежда", "Аксессуары", "Косметика", "Текстиль",
    "Игрушки", "Запчасти авто", "Бытовая техника", "Обувь", "Сумки",
]

EXPENSE_COMMENTS_AVIA = [
    "Оплата авиа-фрахта рейс CA-880",
    "Таможенное оформление Гуанчжоу→Душанбе",
    "Терминальные сборы Шэньчжэнь",
    "Авиаперевозка партии электроники",
    "Аэропортовый сбор Душанбе",
]
EXPENSE_COMMENTS_TRUCK = [
    "Дальнобой Кашгар→Душанбе",
    "Топливо для фуры рейс 22",
    "ТО грузовика 18-тонник",
    "Зарплата водителя за рейс",
    "Транзитные сборы Кыргызстан",
    "Загрузка склад Иу",
]

RESERVED_TPS = {7, 111, 222, 333, 444, 555, 666, 777, 888, 999}


# ─── Утилиты ──────────────────────────────────────────────────────────────────


def random_track() -> str:
    prefix = random.choice(CN_TRACK_PREFIXES)
    digits = "".join(random.choices("0123456789", k=9))
    suffix = random.choice(CN_TRACK_SUFFIXES)
    return f"{prefix}{digits}{suffix}"


def random_phone() -> str:
    return "+992" + "".join(random.choices("0123456789", k=9))


def random_telegram_id() -> int:
    return random.randint(100_000_000, 999_999_999)


def random_full_name() -> str:
    return f"{random.choice(TJ_FIRST_NAMES)} {random.choice(TJ_LAST_NAMES)}"


def random_date_within(days_ago: int) -> datetime:
    # Naive UTC — модели хранят DateTime без timezone, asyncpg откажется
    # писать tz-aware значения в TIMESTAMP WITHOUT TIME ZONE.
    delta = timedelta(seconds=random.randint(0, days_ago * 86400))
    return datetime.utcnow() - delta


# ─── Сид ─────────────────────────────────────────────────────────────────────


async def seed():
    engine = create_async_engine(settings.database_url_resolved)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        count = (await session.execute(select(func.count()).select_from(Client))).scalar_one()
        if count > 20:
            print(f"⚠ В clients уже {count} записей, выхожу без изменений.")
            return

        print("Старт seed демо-данных...")

        # Staff
        owner = (await session.execute(
            select(StaffUser).where(StaffUser.role == "owner")
        )).scalar_one_or_none()
        if not owner:
            print("⚠ Не найден owner — убедись что lifespan-сид прошёл.")
            return

        staff_pool: list[StaffUser] = [owner]
        for login, full_name, role, perms in [
            ("china_admin", "Шохрух Каримов", "admin_china",
             ["dashboard", "parcels_china", "parcels_list", "clients", "tariffs"]),
            ("ds_admin", "Фируза Назарова", "admin_dushanbe",
             ["dashboard", "parcels_dushanbe", "parcels_list", "issuance",
              "issuance_history", "clients", "unresolved", "expenses"]),
            ("operator1", "Далер Шарипов", "staff", ["parcels_dushanbe", "issuance"]),
            ("operator2", "Зарина Холова", "staff", ["parcels_china"]),
        ]:
            existing = (await session.execute(
                select(StaffUser).where(StaffUser.login == login)
            )).scalar_one_or_none()
            if existing:
                staff_pool.append(existing)
                continue
            s = StaffUser(
                login=login, full_name=full_name,
                password_hash=hash_password("Demo123!"),
                role=role,
                permissions=json.dumps(perms),
                is_active=True,
            )
            session.add(s)
            staff_pool.append(s)
        await session.flush()
        print(f"  Staff: {len(staff_pool)}")

        # Warehouses
        warehouses: list[Warehouse] = []
        for name, city, addr in CHINA_WAREHOUSES:
            w = Warehouse(
                name=name, type="china", country="CN", city=city,
                phone="+86" + "".join(random.choices("0123456789", k=10)),
                region="Guangdong" if city in ("Гуанчжоу", "Шэньчжэнь") else "Other",
                address=addr,
            )
            session.add(w)
            warehouses.append(w)
        for name, city, addr in DUSHANBE_WAREHOUSES:
            w = Warehouse(
                name=name, type="dushanbe", country="TJ", city=city,
                phone="+992" + "".join(random.choices("0123456789", k=9)),
                region="Tajikistan", address=addr,
            )
            session.add(w)
            warehouses.append(w)
        await session.flush()
        china_whs = [w for w in warehouses if w.type == "china"]
        dushanbe_whs = [w for w in warehouses if w.type == "dushanbe"]
        print(f"  Warehouses: {len(warehouses)}")

        # Tariffs
        tariff_avia = Tariff(
            method="avia", price_per_kg=Decimal("55.00"),
            price_per_m3=None, currency="TJS", is_active=True, created_by=owner.id,
        )
        tariff_truck = Tariff(
            method="truck", price_per_kg=Decimal("12.50"),
            price_per_m3=Decimal("3200.00"), currency="TJS", is_active=True, created_by=owner.id,
        )
        session.add_all([tariff_avia, tariff_truck])
        await session.flush()
        print("  Tariffs: 2")

        # Clients
        clients: list[Client] = []
        used_tps: set[int] = set()
        target_count = 84
        num = 0
        while len(clients) < target_count:
            num += 1
            if num in RESERVED_TPS or num in used_tps:
                continue
            used_tps.add(num)
            tps_code = f"TPS{num:03d}" if num < 1000 else f"TPS{num}"
            status = random.choices(
                ["active", "active", "active", "active", "blocked"], k=1
            )[0]
            created = random_date_within(180)
            c = Client(
                telegram_id=random_telegram_id(),
                tps_code=tps_code,
                full_name=random_full_name(),
                phone=random_phone(),
                address=random.choice([None, "Душанбе", "Худжанд", "Бохтар", "Куляб"]),
                lang=random.choice(["ru", "ru", "ru", "tj"]),
                status=status,
                created_at=created,
                last_activity_at=created + timedelta(days=random.randint(0, 60)),
            )
            session.add(c)
            clients.append(c)
        await session.flush()
        active_clients = [c for c in clients if c.status == "active"]
        print(f"  Clients: {len(clients)} ({len(active_clients)} active)")

        # Parcels China
        china_parcels: list[ParcelChina] = []
        used_tracks: set[str] = set()
        while len(china_parcels) < 85:
            tr = random_track()
            if tr in used_tracks:
                continue
            used_tracks.add(tr)
            p = ParcelChina(
                track_id=tr,
                warehouse_id=random.choice(china_whs).id,
                created_by=random.choice([owner.id, staff_pool[1].id, staff_pool[4].id]),
                created_at=random_date_within(90),
            )
            session.add(p)
            china_parcels.append(p)
        await session.flush()
        print(f"  ParcelsChina: {len(china_parcels)}")

        # Parcels Dushanbe
        dushanbe_parcels: list[ParcelDushanbe] = []
        while len(dushanbe_parcels) < 85:
            tr = random_track()
            if tr in used_tracks:
                continue
            used_tracks.add(tr)
            client = random.choice(active_clients)
            method = random.choices(["avia", "truck"], weights=[0.4, 0.6], k=1)[0]
            weight = Decimal(str(round(random.uniform(0.5, 30.0), 3)))
            volume = (
                Decimal(str(round(random.uniform(0.005, 0.5), 4)))
                if method == "truck" else None
            )
            tariff = tariff_avia if method == "avia" else tariff_truck

            if method == "avia":
                amount = (weight * tariff.price_per_kg).quantize(Decimal("0.01"))
            else:
                by_kg = weight * tariff.price_per_kg
                by_m3 = (volume or Decimal("0")) * (tariff.price_per_m3 or Decimal("0"))
                amount = max(by_kg, by_m3).quantize(Decimal("0.01"))

            created_at = random_date_within(60)
            status = random.choices(
                ["received_dushanbe", "issued"], weights=[0.55, 0.45], k=1
            )[0]
            notified = (
                created_at + timedelta(hours=random.randint(1, 48))
                if random.random() < 0.85 else None
            )

            p = ParcelDushanbe(
                track_id=tr,
                client_id=client.id,
                status=status,
                weight_kg=weight,
                volume_m3=volume,
                delivery_method=method,
                warehouse_id=random.choice(dushanbe_whs).id,
                amount_due=amount,
                tariff_snapshot=tariff.price_per_kg,
                tariff_snapshot_data={
                    "kg": str(tariff.price_per_kg),
                    "m3": str(tariff.price_per_m3) if tariff.price_per_m3 else None,
                    "currency": tariff.currency,
                },
                has_china_registration=random.random() < 0.7,
                comment=random.choice([None, None, random.choice(CHINA_GOODS)]),
                shelf=random.choice(
                    [None, f"A{random.randint(1, 20)}", f"B{random.randint(1, 20)}"]
                ),
                notified_at=notified,
                created_by=random.choice([owner.id, staff_pool[2].id, staff_pool[3].id]),
                created_at=created_at,
                updated_at=created_at,
            )
            session.add(p)
            dushanbe_parcels.append(p)
        await session.flush()
        issued = [p for p in dushanbe_parcels if p.status == "issued"]
        print(f"  ParcelsDushanbe: {len(dushanbe_parcels)} ({len(issued)} issued)")

        # Issuance Orders + Items
        by_client: dict[int, list[ParcelDushanbe]] = defaultdict(list)
        for p in issued:
            by_client[p.client_id].append(p)

        orders_n = 0
        items_n = 0
        for client_id, parcels in by_client.items():
            i = 0
            while i < len(parcels):
                size = random.randint(1, 4)
                chunk = parcels[i:i + size]
                i += size
                if not chunk:
                    continue
                total_weight = sum((p.weight_kg for p in chunk), Decimal("0"))
                total_amount = sum(
                    (p.amount_due or Decimal("0") for p in chunk), Decimal("0")
                )
                issued_at = max(p.created_at for p in chunk) + timedelta(
                    hours=random.randint(2, 72)
                )
                order = IssuanceOrder(
                    client_id=client_id,
                    staff_id=random.choice([owner.id, staff_pool[2].id]),
                    total_weight=total_weight.quantize(Decimal("0.001")),
                    total_amount=total_amount.quantize(Decimal("0.01")),
                    payment_status=random.choices(
                        ["paid", "debt"], weights=[0.85, 0.15], k=1
                    )[0],
                    payment_method=random.choice(["cash", "card", "transfer"]),
                    comment=random.choice([None, "Выдан полностью", "Без чека"]),
                    issued_at=issued_at,
                )
                session.add(order)
                await session.flush()
                for p in chunk:
                    item = IssuanceItem(
                        issuance_order_id=order.id,
                        parcel_id=p.id,
                        weight_kg=p.weight_kg,
                        volume_m3=p.volume_m3,
                        delivery_method=p.delivery_method,
                        tariff_applied=p.tariff_snapshot or Decimal("0"),
                        custom_price=None,
                        amount=p.amount_due or Decimal("0"),
                        tariff_snapshot_data=p.tariff_snapshot_data,
                    )
                    session.add(item)
                    items_n += 1
                orders_n += 1
        await session.flush()
        print(f"  IssuanceOrders: {orders_n}, IssuanceItems: {items_n}")

        # Expenses
        for _ in range(85):
            category = random.choices(["avia", "truck"], weights=[0.3, 0.7], k=1)[0]
            amount = Decimal(str(round(random.uniform(120, 8500), 2)))
            comment = random.choice(
                EXPENSE_COMMENTS_AVIA if category == "avia" else EXPENSE_COMMENTS_TRUCK
            )
            e = Expense(
                amount=amount, category=category, comment=comment,
                created_by=owner.id, created_at=random_date_within(120),
            )
            session.add(e)
        await session.flush()
        print("  Expenses: 85")

        # NotificationLogs
        notified_parcels = [p for p in dushanbe_parcels if p.notified_at]
        for p in notified_parcels[:80]:
            log = NotificationLog(
                client_id=p.client_id,
                parcel_id=p.id,
                notification_type="parcel_received",
                status=random.choices(["sent", "sent", "sent", "failed"], k=1)[0],
                error=None,
                sent_at=p.notified_at,
            )
            session.add(log)
        await session.flush()
        print(f"  NotificationLogs: {min(80, len(notified_parcels))}")

        # Unresolved
        for _ in range(12):
            u = UnresolvedParcel(
                track_id=random_track(),
                raw_tps_code=f"TPS{random.randint(1, 999):03d}X",
                weight_kg=Decimal(str(round(random.uniform(0.5, 25.0), 3))),
                volume_m3=Decimal(str(round(random.uniform(0.01, 0.3), 4)))
                if random.random() < 0.5 else None,
                delivery_method=random.choice(["avia", "truck", None]),
                comment="TPS-код не распознан",
                resolved=False,
                created_by=staff_pool[2].id,
                created_at=random_date_within(30),
            )
            session.add(u)
        await session.flush()
        print("  Unresolved: 12")

        # Settings
        for k, v in [
            ("tariffs", "Авиа: 55 TJS/кг\nФура: 12.5 TJS/кг или 3200 TJS/м³\nСрок: 12-18 дней"),
            ("support", "Поддержка: +992 900 11 22 33\nWhatsApp: +992 900 11 22 33\nEmail: support@tpscargo.tj"),
            ("company_name", "TPS Cargo Tajikistan"),
            ("currency", "TJS"),
            ("channel_required", "false"),
        ]:
            exists = (await session.execute(
                select(Setting).where(Setting.key == k)
            )).scalar_one_or_none()
            if exists:
                continue
            session.add(Setting(key=k, value=v, updated_by=owner.id))
        await session.flush()
        print("  Settings: 5")

        # Audit logs
        for _ in range(40):
            log = AuditLog(
                staff_id=random.choice([owner.id, staff_pool[1].id, staff_pool[2].id]),
                action=random.choice([
                    "create_parcel", "issue_parcel", "update_client",
                    "create_tariff", "delete_parcel",
                ]),
                entity_type=random.choice(["parcel", "client", "tariff", "issuance"]),
                entity_id=random.randint(1, 80),
                before_json=None,
                after_json={"demo": True},
                ip_address="127.0.0.1",
                created_at=random_date_within(60),
            )
            session.add(log)
        await session.flush()
        print("  AuditLogs: 40")

        await session.commit()
        print("\n✅ Готово.")
        print("\nДемо-логины для UI (пароль: Demo123!):")
        print("  china_admin   — Админ Китай")
        print("  ds_admin      — Админ Душанбе")
        print("  operator1     — Сотрудник (выдача)")
        print("  operator2     — Сотрудник (приёмка Китай)")


if __name__ == "__main__":
    asyncio.run(seed())
