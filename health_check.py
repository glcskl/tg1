#!/usr/bin/env python3
"""Проверяет /health задеплоенного бота и дописывает строку в health.log.

Запуск: python3 health_check.py
Строка лога: <UTC-время>\t<HTTP-код>\t<латентность, мс>\t<up|down>
Код возврата 1, если сервис не ответил 200 — так падение видно в Actions.
"""
import os
import sys
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

URL = os.environ.get("BOT_HEALTH_URL", "https://tg-schedule-bot-duqr.onrender.com/health")
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "health.log")
TIMEOUT = 120


def check(url: str = URL, timeout: int = TIMEOUT) -> dict:
    started = time.monotonic()
    request = Request(url, headers={"User-Agent": "health-check/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read(256)
            code = response.status
    except HTTPError as exc:
        code = exc.code
    except URLError as exc:
        elapsed = round((time.monotonic() - started) * 1000)
        return {"code": 0, "ms": elapsed, "ok": False, "error": str(exc.reason)}
    elapsed = round((time.monotonic() - started) * 1000)
    return {"code": code, "ms": elapsed, "ok": code == 200}


def format_line(result: dict, now: datetime | None = None) -> str:
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ")
    state = "up" if result["ok"] else "down"
    return f"{stamp}\t{result['code']}\t{result['ms']} ms\t{state}\n"


def main() -> int:
    result = check()
    with open(LOG_PATH, "a", encoding="utf-8") as log:
        log.write(format_line(result))
    print(f"{URL} -> HTTP {result['code']} in {result['ms']} ms")
    if not result["ok"]:
        print(f"health check failed: {result.get('error', 'unexpected status')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
