import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart

from src.config import ADMIN_IDS
from src.handlers.admin import show_admin_panel
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.config import BOT_TOKEN, REDIS_URL
from src.db import (
    get_unnotified_parcels,
    init_db,
    mark_notified,
)
from src.fmt import fmt_parcel_arrived
from src.handlers.admin import router as admin_router
from src.handlers.client import (
    client_start_handler,
    router as client_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

if REDIS_URL:
    from aiogram.fsm.storage.redis import RedisStorage

    storage = RedisStorage.from_url(REDIS_URL)
    log.info("FSM storage: Redis (%s)", REDIS_URL.split("@")[-1])
else:
    from aiogram.fsm.storage.memory import MemoryStorage

    storage = MemoryStorage()
    log.warning(
        "FSM storage: MemoryStorage — состояния не переживут "
        "рестарт. Установите REDIS_URL для продакшена.",
    )

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Add it to .env")

dp = Dispatcher(storage=storage)
bot = Bot(token=BOT_TOKEN)

NOTIFY_CHECK_INTERVAL = 60
NOTIFY_SEND_DELAY = 0.05  # ~20 сообщений/сек — запас от лимита Telegram


@dp.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    if msg.from_user.id in ADMIN_IDS:
        await show_admin_panel(bot, state, msg.from_user.id)
        return
    await client_start_handler(msg, state, bot)


# admin-id фильтруется на каждом хендлере, а не на роутере, чтобы
# админ как клиент попадал в client_router своими FSM-кнопками.
dp.include_router(admin_router)
dp.include_router(client_router)


async def notification_loop(bot: Bot, stop_event: asyncio.Event):
    while not stop_event.is_set():
        try:
            parcels = await get_unnotified_parcels()
            for p in parcels:
                if stop_event.is_set():
                    break
                try:
                    # mark_notified до send: на рестарте между шагами
                    # хуже всего — потерянное уведомление, не дубль.
                    await mark_notified(p["id"])
                    await bot.send_message(
                        chat_id=p["telegram_id"],
                        text=fmt_parcel_arrived(
                            p["track_id"], p["lang"],
                        ),
                    )
                    log.info(
                        "Уведомление отправлено: "
                        "%s -> %s",
                        p["track_id"],
                        p["telegram_id"],
                    )
                except Exception as e:
                    log.warning(
                        "Не удалось отправить "
                        "уведомление %s: %s",
                        p["telegram_id"], e,
                    )
                await asyncio.sleep(NOTIFY_SEND_DELAY)
        except Exception:
            log.exception("notification_loop tick failed")
        try:
            await asyncio.wait_for(
                stop_event.wait(), timeout=NOTIFY_CHECK_INTERVAL,
            )
        except asyncio.TimeoutError:
            pass


async def main():
    await init_db()
    log.info("Бот запущен")

    stop_event = asyncio.Event()
    notif_task = asyncio.create_task(
        notification_loop(bot, stop_event),
    )
    try:
        await dp.start_polling(bot, handle_signals=True)
    finally:
        log.info("Stopping notification_loop...")
        stop_event.set()
        try:
            await asyncio.wait_for(notif_task, timeout=10)
        except asyncio.TimeoutError:
            log.warning(
                "notification_loop did not stop in 10s, cancelling",
            )
            notif_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
