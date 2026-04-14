"""
📝  Buyurtma berish — to'liq FSM flow
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import settings
from database.db import AsyncSessionLocal
from database.queries import UserQueries, ServiceQueries, OrderQueries
from keyboards.kb import (
    services_inline_kb, contact_kb, back_kb,
    skip_back_kb, confirm_order_kb, main_menu_kb, order_status_kb,
)
from states.forms import OrderForm
from utils.helpers import validate_phone, validate_name, format_order

log = logging.getLogger(__name__)
router = Router()


# ── 1. Xizmat tanlash ──────────────────────────────────────────

@router.message(F.text == "📝 Buyurtma berish")
@router.callback_query(F.data.startswith("order_svc_"))
async def start_order(event: Message | CallbackQuery, state: FSMContext):
    """Buyurtma jarayonini boshlash"""
    async with AsyncSessionLocal() as session:
        services = await ServiceQueries.get_all(session, active_only=True)

    if not services:
        text = "😔 Hozircha buyurtma qabul qilinmayapti."
        if isinstance(event, CallbackQuery):
            await event.message.answer(text)
            await event.answer()
        else:
            await event.answer(text)
        return

    # Agar xizmat allaqachon tanlangan bo'lsa (callback orqali kelsa)
    if isinstance(event, CallbackQuery) and event.data.startswith("order_svc_"):
        svc_id = int(event.data.split("_")[2])
        await state.update_data(service_id=svc_id)
        await state.set_state(OrderForm.entering_name)
        await event.message.answer(
            "👤 Ismingizni kiriting:",
            reply_markup=back_kb(),
        )
        await event.answer()
        return

    # Xizmat tanlatish
    await state.set_state(OrderForm.choosing_service)
    text = "🛠 Qaysi xizmat kerak?\n\nQuyidagi ro'yxatdan tanlang:"
    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=services_inline_kb(services))
        await event.answer()
    else:
        await event.answer(text, reply_markup=services_inline_kb(services))


@router.callback_query(OrderForm.choosing_service, F.data.startswith("svc_"))
async def service_chosen(callback: CallbackQuery, state: FSMContext):
    svc_id = int(callback.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        svc = await ServiceQueries.get_by_id(session, svc_id)

    if not svc:
        await callback.answer("Xizmat topilmadi!", show_alert=True)
        return

    await state.update_data(service_id=svc_id, service_name=svc.name)
    await state.set_state(OrderForm.entering_name)
    await callback.message.answer(
        f"✅ Tanlandi: <b>{svc.name}</b>\n\n"
        "👤 To'liq ismingizni kiriting:",
        reply_markup=back_kb(),
    )
    await callback.answer()


# ── 2. Ism kiritish ────────────────────────────────────────────

@router.message(OrderForm.entering_name)
async def name_entered(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return

    if not validate_name(message.text):
        await message.answer("❌ Ism kamida 2 ta harf bo'lishi kerak. Qayta kiriting:")
        return

    await state.update_data(client_name=message.text.strip())
    await state.set_state(OrderForm.entering_phone)
    await message.answer(
        "📱 Telefon raqamingizni yuboring:\n"
        "<i>(Misol: +998901234567 yoki tugmani bosing)</i>",
        reply_markup=contact_kb(),
    )


# ── 3. Telefon raqam ───────────────────────────────────────────

@router.message(OrderForm.entering_phone, F.contact)
async def phone_from_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await state.update_data(phone=phone)
    await _ask_comment(message, state)


@router.message(OrderForm.entering_phone, F.text)
async def phone_from_text(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(OrderForm.entering_name)
        await message.answer("👤 Ismingizni kiriting:", reply_markup=back_kb())
        return

    phone = validate_phone(message.text)
    if not phone:
        await message.answer(
            "❌ Raqam noto'g'ri formatda.\n"
            "To'g'ri misol: <code>+998901234567</code> yoki <code>901234567</code>"
        )
        return

    await state.update_data(phone=phone)
    await _ask_comment(message, state)


async def _ask_comment(message: Message, state: FSMContext):
    await state.set_state(OrderForm.entering_comment)
    await message.answer(
        "💬 Buyurtmangiz haqida qo'shimcha izoh yozing:\n"
        "<i>(O'tkazib yuborish mumkin)</i>",
        reply_markup=skip_back_kb(),
    )


# ── 4. Izoh ────────────────────────────────────────────────────

@router.message(OrderForm.entering_comment)
async def comment_entered(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(OrderForm.entering_phone)
        await message.answer("📱 Telefon raqamingizni yuboring:", reply_markup=contact_kb())
        return

    comment = None if message.text == "⏭ O'tkazib yuborish" else message.text.strip()
    await state.update_data(comment=comment)
    await state.set_state(OrderForm.uploading_file)
    await message.answer(
        "📎 Fayl yoki rasm yuklashingiz mumkin:\n"
        "<i>(O'tkazib yuborish mumkin)</i>",
        reply_markup=skip_back_kb(),
    )


# ── 5. Fayl yuklash ────────────────────────────────────────────

@router.message(OrderForm.uploading_file, F.document | F.photo)
async def file_uploaded(message: Message, state: FSMContext):
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_id = None

    await state.update_data(file_id=file_id)
    await _show_confirm(message, state)


@router.message(OrderForm.uploading_file, F.text)
async def file_skip(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(OrderForm.entering_comment)
        await message.answer("💬 Izoh yozing:", reply_markup=skip_back_kb())
        return
    await state.update_data(file_id=None)
    await _show_confirm(message, state)


async def _show_confirm(message: Message, state: FSMContext):
    """Tasdiqlash sahifasini ko'rsatish"""
    data = await state.get_data()
    svc_name = data.get("service_name", "—")
    text = (
        "📋 <b>Buyurtmangizni tekshiring:</b>\n\n"
        f"🛠 Xizmat: <b>{svc_name}</b>\n"
        f"👤 Ism: <b>{data.get('client_name')}</b>\n"
        f"📱 Telefon: <code>{data.get('phone')}</code>\n"
        f"💬 Izoh: {data.get('comment') or '—'}\n"
        f"📎 Fayl: {'✅ biriktirilgan' if data.get('file_id') else '—'}\n\n"
        "Tasdiqlaysizmi?"
    )
    await state.set_state(OrderForm.confirming)
    await message.answer(text, reply_markup=confirm_order_kb())


# ── 6. Tasdiqlash ──────────────────────────────────────────────

@router.message(OrderForm.confirming, F.text == "✅ Tasdiqlash")
async def confirm_order(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        user = await UserQueries.get_by_telegram_id(session, message.from_user.id)
        if not user:
            await message.answer("❌ Xatolik. Qaytadan /start bosing.")
            return

        order = await OrderQueries.create(
            session,
            user_id=user.id,
            service_id=data.get("service_id"),
            client_name=data["client_name"],
            phone=data["phone"],
            comment=data.get("comment"),
            file_id=data.get("file_id"),
        )
        # Service nomini olish
        svc = await ServiceQueries.get_by_id(session, data.get("service_id"))
        if svc:
            order.service = svc

    # Foydalanuvchiga tasdiq
    await message.answer(
        f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"🔢 Buyurtma raqami: <b>#{order.id}</b>\n"
        "Tez orada siz bilan bog'lanamiz. 🙏",
        reply_markup=main_menu_kb(),
    )

    # Adminga yuborish
    admin_text = (
        f"🔔 <b>YANGI BUYURTMA!</b>\n\n"
        f"📦 #{order.id} | 🛠 {data.get('service_name', '—')}\n"
        f"👤 {data['client_name']}\n"
        f"📱 <code>{data['phone']}</code>\n"
        f"🔗 tg://user?id={message.from_user.id}\n"
    )
    if data.get("comment"):
        admin_text += f"💬 {data['comment']}\n"
    admin_text += f"🕐 {order.created_at.strftime('%d.%m.%Y %H:%M')}"

    for admin_id in settings.ADMIN_IDS:
        try:
            if data.get("file_id"):
                await bot.send_document(
                    admin_id, data["file_id"],
                    caption=admin_text,
                    reply_markup=order_status_kb(order.id),
                )
            else:
                await bot.send_message(
                    admin_id, admin_text,
                    reply_markup=order_status_kb(order.id),
                )
        except Exception as e:
            log.error(f"Admin {admin_id} ga yuborishda xato: {e}")

    log.info(f"✅ Yangi buyurtma #{order.id} — {data['client_name']}")


@router.message(OrderForm.confirming, F.text == "✏️ Qayta kiritish")
async def restart_order(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔄 Qaytadan boshlanmoqda...",
        reply_markup=main_menu_kb(),
    )
    await start_order(message, state)


@router.message(OrderForm.confirming, F.text == "❌ Bekor qilish")
async def cancel_order(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Buyurtma bekor qilindi.", reply_markup=main_menu_kb())
