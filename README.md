# tg1 — VSTU schedule Telegram bot

A Telegram bot that publishes the VSTU university timetable directly in chat, so students do not have to open a set of separate PDF files. The bot detects the current academic week on its own, shows classes grouped by day and time slot, and lists exams and credits separately from regular lessons.

## Features

- Automatic numerator and denominator detection, so the bot always shows the correct week
- Timetable kept as structured JSON instead of static documents
- Exams and credits listed separately from regular classes
- Subscription check against a Telegram channel before the schedule opens
- Two run modes: long polling for local work, webhook for hosting
- Keep-alive mechanism that keeps the free hosting tier awake
- Scheduled broadcasts driven by GitHub Actions

## Tech stack

| Layer | Technology |
| --- | --- |
| Language | Python 3 |
| Framework | aiogram 3 |
| Web layer | Flask |
| WSGI server | Gunicorn |
| Configuration | python-dotenv |
| HTTP client | requests |
| Hosting | Render, free tier |

## Getting started

### Requirements

- Python 3.11 or newer
- A bot token from [@BotFather](https://t.me/BotFather)

### Environment variables

| Variable | Required | Description |
| --- | --- | --- |
| `BOT_TOKEN` | yes | Token issued by BotFather |
| `BOT_URL` | webhook mode | Public HTTPS URL of the deployed instance |
| `PING_INTERVAL` | no | Keep-alive interval in seconds |
| `RENDER_EXTERNAL_URL` | no | Injected by Render automatically |

Create a `.env` file in the project root:

```
BOT_TOKEN=123456:ABCDEF...
```

### Installation

```bash
git clone https://github.com/glcskl/tg1.git
cd tg1
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running

Local development with long polling:

```bash
python bot.py
```

Webhook mode, which is what the hosting platform uses:

```bash
python setup_webhook.py
gunicorn web_app:app
```

## Project structure

```
bot.py            long-polling entry point
web_app.py        Flask application serving the Telegram webhook
setup_webhook.py  registers the webhook URL with Telegram
broadcast.py      scheduled broadcast sender
keep_alive.py     keep-alive pinger for the free hosting tier
schedule.json     timetable, exams and credits
render.yaml       Render service blueprint
Procfile          process definition for the hosting platform
```

## Deployment

`render.yaml` lets Render provision the web service straight from the blueprint. Routine maintenance is handled by three GitHub Actions workflows:

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `keep-alive.yml` | every 5 minutes | pings the service so the free tier does not sleep |
| `redeploy.yml` | manual | forces a redeploy when the service has been stopped |
| `broadcast.yml` | manual | sends a scheduled broadcast |

## Notes

This project is personal and is not affiliated with the university. It reads no data from any university system and is maintained on a best-effort basis.