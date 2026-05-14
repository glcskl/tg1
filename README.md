# 📅 Schedule Bot

Telegram бот для просмотра расписания занятий, экзаменов и зачетов. Поддерживает автоматическое определение недели (числитель/знаменатель) и быстрый доступ к расписанию.

## ✨ Возможности

- 📅 Просмотр расписания по дням недели
- 📝 Расписание экзаменов
- ✅ Расписание зачетов
- 🔄 Автоматическое определение текущей недели (числитель/знаменатель)
- ⚡ **24/7 работа на бесплатном тарифе Render** (с keep-alive механизмом)

## 🚀 Быстрый старт

### Локальный запуск

```bash
# Клонирование
git clone https://github.com/glcskl/tg.git
cd tg

# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
echo "BOT_TOKEN=your_bot_token_here" > .env

# Запуск (polling режим)
python bot.py
```

### Деплой на Render.com

См. подробную инструкцию в [RENDER_DEPLOY_GUIDE.md](RENDER_DEPLOY_GUIDE.md)

## 🔥 Keep-Alive - Бот всегда онлайн!

**Проблема:** На бесплатном тарифе Render сервис "засыпает" через 15 минут неактивности, и первый запрос занимает 30-60 секунд.

**Решение:** Мы реализовали 3 уровня защиты от засыпания:

### Уровень 1: Встроенный Self-Ping ✅

Обновленный `web_app.py` автоматически пингует себя каждые 10 минут - **ничего настраивать не нужно!**

### Уровень 2: UptimeRobot (Рекомендуется) ⭐

Бесплатный внешний мониторинг каждые 5 минут:
1. Зарегистрируйтесь на https://uptimerobot.com
2. Добавьте монитор для URL: `https://your-bot.onrender.com/health`
3. Готово! Бот будет работать 24/7

### Уровень 3: Локальный скрипт

```bash
python keep_alive.py --url https://your-bot.onrender.com
```

📖 **Подробная инструкция:** [KEEP_ALIVE_GUIDE.md](KEEP_ALIVE_GUIDE.md)

## 📁 Структура проекта

```
tg/
├── bot.py              # Версия с polling (aiogram) - для локального запуска
├── web_app.py          # Версия с webhook (Flask) - для Render + self-ping
├── keep_alive.py       # Скрипт для поддержания бота активным
├── schedule.json       # Данные расписания
├── requirements.txt    # Зависимости Python
├── Procfile            # Команда запуска для Render
├── render.yaml         # Конфигурация Render
├── RENDER_DEPLOY_GUIDE.md  # Инструкция по деплою
├── KEEP_ALIVE_GUIDE.md     # Инструкция по keep-alive
└── README.md           # Этот файл
```

## 🛠 Технологии

- Python 3.11
- aiogram 3.x (polling режим)
- Flask + gunicorn (webhook режим)
- requests (Telegram API)

## 📋 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню с кнопками |

### Кнопки меню

- **📅 Расписание** - выбор дня недели для просмотра расписания
- **📝 Экзамены** - расписание экзаменов
- **✅ Зачеты** - расписание зачетов

## 🔧 API Endpoints (web_app.py)

| Endpoint | Описание |
|----------|----------|
| `GET /` | Проверка работы бота |
| `GET /health` | Health check (для мониторинга) |
| `POST /webhook/{BOT_TOKEN}` | Webhook для Telegram |

## 📝 Редактирование расписания

Файл `schedule.json` содержит расписание для двух недель:

```json
{
  "числитель": {
    "пн": [
      {
        "time": "09:50-11:25",
        "kind": "лб",
        "subject": "Системы управления web-контентом",
        "teacher": "Быковский Д.И.",
        "room": "212"
      }
    ]
  },
  "знаменатель": { ... }
}
```

Типы занятий (`kind`):
- `лк` - лекция 📖
- `лб` - лабораторная 🔬
- `пр` - практика ✏️

## 🧪 Тестирование

```bash
# Проверка health endpoint
curl https://your-bot.onrender.com/health

# Ожидаемый ответ
{
  "status": "ok",
  "service": "tg-schedule-bot",
  "timestamp": "2024-01-15T10:30:00",
  "self_ping_enabled": true
}
```

## 📚 Документация

- [RENDER_DEPLOY_GUIDE.md](RENDER_DEPLOY_GUIDE.md) - Инструкция по деплою на Render
- [KEEP_ALIVE_GUIDE.md](KEEP_ALIVE_GUIDE.md) - Как держать бота всегда активным

## 📄 Лицензия

MIT