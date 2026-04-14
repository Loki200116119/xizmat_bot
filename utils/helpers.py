"""
🔧  Yordamchi funksiyalar
"""

import re
from database.models import Order, OrderStatus, STATUS_LABELS, Service


def format_order(order: Order, show_user: bool = True) -> str:
    """Buyurtmani chiroyli ko'rinishda formatlash"""
    status_label = STATUS_LABELS.get(order.status, order.status)
    svc_name = order.service.name if order.service else "—"
    lines = [
        f"📦 <b>Buyurtma #{order.id}</b>",
        f"📌 Holat: {status_label}",
        f"🛠 Xizmat: {svc_name}",
    ]
    if show_user:
        lines.append(f"👤 Mijoz: <b>{order.client_name}</b>")
        lines.append(f"📱 Telefon: <code>{order.phone}</code>")
        if order.user:
            uname = f"@{order.user.username}" if order.user.username else f"id:{order.user.telegram_id}"
            lines.append(f"🔗 Telegram: {uname}")
    if order.comment:
        lines.append(f"💬 Izoh: {order.comment}")
    if order.file_id:
        lines.append("📎 Fayl biriktirilgan")
    lines.append(f"🕐 {order.created_at.strftime('%d.%m.%Y %H:%M')}")
    return "\n".join(lines)


def format_service(svc: Service) -> str:
    """Xizmatni chiroyli ko'rinishda formatlash"""
    lines = [
        f"🛠 <b>{svc.name}</b>",
    ]
    if svc.description:
        lines.append(f"\n{svc.description}")
    if svc.price:
        lines.append(f"\n💰 <b>Narxi:</b> {svc.price}")
    return "\n".join(lines)


def validate_phone(phone: str) -> str | None:
    """Telefon raqamni tekshirish va normallashtirish"""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    if digits.startswith("8") and len(digits) == 11:
        return f"+7{digits[1:]}"
    if len(digits) == 9:
        return f"+998{digits}"
    return None


def validate_name(name: str) -> bool:
    return 2 <= len(name.strip()) <= 100


def paginate(items: list, page: int, per_page: int) -> tuple[list, int]:
    """Sahifalash: (sahifa elementi, jami sahifalar)"""
    total_pages = max(1, (len(items) + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    return items[start:start + per_page], total_pages
