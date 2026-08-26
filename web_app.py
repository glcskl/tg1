import os
import json
import threading
import time
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

# URL для self-ping (устанавливается автоматически на Render)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

app = Flask(__name__)

# ============================================
# SELF-PING MECHANISM (предотвращает засыпание)
# ============================================

def register_webhook():
    """Автоматически регистрирует webhook при старте на Render."""
    if not RENDER_EXTERNAL_URL:
        return
    webhook_url = f"{RENDER_EXTERNAL_URL}/webhook/{BOT_TOKEN}"
    try:
        result = tg_request(
            "setWebhook",
            {
                "url": webhook_url,
                "allowed_updates": ["message", "callback_query"],
                "drop_pending_updates": True,
            },
        )
        if result.get("ok"):
            print(f"[Webhook] ✅ Зарегистрирован: {webhook_url}")
        else:
            print(f"[Webhook] ❌ Ошибка: {result.get('description')}")
    except Exception as e:
        print(f"[Webhook] ❌ Ошибка: {e}")


def self_ping_worker():
    """
    Фоновый поток для периодического self-ping.
    Render усыпляет сервис через 15 минут неактивности.
    Пинг каждые 10 минут держит сервис активным.
    """
    # Ждем 10 секунд, чтобы сервер успел запуститься, и регистрируем webhook
    time.sleep(10)
    register_webhook()

    # Ждем 30 секунд при старте, чтобы сервер успел запуститься
    time.sleep(30)
    
    while True:
        try:
            if RENDER_EXTERNAL_URL:
                # Пингуем сами себя
                response = requests.get(
                    f"{RENDER_EXTERNAL_URL}/health",
                    timeout=30,
                    headers={"User-Agent": "SelfPing/1.0"}
                )
                if response.status_code == 200:
                    print(f"[Keep-Alive] ✅ Self-ping успешен")
                else:
                    print(f"[Keep-Alive] ⚠️ Self-ping статус: {response.status_code}")
            else:
                # Если нет RENDER_EXTERNAL_URL, просто логируем
                pass
        except Exception as e:
            print(f"[Keep-Alive] ❌ Ошибка self-ping: {e}")
        
        # Пинг каждые 10 минут (600 секунд)
        # Render усыпляет через 15 минут, так что 10 минут - безопасный интервал
        time.sleep(600)


# Запускаем self-ping поток только если мы на Render
if RENDER_EXTERNAL_URL:
    ping_thread = threading.Thread(target=self_ping_worker, daemon=True)
    ping_thread.start()
    print(f"[Keep-Alive] 🚀 Запущен self-ping для {RENDER_EXTERNAL_URL}")


# ============================================
# ХРАНИЛИЩЕ ПОЛЬЗОВАТЕЛЕЙ (в памяти; снапшот в users.json делает GitHub Actions)
# ============================================

USERS_SNAPSHOT_URL = "https://raw.githubusercontent.com/glcskl/tg/main/users.json"

_users_lock = threading.Lock()
_known_users = set()


def _load_known_users() -> None:
    """При старте подгружаем ранее сохранённых пользователей из репозитория."""
    global _known_users
    try:
        resp = requests.get(USERS_SNAPSHOT_URL, timeout=15)
        if resp.status_code == 200:
            with _users_lock:
                _known_users = set(resp.json())
        print(f"[Users] 📂 Загружено пользователей: {len(_known_users)}")
    except Exception as e:
        print(f"[Users] ⚠️ Не удалось загрузить users.json: {e}")


_load_known_users()


def record_user(chat_id) -> None:
    if chat_id is None:
        return
    with _users_lock:
        if chat_id in _known_users:
            return
        _known_users.add(int(chat_id))
    print(f"[Users] ➕ Новый пользователь: {chat_id} (всего: {len(_known_users)})")


# ============================================
# ДАННЫЕ БОТА
# ============================================

DAYS = [("пн", "Понедельник"), ("вт", "Вторник"), ("ср", "Среда"), ("чт", "Четверг"), ("пт", "Пятница")]

# Канал обязательной подписки
REQUIRED_CHANNEL = "@startupspacevstu"
CHANNEL_URL = "https://t.me/startupspacevstu"

SUB_TEXT = (
    "🔒 *Бот работает только для подписчиков канала*\n\n"
    "1️⃣ Подпишись на канал 👇\n"
    "2️⃣ Вернись сюда и нажми «🔄 Я подписался»"
)


def is_subscribed(user_id: int) -> bool:
    """Проверяет подписку пользователя на обязательный канал."""
    try:
        result = tg_request(
            "getChatMember",
            {"chat_id": REQUIRED_CHANNEL, "user_id": user_id},
        )
        status = (result.get("result") or {}).get("status")
        return result.get("ok") and status in ("creator", "administrator", "member", "restricted")
    except Exception as e:
        print(f"[SubCheck] ❌ Ошибка проверки подписки у {user_id}: {e}")
        return False


def subscription_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "📢 Подписаться на канал", "url": CHANNEL_URL}],
            [{"text": "🔄 Я подписался", "callback_data": "check_sub"}],
        ]
    }

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


# ============================================
# КЛАВИАТУРЫ
# ============================================

def main_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "📅 Расписание", "callback_data": "schedule"},
            ]
        ]
    }


def day_keyboard() -> dict:
    days_row = [
        {"text": title, "callback_data": f"day:{key}"}
        for key, title in DAYS
    ]
    back_row = [{"text": "🔙 Назад", "callback_data": "back"}]
    return {"inline_keyboard": [days_row, back_row]}


def back_keyboard() -> dict:
    return {
        "inline_keyboard": [[{"text": "🔙 Назад", "callback_data": "back"}]]
    }


# ============================================
# ФОРМАТИРОВАНИЕ
# ============================================

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


# ============================================
# TELEGRAM API
# ============================================

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
    user_id = (message.get("from") or {}).get("id")
    text = (message.get("text") or "").strip()

    record_user(chat_id)

    if text in ("/start", "start"):
        if user_id and not is_subscribed(user_id):
            tg_request(
                "sendMessage",
                {
                    "chat_id": chat_id,
                    "text": SUB_TEXT,
                    "parse_mode": "Markdown",
                    "reply_markup": subscription_keyboard(),
                },
            )
            return

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

    record_user(chat_id)

    # Проверка подписки перед любым действием
    user_id = (callback_query.get("from") or {}).get("id")
    if user_id and not is_subscribed(user_id):
        if data == "check_sub":
            tg_request(
                "answerCallbackQuery",
                {
                    "callback_query_id": callback_id,
                    "text": "❌ Ты ещё не подписан на канал. Подпишись и нажми «Я подписался» ещё раз.",
                    "show_alert": True,
                },
            )
        else:
            tg_request(
                "editMessageText",
                {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": SUB_TEXT,
                    "parse_mode": "Markdown",
                    "reply_markup": subscription_keyboard(),
                },
            )
            tg_request("answerCallbackQuery", {"callback_query_id": callback_id})
        return

    # Кнопка "Назад" / "Я подписался" (после успешной проверки)
    if data in ("back", "check_sub"):
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


# ============================================
# ROUTES
# ============================================

@app.get("/")
def index():
    return "Bot is running."


@app.get("/health")
def health():
    """Health check endpoint для мониторинга и self-ping."""
    return {
        "status": "ok",
        "service": "tg-schedule-bot",
        "timestamp": datetime.now().isoformat(),
        "self_ping_enabled": bool(RENDER_EXTERNAL_URL),
        "known_users": len(_known_users),
    }


@app.get("/users")
def users_dump():
    """Выгружает список пользователей (для синхронизации GitHub Actions)."""
    if request.args.get("key") != BOT_TOKEN:
        return {"error": "unauthorized"}, 401
    with _users_lock:
        return sorted(_known_users)


@app.post(f"/webhook/{BOT_TOKEN}")
def telegram_webhook():
    update = request.get_json(force=True, silent=True) or {}
    handle_update(update)
    # Telegram достаточно кода 200 без тела
    return "", 200


if __name__ == "__main__":
    # Локальный запуск для отладки (например, через ngrok)
    app.run(host="0.0.0.0", port=8000, debug=True)