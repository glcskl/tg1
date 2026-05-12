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

DAYS = [("пн", "Понедельник"), ("вт", "Вторник"), ("ср", "Среда"), ("чт", "Четверг"), ("пт", "Пятница")]

# Данные экзаменов
EXAMS = [
    {"date": "11.06.26", "subject": "Основы машинного обучения", "teacher": "Никонова Т.В.", "time": "8:30", "room": "4-506"},
    {"date": "15.06.26", "subject": "Системы управления веб-контентом", "teacher": "Бизюк А.Н.", "time": "8:30", "room": "122"},
    {"date": "19.06.26", "subject": "Электронные финансы", "teacher": "Советникова О.П.", "time": "8:30", "room": "4-310"},
    {"date": "23.06.26", "subject": "Электронный бизнес", "teacher": "Краенкова К.И.", "time": "8:30", "room": "4-318"},
    {"date": "27.06.26", "subject": "Анализ хозяйственной деятельности", "teacher": "Солодкий Д.Т.", "time": "8:30", "room": "4-702"},
]

# Данные зачетов
CREDITS = [
    {"date": "01.06.26", "subject": "Институциональная система информационного общества", "teacher": "Грузневич Е.С.", "time": "11:40", "room": "4-311"},
    {"date": "02.06.26", "subject": "Физическая культура", "teacher": "Козлов А.Н.", "time": "9:50", "room": "Главный спортзал"},
    {"date": "04.06.26", "subject": "Теория отраслевых рынков", "teacher": "Демидова М.А.", "time": "11:40", "room": "4-502"},
    {"date": "04.06.26", "subject": "Логистика и управление цепями поставок", "teacher": "Жучкевич О.Н.", "time": "15:40", "room": "4-502"},
]

# Определяем текущую неделю (числитель/знаменатель)
def get_current_week() -> str:
    week_number = datetime.now().isocalendar()[1]
    if week_number % 2 == 0:
        return "числитель"
    else:
        return "знаменатель"


def load_schedule() -> dict:
    with open("schedule.json", "r", encoding="utf-8") as f:
        return json.load(f)


# Главное меню с 3 кнопками
def main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Расписание", callback_data="schedule")
    kb.button(text="📝 Экзамены", callback_data="exams")
    kb.button(text="✅ Зачеты", callback_data="credits")
    kb.adjust(3)
    return kb.as_markup()


# Клавиатура дней недели
def day_keyboard():
    kb = InlineKeyboardBuilder()
    for key, title in DAYS:
        kb.button(text=title, callback_data=f"day:{key}")
    kb.button(text="🔙 Назад", callback_data="back")
    kb.adjust(5, 1)
    return kb.as_markup()


# Клавиатура "Назад"
def back_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="back")
    return kb.as_markup()


def format_day(schedule: dict, week: str, day: str) -> str:
    items = schedule.get(week, {}).get(day, [])
    day_name = dict(DAYS).get(day, day)

    header = f"📅 *{day_name.upper()}*\n📅 Неделя: *{week}*\n"
    if not items:
        return header + "\n✅ Нет пар"

    lines = [header]
    for i, it in enumerate(items, 1):
        time = (it.get("time") or "").strip()
        subject = (it.get("subject") or "").strip()
        kind = (it.get("kind") or "").strip()
        teacher = (it.get("teacher") or "").strip()
        room = (it.get("room") or "").strip()

        title = subject
        if kind:
            kind_emoji = {"лк": "📖", "лб": "🔬", "пр": "✏️"}.get(kind, "📚")
            title = f"{subject} ({kind_emoji} {kind})"

        block = [f"{i}️⃣ ⏰ *{time}*", f"   📚 {title}"]

        if teacher:
            block.append(f"   👤 {teacher}")
        if room:
            block.append(f"   🏫 {room}")

        lines.append("\n".join(block))

    return "\n\n".join(lines).strip()


def format_exams() -> str:
    lines = ["📝 *ЭКЗАМЕНЫ*\n"]
    for exam in EXAMS:
        lines.append(f"📅 *{exam['date']}*")
        lines.append(f"📚 {exam['subject']}")
        lines.append(f"👤 {exam['teacher']}")
        lines.append(f"⏰ {exam['time']}")
        lines.append(f"🏫 Кабинет: {exam['room']}")
        lines.append("")  # Пустая строка между экзаменами
    
    return "\n".join(lines).strip()


def format_credits() -> str:
    lines = ["✅ *ЗАЧЕТЫ*\n"]
    for credit in CREDITS:
        lines.append(f"📅 *{credit['date']}*")
        lines.append(f"📚 {credit['subject']}")
        lines.append(f"👤 {credit['teacher']}")
        lines.append(f"⏰ {credit['time']}")
        lines.append(f"🏫 {credit['room']}")
        lines.append("")  # Пустая строка между зачетами
    
    return "\n".join(lines).strip()


# Хендлеры
async def start(message: Message):
    week = get_current_week()
    await message.answer(
        f"👋 Привет!\n📅 Текущая неделя: *{week}*\n\nВыбери действие 👇",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )


async def back_to_main(cb: CallbackQuery):
    week = get_current_week()
    await cb.message.edit_text(
        f"👋 Привет!\n📅 Текущая неделя: *{week}*\n\nВыбери действие 👇",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )
    await cb.answer()


async def show_schedule_menu(cb: CallbackQuery):
    week = get_current_week()
    await cb.message.edit_text(
        f"📅 *Расписание занятий*\n📅 Неделя: *{week}*\n\nВыбери день 👇",
        reply_markup=day_keyboard(),
        parse_mode="Markdown"
    )
    await cb.answer()


async def show_exams(cb: CallbackQuery):
    text = format_exams()
    await cb.message.edit_text(
        text,
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )
    await cb.answer()


async def show_credits(cb: CallbackQuery):
    text = format_credits()
    await cb.message.edit_text(
        text,
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )
    await cb.answer()


async def set_day(cb: CallbackQuery):
    day = cb.data.split(":", 1)[1]
    week = get_current_week()

    schedule = load_schedule()
    text = format_day(schedule, week, day)

    await cb.message.edit_text(
        text,
        reply_markup=day_keyboard(),
        parse_mode="Markdown"
    )
    await cb.answer()


async def fallback(message: Message):
    await message.answer("Напиши /start чтобы открыть меню 🙂")


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрируем хендлеры
    dp.message.register(start, F.text.in_({"/start", "start"}))
    dp.callback_query.register(back_to_main, F.data == "back")
    dp.callback_query.register(show_schedule_menu, F.data == "schedule")
    dp.callback_query.register(show_exams, F.data == "exams")
    dp.callback_query.register(show_credits, F.data == "credits")
    dp.callback_query.register(set_day, F.data.startswith("day:"))
    dp.message.register(fallback)
    
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())