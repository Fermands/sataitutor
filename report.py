import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import init_db, add_user, get_user,get_fulluserdata

class Register(StatesGroup):
    problem=State()

TOKEN ="token"
router = Router()
bot = Bot(token=TOKEN)

@router.message(CommandStart())
async def start_bot(message:Message,state:FSMContext):
    await message.answer(text="🚨 Report a bug or problem here:")
    await state.set_state(Register.problem)
@router.message(StateFilter(Register.problem))
async def send_prove(message: Message, state: FSMContext):
    user=message.from_user.id
    username=message.from_user.username
    user_report=message.text
    await message.answer(text="✅ We have received your problem/bug and will get in touch with you soon.")
    group_id= -group
    report = (
        f"⚠️ NEW BUG OR PROBLEM\n"
        f"🆔 ID:{user}\n"
        f"🆔 Username: @{username}\n"
        f"❌ BUG/PROBLEM: {user_report}"

    )
    await bot.send_message(group_id,report)

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

