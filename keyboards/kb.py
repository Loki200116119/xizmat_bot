"""
⌨️  Barcha klaviaturalar — reply va inline
"""

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import Service, Order, OrderStatus, STATUS_LABELS


# ══════════════════════════════════════════════════════════════
#                    📌  REPLY KEYBOARDS
# ══════════════════════════════════════════════════════════════

def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛠 Xizmatlar"), KeyboardButton(text="📝 Buyurtma berish")],
            [KeyboardButton(text="📋 Buyurtmalarim"), KeyboardButton(text="ℹ️ Biz haqimizda")],
            [KeyboardButton(text="📞 Bog'lanish"), KeyboardButton(text="❓ Yordam")],
            [KeyboardButton(text="🤖 AI bilan suhbat")],
        ],
        resize_keyboard=True,
    )


def admin_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Buyurtmalar"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="🛠 Xizmatlarni boshqarish"), KeyboardButton(text="👥 Foydalanuvchilar")],
            [KeyboardButton(text="🤖 AI bilan suhbat"), KeyboardButton(text="📢 Broadcast")],
            [KeyboardButton(text="🏠 Asosiy menyu")],
        ],
        resize_keyboard=True,
    )


def contact_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True,
    )


def skip_back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ O'tkazib yuborish")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True,
    )


def confirm_order_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Tasdiqlash")],
            [KeyboardButton(text="✏️ Qayta kiritish"), KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
    )


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# ══════════════════════════════════════════════════════════════
#                    🔘  INLINE KEYBOARDS
# ══════════════════════════════════════════════════════════════

def services_inline_kb(services: list[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        builder.button(
            text=f"{'✅' if svc.is_active else '🔴'} {svc.name}",
            callback_data=f"svc_{svc.id}"
        )
    builder.adjust(1)
    return builder.as_markup()


def service_detail_kb(service_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Buyurtma berish", callback_data=f"order_svc_{service_id}")],
        [InlineKeyboardButton(text="🔙 Xizmatlar", callback_data="back_to_services")],
    ])


def order_status_kb(order_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status, label in STATUS_LABELS.items():
        builder.button(
            text=label,
            callback_data=f"setstatus_{order_id}_{status.value}"
        )
    builder.button(text="💬 Xabar yuborish", callback_data=f"msg_user_{order_id}")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


def admin_orders_filter_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🆕 Yangi",        callback_data="filter_new")
    builder.button(text="⚙️ Jarayonda",    callback_data="filter_in_process")
    builder.button(text="✅ Tugallangan",  callback_data="filter_done")
    builder.button(text="❌ Bekor",        callback_data="filter_cancelled")
    builder.button(text="📋 Hammasi",      callback_data="filter_all")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def admin_service_manage_kb(services: list[Service]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for svc in services:
        status = "✅" if svc.is_active else "🔴"
        builder.button(text=f"{status} {svc.name}", callback_data=f"manage_svc_{svc.id}")
    builder.button(text="➕ Yangi xizmat qo'shish", callback_data="add_service")
    builder.adjust(1)
    return builder.as_markup()


def service_edit_actions_kb(service_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Nomini o'zgartir", callback_data=f"edit_name_{service_id}"),
            InlineKeyboardButton(text="💰 Narxini o'zgartir", callback_data=f"edit_price_{service_id}"),
        ],
        [
            InlineKeyboardButton(text="📝 Tavsifini o'zgartir", callback_data=f"edit_desc_{service_id}"),
            InlineKeyboardButton(text="👁 Ko'rinishni o'zgartir", callback_data=f"toggle_svc_{service_id}"),
        ],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"del_svc_{service_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_svc_list")],
    ])


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Bekor", callback_data="broadcast_cancel"),
        ]
    ])
