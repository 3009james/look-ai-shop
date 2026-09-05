import asyncio
import contextlib

from .config import get_settings

settings = get_settings()
bot = None
_polling_task: asyncio.Task | None = None


async def start_bot() -> None:
    """Start aiogram polling only when BOT_TOKEN is configured.

    Imports are intentionally lazy so the web storefront can still be previewed
    in DEV_MODE even in an environment where Telegram dependencies are absent.
    """
    global bot, _polling_task
    if not settings.bot_token:
        return

    from aiogram import Bot, Dispatcher
    from aiogram.filters import Command, CommandStart
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo

    dp = Dispatcher()
    bot = Bot(settings.bot_token)

    def shop_keyboard() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✨ Открыть LOOK AI", web_app=WebAppInfo(url=settings.webapp_url))
        ]])

    @dp.message(CommandStart())
    async def start(message):
        await message.answer(
            "Добро пожаловать в LOOK AI — магазин одежды с персональным ИИ-стилистом.\n\n"
            "Откройте магазин, подберите образ и оформите заказ прямо внутри Telegram.",
            reply_markup=shop_keyboard(),
        )

    @dp.message(Command("shop"))
    async def shop(message):
        await message.answer("Открыть магазин:", reply_markup=shop_keyboard())

    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(text="LOOK AI", web_app=WebAppInfo(url=settings.webapp_url))
    )
    _polling_task = asyncio.create_task(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))


async def stop_bot() -> None:
    global bot, _polling_task
    if _polling_task:
        _polling_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _polling_task
    if bot:
        await bot.session.close()
