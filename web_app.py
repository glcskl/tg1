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


def schedule_path() -> str:
    return os.path.join(BASE_DIR, "schedule.json")


def load_schedule() -> dict:
    with open(schedule_path(), "r", encoding="utf-8") as f:
        return json.load(f)


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


def day_keyboard() -> dict:
    """Инлайн-клавиатура для выбора дня."""
    days_row = [
        {"text": title, "callback_data": f"day:{key}"}
        for key, title in DAYS
    ]

    return {"inline_keyboard": [days_row]}


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
    user_id = message.get("from", {}).get("id")
    text = (message.get("text") or "").strip()

    if not user_id:
        return

    if text in ("/start", "start"):
        user_state[user_id] = {"day": None}
        week = get_current_week()
        tg_request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": f"Привет! Текущая неделя: *{week}*\nВыбери день 👇",
                "parse_mode": "Markdown",
                "reply_markup": day_keyboard(),
            },
        )
    else:
        tg_request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "Напиши /start чтобы открыть меню расписания 🙂",
            },
        )


def handle_callback_query(callback_query: dict) -> None:
    data = callback_query.get("data") or ""
    message = callback_query.get("message") or {}
    chat_id = message.get("chat", {}).get("id")
    message_id = message.get("message_id")
    user_id = callback_query.get("from", {}).get("id")
    callback_id = callback_query.get("id")

    if not (chat_id and message_id and user_id and callback_id):
        return

    # Обработка выбора дня
    if data.startswith("day:"):
        day = data.split(":", 1)[1]
        st = user_state.setdefault(user_id, {"day": None})
        week = get_current_week()

        schedule = load_schedule()
        text = format_day(schedule, week, day)

        st["day"] = day
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
