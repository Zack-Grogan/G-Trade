"""In-process trading runtime state (framework-neutral; no HTTP)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Optional

from src.runtime.zone_surface import ZONE_SEMANTICS_VERSION


class TradingState:
    """Global trading state container."""

    def __init__(self):
        self.status: str = "stopped"
        self.running: bool = False
        self.tenant_id: Optional[str] = None
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
            "tenant_id": self.tenant_id,
            "data_mode": self.data_mode,
            "zone": {
                "name": self.current_zone,
                "state": self.zone_state,
                "semantics_version": ZONE_SEMANTICS_VERSION,
            },
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
                "last_backfill": self.last_backfill,
            },
        }

    def to_health_dict(self) -> dict[str, Any]:
        return {
            "status": self.effective_status(),
            "tenant_id": self.tenant_id,
            "data_mode": self.data_mode,
            "zone": self.current_zone or "inactive",
            "zone_state": self.zone_state,
            "zone_semantics_version": ZONE_SEMANTICS_VERSION,
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
    from src.observability import get_observability_store

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
