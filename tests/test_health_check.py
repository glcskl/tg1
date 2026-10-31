import time
from datetime import datetime, timezone

import health_check


class _FakeResponse:
    def __init__(self, status=200):
        self.status = status

    def read(self, _size):
        return b"{}"

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_check_reports_up_on_200(monkeypatch, tmp_path):
    monkeypatch.setattr(health_check, "urlopen", lambda request, timeout: _FakeResponse(200))

    result = health_check.check("https://example.test/health", timeout=1)

    assert result["ok"] is True
    assert result["code"] == 200
    assert isinstance(result["ms"], int)


def test_check_reports_down_on_http_error(monkeypatch):
    def raise_error(request, timeout):
        raise health_check.HTTPError(request.full_url, 503, "unavailable", None, None)

    monkeypatch.setattr(health_check, "urlopen", raise_error)

    result = health_check.check("https://example.test/health", timeout=1)

    assert result["ok"] is False
    assert result["code"] == 503


def test_check_reports_down_on_connection_error(monkeypatch):
    def raise_error(request, timeout):
        raise health_check.URLError("connection refused")

    monkeypatch.setattr(health_check, "urlopen", raise_error)

    result = health_check.check("https://example.test/health", timeout=1)

    assert result["ok"] is False
    assert result["code"] == 0
    assert "connection refused" in result["error"]


def test_format_line_layout():
    when = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)

    line = health_check.format_line({"code": 200, "ms": 512, "ok": True}, now=when)

    assert line == "2026-10-31T12:00:00Z\t200\t512 ms\tup\n"


def test_format_line_marks_down():
    when = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)

    line = health_check.format_line({"code": 503, "ms": 42, "ok": False}, now=when)

    assert line.endswith("\tdown\n")


def test_main_appends_line_and_returns_zero(monkeypatch, tmp_path):
    log_path = tmp_path / "health.log"
    monkeypatch.setattr(health_check, "LOG_PATH", str(log_path))
    monkeypatch.setattr(health_check, "check", lambda: {"code": 200, "ms": 100, "ok": True})

    assert health_check.main() == 0
    assert log_path.read_text(encoding="utf-8").count("\tup\n") == 1

    health_check.main()
    assert len(log_path.read_text(encoding="utf-8").splitlines()) == 2


def test_main_returns_one_when_service_down(monkeypatch, tmp_path):
    monkeypatch.setattr(health_check, "LOG_PATH", str(tmp_path / "health.log"))
    monkeypatch.setattr(
        health_check,
        "check",
        lambda: {"code": 0, "ms": 5, "ok": False, "error": "timeout"},
    )

    assert health_check.main() == 1


def test_check_uses_configured_url(monkeypatch):
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["agent"] = request.get_header("User-agent")
        return _FakeResponse(200)

    monkeypatch.setattr(health_check, "urlopen", fake_urlopen)

    health_check.check("https://example.test/health")

    assert seen["url"] == "https://example.test/health"
    assert seen["agent"] == "health-check/1.0"
