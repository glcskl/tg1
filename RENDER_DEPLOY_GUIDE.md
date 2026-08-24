# Инструкция по деплою Telegram-бота на Render

## Обзор проекта

Проект содержит Telegram-бота для просмотра расписания с двумя реализациями:
- `bot.py` - версия с polling (aiogram)
- `web_app.py` - версия с webhook (Flask) - **используется для деплоя на Render**

## Шаг 1: Создание аккаунта на Render

1. Перейдите на https://render.com
2. Нажмите "Sign Up" или "Log In"
3. Войдите через GitHub (рекомендуется) или создайте аккаунт по email

## Шаг 2: Создание Web Service

1. После входа в аккаунт нажмите кнопку **"New +"** в правом верхнем углу
2. Выберите **"Web Service"**
3. Подключите GitHub-репозиторий:
   - Нажмите **"Connect GitHub"**
   - Авторизуйте Render для доступа к вашим репозиториям
   - Найдите и выберите репозиторий `glcskl/tg`
   - Нажмите **"Connect"**

## Шаг 3: Настройка Web Service

### Основные настройки:

| Параметр | Значение |
|----------|----------|
| **Name** | `tg-schedule-bot` (или любое другое имя) |
| **Region** | `Oregon (US West)` или ближайший к вам регион |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn web_app:app` |

### Детальная настройка:

1. **Name**: Введите имя вашего сервиса (например, `tg-schedule-bot`)
2. **Region**: Выберите регион (Oregon, Frankfurt, Singapore и т.д.)
3. **Branch**: Убедитесь, что выбрана ветка `main`
4. **Runtime**: Render автоматически определит Python, но убедитесь, что выбран `Python 3`
5. **Instance Type**: Выберите **"Free"** для бесплатного тарифа

### Build & Deploy:

1. **Build Command**: 
   ```
   pip install -r requirements.txt
   ```
2. **Start Command**: 
   ```
   gunicorn web_app:app
   ```

## Шаг 4: Добавление переменных окружения

1. Прокрутите вниз до раздела **"Environment Variables"**
2. Нажмите **"Add Environment Variable"**
3. Добавьте следующие переменные:

| Key | Value | Синхронизация |
|-----|-------|--------------|
| `BOT_TOKEN` | `<ВАШ_ТОКЕН>` | - |
| `PYTHON_VERSION` | `3.11.0` | - |

**Важно**: `BOT_TOKEN` - это токен вашего Telegram-бота, который вы предоставили ранее.

## Шаг 5: Создание Web Service

1. Нажмите кнопку **"Create Web Service"** в нижней части страницы
2. Render начнет процесс сборки и деплоя
3. Подождите несколько минут, пока процесс завершится

## Шаг 6: Получение URL веб-сервиса

После успешного деплоя:

1. Render предоставит URL вашего сервиса (например, `https://tg-schedule-bot.onrender.com`)
2. Скопируйте этот URL - он понадобится для настройки webhook

## Шаг 7: Настройка Webhook для Telegram-бота

После деплоя нужно настроить webhook, чтобы Telegram отправлял обновления на ваш сервер.

### Способ 1: Через браузер (простой)

Откройте в браузере следующую ссылку, заменив `YOUR_URL` на URL вашего сервиса:

```
https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=https://YOUR_URL.onrender.com/webhook/<ВАШ_ТОКЕН>
```

Пример:
```
https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=https://tg-schedule-bot.onrender.com/webhook/<ВАШ_ТОКЕН>
```

### Способ 2: Через терминал

```bash
curl -X POST "https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=https://YOUR_URL.onrender.com/webhook/<ВАШ_ТОКЕН>"
```

### Способ 3: Проверка webhook

Чтобы проверить статус webhook:

```
https://api.telegram.org/bot<ВАШ_ТОКЕН>/getWebhookInfo
```

## Шаг 8: Проверка работы бота

1. Откройте Telegram
2. Найдите своего бота по имени или через @username
3. Нажмите **"Start"** или отправьте `/start`
4. Бот должен ответить: "Привет! Выбери неделю 👇"

## Шаг 9: Мониторинг логов

Для просмотра логов в Render:

1. Перейдите на страницу вашего Web Service
2. Нажмите на вкладку **"Logs"**
3. Здесь вы увидите все логи работы приложения

## Структура проекта

```
tg/
├── .gitignore          # Исключаемые файлы для Git
├── Procfile            # Команда запуска для Render
├── README.md           # Документация проекта
├── bot.py              # Версия бота с polling (aiogram)
├── requirements.txt    # Зависимости Python
├── schedule.json       # Файл с расписанием
├── web_app.py          # Версия бота с webhook (Flask) - используется для деплоя
└── RENDER_DEPLOY_GUIDE.md  # Эта инструкция
```

## Возможные проблемы и решения

### Проблема: Бот не отвечает

**Решение:**
1. Проверьте логи в Render (вкладка "Logs")
2. Убедитесь, что webhook настроен правильно
3. Проверьте, что переменная `BOT_TOKEN` задана верно

### Проблема: Ошибка при деплое

**Решение:**
1. Проверьте, что все файлы загружены на GitHub
2. Убедитесь, что `requirements.txt` содержит все зависимости
3. Проверьте, что `Procfile` существует и содержит правильную команду

### Проблема: Webhook не работает

**Решение:**
1. Проверьте URL webhook - он должен быть доступен извне
2. Убедитесь, что путь `/webhook/BOT_TOKEN` правильный
3. Проверьте статус webhook через `getWebhookInfo`

### Проблема: Сервис на Render не запускается

**Решение:**
1. Проверьте, что `Start Command` правильный: `gunicorn web_app:app`
2. Убедитесь, что `gunicorn` установлен (добавлен в `requirements.txt`)
3. Проверьте, что `web_app.py` существует и не содержит ошибок

## Бесплатный тариф Render

На бесплатном тарифе:
- Сервис "засыпает" через 15 минут неактивности
- Пробуждение занимает ~30 секунд
- 750 часов в месяц (примерно 24/7)
- 512 MB RAM
- 0.1 CPU

Для постоянной работы бота webhook - это идеальное решение, так как бот будет активироваться при каждом сообщении от Telegram.

## Обновление кода

Для обновления кода:

1. Внесите изменения в локальные файлы
2. Закоммитьте изменения:
   ```bash
   git add .
   git commit -m "Описание изменений"
   git push
   ```
3. Render автоматически обнаружит изменения и перезапустит сервис

## Дополнительные ресурсы

- [Render Documentation](https://render.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

---

**Удачи с деплоем!** 🚀
