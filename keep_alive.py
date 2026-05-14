#!/usr/bin/env python3
"""
Keep-Alive скрипт для Telegram бота на Render.com

Этот скрипт периодически пингует ваш бот, чтобы он не "засыпал" 
на бесплатном тарифе Render (который усыпляет сервис через 15 минут неактивности).

Запуск:
    python keep_alive.py --url https://your-bot.onrender.com --interval 10

Или с переменной окружения:
    export BOT_URL=https://your-bot.onrender.com
    python keep_alive.py
"""

import os
import sys
import time
import argparse
import signal
from datetime import datetime

try:
    import requests
except ImportError:
    print("Ошибка: нужно установить requests")
    print("Выполните: pip install requests")
    sys.exit(1)


class KeepAlive:
    def __init__(self, url: str, interval_minutes: int = 10, timeout: int = 30):
        self.url = url.rstrip("/")
        self.interval_minutes = interval_minutes
        self.timeout = timeout
        self.running = True
        self.success_count = 0
        self.error_count = 0
        
        # Обработка сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print(f"\n[{self._timestamp()}] Получен сигнал остановки, завершаем работу...")
        self.running = False
    
    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def ping(self) -> bool:
        """Пингует сервер и возвращает True если успешно"""
        try:
            # Пингуем корневой эндпоинт
            response = requests.get(
                f"{self.url}/",
                timeout=self.timeout,
                headers={"User-Agent": "KeepAlive-Bot/1.0"}
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"[{self._timestamp()}] ⚠️ Статус: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"[{self._timestamp()}] ⏱️ Таймаут (сервер просыпается?)")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"[{self._timestamp()}] ❌ Ошибка подключения: {e}")
            return False
        except Exception as e:
            print(f"[{self._timestamp()}] ❌ Неизвестная ошибка: {e}")
            return False
    
    def run(self):
        """Основной цикл пинга"""
        print(f"[{self._timestamp()}] 🚀 Запуск Keep-Alive для {self.url}")
        print(f"[{self._timestamp()}] ⏰ Интервал: каждые {self.interval_minutes} минут")
        print(f"[{self._timestamp()}] 🛑 Нажмите Ctrl+C для остановки\n")
        
        # Первый пинг сразу при запуске
        if self.ping():
            self.success_count += 1
            print(f"[{self._timestamp()}] ✅ Пинг успешен (#{self.success_count})")
        else:
            self.error_count += 1
        
        while self.running:
            # Ждем перед следующим пингом
            for _ in range(self.interval_minutes * 60):
                if not self.running:
                    break
                time.sleep(1)
            
            if not self.running:
                break
            
            # Пингуем
            if self.ping():
                self.success_count += 1
                print(f"[{self._timestamp()}] ✅ Пинг успешен (#{self.success_count})")
            else:
                self.error_count += 1
                # При ошибке пробуем еще раз через минуту
                print(f"[{self._timestamp()}] 🔄 Повторная попытка через 1 минуту...")
                time.sleep(60)
                if self.ping():
                    self.success_count += 1
                    print(f"[{self._timestamp()}] ✅ Повторный пинг успешен")
        
        # Итоговая статистика
        print(f"\n[{self._timestamp()}] 📊 Статистика:")
        print(f"   ✅ Успешных пингов: {self.success_count}")
        print(f"   ❌ Ошибок: {self.error_count}")


def main():
    parser = argparse.ArgumentParser(
        description="Keep-Alive скрипт для Telegram бота на Render.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python keep_alive.py --url https://tg-schedule-bot.onrender.com
  python keep_alive.py --url https://tg-schedule-bot.onrender.com --interval 12
  BOT_URL=https://tg-schedule-bot.onrender.com python keep_alive.py
        """
    )
    
    parser.add_argument(
        "--url", "-u",
        type=str,
        default=os.getenv("BOT_URL", ""),
        help="URL вашего бота на Render (например, https://tg-schedule-bot.onrender.com)"
    )
    
    parser.add_argument(
        "--interval", "-i",
        type=int,
        default=int(os.getenv("PING_INTERVAL", "10")),
        help="Интервал пинга в минутах (по умолчанию: 10, максимум рекомендуется: 14)"
    )
    
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=30,
        help="Таймаут запроса в секундах (по умолчанию: 30)"
    )
    
    args = parser.parse_args()
    
    if not args.url:
        print("❌ Ошибка: нужно указать URL бота")
        print("Используйте --url или установите переменную окружения BOT_URL")
        print("\nПример:")
        print("  python keep_alive.py --url https://tg-schedule-bot.onrender.com")
        sys.exit(1)
    
    # Проверяем что URL выглядит правильно
    if not args.url.startswith("http"):
        print(f"❌ Ошибка: URL должен начинаться с http:// или https://")
        sys.exit(1)
    
    # Предупреждение если интервал слишком большой
    if args.interval >= 15:
        print("⚠️ Предупреждение: интервал >= 15 минут может не предотвратить засыпание!")
        print("   Рекомендуется интервал 10-14 минут")
    
    keep_alive = KeepAlive(
        url=args.url,
        interval_minutes=args.interval,
        timeout=args.timeout
    )
    keep_alive.run()


if __name__ == "__main__":
    main()