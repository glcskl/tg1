import json
import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Нет BOT_TOKEN. Создай .env и добавь BOT_TOKEN=...")

DAYS = [("пн", "Понедельник"), ("вт", "Вторник"), ("ср", "Среда"), ("чт", "Четверг"), ("пт", "Пятница")]

# Канал обязательной подписки
REQUIRED_CHANNEL = "@startupspacevstu"
CHANNEL_URL = "https://t.me/startupspacevstu"

SUB_TEXT = (
    "👋 Привет ребята!\n\n"
    "Новое расписание уже есть в боте — подпишитесь на канал *StartUp Space VSTU*, "
    "чтобы пользоваться расписанием 7 семестра 👇"
)


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ("creator", "administrator", "member", "restricted")
    except Exception as e:
        print(f"[SubCheck] ❌ Ошибка проверки подписки у {user_id}: {e}")
        return False


def subscription_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📢 Подписаться на канал", url=CHANNEL_URL)
    kb.button(text="🔄 Я подписался", callback_data="check_sub")
    kb.adjust(1)
    return kb.as_markup()

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
    {"date": "05.06.26", "subject": "Логистика и управление цепями поставок", "teacher": "Жучкевич О.Н.", "time": "15:40", "room": "4-502"},
]

# Определяем текущую неделю (числитель/знаменатель)
DEFAULT_GROUP = "4Ээб-4"
USER_GROUPS = {}


def get_current_week() -> str:
    week_number = datetime.now().isocalendar()[1]
    if week_number % 2 == 0:
        return "числитель"
    else:
        return "знаменатель"


def load_schedule() -> dict:
    with open(os.path.join(BASE_DIR, "schedule.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def load_assessments() -> dict:
    with open(os.path.join(BASE_DIR, "assessments.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def all_groups() -> list:
    data = load_assessments()
    return sorted(set(data.get("exams", {})) | set(data.get("credits", {})))


def get_group(user_id) -> str:
    return USER_GROUPS.get(user_id, DEFAULT_GROUP)


def set_group(user_id, group: str) -> None:
    if user_id:
        USER_GROUPS[user_id] = group


# Главное меню
def main_keyboard(user_id=None):
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Расписание", callback_data="schedule")
    kb.button(text="✅ Зачёты", callback_data="credits")
    kb.button(text="📝 Экзамены", callback_data="exams")
    kb.button(text=f"👥 Группа: {get_group(user_id)}", callback_data="groups")
    kb.adjust(1, 2, 1)
    return kb.as_markup()


def group_keyboard(prefix: str):
    kb = InlineKeyboardBuilder()
    for group in all_groups():
        kb.button(text=group, callback_data=f"{prefix}:{group}")
    kb.button(text="🔙 Назад", callback_data="back")
    kb.adjust(2)
    return kb.as_markup()


def assessment_keyboard(prefix: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 Сменить группу", callback_data=prefix)
    kb.button(text="🔙 Назад", callback_data="back")
    kb.adjust(1)
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


# Номер пары по времени начала звонка
PAIR_BY_START = {
    "08:00": 1,
    "09:50": 2,
    "11:40": 3,
    "14:00": 4,
    "15:45": 5,
    "17:30": 6,
    "19:15": 7,
}


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

        num = PAIR_BY_START.get(time.split("-")[0], i)
        title = subject
        if kind:
            kind_emoji = {"лк": "📖", "лб": "🔬", "пр": "✏️"}.get(kind, "📚")
            title = f"{subject} ({kind_emoji} {kind})"

        block = [f"{num}️⃣ ⏰ *{time}*", f"   📚 {title}"]

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


def format_group_assessments(kind: str, group: str) -> str:
    title = "ЭКЗАМЕНЫ" if kind == "exams" else "ЗАЧЕТЫ"
    icon = "📝" if kind == "exams" else "✅"
    items = load_assessments().get(kind, {}).get(group, [])
    lines = [f"{icon} *{title}*\n👥 Группа: *{group}*\n"]
    if not items:
        return "\n".join(lines).strip() + "\n\nНет данных по этой группе."
    for item in items:
        weekday = (item.get("weekday") or "").strip()
        date_line = f"📅 *{item['date']}*"
        if weekday:
            date_line += f" ({weekday})"
        lines.append(date_line)
        lines.append(f"📚 {item['subject']}")
        if item.get("teacher"):
            lines.append(f"👤 {item['teacher']}")
        lines.append(f"⏰ {item['time']}   🏫 {item['room']}")
        lines.append("")
    return "\n".join(lines).strip()


async def ensure_subscribed(cb: CallbackQuery) -> bool:
    if await is_subscribed(cb.bot, cb.from_user.id):
        return True
    await cb.message.edit_text(
        SUB_TEXT,
        reply_markup=subscription_keyboard(),
        parse_mode="Markdown"
    )
    await cb.answer()
    return False


# Последнее сообщение бота в чате (для самоочистки при новом /start)
_last_bot_message = {}


# Хендлеры
async def start(message: Message):
    chat_id = message.chat.id
    if not await is_subscribed(message.bot, message.from_user.id):
        prev = _last_bot_message.pop(chat_id, None)
        if prev:
            try:
                await message.bot.delete_message(chat_id, prev)
            except Exception:
                pass
        sent = await message.answer(SUB_TEXT, reply_markup=subscription_keyboard(), parse_mode="Markdown")
        _last_bot_message[chat_id] = sent.message_id
        return

    prev = _last_bot_message.pop(chat_id, None)
    if prev:
        try:
            await message.bot.delete_message(chat_id, prev)
        except Exception:
            pass

    week = get_current_week()
    sent = await message.answer(
        f"👋 Привет!\n📅 Текущая неделя: *{week}*\n👥 Группа: *{get_group(message.from_user.id)}*\n\nВыбери действие 👇",
        reply_markup=main_keyboard(message.from_user.id),
        parse_mode="Markdown"
    )
    _last_bot_message[chat_id] = sent.message_id


async def back_to_main(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return

    week = get_current_week()
    await cb.message.edit_text(
        f"👋 Привет!\n📅 Текущая неделя: *{week}*\n👥 Группа: *{get_group(cb.from_user.id)}*\n\nВыбери действие 👇",
        reply_markup=main_keyboard(cb.from_user.id),
        parse_mode="Markdown"
    )
    await cb.answer()


async def show_schedule_menu(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return

    week = get_current_week()
    await cb.message.edit_text(
        f"📅 *Расписание занятий*\n📅 Неделя: *{week}*\n\nВыбери день 👇",
        reply_markup=day_keyboard(),
        parse_mode="Markdown"
    )
    await cb.answer()


async def show_exams(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return
    await cb.message.edit_text(
        format_group_assessments("exams", get_group(cb.from_user.id)),
        reply_markup=assessment_keyboard("change_exams"),
        parse_mode="Markdown"
    )
    await cb.answer()


async def show_credits(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return
    await cb.message.edit_text(
        format_group_assessments("credits", get_group(cb.from_user.id)),
        reply_markup=assessment_keyboard("change_credits"),
        parse_mode="Markdown"
    )
    await cb.answer()


async def choose_group(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return
    await cb.message.edit_text(
        f"👥 Выбери группу (сейчас: *{get_group(cb.from_user.id)}*)",
        reply_markup=group_keyboard("group"),
        parse_mode="Markdown"
    )
    await cb.answer()


async def set_group_from_menu(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return
    set_group(cb.from_user.id, cb.data.split(":", 1)[1])
    await cb.message.edit_text(
        f"👥 Группа: *{get_group(cb.from_user.id)}*\n\nВыбери действие 👇",
        reply_markup=main_keyboard(cb.from_user.id),
        parse_mode="Markdown"
    )
    await cb.answer("Группа обновлена")


async def change_exams_group(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return
    await cb.message.edit_text(
        f"📝 Экзамены — выбери группу (сейчас: *{get_group(cb.from_user.id)}*)",
        reply_markup=group_keyboard("exams_group"),
        parse_mode="Markdown"
    )
    await cb.answer()


async def change_credits_group(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return
    await cb.message.edit_text(
        f"✅ Зачёты — выбери группу (сейчас: *{get_group(cb.from_user.id)}*)",
        reply_markup=group_keyboard("credits_group"),
        parse_mode="Markdown"
    )
    await cb.answer()


async def set_exams_group(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return
    group = cb.data.split(":", 1)[1]
    set_group(cb.from_user.id, group)
    await cb.message.edit_text(
        format_group_assessments("exams", group),
        reply_markup=assessment_keyboard("change_exams"),
        parse_mode="Markdown"
    )
    await cb.answer(f"Группа: {group}")


async def set_credits_group(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return
    group = cb.data.split(":", 1)[1]
    set_group(cb.from_user.id, group)
    await cb.message.edit_text(
        format_group_assessments("credits", group),
        reply_markup=assessment_keyboard("change_credits"),
        parse_mode="Markdown"
    )
    await cb.answer(f"Группа: {group}")


async def set_day(cb: CallbackQuery):
    if not await ensure_subscribed(cb):
        return

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
    dp.callback_query.register(back_to_main, F.data.in_({"back", "check_sub"}))
    dp.callback_query.register(show_schedule_menu, F.data == "schedule")
    dp.callback_query.register(show_exams, F.data == "exams")
    dp.callback_query.register(show_credits, F.data == "credits")
    dp.callback_query.register(set_day, F.data.startswith("day:"))
    dp.callback_query.register(choose_group, F.data == "groups")
    dp.callback_query.register(set_group_from_menu, F.data.startswith("group:"))
    dp.callback_query.register(change_exams_group, F.data == "change_exams")
    dp.callback_query.register(set_exams_group, F.data.startswith("exams_group:"))
    dp.callback_query.register(change_credits_group, F.data == "change_credits")
    dp.callback_query.register(set_credits_group, F.data.startswith("credits_group:"))
    dp.message.register(fallback)
    
    print("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())