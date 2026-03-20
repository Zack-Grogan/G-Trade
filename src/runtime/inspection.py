"""Resolve live runtime debug/health views via in-process state or SQLite snapshots."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from src.config import Config
from src.observability import get_observability_store
from src.runtime.state import get_state

logger = logging.getLogger(__name__)


def resolve_log_path(cfg: Config) -> Path:
    project_root = Path(__file__).resolve().parent.parent.parent
    log_path = Path(cfg.logging.file)
    if not log_path.is_absolute():
        log_path = project_root / log_path
    return log_path


def runtime_status_path(cfg: Config, log_path: Optional[Path] = None) -> Path:
    lp = log_path or resolve_log_path(cfg)
    return lp.parent / "runtime" / "runtime_status.json"


def read_runtime_status(cfg: Config, log_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    path = runtime_status_path(cfg, log_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Failed to read runtime status at %s", path, exc_info=True)
        return None


def health_dict_from_debug(debug: dict[str, Any]) -> dict[str, Any]:
    """Match :meth:`TradingState.to_health_dict` keys from a ``to_dict()``-shaped payload."""
    zone = debug.get("zone") or {}
    if isinstance(zone, dict):
        zone_name = zone.get("name") or "inactive"
    else:
        zone_name = str(zone or "inactive")
    pos = debug.get("position") or {}
    risk = debug.get("risk") or {}
    acct = debug.get("account") or {}
    hb = debug.get("heartbeat") or {}
    alpha = debug.get("alpha") or {}
    contracts = pos.get("contracts") if isinstance(pos, dict) else pos
    return {
        "status": debug.get("status"),
        "data_mode": debug.get("data_mode"),
        "zone": zone_name,
        "position": int(contracts or 0),
        "daily_pnl": float((acct.get("daily_pnl") if isinstance(acct, dict) else None) or 0.0),
        "risk_state": (risk.get("state") if isinstance(risk, dict) else None)
        or str(debug.get("risk_state") or "normal"),
        "long_score": float(alpha.get("long_score") or 0.0),
        "short_score": float(alpha.get("short_score") or 0.0),
        "practice_account": acct.get("is_practice") if isinstance(acct, dict) else None,
        "market_stream_connected": hb.get("market_stream_connected"),
    }


def _latest_snapshot_payload_for_run(run_id: Optional[str]) -> Optional[dict[str, Any]]:
    if not run_id:
        return None
    store = get_observability_store()
    rows = store.query_state_snapshots(limit=1, run_id=str(run_id))
    if not rows:
        return None
    payload = rows[0].get("payload")
    return payload if isinstance(payload, dict) else None


def _minimal_debug_from_runtime_status(status: dict[str, Any]) -> dict[str, Any]:
    """When SQLite has not yet persisted a snapshot, expose control-plane fields only."""
    return {
        "run_id": status.get("run_id"),
        "status": status.get("phase") or status.get("status") or "unknown",
        "running": bool(status.get("running")),
        "data_mode": status.get("data_mode") or "unknown",
        "zone": {"name": None, "state": "inactive"},
        "account": {},
        "broker_truth": {},
        "lifecycle": {},
        "heartbeat": {},
    }


def fetch_runtime_debug_state(
    cfg: Config,
    *,
    log_path: Optional[Path] = None,
) -> tuple[Optional[dict[str, Any]], str]:
    """Return ``(debug_dict, source)`` where source is ``in_process``, ``sqlite``, ``status_file``, or ``none``."""
    status = read_runtime_status(cfg, log_path)
    my_pid = os.getpid()

    if status and status.get("running"):
        remote_pid = status.get("pid")
        try:
            remote_pid_int = int(remote_pid) if remote_pid is not None else None
        except (TypeError, ValueError):
            remote_pid_int = None

        if remote_pid_int is not None and remote_pid_int == my_pid:
            return get_state().to_dict(), "in_process"

        if remote_pid_int is not None and remote_pid_int != my_pid:
            snap = _latest_snapshot_payload_for_run(status.get("run_id"))
            if snap:
                return snap, "sqlite"
            logger.debug(
                "No state snapshot yet for run_id=%s; using runtime_status.json only",
                status.get("run_id"),
            )
            return _minimal_debug_from_runtime_status(status), "status_file"

    # No active runtime status — still allow in-process dict for same-process tools/tests
    st = get_state()
    if st.running or (st.status and str(st.status).lower() not in {"", "stopped"}):
        return st.to_dict(), "in_process"

    return None, "none"


def fetch_runtime_health_dict(
    cfg: Config,
    *,
    log_path: Optional[Path] = None,
) -> tuple[dict[str, Any], str]:
    """Return ``(health_dict, source)`` for CLI display."""
    debug, src = fetch_runtime_debug_state(cfg, log_path=log_path)
    if debug:
        return health_dict_from_debug(debug), src
    return get_state().to_health_dict(), "in_process"
