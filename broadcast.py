#!/usr/bin/env python3
"""Рассылка сообщения всем пользователям бота из users.json.

Использование: python broadcast.py "Текст сообщения"
Токен берётся из переменной окружения BOT_TOKEN.
"""
import json
import os
import sys
import time

import requests


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: python broadcast.py \"Текст сообщения\"")
        sys.exit(1)

    message = sys.argv[1]
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ Нет переменной окружения BOT_TOKEN")
        sys.exit(1)

    with open("users.json", encoding="utf-8") as f:
        users = json.load(f)

    print(f"Получателей в базе: {len(users)}")
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
                if "blocked" in description or "chat not found" in description or "deactivated" in description:
                    blocked += 1
                    print(f"  ⛔ {chat_id}: {description}")
                else:
                    failed += 1
                    print(f"  ⚠️ {chat_id}: {description}")
        except Exception as e:
            failed += 1
            print(f"  ❌ {chat_id}: {e}")
        time.sleep(1.1)  # лимит Telegram ~1 сообщение/сек на чат

    print(f"\nИтог: ✅ {sent} | ⛔ заблокировали/недоступны: {blocked} | ⚠️ ошибки: {failed}")


if __name__ == "__main__":
    main()
