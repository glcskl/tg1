# Schedule Bot

Telegram бот для просмотра расписания занятий. Поддерживает выбор недели (числитель/знаменатель) и дня недели.

## Технологии

- Python 3.8+
- aiogram 3.7.0
- python-dotenv 1.0.0

## Установка и запуск локально

1. Склонируйте репозиторий
2. Перейдите в папку с ботом:
   ```bash
   cd schedule_bot
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Создайте файл `.env` из `.env.example` и добавьте токен вашего бота
5. Запустите бота:
   ```bash
   python bot.py
   ```

## Развертывание на хостинге

### Option 1: Heroku (бесплатный тариф)

1. Создайте аккаунт на [Heroku](https://heroku.com/)
2. Установите [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
3. В папке с ботом выполните:
   ```bash
   heroku login
   heroku create your-app-name
   heroku git:remote -a your-app-name
   ```
4. Настройте переменные окружения:
   ```bash
   heroku config:set BOT_TOKEN=your_bot_token
   ```
5. Создайте файл `Procfile` (если не существует):
   ```
   worker: python bot.py
   ```
6. Задеплоите код:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push heroku main
   ```
7. Запустите воркер:
   ```bash
   heroku ps:scale worker=1
   ```

### Option 2: PythonAnywhere (бесплатный тариф)

1. Создайте аккаунт на [PythonAnywhere](https://www.pythonanywhere.com/)
2. Загрузите файлы бота в личный кабинет
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt --user
   ```
4. Создайте таску для запуска бота:
   - Перейдите в раздел "Tasks"
   - Создайте новую задачу
   - Укажите команду: `python3 /home/your_username/schedule_bot/bot.py`
   - Настройте интервал запуска (рекомендуется раз в 24 часа)

### Option 3: Docker

1. Установите Docker и Docker Compose
2. Создайте файл `docker-compose.yml`:
   ```yaml
   version: '3'
   services:
     bot:
       build: .
       container_name: schedule_bot
       environment:
         - BOT_TOKEN=your_bot_token
       volumes:
         - .:/app
       restart: unless-stopped
   ```
3. Создайте Dockerfile:
   ```dockerfile
   FROM python:3.10-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   CMD ["python", "bot.py"]
   ```
4. Запустите контейнер:
   ```bash
   docker-compose up -d
   ```

## Структура проекта

- `bot.py` - Основной скрипт бота
- `schedule.json` - Данные расписания
- `requirements.txt` - Зависимости
- `.env` - Переменные окружения
- `.env.example` - Пример файла с переменными окружения

## Команды бота

- `/start` - Начать работу с ботом
- Любой другой текст - Выводит подсказку о начале работы

## Использование

1. Отправьте `/start` боту
2. Выберите тип недели (числитель или знаменатель)
3. Выберите день недели
4. Посмотрите расписание

## Редактирование расписания

Чтобы изменить расписание, отредактируйте файл `schedule.json` в соответствии с существующим форматом.

