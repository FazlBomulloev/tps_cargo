# Cargo TPS — заметки для AI-агентов

Карго-сервис Китай → Душанбе. Учёт посылок, выдач, клиентов.

## Архитектура
- `backend/` — FastAPI + SQLAlchemy + Alembic (PostgreSQL prod, SQLite dev). Источник правды.
- `src/` — Telegram-бот (aiogram 3, asyncio). Работает с той же БД через свои модели (src/models.py — дублирует backend, известный долг).
- `frontend/` — React 18 + AntD 5 + Vite. Админ-панель.
- Бот ↔ API через `x-bot-secret` (env `API_BOT_SECRET`).

## Доменные инварианты
- `track_id` уникален глобально. Нормализуется через `normalize_track`.
- `tps_code` — внутренний ID клиента, формат `TPS{N:03d}` (например, `TPS042`). Зарезервированы 7, 111, 222, 333, 444, 555, 666, 777, 888, 999.
- Выдача (issuance) — atomic с `SELECT FOR UPDATE` на posylki. UNIQUE на `issuance_items.parcel_id` — защита от двойной выдачи.
- `delivery_method`: `avia` (по весу) или `truck` (max(byKg, byM3)).
- Деньги хранятся как `Decimal`, в JSON — float через `quantize(0.01)`.

## Опасные места
- `notification_loop` в боте: сначала `mark_notified` (commit), потом `send_message` — иначе дубли.
- `create_issuance`: всегда с `with_for_update()`.
- `create_client_with_tps_code`: retry на `IntegrityError` (race tps_code).
- `_check_sub` в боте: fail-open при недоступности канала.
- Alembic: одна цепочка миграций в `backend/alembic/versions/`. НЕТ `create_all` в runtime.

## Env (см. `.env.example`)
- `JWT_SECRET_KEY`, `API_BOT_SECRET` — обязательны, ≥32 символа
- `POSTGRES_PASSWORD` — обязателен в compose
- `ADMIN_IDS` — comma-separated telegram_id админов бота
- `REDIS_URL` — для FSM бота (fallback MemoryStorage с warning)
- `CORS_ORIGINS` — для api
- `TRUSTED_PROXIES` — для X-Forwarded-For (опционально)
