"""Local Flask operator console for the trader runtime."""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from flask import Flask, Response, abort, jsonify, render_template, request, stream_with_context
from werkzeug.serving import make_server

from src.config import Config, ServerConfig, get_config
from src.observability import get_observability_store

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_STATIC_DIR = Path(__file__).resolve().parent / "static"
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")
CHART_DEFAULT_LOOKBACK_HOURS = 48
CHART_MIN_LOOKBACK_HOURS = 1
CHART_MAX_LOOKBACK_HOURS = 24 * 14
NOISE_LOGGERS = {"werkzeug"}
NOISE_LOG_FRAGMENTS = (
    ' "GET / HTTP/1.1"',
    ' "GET /chart HTTP/1.1"',
    ' "GET /trades HTTP/1.1"',
    ' "GET /logs HTTP/1.1"',
    ' "GET /system HTTP/1.1"',
    ' "GET /api/',
    ' "GET /stream/',
    ' "GET /static/',
    ' "GET /favicon',
)

# Registry of typed notification cards.
# Each entry maps a log message prefix to a display config.
# Fields per entry:
#   type        — short singular name used as CSS class suffix
#   label       — display name shown in card header
#   icon        — SVG path name (keys in SVG_ICON_PATHS below)
#   summary     — human-readable one-liner (None = derive from fields)
#   fields      — ordered list of field specs:
#     key       — raw token name from the log (e.g. "decisions_last_min")
#     label     — short human label (e.g. "dec/min")
#     unit      — optional suffix rendered after the value
#     color     — optional CSS var name for value color ("good", "danger", "warn", "accent")
#     fmt       — optional format hint: "price" (2dp), "bool" (Yes/No), "int"
NOTIFICATION_TYPES: dict[str, dict[str, Any]] = {
    "runtime_heartbeat": {
        "type": "runtime_heartbeat",
        "label": "Heartbeat",
        "icon": "activity",
        "summary": None,
        "fields": [
            {"key": "mode", "label": "mode", "color": "accent"},
            {"key": "zone", "label": "zone", "color": "accent"},
            {"key": "position", "label": "pos", "fmt": "int"},
            {"key": "last_price", "label": "price", "fmt": "price"},
            {"key": "decisions_last_min", "label": "dec/min", "fmt": "int"},
            {"key": "fail_safe", "label": "fail-safe", "fmt": "bool"},
        ],
    },
    "market_stream_heartbeat": {
        "type": "market_heartbeat",
        "label": "Market",
        "icon": "trending-up",
        "summary": None,
        "fields": [
            {"key": "symbol", "label": "symbol", "color": "accent"},
            {"key": "quotes", "label": "quotes", "fmt": "int"},
            {"key": "last_price", "label": "price", "fmt": "price"},
        ],
    },
    "broker_order_cancelled": {
        "type": "broker_order",
        "label": "Order Cancelled",
        "icon": "arrow-up-right",
        "summary": "Order {order_id} cancelled",
        "fields": [
            {"key": "order_id", "label": "order"},
        ],
    },
    "broker_order_cancel_failed": {
        "type": "broker_order",
        "label": "Cancel Failed",
        "icon": "arrow-up-right",
        "summary": "Cancel failed for {order_id}",
        "fields": [
            {"key": "order_id", "label": "order"},
            {"key": "error", "label": "error"},
        ],
    },
    "Position opened": {
        "type": "position_open",
        "label": "Position",
        "icon": "plus-circle",
        "summary": "{direction} {contracts} @ {entry_price}",
        "fields": [
            {"key": "contracts", "label": "contracts", "fmt": "int"},
            {"key": "direction", "label": "dir"},
            {"key": "entry_price", "label": "price", "fmt": "price"},
        ],
    },
    "Trade blocked by risk manager": {
        "type": "blocked",
        "label": "Blocked",
        "icon": "lock",
        "summary": "{reason}",
        "fields": [
            {"key": "reason", "label": "reason"},
        ],
    },
    "Entry skipped because": {
        "type": "skipped",
        "label": "Skipped",
        "icon": "minus-circle",
        "summary": "{reason}",
        "fields": [
            {"key": "reason", "label": "reason"},
        ],
    },
    "Fail-safe lockout activated": {
        "type": "failsafe",
        "label": "Fail-Safe",
        "icon": "alert-triangle",
        "summary": "{reason}",
        "fields": [
            {"key": "reason", "label": "reason"},
        ],
    },
    "Flatten requested": {
        "type": "flatten",
        "label": "Flatten",
        "icon": "x-circle",
        "summary": "Flatten: {reason}",
        "fields": [
            {"key": "reason", "label": "reason"},
        ],
    },
    "Loss recorded": {
        "type": "loss",
        "label": "Loss",
        "icon": "trending-down",
        "summary": "Consecutive losses: {consecutive_losses}",
        "fields": [
            {"key": "consecutive_losses", "label": "streak", "fmt": "int"},
        ],
    },
    "Daily loss limit": {
        "type": "daily_limit",
        "label": "Daily Limit",
        "icon": "shield-alert",
        "summary": "Daily loss limit hit: ${loss}",
        "fields": [
            {"key": "loss", "label": "loss", "fmt": "price"},
        ],
    },
    "Consecutive loss limit": {
        "type": "consecutive_loss",
        "label": "Consecutive Loss",
        "icon": "shield-alert",
        "summary": "Consecutive loss limit hit",
        "fields": [
            {"key": "consecutive_losses", "label": "streak", "fmt": "int"},
        ],
    },
    "Daily counters reset": {
        "type": "risk",
        "label": "Risk",
        "icon": "shield",
        "summary": "Daily counters reset",
        "fields": [],
    },
    "Risk state reduced": {
        "type": "risk",
        "label": "Risk",
        "icon": "shield",
        "summary": "Risk state reduced",
        "fields": [],
    },
    "Risk state reset": {
        "type": "risk",
        "label": "Risk",
        "icon": "shield",
        "summary": "Risk state reset to normal",
        "fields": [],
    },
}

SVG_ICON_PATHS: dict[str, str] = {
    "activity": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
    "trending-up": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
    "arrow-up-right": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="7" y1="17" x2="17" y2="7"></line><polyline points="7 7 17 7 17 17"></polyline></svg>',
    "plus-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>',
    "lock": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>',
    "minus-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>',
    "alert-triangle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>',
    "x-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>',
    "trending-down": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>',
    "shield-alert": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
    "shield": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>',
    "briefcase": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>',
}


class TradingState:
    """Global trading state container."""

    def __init__(self):
        self.status: str = "stopped"
        self.running: bool = False
        self.current_zone: Optional[str] = None
        self.zone_state: str = "inactive"
        self.current_strategy: Optional[str] = None
        self.position: int = 0
        self.position_pnl: float = 0
        self.daily_pnl: float = 0
        self.account_balance: float = 50000
        self.account_equity: float = 0
        self.account_available: float = 0
        self.account_margin_used: float = 0
        self.account_open_pnl: float = 0
        self.account_realized_pnl: float = 0
        self.account_id: Optional[str] = None
        self.account_name: Optional[str] = None
        self.account_is_practice: Optional[bool] = None
        self.data_mode: str = "unknown"
        self.long_score: float = 0
        self.short_score: float = 0
        self.flat_bias: float = 0
        self.active_vetoes: list = []
        self.matrix_version: Optional[str] = None
        self.last_entry_reason: Optional[str] = None
        self.last_exit_reason: Optional[str] = None
        self.active_session: Optional[str] = None
        self.anchored_vwaps: dict[str, Any] = {}
        self.vwap_bands: dict[str, Any] = {}
        self.volume_profile: dict[str, Any] = {}
        self.order_flow: dict[str, Any] = {}
        self.regime: dict[str, Any] = {"state": None, "reason": None}
        self.execution: dict[str, Any] = {}
        self.broker_truth: dict[str, Any] = {}
        self.heartbeat: dict[str, Any] = {}
        self.event_context: dict[str, Any] = {}
        self.replay_summary: Optional[dict[str, Any]] = None
        self.last_signal: Optional[dict[str, Any]] = None
        self.last_price: Optional[float] = None
        self.uptime_seconds: float = 0
        self.start_time: float = 0
        self.risk_state: str = "normal"
        self.trades_today: int = 0
        self.trades_this_hour: int = 0
        self.trades_this_zone: int = 0
        self.max_daily_loss: float = 0
        self.consecutive_losses: int = 0
        self.errors: list = []
        self.run_id: Optional[str] = None
        self.code_version: Optional[str] = None
        self.git_commit: Optional[str] = None
        self.git_branch: Optional[str] = None
        self.config_path: Optional[str] = None
        self.config_hash: Optional[str] = None
        self.observability_db_path: Optional[str] = None
        self.mcp_url: Optional[str] = None
        self.last_backfill: Optional[dict[str, Any]] = None
        self.lifecycle: dict[str, Any] = {}

    def effective_status(self) -> str:
        heartbeat = self.heartbeat or {}
        mode = str(self.data_mode or "unknown").lower()
        raw_status = str(self.status or "stopped").lower()

        if not self.running:
            return raw_status
        if mode == "replay":
            return mode
        if raw_status not in {"running", "healthy"}:
            return raw_status

        degraded = any(
            [
                bool(heartbeat.get("market_stream_error")),
                bool(heartbeat.get("feed_stale")),
                bool(heartbeat.get("broker_ack_stale")),
                bool(heartbeat.get("protection_timeout")),
                bool(heartbeat.get("fail_safe_lockout")),
                mode == "live" and heartbeat.get("market_stream_connected") is False,
            ]
        )
        return "degraded" if degraded else "healthy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.effective_status(),
            "process_status": self.status,
            "running": self.running,
            "data_mode": self.data_mode,
            "zone": {"name": self.current_zone, "state": self.zone_state},
            "strategy": self.current_strategy,
            "alpha": {
                "long_score": self.long_score,
                "short_score": self.short_score,
                "flat_bias": self.flat_bias,
                "active_vetoes": self.active_vetoes,
                "matrix_version": self.matrix_version,
                "last_entry_reason": self.last_entry_reason,
                "last_exit_reason": self.last_exit_reason,
                "active_session": self.active_session,
            },
            "session_context": {
                "anchored_vwaps": self.anchored_vwaps,
                "vwap_bands": self.vwap_bands,
                "volume_profile": self.volume_profile,
            },
            "order_flow": self.order_flow,
            "regime": self.regime,
            "position": {"contracts": self.position, "pnl": self.position_pnl},
            "account": {
                "id": self.account_id,
                "name": self.account_name,
                "balance": self.account_balance,
                "equity": self.account_equity,
                "available": self.account_available,
                "margin_used": self.account_margin_used,
                "open_pnl": self.account_open_pnl,
                "realized_pnl": self.account_realized_pnl,
                "daily_pnl": self.daily_pnl,
                "is_practice": self.account_is_practice,
            },
            "risk": {
                "state": self.risk_state,
                "trades_today": self.trades_today,
                "trades_this_hour": self.trades_this_hour,
                "trades_this_zone": self.trades_this_zone,
                "max_daily_loss": self.max_daily_loss,
                "consecutive_losses": self.consecutive_losses,
            },
            "execution": self.execution,
            "broker_truth": self.broker_truth,
            "heartbeat": self.heartbeat,
            "event_context": self.event_context,
            "replay_summary": self.replay_summary,
            "last_signal": self.last_signal,
            "last_price": self.last_price,
            "uptime_seconds": self.uptime_seconds,
            "errors": self.errors[-10:],
            "lifecycle": self.lifecycle,
            "observability": {
                "run_id": self.run_id,
                "code_version": self.code_version,
                "git_commit": self.git_commit,
                "git_branch": self.git_branch,
                "config_path": self.config_path,
                "config_hash": self.config_hash,
                "sqlite_path": self.observability_db_path,
                "mcp_url": self.mcp_url,
                "last_backfill": self.last_backfill,
            },
        }

    def to_health_dict(self) -> dict[str, Any]:
        return {
            "status": self.effective_status(),
            "data_mode": self.data_mode,
            "zone": self.current_zone or "inactive",
            "position": self.position,
            "daily_pnl": self.daily_pnl,
            "risk_state": self.risk_state,
            "long_score": self.long_score,
            "short_score": self.short_score,
            "practice_account": self.account_is_practice,
            "market_stream_connected": (self.heartbeat or {}).get("market_stream_connected"),
        }


_state = TradingState()


def get_state() -> TradingState:
    return _state


def set_state(**kwargs):
    for key, value in kwargs.items():
        if hasattr(_state, key):
            setattr(_state, key, value)


def record_error(message: str) -> None:
    entry = {"timestamp": datetime.now(UTC).isoformat(), "message": str(message)}
    _state.errors.append(entry)
    if len(_state.errors) > 100:
        _state.errors = _state.errors[-100:]
    get_observability_store().record_event(
        category="system",
        event_type="recorded_error",
        source=__name__,
        payload={"message": str(message)},
        event_time=datetime.now(UTC),
        action="record_error",
        reason=str(message),
    )


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _pacific_calendar_day_bounds_utc(
    reference: Optional[datetime] = None,
) -> tuple[datetime, datetime]:
    """UTC [start, end] inclusive for the America/Los_Angeles calendar day containing `reference`.

    Matches :func:`_format_datetime` / console.js Pacific formatting so "today" is the operator's
    trading day, not the engine session or risk counter window.
    """
    ref = reference if reference is not None else _utcnow()
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=UTC)
    else:
        ref = ref.astimezone(UTC)
    ref_pt = ref.astimezone(PACIFIC_TZ)
    start_pt = ref_pt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_pt = start_pt + timedelta(days=1) - timedelta(microseconds=1)
    return start_pt.astimezone(UTC), end_pt.astimezone(UTC)


def _ledger_calendar_day_trade_stats(store, state: TradingState) -> dict[str, int]:
    """Realized broker ledger rows (non-null PnL) for the current Pacific calendar day."""
    start_utc, end_utc = _pacific_calendar_day_bounds_utc()
    rows = store.query_account_trades(
        limit=5000,
        ascending=False,
        account_id=state.account_id or None,
        start_time=start_utc,
        end_time=end_utc,
    )
    trades = 0
    losses = 0
    for row in rows:
        pnl = _coerce_float(row.get("profit_and_loss"))
        if pnl is None:
            continue
        trades += 1
        if pnl < 0:
            losses += 1
    return {"trades": trades, "losses": losses}


def _coerce_float(value: Any) -> Optional[float]:
    if value in {None, ""}:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _coerce_int(value: Any) -> Optional[int]:
    if value in {None, ""}:
        return None
    try:
        return int(float(value))
    except Exception:
        return None


def _parse_dt(value: Any) -> Optional[datetime]:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _to_iso(value: Any) -> Optional[str]:
    dt = _parse_dt(value)
    return dt.isoformat() if dt is not None else None


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)


def _format_money(value: Any) -> str:
    number = _coerce_float(value)
    if number is None:
        return "-"
    return f"${number:,.2f}"


def _format_number(value: Any, digits: int = 2) -> str:
    number = _coerce_float(value)
    if number is None:
        return "-"
    return f"{number:,.{digits}f}"


def _format_integer(value: Any) -> str:
    number = _coerce_int(value)
    if number is None:
        return "-"
    return f"{number:,}"


def _format_datetime(value: Any) -> str:
    dt = _parse_dt(value)
    if dt is None:
        return "-"
    return dt.astimezone(PACIFIC_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def _seconds(value: Any) -> Optional[int]:
    dt = _parse_dt(value)
    if dt is None:
        return None
    return int(dt.timestamp())


def _zone_label(zone: Any, *, default: str = "inactive") -> str:
    if isinstance(zone, dict):
        name = zone.get("name")
        state = str(zone.get("state") or "").strip().lower()
        if name:
            return str(name)
        if state == "active":
            return "Outside"
        return default
    if zone in {None, ""}:
        return default
    return str(zone)


def _direction_label(value: Any) -> str:
    direction = _coerce_int(value)
    if direction is None:
        text = str(value or "").strip().lower()
        if text in {"buy", "long"}:
            return "Long"
        if text in {"sell", "short"}:
            return "Short"
        return str(value or "-")
    if direction > 0:
        return "Long"
    if direction < 0:
        return "Short"
    return "Flat"


def _sort_by_timestamp_desc(rows: list[dict[str, Any]], *keys: str) -> list[dict[str, Any]]:
    def _row_key(row: dict[str, Any]) -> tuple[float, int]:
        for key in keys:
            dt = _parse_dt(row.get(key))
            if dt is not None:
                return (dt.timestamp(), _coerce_int(row.get("id")) or 0)
        return (0.0, _coerce_int(row.get("id")) or 0)

    return sorted(rows, key=_row_key, reverse=True)


def _sort_by_local_session(rows: list[dict[str, Any]], *keys: str) -> list[dict[str, Any]]:
    def _row_key(row: dict[str, Any]) -> tuple[int, str, int]:
        dt_value: Optional[datetime] = None
        for key in keys:
            dt_value = _parse_dt(row.get(key))
            if dt_value is not None:
                break
        if dt_value is None:
            return (0, "", _coerce_int(row.get("id")) or 0)
        local_dt = dt_value.astimezone(PACIFIC_TZ)
        return (
            -local_dt.date().toordinal(),
            local_dt.strftime("%H:%M:%S.%f"),
            _coerce_int(row.get("id")) or 0,
        )

    return sorted(rows, key=_row_key)


def _order_side_label(value: Any) -> str:
    direction = _coerce_int(value)
    if direction is None:
        text = str(value or "").strip().lower()
        if text in {"buy", "long", "bid", "b"}:
            return "Buy"
        if text in {"sell", "short", "ask", "s"}:
            return "Sell"
        return str(value or "-")
    if direction == 0:
        return "Buy"
    if direction == 1:
        return "Sell"
    return _direction_label(direction)


def _is_noise_log(row: dict[str, Any]) -> bool:
    logger_name = str(row.get("logger_name") or "").strip().lower()
    if logger_name in NOISE_LOGGERS:
        return True
    message = str(row.get("message") or "")
    return any(fragment in message for fragment in NOISE_LOG_FRAGMENTS)


def _filter_operator_logs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if not _is_noise_log(row)]


def _compact_log_source(logger_name: Any, source: Any) -> str:
    logger = str(logger_name or "").strip().lower()
    mapping = (
        ("src.market.topstep_client", "Broker"),
        ("src.engine.trading_engine", "Engine"),
        ("src.execution.executor", "Executor"),
        ("src.engine.risk_manager", "Risk"),
        ("src.server.flask_console", "Console"),
        ("src.server.debug_server", "Health"),
        ("src.cli", "CLI"),
        ("src.bridge.railway_bridge", "Bridge"),
        ("src.observability.store", "SQLite"),
    )
    for prefix, label in mapping:
        if logger.startswith(prefix):
            return label
    if logger:
        return logger.split(".")[-1].replace("_", " ").title()
    text = str(source or "").strip()
    return text.replace("-", " ").title() if text else "Runtime"


def _parse_log_type(message: str) -> tuple[str, dict[str, Any]] | tuple[None, None]:
    """Match a log message against NOTIFICATION_TYPES prefixes. Returns (type_key, schema) or (None, None)."""
    for prefix, schema in NOTIFICATION_TYPES.items():
        if message.startswith(prefix):
            return prefix, schema
    return None, None


def _parse_tokens(text: str) -> dict[str, str]:
    """Parse all key=value tokens from a log message into a flat dict."""
    tokens: dict[str, str] = {}
    for token in text.split():
        if "=" in token:
            k, _, v = token.partition("=")
            tokens[k.strip()] = v.strip()
    return tokens


def _format_chip_value(value: str) -> str:
    """Strip common prefixes, replace underscores with spaces, and title-case for chip display."""
    prefixes = ("blackout_", "matrix_", "failsafe_", "risk_", "zone_")
    for prefix in prefixes:
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value.replace("_", " ").title()


def _fmt_value(value: str, fmt: str | None) -> str:
    """Format a raw token value according to its format hint."""
    if fmt == "bool":
        return "Yes" if value.lower() in ("true", "1") else "No"
    if fmt == "price":
        try:
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return value
    if fmt == "int":
        try:
            return str(int(float(value)))
        except (ValueError, TypeError):
            return value
    return value


def _token_color(raw_key: str, value: str, schema_color: str | None) -> str:
    """Determine CSS color class for a field based on its actual value, overriding schema defaults."""
    if raw_key == "direction":
        if value in ("long", "Long"):
            return "good"
        if value in ("short", "Short"):
            return "danger"
    if raw_key == "fail_safe":
        if value in ("True", "true", "1"):
            return "danger"
        return ""
    if raw_key == "position":
        try:
            pos = int(float(value))
            if pos > 0:
                return "good"
            if pos < 0:
                return "danger"
            return ""
        except (ValueError, TypeError):
            return ""
    return schema_color or ""


def _build_display_fields(schema: dict[str, Any], tokens: dict[str, str]) -> list[dict[str, str]]:
    """Build the ordered list of display-field dicts for a matched notification type."""
    fields_spec = schema.get("fields") or []
    display_fields: list[dict[str, str]] = []
    for spec in fields_spec:
        raw_key = spec.get("key") or ""
        value = tokens.get(raw_key)
        if value is None:
            continue
        fmt = spec.get("fmt")
        unit = spec.get("unit", "")
        display_fields.append(
            {
                "label": spec.get("label", raw_key),
                "value": _fmt_value(_format_chip_value(value), fmt) + unit,
                "color": _token_color(raw_key, value, schema_color=spec.get("color")),
            }
        )
    return display_fields


def _build_summary(schema: dict[str, Any], tokens: dict[str, str]) -> str:
    """Build the human-readable summary line for a notification card."""
    template = schema.get("summary")
    if template:
        try:
            return template.format(**tokens)
        except KeyError:
            pass
    # Fallback: derive summary from the first few fields
    fields = schema.get("fields") or []
    parts = []
    for spec in fields[:3]:
        key = spec.get("key") or ""
        value = tokens.get(key)
        if value is not None:
            parts.append(_fmt_value(value, spec.get("fmt")))
    return " · ".join(parts) if parts else ""


def _compact_log_message(message: Any) -> str:
    """Legacy fallback: produce a plain-text one-liner from a log message."""
    text = str(message or "").strip()
    if not text:
        return "-"
    if text.startswith("Using account: "):
        return text.replace("Using account: ", "Account: ", 1)
    if text.startswith("startup_endpoints "):
        text = text.replace("startup_endpoints ", "", 1)
        parts = []
        for token in text.split():
            if token.startswith("health_url="):
                parts.append(f"health {token.split('=', 1)[1]}")
            elif token.startswith("debug_url="):
                parts.append(f"console {token.split('=', 1)[1]}")
            elif token.startswith("mcp_url="):
                parts.append(f"mcp {token.split('=', 1)[1]}")
            elif token.startswith("current_zone="):
                parts.append(f"zone {token.split('=', 1)[1]}")
            elif token.startswith("zone_state="):
                parts.append(f"state {token.split('=', 1)[1]}")
        return "Startup endpoints: " + " · ".join(parts)
    if text.startswith("startup_summary "):
        text = text.replace("startup_summary ", "", 1)
        keep = []
        for token in text.split():
            if token.startswith(
                (
                    "capital=",
                    "max_contracts=",
                    "trade_outside_hotzones=",
                    "matrix_version=",
                )
            ):
                keep.append(token.replace("=", " "))
        return "Startup summary: " + " · ".join(keep)
    # For typed notifications, return empty — card handles the summary
    notif_type, _ = _parse_log_type(text)
    if notif_type:
        return ""
    return text


def _render_notification_card(item: dict[str, Any]) -> str:
    """Build the HTML string for a typed notification card."""
    schema = item.get("notif_schema") or {}
    notif_type = item.get("notif_type", "")  # already set to schema["type"]
    icon = item.get("notif_icon", "")
    summary = item.get("notif_summary", "")
    display_fields = item.get("display_fields", [])

    # Build field chips
    chips_html = ""
    if display_fields:
        chips = []
        for f in display_fields:
            color_cls = f"is-{f['color']}" if f.get("color") else ""
            chips.append(
                f'<span class="chip {color_cls}">'
                f'<span class="chip-label">{f["label"]}</span>'
                f'<span class="chip-sep">&nbsp;</span>'
                f'<span class="chip-val">{f["value"]}</span>'
                f"</span>"
            )
        chips_html = '<div class="notif-fields">' + "".join(chips) + "</div>"

    card_class = f"notif notif-{notif_type}" if notif_type else "notif"
    icon_html = f'<span class="notif-icon">{icon}</span>' if icon else ""
    label = schema.get("label", notif_type.title()) if notif_type else ""

    return (
        f'<div class="{card_class}">'
        f"{icon_html}"
        f'<div class="notif-body">'
        f'<div class="notif-label">{label}</div>'
        f'<div class="notif-summary">{summary}</div>'
        f"{chips_html}"
        f"</div>"
        f"</div>"
    )


def _render_log_item(item: dict[str, Any]) -> str:
    """Build the complete HTML string for a single log stack-item."""
    timestamp = item.get("logged_at", "")
    level = item.get("level", "INFO")
    source = item.get("display_source") or item.get("logger_name") or item.get("source") or ""
    header = f'<div class="stack-title">{_format_datetime(timestamp)}</div><div class="stack-subtle">{level} · {source}</div>'

    notif_type = item.get("notif_type", "")
    if notif_type:
        card_html = _render_notification_card(item)
        return f'<div class="stack-item">{header}{card_html}</div>'

    # Legacy display
    display_message = item.get("display_message") or item.get("message") or ""
    fields_html = ""
    display_fields = item.get("display_fields")
    if display_fields and isinstance(display_fields, list):
        rows = []
        for f in display_fields:
            rows.append(f"<dt>{f.get('label', '')}</dt><dd>{f.get('value', '')}</dd>")
        fields_html = '<dl class="display-fields">' + "".join(rows) + "</dl>"
    elif display_fields and isinstance(display_fields, dict):
        rows = []
        for k, v in display_fields.items():
            rows.append(f"<dt>{k}</dt><dd>{v}</dd>")
        fields_html = '<dl class="display-fields">' + "".join(rows) + "</dl>"

    return f'<div class="stack-item">{header}<div>{display_message}</div>{fields_html}</div>'


def _render_operator_logs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rendered: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        item = dict(row)
        item["display_source"] = _compact_log_source(row.get("logger_name"), row.get("source"))
        raw_message = str(row.get("message") or "")
        item["display_message"] = _compact_log_message(raw_message)

        # Try to match a typed notification
        notif_type, schema = _parse_log_type(raw_message)
        if notif_type:
            tokens = _parse_tokens(raw_message)
            css_type = schema.get("type", notif_type)
            item["notif_type"] = css_type
            item["notif_schema"] = schema
            item["notif_icon"] = SVG_ICON_PATHS.get(schema.get("icon", ""), "")
            item["notif_summary"] = _build_summary(schema, tokens)
            item["display_fields"] = _build_display_fields(schema, tokens)
            item["card_html"] = _render_notification_card(item)
            key = (str(item.get("level") or ""), str(item.get("display_source") or ""), css_type)
        else:
            # Legacy: display_fields as plain key→value (backwards compat)
            if "=" in raw_message:
                legacy_fields: list[dict[str, str]] = []
                for token in raw_message.split():
                    if "=" in token:
                        k, _, v = token.partition("=")
                        legacy_fields.append({"label": k.strip(), "value": v.strip(), "color": ""})
                if legacy_fields:
                    item["display_fields"] = legacy_fields
            key = (
                str(item.get("level") or ""),
                str(item.get("display_source") or ""),
                str(item.get("display_message") or ""),
            )

        if key in seen:
            continue
        seen.add(key)
        rendered.append(item)
    return rendered


def _first_numeric(mapping: Any, needles: list[str]) -> Optional[float]:
    if isinstance(mapping, dict):
        for key, value in mapping.items():
            key_text = str(key).lower()
            if any(needle in key_text for needle in needles):
                number = _coerce_float(value)
                if number is not None:
                    return number
            number = _first_numeric(value, needles)
            if number is not None:
                return number
    elif isinstance(mapping, list):
        for item in mapping:
            number = _first_numeric(item, needles)
            if number is not None:
                return number
    else:
        return _coerce_float(mapping)
    return None


def _constant_series(candles: list[dict[str, Any]], value: Optional[float]) -> list[dict[str, Any]]:
    if value is None:
        return []
    return [{"time": candle["time"], "value": value} for candle in candles]


def _resolve_chart_lookback_hours(value: Any) -> int:
    parsed = _coerce_int(value)
    if parsed is None:
        return CHART_DEFAULT_LOOKBACK_HOURS
    return max(CHART_MIN_LOOKBACK_HOURS, min(parsed, CHART_MAX_LOOKBACK_HOURS))


def _chart_market_limit(lookback_hours: int) -> int:
    # Heuristic cap for tick query volume while allowing longer chart windows.
    return max(25000, min(200000, lookback_hours * 7000))


def _bucket_minute_epoch(value: Any) -> Optional[int]:
    dt = _parse_dt(value)
    if dt is None:
        return None
    return int(dt.timestamp() // 60) * 60


def _compact_marker_text(prefix: str, detail: Any, max_len: int = 20) -> str:
    text = str(detail or "").replace("_", " ").strip()
    if len(text) > max_len:
        text = text[: max_len - 3].rstrip() + "..."
    return f"{prefix} {text}".strip()


def _decision_score_series(decisions: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    buckets: dict[int, float] = {}
    for row in decisions:
        bucket = _bucket_minute_epoch(row.get("decided_at"))
        value = _coerce_float(row.get(key))
        if bucket is None or value is None:
            continue
        buckets[bucket] = value
    return [{"time": ts, "value": buckets[ts]} for ts in sorted(buckets)]


def _decision_markers(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for row in decisions:
        bucket = _bucket_minute_epoch(row.get("decided_at"))
        if bucket is None:
            continue
        action = str(row.get("action") or "").upper()
        outcome = str(row.get("outcome") or "").lower()
        reason = row.get("reason") or row.get("outcome_reason") or ""
        if action == "LONG":
            markers.append(
                {
                    "time": bucket,
                    "position": "belowBar",
                    "color": "#22c55e",
                    "shape": "arrowUp",
                    "text": _compact_marker_text("L", reason),
                }
            )
        elif action == "SHORT":
            markers.append(
                {
                    "time": bucket,
                    "position": "aboveBar",
                    "color": "#ef4444",
                    "shape": "arrowDown",
                    "text": _compact_marker_text("S", reason),
                }
            )
        elif action in {"EXIT", "FLAT"} or outcome in {"flatten_request", "flatten_submitted"}:
            markers.append(
                {
                    "time": bucket,
                    "position": "inBar",
                    "color": "#f59e0b",
                    "shape": "square",
                    "text": _compact_marker_text("Flat", reason),
                }
            )
        elif outcome in {"entry_blocked", "entry_skipped", "entry_rejected"}:
            markers.append(
                {
                    "time": bucket,
                    "position": "inBar",
                    "color": "#94a3b8",
                    "shape": "circle",
                    "text": _compact_marker_text("Block", reason),
                }
            )
    return markers


def _execution_markers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for row in rows:
        bucket = _bucket_minute_epoch(row.get("observed_at"))
        if bucket is None:
            continue
        status = str(row.get("status") or "").lower()
        event_type = str(row.get("event_type") or "").lower()
        role = str(row.get("role") or "").lower()
        side = _order_side_label(row.get("side")).lower()
        reason = row.get("reason") or role or event_type or status

        is_fill = "fill" in status or "fill" in event_type
        is_flatten = role == "flatten" or "flatten" in event_type
        is_protective = bool(row.get("is_protective")) or role in {"stop_loss", "take_profit"}
        is_submitted = "submit" in event_type or status in {"new", "submitted", "working", "open"}

        if is_fill:
            is_buy = side == "buy"
            markers.append(
                {
                    "time": bucket,
                    "position": "belowBar" if is_buy else "aboveBar",
                    "color": "#22c55e" if is_buy else "#ef4444",
                    "shape": "circle",
                    "text": _compact_marker_text("Fill", reason),
                }
            )
        elif is_flatten:
            markers.append(
                {
                    "time": bucket,
                    "position": "inBar",
                    "color": "#f59e0b",
                    "shape": "square",
                    "text": _compact_marker_text("Flatten", reason),
                }
            )
        elif is_protective:
            markers.append(
                {
                    "time": bucket,
                    "position": "inBar",
                    "color": "#64748b",
                    "shape": "square",
                    "text": _compact_marker_text("Protect", reason),
                }
            )
        elif is_submitted:
            markers.append(
                {
                    "time": bucket,
                    "position": "inBar",
                    "color": "#38bdf8",
                    "shape": "circle",
                    "text": _compact_marker_text("Order", reason),
                }
            )
    return markers


def _clip_markers_to_candle_window(
    markers: list[dict[str, Any]], candles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not candles:
        return markers
    first_candle_time = candles[0].get("time", 0)
    last_candle_time = candles[-1].get("time", 0)
    return [
        marker
        for marker in markers
        if first_candle_time <= (marker.get("time", 0) or 0) <= last_candle_time
    ]


def _dedupe_markers(markers: list[dict[str, Any]], max_per_bucket: int = 5) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    per_bucket: dict[int, int] = {}
    for marker in sorted(markers, key=lambda item: item.get("time", 0) or 0):
        marker_time = int(marker.get("time", 0) or 0)
        key = (
            marker_time,
            marker.get("shape"),
            marker.get("position"),
            marker.get("text"),
            marker.get("color"),
        )
        if key in seen:
            continue
        if per_bucket.get(marker_time, 0) >= max_per_bucket:
            continue
        seen.add(key)
        per_bucket[marker_time] = per_bucket.get(marker_time, 0) + 1
        deduped.append(marker)
    return deduped


def _clip_series_to_candle_window(
    series: list[dict[str, Any]], candles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not candles:
        return series
    first_candle_time = candles[0].get("time", 0)
    last_candle_time = candles[-1].get("time", 0)
    return [
        point
        for point in series
        if first_candle_time <= (point.get("time", 0) or 0) <= last_candle_time
    ]


def _recent_market_rows(
    store,
    *,
    run_id: Optional[str],
    symbol: Optional[str] = None,
    hours: int = 8,
    limit: int = 25000,
) -> list[dict[str, Any]]:
    start_time = _utcnow() - timedelta(hours=hours)
    rows = store.query_market_tape(
        limit=limit,
        ascending=False,
        run_id=run_id,
        symbol=symbol,
        start_time=start_time,
    )
    if run_id and len(rows) < 200:
        fallback_rows = store.query_market_tape(
            limit=limit,
            ascending=False,
            symbol=symbol,
            start_time=start_time,
        )
        if len(fallback_rows) > len(rows) * 2:
            logger.warning(
                "Market tape has only %d rows for run_id=%s in %dh window; "
                "including %d rows from other runs",
                len(rows),
                run_id,
                hours,
                len(fallback_rows),
            )
            rows = fallback_rows
    return rows


def _latest_run_id(store, state: TradingState) -> Optional[str]:
    if state.run_id:
        return state.run_id
    runs = store.query_run_manifests(limit=1)
    if runs:
        return runs[0].get("run_id")
    completed = store.query_completed_trades(limit=1, include_non_authoritative=True)
    if completed:
        return completed[0].get("run_id")
    return None


def _series_price(row: dict[str, Any]) -> Optional[float]:
    for key in ("last",):
        price = _coerce_float(row.get(key))
        if price is not None and price > 0:
            return price
    bid = _coerce_float(row.get("bid"))
    ask = _coerce_float(row.get("ask"))
    if bid is not None and bid <= 0:
        bid = None
    if ask is not None and ask <= 0:
        ask = None
    if bid is not None and ask is not None:
        return (bid + ask) / 2.0
    if bid is not None:
        return bid
    if ask is not None:
        return ask
    return None


def _build_candles(
    market_rows: list[dict[str, Any]], *, max_candles: int = 500
) -> list[dict[str, Any]]:
    buckets: dict[int, dict[str, Any]] = {}
    for row in market_rows:
        timestamp = _parse_dt(row.get("captured_at"))
        latency_ms = _coerce_int(row.get("latency_ms"))
        if timestamp is not None and latency_ms is not None and 0 < latency_ms < 5000:
            timestamp = timestamp - timedelta(milliseconds=latency_ms)
        price = _series_price(row)
        if timestamp is None or price is None:
            continue
        bucket = int(timestamp.timestamp() // 60) * 60
        candle = buckets.setdefault(
            bucket,
            {
                "time": bucket,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": 0,
            },
        )
        candle["high"] = max(candle["high"], price)
        candle["low"] = min(candle["low"], price)
        candle["close"] = price
        volume = _coerce_int(row.get("volume"))
        is_cumulative = bool(row.get("volume_is_cumulative"))
        if volume is not None:
            if is_cumulative:
                candle["volume"] = volume
            else:
                candle["volume"] += volume
    candles = [buckets[key] for key in sorted(buckets)]
    return candles[-max(max_candles, 1) :]


def _trade_marker_direction(direction: Any) -> str:
    if _coerce_int(direction) and _coerce_int(direction) > 0:
        return "long"
    if _coerce_int(direction) and _coerce_int(direction) < 0:
        return "short"
    return "flat"


def _trade_markers(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for trade in trades:
        direction = _coerce_int(trade.get("direction"))
        entry_time = _seconds(trade.get("entry_time"))
        exit_time = _seconds(trade.get("exit_time"))
        entry_price = _coerce_float(trade.get("entry_price"))
        exit_price = _coerce_float(trade.get("exit_price"))
        if entry_time is not None and entry_price is not None and direction is not None:
            bucket_time = (entry_time // 60) * 60
            markers.append(
                {
                    "time": bucket_time,
                    "position": "belowBar" if direction > 0 else "aboveBar",
                    "color": "#16a34a" if direction > 0 else "#dc2626",
                    "shape": "arrowUp" if direction > 0 else "arrowDown",
                    "text": f"Entry #{trade.get('id') or trade.get('trade_id')}",
                }
            )
        if exit_time is not None and exit_price is not None:
            bucket_time = (exit_time // 60) * 60
            markers.append(
                {
                    "time": bucket_time,
                    "position": "aboveBar" if direction and direction > 0 else "belowBar",
                    "color": "#94a3b8",
                    "shape": "circle",
                    "text": f"Exit {trade.get('pnl', 0):.2f}",
                }
            )
    return markers


def _account_trade_markers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for trade in rows:
        trade_time = _seconds(trade.get("occurred_at"))
        price = _coerce_float(trade.get("price"))
        if trade_time is None or price is None:
            continue
        side = str(trade.get("side_label") or trade.get("side") or "").lower()
        is_long = side in {"long", "buy"}
        pnl = _coerce_float(trade.get("profit_and_loss")) or 0.0
        bucket_time = (trade_time // 60) * 60
        markers.append(
            {
                "time": bucket_time,
                "position": "belowBar" if is_long else "aboveBar",
                "color": "#16a34a" if pnl >= 0 else "#dc2626",
                "shape": "circle",
                "text": f"Broker fill {pnl:+.2f}",
            }
        )
    return markers


def _completed_trade_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("trade_id") or "",
        row.get("position_id") or "",
        row.get("decision_id") or "",
        row.get("entry_time"),
        row.get("exit_time"),
        row.get("direction"),
        _coerce_float(row.get("entry_price")),
        _coerce_float(row.get("exit_price")),
        _coerce_float(row.get("pnl")),
        _coerce_int(row.get("contracts")),
        row.get("zone"),
    )


def _canonical_completed_trades(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered = [row for row in rows if row.get("account_id")]
    seen: set[tuple[Any, ...]] = set()
    deduped: list[dict[str, Any]] = []
    for row in filtered:
        key = _completed_trade_key(row)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return _sort_by_timestamp_desc(deduped, "exit_time", "entry_time", "inserted_at")


def _canonical_account_trades(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["side_label"] = _order_side_label(item.get("side"))
        cleaned.append(item)
    return _sort_by_timestamp_desc(cleaned, "occurred_at", "inserted_at")


def _trade_summary_from_account_trades(rows: list[dict[str, Any]]) -> dict[str, Any]:
    realized = [row for row in rows if _coerce_float(row.get("profit_and_loss")) is not None]
    net_pnl = sum(_coerce_float(row.get("profit_and_loss")) or 0.0 for row in realized)
    win_count = sum(1 for row in realized if (_coerce_float(row.get("profit_and_loss")) or 0.0) > 0)
    loss_count = sum(
        1 for row in realized if (_coerce_float(row.get("profit_and_loss")) or 0.0) < 0
    )
    return {
        "count": len(realized),
        "net_pnl": net_pnl,
        "win_count": win_count,
        "loss_count": loss_count,
    }


def _compress_account_trade_ledger(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compressed: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        dt = _parse_dt(item.get("occurred_at"))
        cluster_key = (
            (
                dt.astimezone(PACIFIC_TZ).strftime("%Y-%m-%d %H:%M:%S")
                if dt
                else str(item.get("occurred_at") or "")
            ),
            str(item.get("side_label") or ""),
            _coerce_float(item.get("price")),
            item.get("profit_and_loss") is not None,
        )
        if compressed and compressed[-1].get("_cluster_key") == cluster_key:
            previous = compressed[-1]
            previous["fill_count"] = (_coerce_int(previous.get("fill_count")) or 1) + 1
            previous["size"] = (_coerce_int(previous.get("size")) or 0) + (
                _coerce_int(item.get("size")) or 0
            )
            if (
                previous.get("profit_and_loss") is not None
                or item.get("profit_and_loss") is not None
            ):
                previous["profit_and_loss"] = (
                    _coerce_float(previous.get("profit_and_loss")) or 0.0
                ) + (_coerce_float(item.get("profit_and_loss")) or 0.0)
            broker_ids = list(previous.get("broker_trade_ids") or [previous.get("broker_trade_id")])
            broker_ids.append(item.get("broker_trade_id"))
            previous["broker_trade_ids"] = [value for value in broker_ids if value]
            continue
        item["fill_count"] = 1
        item["broker_trade_ids"] = (
            [item.get("broker_trade_id")] if item.get("broker_trade_id") else []
        )
        item["_cluster_key"] = cluster_key
        compressed.append(item)
    for item in compressed:
        item.pop("_cluster_key", None)
    return compressed


def _compute_excursion(trade: dict[str, Any], market_rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_price = _coerce_float(trade.get("entry_price"))
    if entry_price is None:
        return {"mfe": None, "mae": None, "best_at": None, "worst_at": None}
    direction = _coerce_int(trade.get("direction")) or 0
    prices: list[tuple[datetime, float]] = []
    for row in market_rows:
        dt = _parse_dt(row.get("captured_at"))
        price = _series_price(row)
        if dt is None or price is None:
            continue
        prices.append((dt, price))
    if not prices:
        return {"mfe": None, "mae": None, "best_at": None, "worst_at": None}
    best_profit = float("-inf")
    worst_profit = float("inf")
    best_at: Optional[str] = None
    worst_at: Optional[str] = None
    for dt, price in prices:
        if direction >= 0:
            profit = price - entry_price
        else:
            profit = entry_price - price
        if profit > best_profit:
            best_profit = profit
            best_at = dt.isoformat()
        if profit < worst_profit:
            worst_profit = profit
            worst_at = dt.isoformat()
    return {
        "mfe": best_profit if best_profit != float("-inf") else None,
        "mae": worst_profit if worst_profit != float("inf") else None,
        "best_at": best_at,
        "worst_at": worst_at,
    }


def _build_timeline(
    *,
    completed_trade: Optional[dict[str, Any]],
    account_trade: Optional[dict[str, Any]],
    decisions: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    events: list[dict[str, Any]],
    snapshots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if completed_trade:
        rows.append(
            {
                "timestamp": completed_trade.get("entry_time") or completed_trade.get("exit_time"),
                "kind": "trade",
                "title": "Completed trade",
                "detail": completed_trade,
            }
        )
    if account_trade:
        rows.append(
            {
                "timestamp": account_trade.get("occurred_at"),
                "kind": "broker_trade",
                "title": "Broker trade",
                "detail": account_trade,
            }
        )
    for item in decisions:
        rows.append(
            {
                "timestamp": item.get("decided_at"),
                "kind": "decision",
                "title": item.get("action") or item.get("outcome") or "Decision",
                "detail": item,
            }
        )
    for item in orders:
        rows.append(
            {
                "timestamp": item.get("observed_at"),
                "kind": "order",
                "title": item.get("event_type") or item.get("status") or "Order",
                "detail": item,
            }
        )
    for item in events:
        rows.append(
            {
                "timestamp": item.get("event_timestamp"),
                "kind": "event",
                "title": item.get("event_type") or "Event",
                "detail": item,
            }
        )
    for item in snapshots:
        rows.append(
            {
                "timestamp": item.get("captured_at"),
                "kind": "snapshot",
                "title": item.get("status") or item.get("zone") or "Snapshot",
                "detail": item,
            }
        )
    rows.sort(key=lambda item: _parse_dt(item.get("timestamp")) or datetime.min.replace(tzinfo=UTC))
    return rows


def _trade_summary(trade: dict[str, Any], market_rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_time = _parse_dt(trade.get("entry_time"))
    exit_time = _parse_dt(trade.get("exit_time"))
    hold_seconds = None
    if entry_time and exit_time:
        hold_seconds = max(int((exit_time - entry_time).total_seconds()), 0)
    excursion = _compute_excursion(trade, market_rows)
    direction = _coerce_int(trade.get("direction"))
    entry_price = _coerce_float(trade.get("entry_price"))
    exit_price = _coerce_float(trade.get("exit_price"))
    if direction and entry_price is not None and exit_price is not None:
        pnl_points = (exit_price - entry_price) if direction > 0 else (entry_price - exit_price)
    else:
        pnl_points = None
    return {
        "hold_seconds": hold_seconds,
        "hold_minutes": round(hold_seconds / 60.0, 1) if hold_seconds is not None else None,
        "pnl_points": pnl_points,
        "mfe": excursion["mfe"],
        "mae": excursion["mae"],
        "best_at": excursion["best_at"],
        "worst_at": excursion["worst_at"],
        "direction_label": _trade_marker_direction(direction),
    }


def _current_store():
    return get_observability_store()


def _latest_run_bundle(store) -> dict[str, Any]:
    runs = store.query_run_manifests(limit=1)
    if not runs:
        return {}
    return runs[0]


def _build_console_model(state: TradingState, store) -> dict[str, Any]:
    run_id = _latest_run_id(store, state)
    recent_trades = _canonical_completed_trades(
        store.query_completed_trades(limit=8, ascending=False)
    )
    recent_account_trades = _canonical_account_trades(
        store.query_account_trades(limit=8, ascending=False)
    )
    recent_logs = _render_operator_logs(
        _filter_operator_logs(store.query_runtime_logs(limit=80, ascending=False))
    )[:5]
    recent_events = store.query_events(limit=12, ascending=False, run_id=run_id)
    recent_orders = store.query_order_lifecycle(limit=8, ascending=False, run_id=run_id)
    latest_run = _latest_run_bundle(store)
    latest_trade = (
        recent_account_trades[0]
        if recent_account_trades
        else (recent_trades[0] if recent_trades else None)
    )
    broker_truth = state.broker_truth if isinstance(state.broker_truth, dict) else {}
    current_truth = (
        broker_truth.get("current") if isinstance(broker_truth.get("current"), dict) else {}
    )
    broker_position = (
        current_truth.get("position")
        if isinstance(current_truth, dict) and isinstance(current_truth.get("position"), dict)
        else {}
    )
    broker_position_qty = _coerce_int(broker_position.get("quantity")) or 0
    broker_order_count = _coerce_int(current_truth.get("open_order_count")) or 0
    if broker_position_qty:
        broker_truth_status = "position_open"
        broker_truth_summary = (
            f"{_direction_label(broker_position_qty)} {abs(broker_position_qty)} on broker"
        )
    elif broker_order_count:
        broker_truth_status = "working_orders"
        broker_truth_summary = f"{broker_order_count} open broker order(s)"
    else:
        broker_truth_status = "flat"
        broker_truth_summary = "Broker flat, no open orders"
    day_ledger = _ledger_calendar_day_trade_stats(store, state)
    return {
        "state": state.to_dict(),
        "health": state.to_health_dict(),
        "run_id": run_id,
        "latest_run": latest_run,
        "recent_trades": recent_trades,
        "recent_account_trades": recent_account_trades,
        "recent_logs": recent_logs,
        "recent_events": recent_events,
        "recent_orders": recent_orders,
        "latest_trade": latest_trade,
        "summary": {
            "position_label": f"{state.position:+d}",
            "daily_pnl": _format_money(state.daily_pnl),
            "open_pnl": _format_money(state.account_open_pnl),
            "risk_state": state.risk_state,
            "zone": _zone_label({"name": state.current_zone, "state": state.zone_state}),
            "status": state.effective_status(),
            "run_id": run_id or "-",
            "broker_truth_status": broker_truth_status,
            "broker_truth_summary": broker_truth_summary,
            "calendar_day_trades": day_ledger["trades"],
            "calendar_day_losses": day_ledger["losses"],
        },
    }


def _build_chart_model(
    state: TradingState,
    store,
    *,
    lookback_hours: int = CHART_DEFAULT_LOOKBACK_HOURS,
) -> dict[str, Any]:
    lookback_hours = _resolve_chart_lookback_hours(lookback_hours)
    run_id = _latest_run_id(store, state)
    market_rows = _recent_market_rows(
        store,
        run_id=run_id,
        symbol=None,
        hours=lookback_hours,
        limit=_chart_market_limit(lookback_hours),
    )
    max_candles = min(5000, max(500, (lookback_hours * 60) + 120))
    candles = _build_candles(market_rows, max_candles=max_candles)
    if not candles:
        current = _coerce_float(state.last_price)
        now_time = int(_utcnow().timestamp())
        if current is not None:
            candles = [
                {
                    "time": now_time,
                    "open": current,
                    "high": current,
                    "low": current,
                    "close": current,
                    "volume": 0,
                }
            ]
    window_start = _utcnow() - timedelta(hours=lookback_hours)
    decision_limit = max(500, lookback_hours * 120)
    decisions = store.query_decision_snapshots(
        limit=decision_limit,
        ascending=True,
        run_id=run_id,
        start_time=window_start,
        end_time=_utcnow(),
    )
    order_rows = store.query_order_lifecycle(
        limit=decision_limit,
        ascending=True,
        run_id=run_id,
        start_time=window_start,
        end_time=_utcnow(),
    )
    completed_trades = _canonical_completed_trades(
        store.query_completed_trades(
            limit=50,
            ascending=False,
            run_id=run_id,
        )
    )
    account_trades = _canonical_account_trades(
        store.query_account_trades(limit=50, ascending=False, run_id=run_id)
    )
    trade_markers = _trade_markers(list(reversed(completed_trades))) + _account_trade_markers(
        list(reversed(account_trades))
    )
    decision_markers = _decision_markers(decisions)
    execution_markers = _execution_markers(order_rows)
    markers = _dedupe_markers(
        _clip_markers_to_candle_window(
            trade_markers + decision_markers + execution_markers, candles
        )
    )

    session_context = state.to_dict().get("session_context", {})
    anchored_vwaps = (
        session_context.get("anchored_vwaps") if isinstance(session_context, dict) else {}
    )
    vwap_bands = session_context.get("vwap_bands") if isinstance(session_context, dict) else {}
    session_vwap = _first_numeric(anchored_vwaps, ["vwap", "session", "eth", "rth"])
    rth_sigma = _first_numeric(vwap_bands, ["rth_sigma"])
    eth_sigma = _first_numeric(vwap_bands, ["eth_sigma"])
    sigma = rth_sigma if rth_sigma is not None else eth_sigma
    upper_band = (session_vwap + sigma) if session_vwap is not None and sigma is not None else None
    lower_band = (session_vwap - sigma) if session_vwap is not None and sigma is not None else None
    last_price = _coerce_float(state.last_price)
    if last_price is None and candles:
        last_price = _coerce_float(candles[-1].get("close"))
    price_series = _constant_series(candles, last_price)
    vwap_series = _constant_series(candles, session_vwap)
    upper_series = _constant_series(candles, upper_band)
    lower_series = _constant_series(candles, lower_band)
    alpha_long_series = _clip_series_to_candle_window(
        _decision_score_series(decisions, "long_score"), candles
    )
    alpha_short_series = _clip_series_to_candle_window(
        _decision_score_series(decisions, "short_score"), candles
    )
    alpha_flat_series = _clip_series_to_candle_window(
        _decision_score_series(decisions, "flat_bias"), candles
    )
    indicators = {
        "long_score": state.long_score,
        "short_score": state.short_score,
        "flat_bias": state.flat_bias,
        "current_zone": state.current_zone,
        "zone_state": state.zone_state,
        "active_vetoes": state.active_vetoes,
        "regime": state.regime,
        "order_flow": state.order_flow,
        "broker_truth": state.broker_truth,
        "lookback_hours": lookback_hours,
    }
    return {
        "run_id": run_id,
        "symbol": (state.last_signal or {}).get("symbol") or "ES",
        "candles": candles,
        "series": {
            "price": price_series,
            "vwap": vwap_series,
            "upper_band": upper_series,
            "lower_band": lower_series,
            "alpha_long": alpha_long_series,
            "alpha_short": alpha_short_series,
            "alpha_flat": alpha_flat_series,
        },
        "markers": markers,
        "marker_sets": {
            "trade": _clip_markers_to_candle_window(trade_markers, candles),
            "decision": _clip_markers_to_candle_window(decision_markers, candles),
            "execution": _clip_markers_to_candle_window(execution_markers, candles),
        },
        "summary": {
            "status": state.effective_status(),
            "zone": _zone_label({"name": state.current_zone, "state": state.zone_state}),
            "position": state.position,
            "daily_pnl": state.daily_pnl,
            "long_score": state.long_score,
            "short_score": state.short_score,
            "flat_bias": state.flat_bias,
            "last_price": state.last_price,
            "lookback_hours": lookback_hours,
        },
        "indicators": indicators,
        "levels": {
            "session_vwap": session_vwap,
            "upper_band": upper_band,
            "lower_band": lower_band,
            "last_price": last_price,
        },
        "chart_window": {
            "lookback_hours": lookback_hours,
            "window_start": window_start.isoformat(),
            "window_end": _utcnow().isoformat(),
        },
        "recent_trades": account_trades[:5],
    }


def _build_trades_model(state: TradingState, store) -> dict[str, Any]:
    completed_trades = _canonical_completed_trades(
        store.query_completed_trades(limit=150, ascending=False)
    )
    account_trades = _canonical_account_trades(
        store.query_account_trades(limit=150, ascending=False)
    )
    ledger_account_trades = _compress_account_trade_ledger(account_trades)
    recent_runs = store.query_run_manifests(limit=12)
    account_summary = _trade_summary_from_account_trades(account_trades)
    return {
        "state": state.to_dict(),
        "completed_trades": completed_trades,
        "account_trades": account_trades,
        "ledger_account_trades": ledger_account_trades,
        "recent_runs": recent_runs,
        "summary": {
            "completed_count": len(completed_trades),
            "account_trade_count": len(ledger_account_trades),
            "net_pnl": account_summary["net_pnl"],
            "win_count": account_summary["win_count"],
            "loss_count": account_summary["loss_count"],
            "realized_trade_count": account_summary["count"],
        },
    }


def _resolve_trade_reference(store, ref: str) -> dict[str, Any]:
    ref_text = str(ref).strip()
    completed = _canonical_completed_trades(
        store.query_completed_trades(limit=1000, ascending=False)
    )
    for row in completed:
        candidates = {
            str(row.get("id")),
            str(row.get("trade_id")) if row.get("trade_id") is not None else "",
            str(row.get("position_id")) if row.get("position_id") is not None else "",
            str(row.get("decision_id")) if row.get("decision_id") is not None else "",
            str(row.get("attempt_id")) if row.get("attempt_id") is not None else "",
            str(row.get("run_id")) if row.get("run_id") is not None else "",
        }
        if ref_text in candidates:
            return {"kind": "completed_trade", "row": row}
    account_trades = _canonical_account_trades(
        store.query_account_trades(limit=1000, ascending=False)
    )
    for row in account_trades:
        candidates = {
            str(row.get("id")),
            str(row.get("broker_trade_id")) if row.get("broker_trade_id") is not None else "",
            str(row.get("broker_order_id")) if row.get("broker_order_id") is not None else "",
            str(row.get("run_id")) if row.get("run_id") is not None else "",
        }
        if ref_text in candidates:
            return {"kind": "account_trade", "row": row}
    return {"kind": None, "row": None}


def _build_trade_detail_model(state: TradingState, store, ref: str) -> dict[str, Any]:
    resolved = _resolve_trade_reference(store, ref)
    trade = resolved["row"]
    if not trade:
        return {"not_found": True, "ref": ref, "state": state.to_dict()}

    kind = resolved["kind"]
    run_id = trade.get("run_id") or _latest_run_id(store, state)
    entry_time = trade.get("entry_time") or trade.get("occurred_at")
    exit_time = trade.get("exit_time") or trade.get("occurred_at")
    start = _parse_dt(entry_time) or _parse_dt(exit_time) or _utcnow()
    end = _parse_dt(exit_time) or start
    window_start = (start - timedelta(minutes=30)).isoformat()
    window_end = (end + timedelta(minutes=45)).isoformat()
    decisions = store.query_decision_snapshots(
        limit=100,
        ascending=True,
        run_id=run_id,
        start_time=window_start,
        end_time=window_end,
        search=ref,
    )
    orders = store.query_order_lifecycle(
        limit=100,
        ascending=True,
        run_id=run_id,
        start_time=window_start,
        end_time=window_end,
        search=ref,
    )
    events = store.query_events(
        limit=100,
        ascending=True,
        run_id=run_id,
        start_time=window_start,
        end_time=window_end,
        search=ref,
    )
    snapshots = store.query_state_snapshots(
        limit=50,
        ascending=True,
        run_id=run_id,
        start_time=window_start,
        end_time=window_end,
        search=ref,
    )
    market_rows = store.query_market_tape(
        limit=400,
        ascending=True,
        run_id=run_id,
        start_time=window_start,
        end_time=window_end,
    )
    timeline = _build_timeline(
        completed_trade=trade if kind == "completed_trade" else None,
        account_trade=trade if kind == "account_trade" else None,
        decisions=decisions,
        orders=orders,
        events=events,
        snapshots=snapshots,
    )
    summary_source = (
        trade
        if kind == "completed_trade"
        else {
            "direction": trade.get("side") if trade.get("side") is not None else trade.get("size"),
            "entry_time": trade.get("occurred_at"),
            "exit_time": trade.get("occurred_at"),
            "entry_price": trade.get("price"),
            "exit_price": trade.get("price"),
        }
    )
    summary = _trade_summary(summary_source, market_rows)
    display = {
        "entry_time": _format_datetime(
            trade.get("entry_time") if kind == "completed_trade" else trade.get("occurred_at")
        ),
        "exit_time": _format_datetime(
            trade.get("exit_time") if kind == "completed_trade" else trade.get("occurred_at")
        ),
        "entry_price": _format_number(
            trade.get("entry_price") if kind == "completed_trade" else trade.get("price")
        ),
        "exit_price": _format_number(
            trade.get("exit_price") if kind == "completed_trade" else trade.get("price")
        ),
        "pnl": _format_money(
            trade.get("pnl") if kind == "completed_trade" else trade.get("profit_and_loss")
        ),
    }
    related_completed = _canonical_completed_trades(
        store.query_completed_trades(limit=12, ascending=False, run_id=run_id)
    )
    related_account = _canonical_account_trades(
        store.query_account_trades(limit=12, ascending=False, run_id=run_id)
    )
    return {
        "not_found": False,
        "kind": kind,
        "ref": ref,
        "trade": trade,
        "run_id": run_id,
        "summary": summary,
        "timeline": timeline,
        "decisions": decisions,
        "orders": orders,
        "events": events,
        "snapshots": snapshots,
        "market_rows": market_rows[-120:],
        "related_completed_trades": related_completed,
        "related_account_trades": related_account,
        "state": state.to_dict(),
        "display": display,
    }


def _build_logs_model(state: TradingState, store) -> dict[str, Any]:
    run_id = _latest_run_id(store, state)
    logs = _render_operator_logs(
        _filter_operator_logs(store.query_runtime_logs(limit=400, ascending=False, run_id=run_id))
    )[:200]
    events = store.query_events(limit=100, ascending=False, run_id=run_id)
    orders = store.query_order_lifecycle(limit=100, ascending=False, run_id=run_id)
    return {
        "state": state.to_dict(),
        "run_id": run_id,
        "logs": logs,
        "events": events,
        "orders": orders,
        "summary": {
            "log_count": len(logs),
            "event_count": len(events),
            "order_count": len(orders),
        },
    }


def _build_system_model(state: TradingState, store) -> dict[str, Any]:
    recent_runs = store.query_run_manifests(limit=10)
    bridge_health = store.query_bridge_health(limit=20)
    recent_logs = _filter_operator_logs(store.query_runtime_logs(limit=100, ascending=False))[:25]
    return {
        "state": state.to_dict(),
        "health": state.to_health_dict(),
        "db_path": store.get_db_path(),
        "recent_runs": recent_runs,
        "bridge_health": bridge_health,
        "recent_logs": recent_logs,
        "summary": {
            "run_count": len(recent_runs),
            "bridge_health_count": len(bridge_health),
            "log_count": len(recent_logs),
            "observability_enabled": (
                bool(getattr(store.settings, "enabled", False))
                if hasattr(store, "settings")
                else False
            ),
        },
    }


def _page_context(
    title: str, active_page: str, state: TradingState, **extra: Any
) -> dict[str, Any]:
    cfg = get_config()
    pages = [
        {"href": "/", "label": "Console", "active": active_page == "console"},
        {"href": "/chart", "label": "Chart", "active": active_page == "chart"},
        {"href": "/trades", "label": "Trades", "active": active_page == "trades"},
        {"href": "/logs", "label": "Logs", "active": active_page == "logs"},
        {"href": "/system", "label": "System", "active": active_page == "system"},
    ]
    base = {
        "title": title,
        "pages": pages,
        "state": state.to_dict(),
        "health": state.to_health_dict(),
        "server": cfg.server,
    }
    base.update(extra)
    return base


def create_app(config: Optional[Config] = None) -> Flask:
    cfg = config or get_config()
    app = Flask(
        __name__,
        template_folder=str(_TEMPLATE_DIR),
        static_folder=str(_STATIC_DIR),
        static_url_path="/static",
    )
    app.config["GTRADE_CONFIG"] = cfg

    @app.template_filter("money")
    def _money_filter(value: Any) -> str:
        return _format_money(value)

    @app.template_filter("number")
    def _number_filter(value: Any) -> str:
        return _format_number(value)

    @app.template_filter("integer")
    def _integer_filter(value: Any) -> str:
        return _format_integer(value)

    @app.template_filter("dt")
    def _dt_filter(value: Any) -> str:
        return _format_datetime(value)

    @app.template_filter("json")
    def _json_filter(value: Any) -> str:
        return json.dumps(_json_safe(value), indent=2, sort_keys=True)

    @app.get("/health")
    def health() -> Response:
        payload = _json_safe(get_state().to_health_dict())
        status_code = 200 if payload.get("status") == "healthy" else 503
        return jsonify(payload), status_code

    @app.get("/debug")
    def debug() -> Response:
        return jsonify(_json_safe(get_state().to_dict()))

    @app.get("/")
    def console() -> str:
        model = _build_console_model(get_state(), _current_store())
        return render_template(
            "console.html",
            **_page_context("Console", "console", get_state(), model=_json_safe(model)),
        )

    @app.get("/chart")
    def chart() -> str:
        lookback_hours = _resolve_chart_lookback_hours(
            request.args.get("lookback_hours") or request.args.get("hours")
        )
        model = _build_chart_model(get_state(), _current_store(), lookback_hours=lookback_hours)
        return render_template(
            "chart.html", **_page_context("Chart", "chart", get_state(), model=_json_safe(model))
        )

    @app.get("/trades")
    def trades() -> str:
        model = _build_trades_model(get_state(), _current_store())
        return render_template(
            "trades.html", **_page_context("Trades", "trades", get_state(), model=_json_safe(model))
        )

    @app.get("/trades/<ref>")
    def trade_detail(ref: str) -> str:
        model = _build_trade_detail_model(get_state(), _current_store(), ref)
        if model.get("not_found"):
            abort(404)
        return render_template(
            "trade_detail.html",
            **_page_context(f"Trade {ref}", "trades", get_state(), model=_json_safe(model)),
        )

    @app.get("/logs")
    def logs() -> str:
        model = _build_logs_model(get_state(), _current_store())
        return render_template(
            "logs.html", **_page_context("Logs", "logs", get_state(), model=_json_safe(model))
        )

    @app.get("/system")
    def system() -> str:
        model = _build_system_model(get_state(), _current_store())
        return render_template(
            "system.html", **_page_context("System", "system", get_state(), model=_json_safe(model))
        )

    @app.get("/api/state")
    def api_state() -> Response:
        return jsonify(_json_safe(get_state().to_dict()))

    @app.get("/api/chart")
    def api_chart() -> Response:
        lookback_hours = _resolve_chart_lookback_hours(
            request.args.get("lookback_hours") or request.args.get("hours")
        )
        return jsonify(
            _json_safe(
                _build_chart_model(
                    get_state(), _current_store(), lookback_hours=lookback_hours
                )
            )
        )

    @app.get("/api/trades")
    def api_trades() -> Response:
        return jsonify(_json_safe(_build_trades_model(get_state(), _current_store())))

    @app.get("/api/trades/<ref>")
    def api_trade_detail(ref: str) -> Response:
        model = _build_trade_detail_model(get_state(), _current_store(), ref)
        if model.get("not_found"):
            return jsonify({"error": "not_found", "ref": ref}), 404
        return jsonify(_json_safe(model))

    @app.get("/api/logs")
    def api_logs() -> Response:
        return jsonify(_json_safe(_build_logs_model(get_state(), _current_store())))

    @app.get("/api/system")
    def api_system() -> Response:
        return jsonify(_json_safe(_build_system_model(get_state(), _current_store())))

    def _sse_response(event_name: str, payload_fn, interval_seconds: float = 1.0) -> Response:
        def _stream():
            last_signature: Optional[str] = None
            yield ": connected\n\n"
            while True:
                payload = _json_safe(payload_fn())
                signature = json.dumps(payload, sort_keys=True, separators=(",", ":"))
                if signature != last_signature:
                    yield f"data: {signature}\n\n"
                    last_signature = signature
                time.sleep(interval_seconds)

        response = Response(
            stream_with_context(_stream()),
            mimetype="text/event-stream",
        )
        response.headers["Cache-Control"] = "no-cache, no-transform"
        response.headers["X-Accel-Buffering"] = "no"
        return response

    @app.get("/stream/state")
    def stream_state() -> Response:
        return _sse_response("state", lambda: get_state().to_dict(), interval_seconds=1.0)

    @app.get("/stream/chart")
    def stream_chart() -> Response:
        lookback_hours = _resolve_chart_lookback_hours(
            request.args.get("lookback_hours") or request.args.get("hours")
        )
        return _sse_response(
            "chart",
            lambda: _build_chart_model(
                get_state(), _current_store(), lookback_hours=lookback_hours
            ),
            interval_seconds=2.0,
        )

    @app.get("/stream/logs")
    def stream_logs() -> Response:
        return _sse_response(
            "logs", lambda: _build_logs_model(get_state(), _current_store()), interval_seconds=2.0
        )

    return app


class DebugServer:
    """Local Flask server for health and operator console endpoints."""

    def __init__(self, config: Optional[ServerConfig] = None):
        self.config = config or get_config().server
        self.host = self.config.host
        self.health_port = self.config.health_port
        self.debug_port = self.config.debug_port
        self.app = create_app()
        self._health_server = None
        self._debug_server = None
        self._health_thread: Optional[threading.Thread] = None
        self._debug_thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._health_server = make_server(self.host, self.health_port, self.app, threaded=True)
        logger.info("Health/console server started on %s:%s", self.host, self.health_port)
        self._debug_server = make_server(self.host, self.debug_port, self.app, threaded=True)
        logger.info("Debug/console server started on %s:%s", self.host, self.debug_port)
        self._running = True
        self._health_thread = threading.Thread(
            target=self._health_server.serve_forever,
            kwargs={"poll_interval": 0.25},
            daemon=True,
        )
        self._debug_thread = threading.Thread(
            target=self._debug_server.serve_forever,
            kwargs={"poll_interval": 0.25},
            daemon=True,
        )
        self._health_thread.start()
        self._debug_thread.start()

    def stop(self):
        self._running = False
        if self._health_server:
            self._health_server.shutdown()
            self._health_server.server_close()
            self._health_server = None
        if self._debug_server:
            self._debug_server.shutdown()
            self._debug_server.server_close()
            self._debug_server = None
        if self._health_thread and self._health_thread.is_alive():
            self._health_thread.join(timeout=2)
        if self._debug_thread and self._debug_thread.is_alive():
            self._debug_thread.join(timeout=2)
        self._health_thread = None
        self._debug_thread = None
        logger.info("Flask console servers stopped")


_server: Optional[DebugServer] = None


def get_server(force_recreate: bool = False) -> DebugServer:
    global _server
    if force_recreate:
        _server = None
    if _server is None:
        _server = DebugServer()
    return _server
