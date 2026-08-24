#!/usr/bin/env python3
"""
Скрипт для автоматической настройки webhook для Telegram-бота на Render.

Использование:
    python setup_webhook.py <RENDER_URL>

Пример:
    python setup_webhook.py https://tg-schedule-bot.onrender.com
"""

import sys
import requests

import os

# Ваш токен Telegram-бота (задаётся в переменной окружения BOT_TOKEN)
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

def setup_webhook(render_url: str) -> bool:
    """
    Настраивает webhook для Telegram-бота.

    Args:
        render_url: URL вашего сервиса на Render

    Returns:
        True если webhook настроен успешно, иначе False
    """
    # Удаляем слеш в конце, если он есть
    render_url = render_url.rstrip('/')

    # Формируем URL webhook
    webhook_url = f"{render_url}/webhook/{BOT_TOKEN}"

    # API URL для настройки webhook
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"

    print(f"Настройка webhook...")
    print(f"Webhook URL: {webhook_url}")

    try:
        response = requests.post(api_url, json={"url": webhook_url}, timeout=10)
        result = response.json()

        if result.get("ok"):
            print("✅ Webhook успешно настроен!")
            print(f"URL: {webhook_url}")
            return True
        else:
            print(f"❌ Ошибка при настройке webhook:")
            print(f"   {result.get('description', 'Неизвестная ошибка')}")
            return False

    except requests.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False


def get_webhook_info() -> None:
    """Получает информацию о текущем webhook."""
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"

    try:
        response = requests.get(api_url, timeout=10)
        result = response.json()

        if result.get("ok"):
            info = result.get("result", {})
            print("\n📋 Информация о webhook:")
            print(f"   URL: {info.get('url', 'Не настроен')}")
            print(f"   Pending updates: {info.get('pending_update_count', 0)}")
            print(f"   Last error: {info.get('last_error_message', 'Нет')}")
        else:
            print(f"❌ Ошибка при получении информации: {result.get('description')}")

    except requests.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")


def delete_webhook() -> bool:
    """Удаляет текущий webhook."""
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"

    try:
        response = requests.get(api_url, timeout=10)
        result = response.json()

        if result.get("ok"):
            print("✅ Webhook успешно удален!")
            return True
        else:
            print(f"❌ Ошибка при удалении webhook: {result.get('description')}")
            return False

    except requests.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return False


def main():
    """Главная функция."""
    if len(sys.argv) < 2:
        print("Использование: python setup_webhook.py <RENDER_URL> [команда]")
        print("\nКоманды:")
        print("  setup   - настроить webhook (по умолчанию)")
        print("  info    - показать информацию о webhook")
        print("  delete  - удалить webhook")
        print("\nПримеры:")
        print("  python setup_webhook.py https://tg-schedule-bot.onrender.com")
        print("  python setup_webhook.py https://tg-schedule-bot.onrender.com info")
        sys.exit(1)

    render_url = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else "setup"

    if command == "info":
        get_webhook_info()
    elif command == "delete":
        delete_webhook()
    elif command == "setup":
        if setup_webhook(render_url):
            get_webhook_info()
    else:
        print(f"❌ Неизвестная команда: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
