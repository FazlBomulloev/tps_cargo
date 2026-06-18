import asyncio
import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
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


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


class BroadcastSG(StatesGroup):
    waiting_content = State()
    confirm = State()


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


def _confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить рассылку",
                callback_data="admin_broadcast_confirm",
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="admin_cancel",
            ),
        ],
    ])


async def show_admin_panel(bot: Bot, state: FSMContext, user_id: int) -> None:
    """Открывает админ-меню в личке у user_id (используется и /admin, и /start)."""
    await state.clear()
    # Только в личку — даже если команда пришла из группы.
    await bot.send_message(
        user_id,
        "🛠 Админ-панель\n\nВыберите действие:",
        reply_markup=_admin_kb(),
    )


@router.message(Command("admin"), F.from_user.id.in_(ADMIN_IDS))
async def cmd_admin(msg: Message, state: FSMContext, bot: Bot):
    await show_admin_panel(bot, state, msg.from_user.id)


@router.callback_query(
    F.data == "admin_broadcast",
    F.from_user.id.in_(ADMIN_IDS),
)
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


@router.callback_query(
    F.data == "admin_cancel",
    F.from_user.id.in_(ADMIN_IDS),
)
async def cb_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer(
        "Отменено.",
        reply_markup=_admin_kb(),
    )
    await cb.answer()


@router.message(
    BroadcastSG.waiting_content,
    F.from_user.id.in_(ADMIN_IDS),
)
async def on_broadcast_content(
    msg: Message, state: FSMContext, bot: Bot,
):
    recipients = await get_broadcast_recipients()
    if not recipients:
        await state.clear()
        await msg.answer(
            "Получателей нет.",
            reply_markup=_admin_kb(),
        )
        return

    await state.update_data(
        from_chat_id=msg.chat.id,
        message_id=msg.message_id,
    )
    await state.set_state(BroadcastSG.confirm)

    await bot.copy_message(  # превью админу
        chat_id=msg.chat.id,
        from_chat_id=msg.chat.id,
        message_id=msg.message_id,
    )
    await msg.answer(
        "⬆️ Так выглядит сообщение для рассылки.\n\n"
        f"Получателей: {len(recipients)}.\n"
        "Подтвердите отправку.",
        reply_markup=_confirm_kb(),
    )


@router.callback_query(
    BroadcastSG.confirm,
    F.data == "admin_broadcast_confirm",
    F.from_user.id.in_(ADMIN_IDS),
)
async def cb_confirm_broadcast(
    cb: CallbackQuery, state: FSMContext, bot: Bot,
):
    data = await state.get_data()
    from_chat_id = data.get("from_chat_id")
    message_id = data.get("message_id")
    await state.clear()
    await cb.answer()

    if not from_chat_id or not message_id:
        await cb.message.answer(
            "Сообщение для рассылки не найдено, начните заново.",
            reply_markup=_admin_kb(),
        )
        return

    recipients = await get_broadcast_recipients()
    if not recipients:
        await cb.message.answer(
            "Получателей нет.",
            reply_markup=_admin_kb(),
        )
        return

    progress = await cb.message.answer(
        f"🚀 Запускаю рассылку на {len(recipients)} "
        "получателей…",
    )

    sent = 0
    failed = 0
    blocked = 0
    for tid in recipients:
        try:
            await bot.copy_message(
                chat_id=tid,
                from_chat_id=from_chat_id,
                message_id=message_id,
            )
            sent += 1
        except TelegramRetryAfter as e:
            log.warning(
                "Рассылка: flood control, ждём %s сек (получатель %s)",
                e.retry_after, tid,
            )
            await asyncio.sleep(e.retry_after)
            try:
                await bot.copy_message(
                    chat_id=tid,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                )
                sent += 1
            except Exception as retry_e:
                failed += 1
                log.warning(
                    "Рассылка: повтор после RetryAfter не удался "
                    "для %s: %s",
                    tid, retry_e,
                )
        except TelegramForbiddenError:
            blocked += 1
            log.info(
                "Рассылка: получатель %s заблокировал бота", tid,
            )
        except TelegramBadRequest as e:
            failed += 1
            log.warning(
                "Рассылка: bad request для %s: %s", tid, e,
            )
        except TelegramAPIError as e:
            failed += 1
            log.warning(
                "Рассылка: ошибка API Telegram для %s: %s", tid, e,
            )
        await asyncio.sleep(0.05)  # ~20/сек, запас от лимита Telegram

    try:
        await progress.edit_text(
            "✅ Рассылка завершена.\n\n"
            f"Отправлено: {sent}\n"
            f"Заблокировали бота: {blocked}\n"
            f"Ошибок: {failed}",
        )
    except TelegramBadRequest:
        pass  # сообщение слишком старое для редактирования
    await state.clear()
    await cb.message.answer(
        "Готово.",
        reply_markup=_admin_kb(),
    )
