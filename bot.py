import json
import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Нет BOT_TOKEN. Создай .env и добавь BOT_TOKEN=...")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DAYS = [("пн", "Пн"), ("вт", "Вт"), ("ср", "Ср"), ("чт", "Чт"), ("пт", "Пт")]

# Определяем текущую неделю (числитель/знаменатель)
def get_current_week() -> str:
    # Узнаем номер недели в году
    week_number = datetime.now().isocalendar()[1]
    # Четная неделя - знаменатель, нечетная - числитель
    if week_number % 2 == 1:
        return "числитель"
    else:
        return "знаменатель"


# В памяти держим выбор пользователя: { user_id: {"day": "..."} }
user_state: dict[int, dict[str, str | None]] = {}


def load_schedule() -> dict:
    with open("schedule.json", "r", encoding="utf-8") as f:
        return json.load(f)


def day_keyboard():
    kb = InlineKeyboardBuilder()
    for key, title in DAYS:
        kb.button(text=title, callback_data=f"day:{key}")
    kb.adjust(5)
    return kb.as_markup()


def format_day(schedule: dict, week: str, day: str) -> str:
    items = schedule.get(week, {}).get(day, [])
    day_name = dict(DAYS).get(day, day)

    header = f"📅 *{day_name.upper()}* — *{week}*\n"
    if not items:
        return header + "\nНет пар ✅"

    lines = [header]
    # Для понедельника начинаем нумерацию с 2
    start_number = 2 if day == "пн" else 1
    for i, it in enumerate(items, start_number):
        time = (it.get("time") or "").strip()
        subject = (it.get("subject") or "").strip()
        kind = (it.get("kind") or "").strip()
        teacher = (it.get("teacher") or "").strip()
        room = (it.get("room") or "").strip()

        title = subject
        if kind:
            title = f"{subject} ({kind})"

        block = [f"{i}) ⏰ *{time}*", f"   📚 {title}"]

        if teacher:
            block.append(f"   👤 {teacher}")
        if room:
            block.append(f"   🏫 {room}")

        lines.append("\n".join(block))

    return "\n\n".join(lines).strip()


@dp.message(F.text.in_({"/start", "start"}))
async def start(message: Message):
    user_state[message.from_user.id] = {"day": None}
    week = get_current_week()
    await message.answer(
        f"Привет! Текущая неделя: *{week}*\nВыбери день 👇",
        reply_markup=day_keyboard(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("day:"))
async def set_day(cb: CallbackQuery):
    day = cb.data.split(":", 1)[1]
    st = user_state.setdefault(cb.from_user.id, {"day": None})
    week = get_current_week()

    schedule = load_schedule()
    text = format_day(schedule, week, day)

    st["day"] = day
    await cb.message.edit_text(
        text,
        reply_markup=day_keyboard(),
        parse_mode="Markdown"
    )
    await cb.answer()


@dp.message()
async def fallback(message: Message):
    await message.answer("Напиши /start чтобы открыть меню расписания 🙂")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
