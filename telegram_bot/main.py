"""
Sherik Topish Telegram Bot — Asosiy kirish nuqtasi
Ishlatish: python -m telegram_bot.main
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from .config import BOT_TOKEN
from .handlers import start, listing, browse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start",      description="🏠 Boshlanish"),
        BotCommand(command="menu",       description="📌 Asosiy menyu"),
        BotCommand(command="new",        description="📋 Yangi e'lon joylash"),
        BotCommand(command="mylistings", description="📂 Mening e'lonlarim"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Handlerlarni ro'yxatdan o'tkazish
    dp.include_router(start.router)
    dp.include_router(listing.router)
    dp.include_router(browse.router)

    # Bot buyruqlarini o'rnatish
    await set_commands(bot)

    logger.info("🤖 @SheriktopishBot ishga tushdi!")

    # Polling bilan ishlatish (eski webhooklarni tozalash)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.warning(f"Webhook tozalashda ogohlantirish: {e}")

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())

