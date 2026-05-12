import os
import json
from datetime import datetime

import requests
from dotenv import load_dotenv
from flask import Flask, request


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOTENV_PATH = os.path.join(BASE_DIR, ".env")

# Загружаем переменные окружения из .env (если файл есть)
if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Нет BOT_TOKEN. Создай .env и добавь BOT_TOKEN=...")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

app = Flask(__name__)


# Дни и недели такие же, как в aiogram-версии
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


def schedule_path() -> str:
    return os.path.join(BASE_DIR, "schedule.json")


def load_schedule() -> dict:
    with open(schedule_path(), "r", encoding="utf-8") as f:
        return json.load(f)


# Главное меню с 3 кнопками
def main_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "📅 Расписание", "callback_data": "schedule"},
                {"text": "📝 Экзамены", "callback_data": "exams"},
                {"text": "✅ Зачеты", "callback_data": "credits"},
            ]
        ]
    }


# Клавиатура дней недели
def day_keyboard() -> dict:
    days_row = [
        {"text": title, "callback_data": f"day:{key}"}
        for key, title in DAYS
    ]
    back_row = [{"text": "🔙 Назад", "callback_data": "back"}]
    return {"inline_keyboard": [days_row, back_row]}


# Клавиатура "Назад"
def back_keyboard() -> dict:
    return {
        "inline_keyboard": [[{"text": "🔙 Назад", "callback_data": "back"}]]
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
        lines.append("")
    
    return "\n".join(lines).strip()


def format_credits() -> str:
    lines = ["✅ *ЗАЧЕТЫ*\n"]
    for credit in CREDITS:
        lines.append(f"📅 *{credit['date']}*")
        lines.append(f"📚 {credit['subject']}")
        lines.append(f"👤 {credit['teacher']}")
        lines.append(f"⏰ {credit['time']}")
        lines.append(f"🏫 {credit['room']}")
        lines.append("")
    
    return "\n".join(lines).strip()


def tg_request(method: str, params: dict) -> dict:
    """Вспомогательная функция для вызова Telegram Bot API."""
    url = TELEGRAM_API_URL + method
    resp = requests.post(url, json=params, timeout=10)
    try:
        return resp.json()
    except Exception:
        return {}


def handle_message(message: dict) -> None:
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text in ("/start", "start"):
        week = get_current_week()
        tg_request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": f"👋 Привет!\n📅 Текущая неделя: *{week}*\n\nВыбери действие 👇",
                "parse_mode": "Markdown",
                "reply_markup": main_keyboard(),
            },
        )
    else:
        tg_request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "Напиши /start чтобы открыть меню 🙂",
            },
        )


def handle_callback_query(callback_query: dict) -> None:
    data = callback_query.get("data") or ""
    message = callback_query.get("message") or {}
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    callback_id = callback_query.get("id")

    if not (chat_id and message_id and callback_id):
        return

    # Кнопка "Назад"
    if data == "back":
        week = get_current_week()
        tg_request(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"👋 Привет!\n📅 Текущая неделя: *{week}*\n\nВыбери действие 👇",
                "parse_mode": "Markdown",
                "reply_markup": main_keyboard(),
            },
        )
        tg_request("answerCallbackQuery", {"callback_query_id": callback_id})
        return

    # Кнопка "Расписание"
    if data == "schedule":
        week = get_current_week()
        tg_request(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": f"📅 *Расписание занятий*\n📅 Неделя: *{week}*\n\nВыбери день 👇",
                "parse_mode": "Markdown",
                "reply_markup": day_keyboard(),
            },
        )
        tg_request("answerCallbackQuery", {"callback_query_id": callback_id})
        return

    # Кнопка "Экзамены"
    if data == "exams":
        text = format_exams()
        tg_request(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": back_keyboard(),
            },
        )
        tg_request("answerCallbackQuery", {"callback_query_id": callback_id})
        return

    # Кнопка "Зачеты"
    if data == "credits":
        text = format_credits()
        tg_request(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": back_keyboard(),
            },
        )
        tg_request("answerCallbackQuery", {"callback_query_id": callback_id})
        return

    # Выбор дня
    if data.startswith("day:"):
        day = data.split(":", 1)[1]
        week = get_current_week()

        schedule = load_schedule()
        text = format_day(schedule, week, day)

        tg_request(
            "editMessageText",
            {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": day_keyboard(),
            },
        )
        tg_request("answerCallbackQuery", {"callback_query_id": callback_id})
        return

    # На всякий случай отвечаем на любой другой callback
    tg_request("answerCallbackQuery", {"callback_query_id": callback_id})


def handle_update(update: dict) -> None:
    """Роутер для входящих апдейтов Telegram."""
    if "message" in update:
        handle_message(update["message"])
    elif "callback_query" in update:
        handle_callback_query(update["callback_query"])


@app.get("/")
def index():
    return "Bot is running."


@app.post(f"/webhook/{BOT_TOKEN}")
def telegram_webhook():
    update = request.get_json(force=True, silent=True) or {}
    handle_update(update)
    # Telegram достаточно кода 200 без тела
    return "", 200


if __name__ == "__main__":
    # Локальный запуск для отладки (например, через ngrok)
    app.run(host="0.0.0.0", port=8000, debug=True)