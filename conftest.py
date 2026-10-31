import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# web_app требует BOT_TOKEN уже на импорте, в тестах хватает заглушки
os.environ.setdefault("BOT_TOKEN", "123456:test-token")


class _OfflineResponse:
    """Заглушка вместо запроса users.json на GitHub при импорте web_app."""

    status_code = 404

    def json(self):
        return []


requests.get = lambda *args, **kwargs: _OfflineResponse()
