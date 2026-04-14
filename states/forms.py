"""
🧩  FSM States — barcha holat mashinalari
"""

from aiogram.fsm.state import State, StatesGroup


class OrderForm(StatesGroup):
    """Buyurtma berish jarayoni"""
    choosing_service = State()   # Xizmat tanlash
    entering_name    = State()   # Ism kiritish
    entering_phone   = State()   # Telefon raqam
    entering_comment = State()   # Izoh
    uploading_file   = State()   # Fayl yuklash (ixtiyoriy)
    confirming       = State()   # Tasdiqlash


class AdminAddService(StatesGroup):
    """Admin: yangi xizmat qo'shish"""
    name        = State()
    description = State()
    price       = State()


class AdminEditService(StatesGroup):
    """Admin: xizmatni tahrirlash"""
    choosing  = State()
    field     = State()
    new_value = State()


class AdminBroadcast(StatesGroup):
    """Admin: broadcast xabar"""
    writing   = State()
    confirm   = State()


class AdminOrderStatus(StatesGroup):
    """Admin: buyurtma statusini o'zgartirish"""
    choosing_status = State()
class AIChat(StatesGroup):
    chatting = State()