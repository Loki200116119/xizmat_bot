import logging
import os

from aiogram import Router, F, types
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv
from google import genai

from states.forms import AIChat

load_dotenv()

router = Router()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


async def get_ai_response(user_text: str) -> str:
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=user_text,
        )

        if hasattr(response, "text") and response.text:
            return response.text

        return "Javob olinmadi."
    except Exception:
        logging.exception("Gemini xatoligi")
        return "Kechirasiz, AI hozir javob bera olmadi."


@router.message(F.text == "🤖 AI bilan suhbat")
async def enter_ai_chat(message: types.Message, state: FSMContext):
    await state.set_state(AIChat.chatting)
    await message.answer(
        "🤖 AI bilan suhbat boshlandi.\n"
        "Savolingizni yozing.\n"
        "Chiqish uchun /stop deb yozing."
    )


@router.message(F.text == "/stop")
async def stop_ai_chat(message: types.Message, state: FSMContext):
    if await state.get_state() == AIChat.chatting.state:
        await state.clear()
        await message.answer("AI suhbat tugatildi.")
    else:
        await message.answer("Siz AI rejimida emassiz.")


@router.message(AIChat.chatting, F.text)
async def ai_chat_handler(message: types.Message, state: FSMContext):
    await message.bot.send_chat_action(
        chat_id=message.chat.id,
        action=ChatAction.TYPING,
    )

    reply = await get_ai_response(message.text)
    await message.answer(reply)