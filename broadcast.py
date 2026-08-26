#!/usr/bin/env python3
"""Рассылка сообщения всем пользователям бота.

Список пользователей берётся напрямую с живого сервера (/users),
ничего не хранится в репозитории.
Использование: python broadcast.py "Текст сообщения"
"""
import json
import os
import sys
import time
import urllib.request

import requests

SERVER = "https://tg-schedule-bot-duqr.onrender.com"


def main() -> None:
    if len(sys.argv) < 2:
        print('Использование: python broadcast.py "Текст сообщения"')
        sys.exit(1)

    message = sys.argv[1]
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ Нет переменной окружения BOT_TOKEN")
        sys.exit(1)

    try:
        with urllib.request.urlopen(f"{SERVER}/users?key={token}", timeout=30) as r:
            users = json.load(r)
    except Exception as e:
        print(f"❌ Не удалось получить список пользователей: {e}")
        sys.exit(1)

    print(f"Получателей: {len(users)}")
    sent = blocked = failed = 0

    for chat_id in users:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
                timeout=20,
            ).json()
            if resp.get("ok"):
                sent += 1
            else:
                description = resp.get("description", "")
                if any(x in description for x in ("blocked", "chat not found", "deactivated", "Unauthorized")):
                    blocked += 1
                    print(f"  ⛔ {chat_id}: {description}")
                else:
                    failed += 1
                    print(f"  ⚠️ {chat_id}: {description}")
        except Exception as e:
            failed += 1
            print(f"  ❌ {chat_id}: {e}")
        time.sleep(1.1)

    print(f"\nИтог: ✅ {sent} | ⛔ недоступны: {blocked} | ⚠️ ошибки: {failed}")


if __name__ == "__main__":
    main()
