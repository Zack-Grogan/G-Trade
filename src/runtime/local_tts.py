"""Local macOS text-to-speech for operator alerts (uses `say`, no network)."""

from __future__ import annotations

import logging
import queue
import shutil
import subprocess
import threading
from datetime import datetime
from typing import Any, Callable, Optional

import pytz

from src.config.loader import OperatorTtsConfig

logger = logging.getLogger(__name__)

_PHRASES = {
    "filled": "Order filled",
    "partially_filled": "Order partially filled",
    "rejected": "Order rejected",
    "cancelled": "Order cancelled",
    "submit_failed": "Order submit failed",
}


def _format_money_for_speech(amount: float) -> str:
    """Whole dollars without decimals when close to integer; else two decimals with commas."""
    if abs(amount - round(amount)) < 0.005:
        return f"{int(round(amount)):,}"
    return f"{amount:,.2f}"


def _format_exit_time_for_speech(exit_time: datetime, timezone_name: str) -> str:
    tz = pytz.timezone(timezone_name)
    if exit_time.tzinfo is None:
        local = tz.localize(exit_time)
    else:
        local = exit_time.astimezone(tz)
    h = local.hour % 12 or 12
    m = local.minute
    ampm = "AM" if local.hour < 12 else "PM"
    return f"{h}:{m:02d} {ampm}"


def build_realized_pnl_phrase(
    pnl: float,
    exit_time: datetime,
    *,
    timezone_name: str,
    include_time: bool,
) -> str:
    """Spoken line when a position closes (risk-manager trade record)."""
    if abs(pnl) < 0.01:
        base = "Breakeven trade"
    elif pnl > 0:
        base = f"A profit of {_format_money_for_speech(pnl)} dollars"
    else:
        base = f"A loss of {_format_money_for_speech(-pnl)} dollars"
    if include_time:
        when = _format_exit_time_for_speech(exit_time, timezone_name)
        return f"{base} at {when}."
    return f"{base}."


class LocalTtsNotifier:
    """Queue short phrases to the system `say` command without blocking the caller."""

    def __init__(
        self,
        cfg: OperatorTtsConfig,
        *,
        popen: Optional[Callable[..., Any]] = None,
    ) -> None:
        self._cfg = cfg
        self._popen = popen or subprocess.Popen
        self._say_path = shutil.which("say")
        self._warned_no_say = False
        self._queue: queue.Queue[str] = queue.Queue(maxsize=max(1, cfg.max_queue))
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True, name="local-tts")
        self._worker.start()

    def _worker_loop(self) -> None:
        while not self._stop.is_set():
            try:
                text = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self._run_say(text)

    def _run_say(self, text: str) -> None:
        if not self._say_path:
            if not self._warned_no_say:
                logger.debug("Local TTS skipped: `say` not found on PATH")
                self._warned_no_say = True
            return
        cmd: list[str] = [self._say_path]
        if self._cfg.voice:
            cmd.extend(["-v", self._cfg.voice])
        if self._cfg.rate is not None:
            cmd.extend(["-r", str(self._cfg.rate)])
        cmd.append(text)
        try:
            self._popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            logger.debug("Local TTS failed: %s", exc)

    def _enqueue(self, text: str) -> None:
        try:
            self._queue.put_nowait(text)
        except queue.Full:
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self._queue.put_nowait(text)
            except queue.Full:
                pass

    def speak(self, event_key: str, *, mock_mode: bool) -> None:
        if not self._cfg.enabled:
            return
        if mock_mode and not self._cfg.speak_in_mock_mode:
            return
        if event_key not in self._cfg.events:
            return
        text = _PHRASES.get(event_key)
        if not text:
            return
        self._enqueue(text)

    def speak_realized_pnl(
        self,
        pnl: float,
        exit_time: datetime,
        *,
        mock_mode: bool,
        timezone_name: str,
    ) -> None:
        if not self._cfg.enabled:
            return
        if mock_mode and not self._cfg.speak_in_mock_mode:
            return
        if "realized_pnl" not in self._cfg.events:
            return
        text = build_realized_pnl_phrase(
            pnl,
            exit_time,
            timezone_name=timezone_name,
            include_time=self._cfg.include_trade_time_in_speech,
        )
        self._enqueue(text)

    def close(self) -> None:
        self._stop.set()
        self._worker.join(timeout=2.0)
