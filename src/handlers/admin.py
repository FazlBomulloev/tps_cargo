import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.config import ADMIN_IDS
from src.db import get_broadcast_recipients

log = logging.getLogger(__name__)

router = Router(name="admin")

# Все апдейты в этом роутере — только от админов.
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))


class BroadcastSG(StatesGroup):
    waiting_content = State()


def _admin_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📢 Сделать рассылку",
            callback_data="admin_broadcast",
        )],
    ])


def _cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin_cancel",
        )],
    ])


@router.message(Command("admin"))
async def cmd_admin(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "🛠 Админ-панель\n\nВыберите действие:",
        reply_markup=_admin_kb(),
    )


@router.callback_query(F.data == "admin_broadcast")
async def cb_broadcast(cb: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastSG.waiting_content)
    await cb.message.answer(
        "Пришлите сообщение, которое нужно разослать.\n"
        "Поддерживаются: текст, фото, видео, видеокружок, "
        "голосовое, аудио, документ, стикер, GIF — любой "
        "тип сообщения. Caption сохраняется.",
        reply_markup=_cancel_kb(),
    )
    await cb.answer()


@router.callback_query(F.data == "admin_cancel")
async def cb_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer(
        "Отменено.",
        reply_markup=_admin_kb(),
    )
    await cb.answer()


@router.message(BroadcastSG.waiting_content)
async def do_broadcast(
    msg: Message, state: FSMContext, bot: Bot,
):
    await state.clear()
    recipients = await get_broadcast_recipients()
    if not recipients:
        await msg.answer(
            "Получателей нет.",
            reply_markup=_admin_kb(),
        )
        return

    progress = await msg.answer(
        f"🚀 Запускаю рассылку на {len(recipients)} "
        "получателей…",
    )

    sent = 0
    failed = 0
    # copy_message переносит любой тип контента (текст / медиа /
    # стикер / video_note / voice / документ / GIF) с подписью.
    # Это проще и универсальнее, чем разбирать тип вручную.
    for tid in recipients:
        try:
            await bot.copy_message(
                chat_id=tid,
                from_chat_id=msg.chat.id,
                message_id=msg.message_id,
            )
            sent += 1
        except Exception as e:
            failed += 1
            log.warning(
                "Рассылка: не удалось отправить %s: %s",
                tid, e,
            )
        # ~30 сообщений/сек — глобальный лимит Telegram. Держим
        # запас: 20/сек = 50 мс между отправками.
        await asyncio.sleep(0.05)

    await progress.edit_text(
        "✅ Рассылка завершена.\n\n"
        f"Отправлено: {sent}\n"
        f"Ошибок: {failed}",
    )
    await msg.answer(
        "Готово.",
        reply_markup=_admin_kb(),
    )
