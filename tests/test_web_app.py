import json
from datetime import datetime

import pytest

import web_app
from web_app import (
    BOT_TOKEN,
    DAYS,
    EXAMS,
    CREDITS,
    PAIR_BY_START,
    app,
    day_keyboard,
    format_credits,
    format_day,
    format_exams,
    get_current_week,
    load_schedule,
    main_keyboard,
)


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b"Bot is running."


def test_health_payload(client):
    response = client.get("/health")
    assert response.status_code == 200

    payload = response.get_json()
    assert payload["status"] == "ok"
    assert payload["service"] == "tg-schedule-bot"
    assert payload["self_ping_enabled"] is False
    assert isinstance(payload["known_users"], int)
    datetime.fromisoformat(payload["timestamp"])


def test_users_requires_key(client):
    response = client.get("/users")
    assert response.status_code == 401
    assert response.get_json() == {"error": "unauthorized"}

    response = client.get("/users?key=wrong")
    assert response.status_code == 401


def test_users_dump_returns_sorted_known_users(client):
    web_app.record_user(555)
    web_app.record_user(123)

    response = client.get(f"/users?key={BOT_TOKEN}")
    assert response.status_code == 200
    assert response.get_json() == [123, 555]


def test_webhook_accepts_empty_update(client):
    response = client.post(f"/webhook/{BOT_TOKEN}", json={})
    assert response.status_code == 200


def _freeze_week(monkeypatch, iso_week):
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls.fromisocalendar(2026, iso_week, 1)

    monkeypatch.setattr(web_app, "datetime", FixedDatetime)


@pytest.mark.parametrize(
    "iso_week, expected",
    [(2, "числитель"), (3, "знаменатель"), (44, "числитель"), (45, "знаменатель")],
)
def test_current_week_follows_iso_parity(monkeypatch, iso_week, expected):
    _freeze_week(monkeypatch, iso_week)
    assert get_current_week() == expected


def test_schedule_file_covers_both_weeks_and_weekdays():
    schedule = load_schedule()

    assert set(schedule) == {"числитель", "знаменатель"}
    for week in schedule.values():
        assert set(week) == {key for key, _ in DAYS}


def test_format_day_numbers_pairs_by_start_time():
    schedule = {
        "числитель": {
            "пн": [
                {"time": "09:50-11:25", "subject": "Математика", "kind": "лк", "teacher": "Иванов И.И.", "room": "101"},
                {"time": "08:00-09:35", "subject": "Физика", "kind": "лб", "teacher": "", "room": ""},
            ]
        }
    }

    text = format_day(schedule, "числитель", "пн")

    assert "ПОНЕДЕЛЬНИК" in text
    assert "2️⃣ ⏰ *09:50-11:25*" in text
    assert "1️⃣ ⏰ *08:00-09:35*" in text
    assert "Математика (📖 лк)" in text
    assert "Физика (🔬 лб)" in text
    assert "👤 Иванов И.И." in text


def test_format_day_falls_back_to_position_for_unknown_start():
    schedule = {"числитель": {"вт": [{"time": "10:05-11:40", "subject": "Химия"}]}}

    text = format_day(schedule, "числитель", "вт")

    assert "1️⃣ ⏰ *10:05-11:40*" in text


def test_format_day_empty_day_says_no_classes():
    assert format_day({}, "знаменатель", "ср") == (
        "📅 *СРЕДА*\n📅 Неделя: *знаменатель*\n\n✅ Нет пар"
    )


def test_pair_by_start_is_ordered():
    assert list(PAIR_BY_START.values()) == [1, 2, 3, 4, 5, 6, 7]
    assert list(PAIR_BY_START) == sorted(PAIR_BY_START)


def test_format_exams_lists_every_exam():
    text = format_exams()

    assert "*ЭКЗАМЕНЫ*" in text
    for exam in EXAMS:
        assert exam["subject"] in text
        assert exam["date"] in text


def test_format_credits_lists_every_credit():
    text = format_credits()

    assert "*ЗАЧЕТЫ*" in text
    for credit in CREDITS:
        assert credit["subject"] in text
        assert credit["date"] in text


def test_keyboards_structure():
    main = main_keyboard()["inline_keyboard"]
    assert main[0][0]["callback_data"] == "schedule"

    days = day_keyboard()["inline_keyboard"]
    assert [button["callback_data"] for button in days[0]] == [f"day:{key}" for key, _ in DAYS]
    assert days[1][0]["callback_data"] == "back"


def test_schedule_json_is_valid_utf8_json():
    with open(web_app.schedule_path(), encoding="utf-8") as handle:
        data = json.load(handle)

    assert "числитель" in data and "знаменатель" in data
