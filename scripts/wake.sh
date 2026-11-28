#!/usr/bin/env bash
# Быстро разбудить Render-сервис бота.
# Использование: ./scripts/wake.sh [URL]
set -euo pipefail

URL="${1:-https://tg1-schedule-bot.onrender.com/health}"
ATTEMPTS="${ATTEMPTS:-5}"
DELAY="${DELAY:-20}"

for ((i = 1; i <= ATTEMPTS; i++)); do
  code=$(curl --silent --show-error --location \
    --max-time 120 --output /dev/null \
    --write-out "%{http_code}" "$URL" || true)

  if [ "$code" = "200" ]; then
    echo "Бот активен: HTTP $code"
    exit 0
  fi

  echo "Попытка $i/$ATTEMPTS: HTTP $code"
  if [ "$i" -lt "$ATTEMPTS" ]; then
    sleep "$DELAY"
  fi
done

echo "Не удалось разбудить сервис: $URL" >&2
exit 1
