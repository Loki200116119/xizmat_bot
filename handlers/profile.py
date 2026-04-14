"""
👤  Foydalanuvchi profili va buyurtmalar tarixi
"""

from aiogram import Router, F
from aiogram.types import Message

from database.db import AsyncSessionLocal
from database.queries import UserQueries, OrderQueries
from database.models import STATUS_LABELS
from keyboards.kb import main_menu_kb

router = Router()


@router.message(F.text == "📋 Buyurtmalarim")
async def my_orders(message: Message):
    async with AsyncSessionLocal() as session:
        user = await UserQueries.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("Siz hali ro'yxatdan o'tmagansiz. /start bosing.")
            return
        orders = await OrderQueries.get_by_user(session, user.id)

    if not orders:
        await message.answer(
            "📭 Siz hali buyurtma bermadingiz.\n\n"
            "Buyurtma berish uchun <b>📝 Buyurtma berish</b> tugmasini bosing.",
            reply_markup=main_menu_kb(),
        )
        return

    text = f"📋 <b>Sizning buyurtmalaringiz ({len(orders)} ta):</b>\n\n"
    for order in orders[:10]:  # Oxirgi 10 ta
        status = STATUS_LABELS.get(order.status, order.status)
        svc = order.service.name if order.service else "—"
        text += (
            f"• #{order.id} | {svc}\n"
            f"  {status} — {order.created_at.strftime('%d.%m.%Y')}\n\n"
        )

    if len(orders) > 10:
        text += f"<i>... va yana {len(orders) - 10} ta buyurtma</i>"

    await message.answer(text)


@router.message(F.text == "ℹ️ Biz haqimizda")
async def about_us(message: Message):
    from config import settings
    await message.answer(
        f"🏢 <b>{settings.COMPANY_NAME}</b>\n\n"
        "Biz professional xizmatlar ko'rsatamiz.\n\n"
        "✅ Sifatli ish\n"
        "✅ O'z vaqtida yetkazib berish\n"
        "✅ Qulay narxlar\n"
        "✅ Professional jamoa"
    )


@router.message(F.text == "📞 Bog'lanish")
async def contacts(message: Message):
    from config import settings
    await message.answer(
        "📞 <b>Bog'lanish ma'lumotlari</b>\n\n"
        f"📱 Telefon: <code>{settings.COMPANY_PHONE}</code>\n"
        f"💬 Telegram: {settings.COMPANY_USERNAME}\n"
        f"📍 Manzil: {settings.COMPANY_ADDRESS}\n"
        f"🕐 Ish vaqti: {settings.COMPANY_HOURS}"
    )


@router.message(F.text == "❓ Yordam")
async def help_section(message: Message):
    await message.answer(
        "❓ <b>Yordam</b>\n\n"
        "📌 <b>Qanday buyurtma beraman?</b>\n"
        "  1. 🛠 Xizmatlar bo'limidan xizmatni tanlang\n"
        "  2. 📝 Buyurtma berish tugmasini bosing\n"
        "  3. Ma'lumotlaringizni kiriting\n"
        "  4. Tasdiqlang — tez orada bog'lanamiz!\n\n"
        "📌 <b>Buyurtmamni qanday kuzataman?</b>\n"
        "  📋 Buyurtmalarim bo'limida statusini ko'rasiz.\n\n"
        "📌 <b>Savol bo'lsa?</b>\n"
        "  📞 Bog'lanish bo'limida kontaktlar bor."
    )
