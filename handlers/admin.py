"""
👑  Admin panel — to'liq boshqaruv
"""

import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Filter

from config import settings
from database.db import AsyncSessionLocal
from database.queries import UserQueries, ServiceQueries, OrderQueries
from database.models import OrderStatus, STATUS_LABELS
from keyboards.kb import (
    admin_menu_kb, main_menu_kb, admin_orders_filter_kb,
    admin_service_manage_kb, service_edit_actions_kb,
    order_status_kb, broadcast_confirm_kb, back_kb,
)
from states.forms import AdminAddService, AdminBroadcast
from utils.helpers import format_order

log = logging.getLogger(__name__)
router = Router()


# ── Admin filter ──────────────────────────────────────────────

class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in settings.ADMIN_IDS


router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


# ══════════════════════════════════════════════════════════════
#                     📊  STATISTIKA
# ══════════════════════════════════════════════════════════════

@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message):
    async with AsyncSessionLocal() as session:
        total_users   = await UserQueries.count(session)
        new_users     = await UserQueries.count_today(session)
        total_orders  = await OrderQueries.count(session)
        today_orders  = await OrderQueries.count_today(session)
        by_status     = await OrderQueries.count_by_status(session)
        popular       = await OrderQueries.popular_service(session)
        total_svc     = await ServiceQueries.count(session)

    status_lines = "\n".join(
        f"  {STATUS_LABELS.get(k, k)}: <b>{v}</b>"
        for k, v in by_status.items()
    )

    await message.answer(
        "📊 <b>BOT STATISTIKASI</b>\n"
        f"{'─'*30}\n"
        f"👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
        f"🆕 Bugun yangi: <b>{new_users}</b>\n\n"
        f"📦 Jami buyurtmalar: <b>{total_orders}</b>\n"
        f"🆕 Bugun: <b>{today_orders}</b>\n\n"
        f"📋 Buyurtmalar holati:\n{status_lines}\n\n"
        f"🏆 Eng mashhur xizmat: <b>{popular}</b>\n"
        f"🛠 Jami xizmatlar: <b>{total_svc}</b>"
    )


# ══════════════════════════════════════════════════════════════
#                     📦  BUYURTMALAR
# ══════════════════════════════════════════════════════════════

@router.message(F.text == "📦 Buyurtmalar")
async def admin_orders(message: Message):
    await message.answer(
        "📦 <b>Buyurtmalar</b>\n\nFiltr tanlang:",
        reply_markup=admin_orders_filter_kb(),
    )


@router.callback_query(F.data.startswith("filter_"))
async def filter_orders(callback: CallbackQuery):
    status_map = {
        "filter_new":        OrderStatus.NEW,
        "filter_in_process": OrderStatus.IN_PROCESS,
        "filter_done":       OrderStatus.DONE,
        "filter_cancelled":  OrderStatus.CANCELLED,
        "filter_all":        None,
    }
    status = status_map.get(callback.data)

    async with AsyncSessionLocal() as session:
        if status is None:
            orders = await OrderQueries.get_all(session, limit=20)
        else:
            orders = await OrderQueries.get_by_status(session, status)

    if not orders:
        await callback.answer("Buyurtma topilmadi.", show_alert=True)
        return

    await callback.message.edit_text(
        f"📦 <b>Buyurtmalar ({len(orders)} ta)</b>",
        reply_markup=admin_orders_filter_kb(),
    )

    for order in orders[:10]:
        text = format_order(order)
        try:
            await callback.message.answer(text, reply_markup=order_status_kb(order.id))
        except Exception:
            pass

    await callback.answer()


@router.callback_query(F.data.startswith("setstatus_"))
async def set_order_status(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    order_id = int(parts[1])
    new_status = OrderStatus(parts[2])

    async with AsyncSessionLocal() as session:
        await OrderQueries.update_status(session, order_id, new_status)
        order = await OrderQueries.get_by_id(session, order_id)

    if not order:
        await callback.answer("Buyurtma topilmadi!", show_alert=True)
        return

    label = STATUS_LABELS.get(new_status, new_status)
    await callback.answer(f"✅ Status yangilandi: {label}", show_alert=True)

    # Foydalanuvchiga xabar yuborish
    try:
        svc_name = order.service.name if order.service else "—"
        await bot.send_message(
            order.user.telegram_id,
            f"📦 <b>Buyurtmangiz yangilandi!</b>\n\n"
            f"🔢 #{order.id} | {svc_name}\n"
            f"📌 Holat: {label}"
        )
    except Exception as e:
        log.warning(f"Foydalanuvchiga xabar yuborib bo'lmadi: {e}")


@router.callback_query(F.data.startswith("msg_user_"))
async def admin_message_user(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    await state.update_data(reply_order_id=order_id)
    await callback.message.answer(
        f"💬 #{order_id} buyurtma egasiga xabar yozing:",
        reply_markup=back_kb(),
    )
    await callback.answer()


# ══════════════════════════════════════════════════════════════
#                     🛠  XIZMATLARNI BOSHQARISH
# ══════════════════════════════════════════════════════════════

@router.message(F.text == "🛠 Xizmatlarni boshqarish")
async def manage_services(message: Message):
    async with AsyncSessionLocal() as session:
        services = await ServiceQueries.get_all(session, active_only=False)

    await message.answer(
        "🛠 <b>Xizmatlar boshqaruvi</b>\n\nXizmatni tanlang yoki yangisini qo'shing:",
        reply_markup=admin_service_manage_kb(services),
    )


@router.callback_query(F.data.startswith("manage_svc_"))
async def service_manage_detail(callback: CallbackQuery):
    svc_id = int(callback.data.split("_")[2])
    async with AsyncSessionLocal() as session:
        svc = await ServiceQueries.get_by_id(session, svc_id)

    if not svc:
        await callback.answer("Topilmadi!", show_alert=True)
        return

    status = "✅ Faol" if svc.is_active else "🔴 Faol emas"
    await callback.message.edit_text(
        f"🛠 <b>{svc.name}</b>\n\n"
        f"📝 {svc.description or '—'}\n"
        f"💰 {svc.price or '—'}\n"
        f"👁 Holat: {status}",
        reply_markup=service_edit_actions_kb(svc.id),
    )
    await callback.answer()


@router.callback_query(F.data == "add_service")
async def add_service_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminAddService.name)
    await callback.message.answer("➕ <b>Yangi xizmat qo'shish</b>\n\nXizmat nomini kiriting:", reply_markup=back_kb())
    await callback.answer()


@router.message(AdminAddService.name)
async def add_service_name(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminAddService.description)
    await message.answer("📝 Xizmat tavsifini kiriting:")


@router.message(AdminAddService.description)
async def add_service_desc(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(AdminAddService.name)
        await message.answer("Xizmat nomini kiriting:")
        return
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminAddService.price)
    await message.answer("💰 Narxini kiriting (masalan: 200 000 so'm yoki Kelishiladi):")


@router.message(AdminAddService.price)
async def add_service_price(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(AdminAddService.description)
        await message.answer("Tavsifini kiriting:")
        return
    data = await state.get_data()
    await state.clear()

    async with AsyncSessionLocal() as session:
        svc = await ServiceQueries.create(
            session,
            name=data["name"],
            description=data["description"],
            price=message.text.strip(),
        )

    await message.answer(
        f"✅ Xizmat qo'shildi!\n\n"
        f"🛠 <b>{svc.name}</b>\n"
        f"💰 {svc.price}",
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data.startswith("toggle_svc_"))
async def toggle_service(callback: CallbackQuery):
    svc_id = int(callback.data.split("_")[2])
    async with AsyncSessionLocal() as session:
        new_state = await ServiceQueries.toggle_active(session, svc_id)
    status = "✅ faollashtirildi" if new_state else "🔴 o'chirildi"
    await callback.answer(f"Xizmat {status}", show_alert=True)
    await service_manage_detail(callback)


@router.callback_query(F.data.startswith("del_svc_"))
async def delete_service(callback: CallbackQuery):
    svc_id = int(callback.data.split("_")[2])
    async with AsyncSessionLocal() as session:
        await ServiceQueries.delete(session, svc_id)
        services = await ServiceQueries.get_all(session, active_only=False)

    await callback.message.edit_text(
        "🗑 Xizmat o'chirildi.\n\nBoshqa xizmatlarni boshqaring:",
        reply_markup=admin_service_manage_kb(services),
    )
    await callback.answer("✅ O'chirildi")


@router.callback_query(F.data == "back_to_svc_list")
async def back_svc_list(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        services = await ServiceQueries.get_all(session, active_only=False)
    await callback.message.edit_text(
        "🛠 <b>Xizmatlar boshqaruvi</b>:",
        reply_markup=admin_service_manage_kb(services),
    )
    await callback.answer()


# ══════════════════════════════════════════════════════════════
#                     👥  FOYDALANUVCHILAR
# ══════════════════════════════════════════════════════════════

@router.message(F.text == "👥 Foydalanuvchilar")
async def admin_users(message: Message):
    async with AsyncSessionLocal() as session:
        users = await UserQueries.get_all(session, limit=20)
        total = await UserQueries.count(session)

    text = f"👥 <b>Foydalanuvchilar (jami: {total})</b>\n\n"
    for u in users[:15]:
        banned = "🚫" if u.is_banned else "✅"
        uname = f"@{u.username}" if u.username else "—"
        text += f"{banned} <b>{u.full_name}</b> ({uname})\n  ID: <code>{u.telegram_id}</code>\n\n"

    await message.answer(text)


# ══════════════════════════════════════════════════════════════
#                     📢  BROADCAST
# ══════════════════════════════════════════════════════════════

@router.message(F.text == "📢 Broadcast")
async def broadcast_start(message: Message, state: FSMContext):
    await state.set_state(AdminBroadcast.writing)
    await message.answer(
        "📢 <b>Broadcast xabar</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni yozing:\n"
        "<i>(Bekor qilish uchun 🔙 Orqaga)</i>",
        reply_markup=back_kb(),
    )


@router.message(AdminBroadcast.writing)
async def broadcast_written(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_menu_kb())
        return

    await state.update_data(broadcast_text=message.text)
    await state.set_state(AdminBroadcast.confirm)

    async with AsyncSessionLocal() as session:
        count = await UserQueries.count(session)

    await message.answer(
        f"📢 <b>Xabar:</b>\n{message.text}\n\n"
        f"👥 Qabul qiluvchilar: <b>{count} ta</b>\n\n"
        "Yuborilsinmi?",
        reply_markup=broadcast_confirm_kb(),
    )


@router.callback_query(AdminBroadcast.confirm, F.data == "broadcast_confirm")
async def broadcast_send(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    text = data["broadcast_text"]

    async with AsyncSessionLocal() as session:
        user_ids = await UserQueries.get_all_ids(session)

    sent, failed = 0, 0
    status_msg = await callback.message.answer(f"📤 Yuborilmoqda... 0/{len(user_ids)}")

    for i, uid in enumerate(user_ids, 1):
        try:
            await bot.send_message(uid, f"📢 <b>E'lon:</b>\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
        if i % 20 == 0:
            try:
                await status_msg.edit_text(f"📤 Yuborilmoqda... {i}/{len(user_ids)}")
            except Exception:
                pass
        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"✅ <b>Broadcast tugadi!</b>\n\n"
        f"📤 Yuborildi: <b>{sent}</b>\n"
        f"❌ Yuborilmadi: <b>{failed}</b>"
    )
    await callback.answer()


@router.callback_query(AdminBroadcast.confirm, F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi.")
    await callback.answer()
