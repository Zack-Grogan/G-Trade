"""Tests for local macOS TTS notifier."""

from __future__ import annotations

import time
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import pytz

from src.config.loader import OperatorTtsConfig
from src.runtime.local_tts import LocalTtsNotifier, build_realized_pnl_phrase


@pytest.fixture
def say_path() -> str:
    return "/usr/bin/say"


def test_speak_disabled_does_not_invoke_popen(say_path: str) -> None:
    def boom(*_a, **_k):
        raise AssertionError("Popen should not be called")

    cfg = OperatorTtsConfig(enabled=False)
    with patch("src.runtime.local_tts.shutil.which", return_value=say_path):
        n = LocalTtsNotifier(cfg, popen=boom)
        n.speak("filled", mock_mode=False)
        time.sleep(0.15)
        n.close()


def test_speak_mock_mode_skips_without_flag(say_path: str) -> None:
    def boom(*_a, **_k):
        raise AssertionError("Popen should not be called")

    cfg = OperatorTtsConfig(enabled=True, speak_in_mock_mode=False)
    with patch("src.runtime.local_tts.shutil.which", return_value=say_path):
        n = LocalTtsNotifier(cfg, popen=boom)
        n.speak("filled", mock_mode=True)
        time.sleep(0.15)
        n.close()


def test_speak_mock_mode_allowed_when_configured(say_path: str) -> None:
    calls: list[list[str]] = []

    def capture_popen(cmd: list[str], **_k):
        calls.append(cmd)
        return Mock()

    cfg = OperatorTtsConfig(enabled=True, speak_in_mock_mode=True, events=["filled"])
    with patch("src.runtime.local_tts.shutil.which", return_value=say_path):
        n = LocalTtsNotifier(cfg, popen=capture_popen)
        n.speak("filled", mock_mode=True)
        time.sleep(0.25)
        n.close()

    assert calls, "expected say to run when speak_in_mock_mode is true"
    assert calls[0][0] == say_path
    assert "Order filled" in calls[0][-1]


def test_speak_respects_events_allowlist(say_path: str) -> None:
    def boom(*_a, **_k):
        raise AssertionError("Popen should not be called")

    cfg = OperatorTtsConfig(enabled=True, events=["rejected"])
    with patch("src.runtime.local_tts.shutil.which", return_value=say_path):
        n = LocalTtsNotifier(cfg, popen=boom)
        n.speak("filled", mock_mode=False)
        time.sleep(0.15)
        n.close()


def test_speak_enqueues_popen_with_voice_and_rate(say_path: str) -> None:
    calls: list[list[str]] = []

    def capture_popen(cmd: list[str], **_k):
        calls.append(cmd)
        return Mock()

    cfg = OperatorTtsConfig(
        enabled=True,
        voice="Samantha",
        rate=200,
        events=["submit_failed"],
    )
    with patch("src.runtime.local_tts.shutil.which", return_value=say_path):
        n = LocalTtsNotifier(cfg, popen=capture_popen)
        n.speak("submit_failed", mock_mode=False)
        time.sleep(0.25)
        n.close()

    assert calls
    cmd = calls[0]
    assert cmd[0] == say_path
    assert "-v" in cmd and "Samantha" in cmd
    assert "-r" in cmd and "200" in cmd
    assert cmd[-1] == "Order submit failed"


def test_build_realized_pnl_phrase_profit_loss_and_breakeven() -> None:
    tz = "America/Chicago"
    dt = pytz.timezone(tz).localize(datetime(2026, 3, 20, 15, 45, 0))
    profit = build_realized_pnl_phrase(1200.0, dt, timezone_name=tz, include_time=True)
    assert "profit" in profit.lower()
    assert "1,200" in profit
    assert "3:45" in profit and "PM" in profit

    dt2 = pytz.timezone(tz).localize(datetime(2026, 3, 20, 9, 5, 0))
    loss = build_realized_pnl_phrase(-200.0, dt2, timezone_name=tz, include_time=True)
    assert "loss" in loss.lower()
    assert "200" in loss
    assert "9:05" in loss and "AM" in loss

    flat = build_realized_pnl_phrase(0.0, dt, timezone_name=tz, include_time=False)
    assert "breakeven" in flat.lower()

    no_time = build_realized_pnl_phrase(100.0, dt, timezone_name=tz, include_time=False)
    assert "at" not in no_time.lower()
    assert "profit" in no_time.lower()


def test_speak_realized_pnl_enqueues(say_path: str) -> None:
    calls: list[list[str]] = []

    def capture_popen(cmd: list[str], **_k):
        calls.append(cmd)
        return Mock()

    cfg = OperatorTtsConfig(enabled=True, events=["realized_pnl"])
    dt = pytz.UTC.localize(datetime(2026, 3, 20, 20, 45, 0))
    with patch("src.runtime.local_tts.shutil.which", return_value=say_path):
        n = LocalTtsNotifier(cfg, popen=capture_popen)
        n.speak_realized_pnl(1200.0, dt, mock_mode=False, timezone_name="America/Chicago")
        time.sleep(0.3)
        n.close()

    assert calls
    spoken = calls[0][-1]
    assert "profit" in spoken.lower()
    assert "1,200" in spoken


def test_speak_realized_pnl_respects_events_allowlist(say_path: str) -> None:
    def boom(*_a, **_k):
        raise AssertionError("Popen should not be called")

    cfg = OperatorTtsConfig(enabled=True, events=["filled"])
    dt = pytz.UTC.localize(datetime(2026, 3, 20, 20, 0, 0))
    with patch("src.runtime.local_tts.shutil.which", return_value=say_path):
        n = LocalTtsNotifier(cfg, popen=boom)
        n.speak_realized_pnl(500.0, dt, mock_mode=False, timezone_name="America/Chicago")
        time.sleep(0.15)
        n.close()


def test_no_say_binary_skips_without_crashing() -> None:
    def must_not_popen(*_a, **_k):
        raise AssertionError("popen should not run when `say` is missing")

    cfg = OperatorTtsConfig(enabled=True, events=["filled"])
    with patch("src.runtime.local_tts.shutil.which", return_value=None):
        n = LocalTtsNotifier(cfg, popen=must_not_popen)
        n.speak("filled", mock_mode=False)
        time.sleep(0.15)
        n.close()
