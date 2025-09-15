# bot.py
import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from aiogram import types, F, Router, Bot
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from apscheduler.triggers.cron import CronTrigger
from aiogram.fsm.storage.memory import MemoryStorage


import os
import requests


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, time
import pytz

scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tashkent"))

from config import TOKEN
from db import init_db, add_user, get_user1,get_fulluserdata
from vocab import vocab_db, save_user_time,get_user,update_progress,reset_day,change_user_time,get_user11
from datetime import datetime, timedelta
init_db()
vocab_db()

router = Router()


AI_API_KEY = "TOKEN"
AI_API_URL = "SECRET"



class Register(StatesGroup):
    full_name = State()
    age = State()
    sat_score = State()
    phone = State()
    waiting_for_question= State()


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🤖 Ask AI")],
        [KeyboardButton(text="📅 SAT Exam Dates")],
        [KeyboardButton(text="📚 Vocabulary")],
        [KeyboardButton(text="📝 SAT English")],
        [KeyboardButton(text="➗ SAT Math")],
        [KeyboardButton(text="📐 Practise tests")],
        [KeyboardButton(text="📝 Weekly Mock Exam")],
        [KeyboardButton(text="📚 Materials")],
        [KeyboardButton(text="👤 Profile")],
        [KeyboardButton(text="❓ Help")]
    ],
    resize_keyboard=True
)

#MENU COMMMANDS 

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user=get_user1(message.from_user.id)
    if user:
        await message.answer("📌 Choose an option:", reply_markup=main_menu) 
        
    else:
        await message.answer("👋 Hello! Welcome to SAT Tutor Bot.\nLet's get you registered.")
        await message.answer("What is your full name?")
        await state.set_state(Register.full_name)       


@router.message(StateFilter(Register.full_name))
async def process_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await message.answer("Great! How old are you?")
    await state.set_state(Register.age)

@router.message(StateFilter(Register.age))
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Please enter a number for age.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Got it. What is your current SAT score?")
    await state.set_state(Register.sat_score)



@router.message(StateFilter(Register.sat_score))
async def process_sat_score(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Please enter a number for SAT score.")
        return
    await state.update_data(sat_score=int(message.text))

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Share phone number", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer("Last step! Please press the button to share your phone number.", reply_markup=kb)
    await state.set_state(Register.phone)



@router.message(StateFilter(Register.phone))
async def process_phone(message: Message, state: FSMContext):
    if not message.contact or not message.contact.phone_number:
        await message.answer("❌ Please use the button to share your phone number.")
        return

    await state.update_data(phone=message.contact.phone_number)

    data = await state.get_data()

    add_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        full_name=data['full_name'],
        age=data['age'],
        sat_score=data['sat_score'],
        phone=data['phone']
    )

    await message.answer(
        f"✅ Registration complete!\n\n"
        f"👤 Name: {data['full_name']}\n"
        f"🎂 Age: {data['age']}\n"
        f"📊 SAT Score: {data['sat_score']}\n"
        f"📞 Phone: {data['phone']}",
        reply_markup=None  
    )
    await message.answer("📌 Choose an option:", reply_markup=main_menu)

    await state.clear()

@router.message(F.text=="📚 Materials")
async def send_material(message: Message):
    await message.answer("Why did you clicked materials?!")

def generate_time_keyboard():
    buttons = []
    for hour in range(1, 13):
        am_button = InlineKeyboardButton(
            text=f"🕐 {hour} AM", callback_data=f"time_{hour:02d}:00"
        )
        pm_button = InlineKeyboardButton(
            text=f"🕐 {hour} PM", callback_data=f"time_{(hour % 12)+12:02d}:00"
        )
        buttons.append([am_button, pm_button])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "📚 Vocabulary")
async def vocab_menu(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="▶️ Start Learning")],
            [KeyboardButton(text="🔄 Change Reminder Time")],
            [KeyboardButton(text="📅 Review Previous Days")],
            [KeyboardButton(text="⬅️ Back")]
        ],
        resize_keyboard=True
    )
    await message.answer("📚 Welcome to Vocabulary practice!\nChoose an option:", reply_markup=kb)


def word_nav_keyboard(current: int, total: int) -> InlineKeyboardMarkup:
    buttons = []
    if current > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Back", callback_data=f"word_{current-1}"))
    if current < total - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"word_{current+1}"))
    else:
        buttons.append(InlineKeyboardButton(text="✅ Finish", callback_data="finish_day"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

import sqlite3
VOCAB_NAME="vocab.db"
async def reminder_job(bot: Bot, user_id: int):
    user = get_user11(user_id)
    if not user:
        return
    
    time, day, progress = user  # unpack correctly

    words = VOCAB.get(day, [])
    if not words:
        await bot.send_message(user_id, f"No words found for Day {day}.")
        return

   
    if progress >= len(words):
        await bot.send_message(user_id, f"✅ You’ve already finished Day {day}!")
        return

    
    word_index = progress
    word, definition = words[word_index]

    kb = word_nav_keyboard(word_index, len(words))
    await bot.send_message(
        user_id,
        f"⏰ Time to learn!\n📚 Day {day}\n\n📖 Word {word_index + 1}/{len(words)}\n<b>{word}</b> — {definition}",
        reply_markup=kb
    )


def schedule_user(bot: Bot, user_id: int, selected_time: str, start_day: int):
    hour, minute = map(int, selected_time.split(":"))

    scheduler.add_job(
        reminder_job,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=pytz.timezone("Asia/Tashkent")),
        args=[bot, user_id],
        id=f"user_{user_id}",
        replace_existing=True,
    )


VOCAB = {
    1: [
        ("abate", "to lessen, to diminish"),
        ("benevolent", "kind, charitable"),
        ("candid", "honest, truthful"),
        ("daunt", "to intimidate, discourage"),
        ("elated", "extremely happy"),
        ("foster", "to encourage growth or development"),
        ("galvanize", "to inspire into action"),
        ("hackneyed", "overused, cliché"),
        ("iconoclast", "one who challenges tradition"),
        ("jubilant", "joyful, triumphant")
    ],
    2: [
        ("kinetic", "related to motion"),
        ("laconic", "using few words"),
        ("malleable", "easily shaped or influenced"),
        ("nefarious", "evil, wicked"),
        ("obstinate", "stubborn"),
        ("paragon", "a perfect example"),
        ("quandary", "a difficult situation"),
        ("recluse", "a person who avoids others"),
        ("sagacious", "wise, shrewd"),
        ("taciturn", "silent, reserved")
    ],
    3: [
        ("rug5", "related to motion"),
        ("laconic", "using few words"),
        ("malleable", "easily shaped or influenced"),
        ("nefarious", "evil, wicked"),
        ("obstinate", "stubborn"),
        ("paragon", "a perfect example"),
        ("quandary", "a difficult situation"),
        ("recluse", "a person who avoids others"),
        ("sagacious", "wise, shrewd"),
        ("taciturn", "silent, reserved")
    ]
}
async def send_summary(bot: Bot, user_id: int, day: int):
    words = VOCAB.get(day, [])
    text = f"✅ Day {day} finished!\n\nToday's words:\n" + "\n".join([f"• {w} — {d}" for w, d in words])
    await bot.send_message(user_id, text)

    
    next_day = day + 1
    reset_day(user_id, next_day)

    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Change Reminder Time", callback_data="change_time")]
    ])
    await bot.send_message(user_id, "Come back tomorrow at your reminder time!", reply_markup=kb)



from datetime import datetime


@router.message(F.text=="🔄 Change Reminder Time")
async def change_time_reminder1(message:Message):
    kb = generate_time_keyboard()
    await message.answer("Choose option:", reply_markup=kb)




@router.message(F.text == "▶️ Start Learning")
async def start_learning(message: Message):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user:
        # First-time user, set default time and day
        save_user_time(user_id, "09:00", day=1)
        user = get_user(user_id)
    
    time_str, day, progress, next_reminder_str = user
    next_reminder = datetime.fromisoformat(next_reminder_str)
    now = datetime.now()
    
    if now < next_reminder:
        await message.answer(f"⏳ You have already completed today’s session.\n"
                             f"Your next session will be available at {time_str} tomorrow.")
        return

    # Proceed with learning
    words = VOCAB.get(day, [])
    if not words:
        await message.answer("No words found for today!")
        return

    # Send first word
    word = words[0]
    kb = word_nav_keyboard(0, len(words))
    await message.answer(f"📖 Word 1/{len(words)}\n\n<b>{word}</b> - definition here",
                         reply_markup=kb)

    
@router.callback_query(F.data.startswith("word_"))
async def navigate_words(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)

    if not user:
     save_user_time(user_id, "09:00", day=1)  # or whatever default
     user = get_user(user_id)
    _, day, *_ = user
    words = VOCAB.get(day, [])
    index = int(callback.data.split("_")[1])
    word = words[index]

    kb = word_nav_keyboard(index, len(words))
    await callback.message.edit_text(
        f"📖 Word {index+1}/{len(words)}\n\n<b>{word}</b> - definition here",
        reply_markup=kb
    )
@router.callback_query(F.data == "finish_day")
async def finish_day(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = get_user(user_id)
    if not user:
        return
    
    time_str, day, progress, next_reminder_str = user
    words = VOCAB.get(day, [])

    # Show summary
    text = f"🎉 Great job!\nYou’ve finished Day {day}.\n\nToday's words:\n" + \
           "\n".join([f"• {w}" for w in words])
    await callback.message.edit_text(text)

    # Set next day and schedule next reminder
    from datetime import datetime, timedelta
    next_reminder = datetime.now() + timedelta(days=1)
    conn = sqlite3.connect(VOCAB_NAME)
    c = conn.cursor()
    c.execute("UPDATE vocab_users SET current_day=?, progress=0, next_reminder=? WHERE user_id=?",
              (day + 1, next_reminder.isoformat(), user_id))
    conn.commit()
    conn.close()

    await callback.message.answer(
        f"✅ Done! You’ll get your next session tomorrow at {time_str}.\n"
        "If you want to change reminder time, you can do it later."
    )


@router.callback_query(F.data.startswith("time_"))
async def set_time(callback: CallbackQuery, bot: Bot):
    selected_time = callback.data.split("_")[1]  # e.g. "09:00"
    user_id = callback.from_user.id

    # Update time only, keep current_day intact
    change_user_time(user_id, selected_time)

    # Delete inline keyboard
    await callback.message.delete()

    # Schedule daily reminders (do not trigger immediate learning!)
    schedule_user(bot, user_id, selected_time, get_user(user_id)[1])

    await callback.message.answer(f"✅ Your reminder time has been changed to {selected_time}.")

@router.message(F.text=="⬅️ Back")
async def back_reply(message:Message, state: FSMContext):
    await state.clear()
    await message.answer("📌 Choose an option:", reply_markup=main_menu)

def review_days_keyboard(current_day: int):
    buttons = []
    for day in range(1, current_day):
        buttons.append([InlineKeyboardButton(text=f"📖 Day {day}", callback_data=f"review_{day}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(F.text=="📅 Review Previous Days")
async def reviewwords(message: Message):
    user_id = message.from_user.id
    user = get_user11(user_id)
    
    if not user:
        await message.answer("You haven't started learning yet! 📚")
        return

    # unpack correctly
    time, current_day, progress = user

    if current_day == 1:
        await message.answer("You haven't completed any days yet! 🕐")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"📖 Day {day}", callback_data=f"review_{day}")]
            for day in range(1, current_day)  # only past days
        ]
    )
    await message.answer("Select a day to review: 📖", reply_markup=kb)


@router.callback_query(F.data.startswith("review_"))
async def review_day_callback(callback: CallbackQuery):
    day = int(callback.data.split("_")[1])
    words = VOCAB.get(day, [])

    if not words:
        await callback.message.edit_text(f"No words found for Day {day}! ❌")
        return

    text = f"📖 Words from Day {day}:\n" + "\n".join([f"• {w} — {d}" for w, d in words])
    await callback.message.edit_text(text)



@router.message(F.text=="👤 Profile")
async def send_profile(message:Message):
    user=message.from_user.id
    profiile=get_fulluserdata(user)
    if profiile:
     text = (
        f"🆔 Your profile:\n\n"
        f"👤 Name: {profiile['full_name']}\n"
        f"🎂 Age: {profiile['age']}\n"
        f"📊 SAT Score: {profiile['sat_score']}\n"
        f"📞 Phone: {profiile['phone']}\n"
        f"💬 Username: @{profiile['username']}"
    )
     await message.answer(text)
    else:
        await message.answer(f"❌ You are not registered yet.\n"
                             f"⚙️ Click /start"
                        )
@router.message(F.text=="❓ Help")
async def send_help(message:Message):
    info=(
    f"Your personal AI companion for the SAT 🎓.\n"
    f"ℹ️ Buttons:\n"
    f"\n"
    f"\u00A0\u00A0\u00A0📅 SAT Exam Dates – Check upcoming SAT test days & deadlines \n"
    f"\u00A0\u00A0\u00A0📊 Statistics – Track your progress & performance\n"
    f"\u00A0\u00A0\u00A0✏️ Vocabulary – Learn and practice SAT words" )

    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Report a bug or problem",
                   url="https://t.me/helpersatbot_bot" )

    await message.answer(info,reply_markup=builder.as_markup())

@router.message(F.text=="📅 SAT Exam Dates")
async def send_satdates(message:Message):
    text=(
        f"🎓 SAT Exam Dates 2025 👇\n"
        f"\n"
        f"🕒 September 13, 2025 – Registration deadline: August 29, 2025\n"
        f"🕒 October 4, 2025 – Registration deadline: September 23, 2025\n"
        f"🕒 November 8, 2025 – Registration deadline: October 28, 2025\n"
        f"🕒 December 6, 2025 – Registration deadline: November 25, 2025\n"
        f"🕒 March 14, 2026 – Registration deadline: March 3, 2026\n"
        f"🕒 May 2, 2026 – Registration deadline: April 21, 2026\n"
        f"🕒 June 6, 2026 – Registration deadline: May 26, 2026\n"
        f"\n"
        f"ℹ️ For more info and official updates, visit the College Board site:\n"
        f"collegeboard.org"
    )
    await message.answer(text)

@router.message(F.text=="➗ SAT Math")
async def send_mathbutton(message:Message):
    text=(
        f"Hello,how are you?\n"
        f"It is time to learn Math part of SAT"
    )
    await message.answer(text)

@router.message(F.text=="🤖 Ask AI")
async def ai_model(message:Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Back")],
        ],
        resize_keyboard=True
    )
    await message.answer("Send me your question for AI 🤔", reply_markup=kb)
    await state.set_state(Register.waiting_for_question)

@router.message(StateFilter(Register.waiting_for_question))
async def ai_help(message: Message, state: FSMContext):
    question = message.text
    headers = {"Authorization": f"Bearer {AI_API_KEY}"}


    sat_prompt = f"""
You are an SAT Tutor. 
Only answer questions that are directly related to the SAT exam (English, Math, Reading/Writing, test-taking strategies). 
If the user asks about anything unrelated to SAT, reply exactly with:
"It will be good if you ask questions about SAT and only about SAT."

Now, provide a detailed explanation for the following SAT question, emulating the format used by the College Board in their SAT Suite Question Bank.

Question:
{question}

Your explanation must include:

1. Correct Answer Identification: Clearly state the correct answer choice.
2. Justification: Explain why this answer is correct, referencing specific parts of the question or passage as necessary.
3. Distractor Analysis: For each incorrect answer choice, provide a brief explanation of why it is not the best choice.
4. Content Domain and Skill: Identify the content domain (e.g., Information and Ideas, Craft and Structure) and the specific skill being assessed, as categorized by the College Board.

Ensure that your explanation is clear, concise, and educational, aiding in the understanding of the reasoning behind the correct answer.
"""

    data = {
    "model": "", 
    "messages": [{"role": "user", "content": sat_prompt}]
}

    response = requests.post(AI_API_URL, headers=headers, json=data)
    result = response.json()
    ai_answer = result["choices"][0]["message"]["content"]
    

    await message.answer(f"📘 SAT Tutor Answer:\n\n{ai_answer}",parse_mode="Markdown")


@router.message(F.text=="📝 SAT English")
async def send_verbal(message:Message):
    text=(
        f"Hello,how are you?\n"
        f"It is time to learn Verbal part of SAT"
    )
    await message.answer(text)

@router.message(F.text=="📝 Weekly Mock Exam")
async def mock_exam(message:Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🟢 Click Me",url="http://localhost:8080/")]])
    await message.answer("Mock exam:",reply_markup=kb)

# @router.message(F.text=="⏰ Test Reminder")
# async def test_reminder(message: Message):
#     user_id = message.from_user.id
#     await reminder_job(message.bot, user_id)
#     await message.answer("✅ Reminder triggered!")
@router.message(F.text=="📐 Practise tests")
async def practise_tests_bot(message:Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
        [InlineKeyboardButton(text="Practise test 1", callback_data="practise_one")],
        [InlineKeyboardButton(text="Practise test 2", callback_data="practise_two")]
    ]
    )
    kb_reply=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Back")]
        ],
        resize_keyboard=True



    )
    await message.answer("Choose one of the practise tests below",reply_markup=kb_reply)
    await message.answer("Here:", reply_markup=kb)



async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


