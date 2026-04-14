"""
🔄  Umumiy handler — noma'lum xabarlar
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from keyboards.kb import main_menu_kb

router = Router()


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("❌ Amal bekor qilindi.", reply_markup=main_menu_kb())
    else:
        await message.answer("Hech qanday faol amal yo'q.", reply_markup=main_menu_kb())


@router.message(F.text == "🔙 Orqaga")
async def global_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_kb())
