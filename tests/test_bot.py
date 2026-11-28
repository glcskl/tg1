import asyncio
from types import SimpleNamespace

import bot


class FakeBot:
    def __init__(self, status):
        self.status = status

    async def get_chat_member(self, chat_id, user_id):
        assert chat_id == "@startupspacevstu"
        return SimpleNamespace(status=self.status)


class FakeMessage:
    def __init__(self):
        self.texts = []
        self.markups = []

    async def edit_text(self, text, **kwargs):
        self.texts.append(text)
        self.markups.append(kwargs.get("reply_markup"))


class FakeCallback:
    def __init__(self, data="", user_id=42, status="member"):
        self.data = data
        self.from_user = SimpleNamespace(id=user_id)
        self.bot = FakeBot(status)
        self.message = FakeMessage()
        self.answers = []

    async def answer(self, text=None):
        self.answers.append(text)


def test_bot_subscription_check_accepts_administrator():
    for status in ("creator", "administrator", "member", "restricted"):
        assert asyncio.run(bot.is_subscribed(FakeBot(status), 42)) is True
    for status in ("left", "kicked"):
        assert asyncio.run(bot.is_subscribed(FakeBot(status), 42)) is False


def test_bot_callbacks_block_unsubscribed_users():
    bot.USER_GROUPS.clear()
    cb = FakeCallback("exams", status="left")

    asyncio.run(bot.show_exams(cb))

    assert cb.message.texts == [bot.SUB_TEXT]
    assert cb.answers == [None]


def test_bot_administrator_can_open_assessments_and_switch_group():
    bot.USER_GROUPS.clear()
    cb = FakeCallback("exams", status="administrator")

    asyncio.run(bot.show_exams(cb))

    assert "Группа: *4Ээб-4*" in cb.message.texts[0]
    assert "Управление проектом" in cb.message.texts[0]

    cb = FakeCallback("exams_group:4Ээб-4а", status="administrator")
    asyncio.run(bot.set_exams_group(cb))

    assert "Группа: *4Ээб-4а*" in cb.message.texts[0]
    assert bot.get_group(42) == "4Ээб-4а"
    assert cb.answers == ["Группа: 4Ээб-4а"]


def test_bot_keyboards_contain_group_and_assessment_buttons():
    markup = str(bot.main_keyboard(42))
    for text in ("📅 Расписание", "✅ Зачёты", "📝 Экзамены", "👥 Группа: 4Ээб-4"):
        assert text in markup

    groups = str(bot.group_keyboard("exams_group"))
    assert "4Ээб-4" in groups
    assert "4Ээб-4а" in groups
    assert "change_exams" in str(bot.assessment_keyboard("change_exams"))


def test_main_registers_all_new_callbacks(monkeypatch):
    class Register:
        def __init__(self, bucket):
            self.bucket = bucket

        def register(self, handler, *filters):
            self.bucket.append(handler)

    class DispatcherStub:
        def __init__(self):
            self.messages = []
            self.callbacks = []
            self.message = Register(self.messages)
            self.callback_query = Register(self.callbacks)

        async def start_polling(self, bot_instance):
            return None

    dp = DispatcherStub()
    monkeypatch.setattr(bot, "Bot", lambda token: object())
    monkeypatch.setattr(bot, "Dispatcher", lambda: dp)

    asyncio.run(bot.main())

    handlers = {handler.__name__ for handler in dp.callbacks}
    assert {
        "back_to_main",
        "show_schedule_menu",
        "show_exams",
        "show_credits",
        "choose_group",
        "set_group_from_menu",
        "change_exams_group",
        "set_exams_group",
        "change_credits_group",
        "set_credits_group",
        "set_day",
    }.issubset(handlers)
