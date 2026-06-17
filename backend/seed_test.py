"""Заполнение тестовых данных: клиенты + посылки."""
import asyncio
import random
from decimal import Decimal

from app.database import async_session, engine, Base
from app.models.client import Client
from app.models.parcel_china import ParcelChina
from app.models.parcel_dushanbe import ParcelDushanbe

CLIENTS = [
    {
        "telegram_id": 100001,
        "full_name": "Иванов Алексей",
        "phone": "+992901112233",
        "tps_code": "TPS0001",
        "address": "Душанбе, ул. Рудаки 10",
    },
    {
        "telegram_id": 100002,
        "full_name": "Каримова Мадина",
        "phone": "+992902223344",
        "tps_code": "TPS0002",
        "address": "Душанбе, ул. Сомони 45",
    },
    {
        "telegram_id": 100003,
        "full_name": "Назаров Фирдавс",
        "phone": "+992903334455",
        "tps_code": "TPS0003",
        "address": "Душанбе, ул. Исмоили Сомони 100",
    },
    {
        "telegram_id": 100004,
        "full_name": "Рахимова Нигина",
        "phone": "+992904445566",
        "tps_code": "TPS0004",
        "address": "Худжанд, ул. Ленина 5",
    },
    {
        "telegram_id": 100005,
        "full_name": "Шарипов Бахром",
        "phone": "+992905556677",
        "tps_code": "TPS0005",
        "address": "Душанбе, пр. Дружбы Народов 21",
    },
]

TRACKS_CHINA = [
    "SF1234567890",
    "YT2345678901",
    "ZTO345678901",
    "STO456789012",
    "YD5678901234",
    "JD6789012345",
    "EMS789012345",
    "SF8901234567",
    "YT9012345678",
    "ZTO012345678",
    "STO112233445",
    "YD223344556A",
]


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        clients = []
        for data in CLIENTS:
            c = Client(**data, lang="ru")
            db.add(c)
            clients.append(c)
        await db.flush()

        for track in TRACKS_CHINA:
            db.add(ParcelChina(
                track_id=track, created_by=1,
            ))
        await db.flush()

        methods = ["avia", "truck"]
        statuses = [
            "received_dushanbe",
            "received_dushanbe",
            "received_dushanbe",
            "issued",
        ]
        for i, track in enumerate(TRACKS_CHINA[:10]):
            client = clients[i % len(clients)]
            w = Decimal(str(round(
                random.uniform(0.5, 25.0), 3,
            )))
            v = Decimal(str(round(
                random.uniform(0.01, 2.0), 4,
            ))) if random.random() > 0.4 else None
            method = methods[i % 2]
            st = statuses[i % len(statuses)]
            parcel = ParcelDushanbe(
                track_id=track,
                client_id=client.id,
                weight_kg=w,
                volume_m3=v,
                delivery_method=method,
                status=st,
                has_china_registration=True,
                created_by=1,
            )
            if st == "issued":
                parcel.amount_due = Decimal(str(
                    round(float(w) * 10, 2),
                ))
                parcel.tariff_snapshot = Decimal("10.00")
            db.add(parcel)

        await db.commit()
    print("Тестовые данные загружены:")
    print(f"  Клиентов: {len(CLIENTS)}")
    print(f"  Посылок (Китай): {len(TRACKS_CHINA)}")
    print(f"  Посылок (Душанбе): 10")


if __name__ == "__main__":
    asyncio.run(main())
