"""
🚀  /start handler
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

from config import settings
from database.db import AsyncSessionLocal
from database.queries import UserQueries
from keyboards.kb import main_menu_kb, admin_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with AsyncSessionLocal() as session:
        user = await UserQueries.get_or_create(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username,
        )

    if user.is_banned:
        await message.answer("🚫 Siz botdan bloklangansiz.")
        return

    is_admin = message.from_user.id in settings.ADMIN_IDS
    name = message.from_user.first_name

    if is_admin:
        await message.answer(
            f"👑 Xush kelibsiz, <b>{name}</b>!\n\n"
            f"Siz admin sifatida kiryapsiz. Boshqarish panelini tanlang:",
            reply_markup=admin_menu_kb(),
        )
    else:
        await message.answer(
            f"👋 Assalomu alaykum, <b>{name}</b>!\n\n"
            f"🤖 <b>{settings.BOT_NAME}</b> ga xush kelibsiz.\n\n"
            "📌 Quyidagi bo'limlardan birini tanlang:",
            reply_markup=main_menu_kb(),
        )


@router.message(F.text == "🏠 Asosiy menyu")
async def back_to_main(message: Message):
    is_admin = message.from_user.id in settings.ADMIN_IDS
    await message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=admin_menu_kb() if is_admin else main_menu_kb(),
    )
