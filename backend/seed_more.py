"""Аддитивный сидер: добавляет клиентов, посылки (с весами) и выдачи.

Безопасен для повторного запуска: не трогает существующие строки, сам
находит следующие свободные TPS-коды / telegram_id / трек-коды. Использует
уже имеющихся сотрудников, склады и тарифы.

Запуск (из каталога backend):  .venv\\Scripts\\python.exe seed_more.py
"""
import asyncio
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.database import async_session, engine, Base
from app.models.staff import StaffUser
from app.models.client import Client
from app.models.warehouse import Warehouse
from app.models.tariff import Tariff
from app.models.parcel_china import ParcelChina
from app.models.parcel_dushanbe import ParcelDushanbe
from app.models.issuance import IssuanceOrder, IssuanceItem

random.seed()

NOW = datetime.now()
START = NOW - timedelta(days=60)

N_CLIENTS = 15
N_CHINA = 30
N_DUSHANBE = 25  # из китайских "доехали" в Душанбе

FIRST_M = [
    "Фируз", "Шерзод", "Бахтиёр", "Далер", "Рустам", "Аброр", "Сардор",
    "Жасур", "Нодир", "Акмал", "Достон", "Ислом", "Комил", "Парвиз",
    "Равшан", "Сухроб", "Тохир", "Улугбек", "Фаррух", "Хуршед",
]
FIRST_F = [
    "Мадина", "Нигора", "Зарина", "Фарида", "Дилноза", "Гулнора",
    "Парвина", "Сабина", "Шахноза", "Азиза", "Малика", "Нилуфар",
]
LAST = [
    "Рахимов", "Каримов", "Ахмедов", "Назаров", "Усмонов", "Шарипов",
    "Муродов", "Холиков", "Саидов", "Бобоев", "Мирзоев", "Олимов",
    "Тошматов", "Хасанов", "Нуров", "Абдуллоев", "Ганиев", "Давлатов",
]
TRACK_PREFIXES = ["YT", "SF", "LP", "JN", "ZX", "CR", "TX"]
COMMENTS = [
    None, None, None, "Хрупкий товар", "Электроника", "Одежда",
    "Обувь", "Запчасти", "Косметика", "Телефон", "Ноутбук",
]
CITIES = [None, "Душанбе", "Худжанд", "Куляб", "Бохтар", "Турсунзаде"]


def rand_date(start: datetime, end: datetime) -> datetime:
    delta = (end - start).total_seconds()
    return start + timedelta(seconds=random.uniform(0, delta))


def rand_track() -> str:
    return random.choice(TRACK_PREFIXES) + "".join(random.choices(string.digits, k=12))


def rand_phone() -> str:
    code = random.choice(["90", "91", "92", "93", "98", "88", "77"])
    return "+992" + code + "".join(random.choices(string.digits, k=7))


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        staff = (await db.execute(select(StaffUser))).scalars().all()
        if not staff:
            print("ОШИБКА: нет сотрудников. Сначала запусти API (создаётся owner).")
            return
        staff_ids = [s.id for s in staff]
        owner_id = next((s.id for s in staff if s.role == "owner"), staff_ids[0])
        china_admin = next((s.id for s in staff if s.role == "admin_china"), owner_id)
        dush_admin = next((s.id for s in staff if s.role == "admin_dushanbe"), owner_id)

        warehouses = (await db.execute(select(Warehouse))).scalars().all()
        china_wh = [w.id for w in warehouses if w.type == "china"] or (
            [warehouses[0].id] if warehouses else [None]
        )
        dush_wh = next((w.id for w in warehouses if w.type == "dushanbe"),
                       warehouses[0].id if warehouses else None)

        tariffs = (await db.execute(select(Tariff).where(Tariff.is_active == True))).scalars().all()
        t_avia = next((t for t in tariffs if t.method == "avia"), None)
        t_truck = next((t for t in tariffs if t.method == "truck"), None)
        if not t_avia or not t_truck:
            print("ОШИБКА: нет активных тарифов avia/truck. Сначала запусти API.")
            return

        # ── уникальность относительно того, что уже в базе ──
        used_tps = {r[0] for r in (await db.execute(select(Client.tps_code))).all()}
        used_tg = {r[0] for r in (await db.execute(select(Client.telegram_id))).all()}
        used_tracks = {r[0] for r in (await db.execute(select(ParcelChina.track_id))).all()}
        used_tracks |= {r[0] for r in (await db.execute(select(ParcelDushanbe.track_id))).all()}

        next_num = 1
        while f"TPS{next_num:04d}" in used_tps:
            next_num += 1

        # ── Клиенты ──
        clients = []
        for i in range(N_CLIENTS):
            female = random.random() < 0.3
            first = random.choice(FIRST_F if female else FIRST_M)
            last = random.choice(LAST)
            if female and last.endswith(("ов", "ев")):
                last += "а"
            tg = random.randint(100_000_000, 999_999_999)
            while tg in used_tg:
                tg = random.randint(100_000_000, 999_999_999)
            used_tg.add(tg)
            tps = f"TPS{next_num + i:04d}"
            used_tps.add(tps)
            reg = rand_date(START, NOW - timedelta(days=2))
            clients.append(Client(
                telegram_id=tg,
                tps_code=tps,
                full_name=f"{last} {first}",
                phone=rand_phone(),
                address=random.choice(CITIES),
                lang=random.choice(["ru", "tj", "uz"]),
                status="active",
                created_at=reg,
                last_activity_at=rand_date(reg, NOW),
            ))
        db.add_all(clients)
        await db.flush()

        # ── Посылки (Китай) ──
        china = []
        for _ in range(N_CHINA):
            tr = rand_track()
            while tr in used_tracks:
                tr = rand_track()
            used_tracks.add(tr)
            china.append(ParcelChina(
                track_id=tr,
                warehouse_id=random.choice(china_wh),
                created_by=china_admin,
                created_at=rand_date(START, NOW - timedelta(days=1)),
            ))
        db.add_all(china)
        await db.flush()

        # ── Посылки (Душанбе) с весами ──
        arrived = random.sample(china, min(N_DUSHANBE, len(china)))
        dush = []
        for cp in arrived:
            method = random.choices(["avia", "truck"], weights=[70, 30])[0]
            weight = round(random.uniform(0.3, 25.0), 3)
            volume = round(random.uniform(0.01, 2.0), 4) if method == "truck" else None
            tariff = t_avia if method == "avia" else t_truck
            if method == "avia":
                amount = round(weight * float(tariff.price_per_kg), 2)
            else:
                amount = round(max(
                    weight * float(tariff.price_per_kg),
                    float(volume or 0) * float(tariff.price_per_m3 or 0),
                ), 2)
            arrival = cp.created_at + timedelta(days=random.randint(2, 14))
            if arrival > NOW:
                arrival = NOW - timedelta(hours=random.randint(1, 36))
            dush.append(ParcelDushanbe(
                track_id=cp.track_id,
                client_id=random.choice(clients).id,
                status="received_dushanbe",
                weight_kg=Decimal(str(weight)),
                volume_m3=Decimal(str(volume)) if volume else None,
                delivery_method=method,
                warehouse_id=dush_wh,
                amount_due=Decimal(str(amount)),
                tariff_snapshot=tariff.price_per_kg,
                has_china_registration=True,
                comment=random.choice(COMMENTS),
                notified_at=arrival,
                created_by=dush_admin,
                created_at=arrival,
                updated_at=arrival,
            ))
        db.add_all(dush)
        await db.flush()

        # ── Выдачи: ~60% посылок, сгруппировано по клиентам ──
        to_issue = random.sample(dush, int(len(dush) * 0.6))
        by_client: dict[int, list] = {}
        for p in to_issue:
            by_client.setdefault(p.client_id, []).append(p)

        orders = 0
        for cid, batch in by_client.items():
            random.shuffle(batch)
            i = 0
            while i < len(batch):
                group = batch[i:i + random.randint(1, 3)]
                i += len(group)
                total_w = sum(float(p.weight_kg) for p in group)
                total_a = sum(float(p.amount_due or 0) for p in group)
                issued_at = max(p.created_at for p in group) + timedelta(days=random.randint(1, 5))
                if issued_at > NOW:
                    issued_at = NOW - timedelta(hours=random.randint(1, 12))
                pay_status = random.choices(["paid", "debt"], weights=[80, 20])[0]
                pay_method = random.choice(["cash", "transfer"]) if pay_status == "paid" else None
                order = IssuanceOrder(
                    client_id=cid,
                    staff_id=random.choice([owner_id, dush_admin]),
                    total_weight=Decimal(str(round(total_w, 3))),
                    total_amount=Decimal(str(round(total_a, 2))),
                    payment_status=pay_status,
                    payment_method=pay_method,
                    comment=random.choice([None, None, "Самовывоз", "Доставка курьером"]),
                    issued_at=issued_at,
                )
                db.add(order)
                await db.flush()
                for p in group:
                    rate = t_avia.price_per_kg if p.delivery_method == "avia" else t_truck.price_per_kg
                    db.add(IssuanceItem(
                        issuance_order_id=order.id,
                        parcel_id=p.id,
                        weight_kg=p.weight_kg,
                        volume_m3=p.volume_m3,
                        delivery_method=p.delivery_method,
                        tariff_applied=rate,
                        amount=p.amount_due or Decimal("0"),
                    ))
                    p.status = "issued"
                    p.updated_at = issued_at
                orders += 1

        await db.commit()
        print("Добавлено:")
        print(f"  Клиентов:           {len(clients)}  (с {next_num:04d})")
        print(f"  Посылок (Китай):    {len(china)}")
        print(f"  Посылок (Душанбе):  {len(dush)}")
        print(f"  Выдач:              {orders}  ({len(to_issue)} посылок)")


if __name__ == "__main__":
    asyncio.run(main())
