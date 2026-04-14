"""
🛠  Xizmatlar handler
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.db import AsyncSessionLocal
from database.queries import ServiceQueries
from keyboards.kb import services_inline_kb, service_detail_kb, main_menu_kb
from utils.helpers import format_service

router = Router()


@router.message(F.text == "🛠 Xizmatlar")
async def show_services(message: Message):
    async with AsyncSessionLocal() as session:
        services = await ServiceQueries.get_all(session, active_only=True)

    if not services:
        await message.answer("😔 Hozircha mavjud xizmatlar yo'q.")
        return

    await message.answer(
        "🛠 <b>Bizning xizmatlarimiz</b>\n\nQiziqtirgan xizmatni tanlang:",
        reply_markup=services_inline_kb(services),
    )


@router.callback_query(F.data.startswith("svc_"))
async def service_detail(callback: CallbackQuery):
    service_id = int(callback.data.split("_")[1])
    async with AsyncSessionLocal() as session:
        svc = await ServiceQueries.get_by_id(session, service_id)

    if not svc or not svc.is_active:
        await callback.answer("❌ Xizmat topilmadi yoki faol emas.", show_alert=True)
        return

    await callback.message.edit_text(
        format_service(svc),
        reply_markup=service_detail_kb(svc.id),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery):
    async with AsyncSessionLocal() as session:
        services = await ServiceQueries.get_all(session, active_only=True)

    await callback.message.edit_text(
        "🛠 <b>Bizning xizmatlarimiz</b>\n\nQiziqtirgan xizmatni tanlang:",
        reply_markup=services_inline_kb(services),
    )
    await callback.answer()
