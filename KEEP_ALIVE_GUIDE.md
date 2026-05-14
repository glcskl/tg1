# 🚀 Keep-Alive Guide - Как держать бота всегда активным

## Проблема

На бесплатном тарифе Render.com:
- Сервис "засыпает" через **15 минут** неактивности
- "Пробуждение" (cold start) занимает **30-60 секунд**
- Пользователи видят задержку при нажатии кнопок в боте

## ✅ Решение

Мы реализовали **3 уровня защиты** от засыпания:

---

## Уровень 1: Встроенный Self-Ping (Автоматический)

### Как это работает

Обновленный `web_app.py` содержит встроенный механизм self-ping:
- Каждые 10 минут бот "пингует" сам себя через `/health` эндпоинт
- Это предотвращает засыпание сервиса

### Что нужно сделать

**Ничего!** Это работает автоматически на Render.com.

Переменная окружения `RENDER_EXTERNAL_URL` автоматически устанавливается Render'ом, и self-ping запускается при старте.

### Проверка

После деплоя проверьте логи Render - вы увидите:
```
[Keep-Alive] 🚀 Запущен self-ping для https://your-bot.onrender.com
[Keep-Alive] ✅ Self-ping успешен
```

---

## Уровень 2: UptimeRobot (Рекомендуется)

### Почему нужен

Self-ping внутри Render может не сработать если:
- Рендер перезагружает сервис
- Происходит внутренняя ошибка

**UptimeRobot** - бесплатный внешний сервис мониторинга, который пингует ваш бот извне.

### Настройка UptimeRobot

1. **Регистрация**
   - Перейдите на https://uptimerobot.com
   - Нажмите "Sign Up Free"
   - Создайте бесплатный аккаунт

2. **Добавление мониторинга**
   - Нажмите **"+ Add New Monitor"**
   - Заполните поля:
     - **Monitor Type**: HTTP(s)
     - **Friendly Name**: TG Schedule Bot
     - **URL**: `https://your-bot.onrender.com/health` (замените на ваш URL)
     - **Monitoring Interval**: 5 минут (бесплатно)
   - Нажмите **"Create Monitor"**

3. **Результат**
   - UptimeRobot будет пинговать ваш бот каждые 5 минут
   - Это гарантирует, что бот никогда не уснет
   - Плюс вы получите уведомления если бот упадет

### Преимущества UptimeRobot

- ✅ Полностью бесплатно
- ✅ Пинг каждые 5 минут
- ✅ Уведомления на email при падении
- ✅ Статистика аптайма
- ✅ Работает извне (надежнее self-ping)

---

## Уровень 3: Локальный Keep-Alive скрипт

### Когда использовать

- Если не хотите зависеть от внешних сервисов
- Если есть свой сервер/VPS
- Для локального тестирования

### Запуск

```bash
# Установка зависимостей
pip install requests

# Запуск с указанием URL
python keep_alive.py --url https://your-bot.onrender.com

# С интервалом 12 минут
python keep_alive.py --url https://your-bot.onrender.com --interval 12

# Через переменную окружения
export BOT_URL=https://your-bot.onrender.com
python keep_alive.py
```

### Запуск в фоне (Linux/Mac)

```bash
# Запуск в фоне
nohup python keep_alive.py --url https://your-bot.onrender.com > keep_alive.log 2>&1 &

# Остановка
ps aux | grep keep_alive
kill <PID>
```

### Запуск через systemd (Linux)

Создайте файл `/etc/systemd/system/keep-alive-bot.service`:

```ini
[Unit]
Description=Keep Alive for TG Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/tg-bot
ExecStart=/usr/bin/python3 /path/to/tg-bot/keep_alive.py --url https://your-bot.onrender.com
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable keep-alive-bot
sudo systemctl start keep-alive-bot
```

---

## 📊 Сравнение методов

| Метод | Стоимость | Надежность | Настройка |
|-------|-----------|------------|------------|
| Self-Ping (встроенный) | Бесплатно | ⭐⭐⭐ | Автоматически |
| UptimeRobot | Бесплатно | ⭐⭐⭐⭐⭐ | 2 минуты |
| Локальный скрипт | Бесплатно | ⭐⭐⭐⭐ | Требует сервер |

---

## 🔧 Обновление деплоя

### Шаг 1: Обновите код на GitHub

```bash
cd /path/to/tg-bot
git add .
git commit -m "Add keep-alive mechanism"
git push
```

### Шаг 2: Render автоматически передеплоит

Или можете нажать "Manual Deploy" в панели Render.

### Шаг 3: Проверьте логи

В панели Render → Logs вы должны увидеть:
```
[Keep-Alive] 🚀 Запущен self-ping для https://your-bot.onrender.com
```

---

## 🧪 Тестирование

### Проверка health endpoint

```bash
curl https://your-bot.onrender.com/health
```

Ожидаемый ответ:
```json
{
  "status": "ok",
  "service": "tg-schedule-bot",
  "timestamp": "2024-01-15T10:30:00",
  "self_ping_enabled": true
}
```

### Проверка в Telegram

1. Откройте бота в Telegram
2. Нажмите `/start`
3. Быстро нажимайте кнопки - они должны реагировать мгновенно
4. Подождите 20 минут
5. Снова нажмите кнопку - должна быть мгновенная реакция

---

## ❓ FAQ

### Q: Почему бот все еще тормозит?

**A:** Проверьте:
1. Логи Render - работает ли self-ping
2. Настроен ли UptimeRobot
3. Не превысили ли лимиты бесплатного тарифа (750 часов/месяц)

### Q: Self-ping не работает

**A:** Убедитесь что:
1. Переменная `RENDER_EXTERNAL_URL` установлена (Render делает это автоматически)
2. Проверьте логи на наличие ошибок

### Q: Можно ли использовать несколько методов?

**A:** Да! Рекомендуется использовать:
- Self-Ping (встроенный) + UptimeRobot = максимальная надежность

---

## 📝 Итог

**Минимальная настройка:**
1. Обновите код на GitHub
2. Render автоматически передеплоит
3. Self-ping начнет работать автоматически

**Рекомендуемая настройка:**
1. Обновите код
2. Настройте UptimeRobot (2 минуты)
3. Бот будет работать 24/7 без задержек

---

**Удачи! 🎉**