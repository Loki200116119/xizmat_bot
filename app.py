"""
╔══════════════════════════════════════════════════════════════╗
║          🚀 PROFESSIONAL XIZMAT / BUYURTMA BOT               ║
║          Aiogram 3 | SQLAlchemy | FSM | Admin Panel          ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import logging

from google import genai
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from database.db import init_db
from handlers import start, services, orders, profile, admin, common, ai_handler
from middlewares.throttling import ThrottlingMiddleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


async def main():
    await init_db()
    log.info("✅ Ma'lumotlar bazasi tayyor")

    gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    log.info("✅ Gemini AI ulandi")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp["gemini_client"] = gemini_client

    dp.message.middleware(ThrottlingMiddleware(rate_limit=1.5))

    dp.include_router(common.router)
    dp.include_router(start.router)
    dp.include_router(services.router)
    dp.include_router(orders.router)
    dp.include_router(profile.router)
    dp.include_router(admin.router)
    dp.include_router(ai_handler.router)

    for admin_id in settings.ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "✅ <b>Bot ishga tushdi!</b>\n"
                "Barcha tizimlar tayyor.",
            )
        except Exception:
            pass

    log.info("🚀 Bot polling boshlandi...")
    try:
        await dp.start_polling(
            bot,
            skip_updates=True,
            allowed_updates=dp.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())