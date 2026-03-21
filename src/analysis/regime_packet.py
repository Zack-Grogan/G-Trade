"""Local regime packet and trade review analysis."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from statistics import mean
from typing import Any, Iterable, Optional

import pytz

from src.config import Config, get_config
from src.observability import ObservabilityStore, get_observability_store
from src.runtime.inspection import fetch_runtime_debug_state, health_dict_from_debug
from src.runtime.state import get_state

PACIFIC_TZ = pytz.timezone("America/Los_Angeles")


def _parse_dt(value: Any) -> Optional[datetime]:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _to_pt(value: Any) -> Optional[datetime]:
    parsed = _parse_dt(value)
    return parsed.astimezone(PACIFIC_TZ) if parsed else None


def _best_price(row: dict[str, Any]) -> Optional[float]:
    for key in ("last", "bid", "ask"):
        value = row.get(key)
        if value not in {None, ""}:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number > 0:
                return number
    return None


def _coerce_float(value: Any) -> Optional[float]:
    try:
        if value in {None, ""}:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_trade(trade: dict[str, Any]) -> dict[str, Any]:
    item = dict(trade)
    item["entry_dt"] = _parse_dt(item.get("entry_time"))
    item["exit_dt"] = _parse_dt(item.get("exit_time"))
    item["entry_pt"] = _to_pt(item.get("entry_time"))
    item["exit_pt"] = _to_pt(item.get("exit_time"))
    item["pnl"] = float(item.get("pnl") or 0.0)
    item["entry_price"] = float(item.get("entry_price") or 0.0)
    item["exit_price"] = float(item.get("exit_price") or 0.0)
    item["contracts"] = int(item.get("contracts") or 0)
    item["direction"] = int(item.get("direction") or 0)
    return item


def _trade_direction_label(trade: dict[str, Any]) -> str:
    direction = int(trade.get("direction") or 0)
    return "LONG" if direction > 0 else "SHORT" if direction < 0 else "FLAT"


def _duration_hours(trade: dict[str, Any]) -> float:
    entry_dt = trade.get("entry_dt")
    exit_dt = trade.get("exit_dt")
    if not entry_dt or not exit_dt:
        return 0.0
    return round((exit_dt - entry_dt).total_seconds() / 3600.0, 2)


def _resolve_account_id(account_id: Optional[str]) -> Optional[str]:
    if account_id:
        return account_id
    state = get_state()
    if state.account_id:
        return state.account_id
    return None


def _load_runtime_state(cfg: Config) -> tuple[dict[str, Any], dict[str, Any], str]:
    debug, source = fetch_runtime_debug_state(cfg)
    if debug:
        return debug, health_dict_from_debug(debug), source
    state = get_state()
    return state.to_dict(), state.to_health_dict(), "in_process"


def _current_price_at_or_after(
    rows: list[dict[str, Any]], target: datetime
) -> Optional[dict[str, Any]]:
    for row in rows:
        captured_at = _parse_dt(row.get("captured_at"))
        if captured_at is not None and captured_at >= target:
            price = _best_price(row)
            if price is not None:
                return {"captured_at": captured_at.isoformat(), "price": price}
    return None


def _compute_excursions(trade: dict[str, Any], tape_rows: list[dict[str, Any]]) -> dict[str, Any]:
    entry_price = trade["entry_price"]
    direction = trade["direction"]
    if entry_price <= 0 or direction == 0 or not tape_rows:
        return {
            "mfe_points": None,
            "mae_points": None,
            "time_to_best_profit_minutes": None,
            "time_to_worst_drawdown_minutes": None,
            "trade_duration_hours": _duration_hours(trade),
        }

    best_points: Optional[float] = None
    worst_points: Optional[float] = None
    best_time: Optional[datetime] = None
    worst_time: Optional[datetime] = None
    entry_dt = trade["entry_dt"]

    for row in tape_rows:
        price = _best_price(row)
        captured_at = _parse_dt(row.get("captured_at"))
        if price is None or captured_at is None or entry_dt is None:
            continue
        move = (price - entry_price) * direction
        if best_points is None or move > best_points:
            best_points = move
            best_time = captured_at
        if worst_points is None or move < worst_points:
            worst_points = move
            worst_time = captured_at

    def _minutes_from_entry(ts: Optional[datetime]) -> Optional[float]:
        if not entry_dt or not ts:
            return None
        return round((ts - entry_dt).total_seconds() / 60.0, 2)

    return {
        "mfe_points": round(best_points or 0.0, 4) if best_points is not None else None,
        "mae_points": round(worst_points or 0.0, 4) if worst_points is not None else None,
        "time_to_best_profit_minutes": _minutes_from_entry(best_time),
        "time_to_worst_drawdown_minutes": _minutes_from_entry(worst_time),
        "trade_duration_hours": _duration_hours(trade),
    }


def _candles_from_tape(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for row in rows:
        ts = _parse_dt(row.get("captured_at"))
        price = _best_price(row)
        if ts is None or price is None:
            continue
        bucket = ts.astimezone(PACIFIC_TZ).replace(second=0, microsecond=0).isoformat()
        candle = buckets.get(bucket)
        if candle is None:
            candle = {
                "time": bucket,
                "open": price,
                "high": price,
                "low": price,
                "close": price,
                "volume": float(row.get("last_size") or row.get("volume") or 0.0),
            }
            buckets[bucket] = candle
            continue
        candle["high"] = max(candle["high"], price)
        candle["low"] = min(candle["low"], price)
        candle["close"] = price
        candle["volume"] += float(row.get("last_size") or row.get("volume") or 0.0)
    return [buckets[key] for key in sorted(buckets.keys())]


def _select_entry_decision(
    trade: dict[str, Any], decision_rows: list[dict[str, Any]]
) -> Optional[dict[str, Any]]:
    if not decision_rows:
        return None
    decision_id = trade.get("decision_id")
    attempt_id = trade.get("attempt_id")
    direction_action = (
        "LONG" if trade["direction"] > 0 else "SHORT" if trade["direction"] < 0 else None
    )
    entry_dt = trade["entry_dt"]

    scored: list[tuple[tuple[int, float], dict[str, Any]]] = []
    for row in decision_rows:
        decided_at = _parse_dt(row.get("decided_at"))
        if decided_at is None or entry_dt is None:
            continue
        score = 0
        if decision_id and row.get("decision_id") == decision_id:
            score += 4
        if attempt_id and row.get("attempt_id") == attempt_id:
            score += 2
        if direction_action and row.get("action") == direction_action:
            score += 2
        if row.get("outcome") in {"entry_submitted", "order_submitted"}:
            score += 1
        time_distance = abs((entry_dt - decided_at).total_seconds())
        scored.append(((score, -time_distance), row))
    if not scored:
        return None
    return max(scored, key=lambda item: item[0])[1]


def _extract_exit_reason(trade: dict[str, Any], events: list[dict[str, Any]]) -> str:
    payload = trade.get("payload") or {}
    if payload.get("reason"):
        return str(payload["reason"])
    trade_id = trade.get("trade_id")
    candidates = []
    for row in events:
        if row.get("event_type") == "position_closed":
            if trade_id and row.get("payload", {}).get("trade_id") == trade_id:
                return str(row.get("reason") or "position_closed")
            candidates.append(row)
    if candidates:
        return str(candidates[-1].get("reason") or "position_closed")
    return "unknown"


def _compare_exit_candidates(
    trade: dict[str, Any],
    tape_rows: list[dict[str, Any]],
    cfg: Config,
) -> list[dict[str, Any]]:
    if trade["entry_dt"] is None:
        return []
    policy_tz = pytz.timezone(cfg.strategy.session_exit_timezone)
    entry_local = trade["entry_dt"].astimezone(policy_tz)
    checkpoint_specs = [
        ("morning_zone_end", "06:30"),
        ("session_checkpoint", cfg.strategy.session_exit_checkpoint_time),
        ("hard_flat", cfg.strategy.session_exit_hard_flat_time),
    ]
    results: list[dict[str, Any]] = []
    for label, clock_value in checkpoint_specs:
        hour, minute = [int(part) for part in clock_value.split(":", 1)]
        target_local = entry_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_local < entry_local:
            continue
        target_utc = target_local.astimezone(UTC)
        match = _current_price_at_or_after(tape_rows, target_utc)
        if not match:
            continue
        price = float(match["price"])
        pnl_points = (price - trade["entry_price"]) * trade["direction"]
        results.append(
            {
                "label": label,
                "target_time": target_local.isoformat(),
                "observed_at": match["captured_at"],
                "price": round(price, 4),
                "pnl_points": round(pnl_points, 4),
                "pnl_dollars": round(pnl_points * 50 * max(trade["contracts"], 1), 2),
            }
        )
    results.append(
        {
            "label": "actual_exit",
            "target_time": trade["exit_pt"].isoformat() if trade.get("exit_pt") else None,
            "observed_at": trade["exit_dt"].isoformat() if trade.get("exit_dt") else None,
            "price": round(trade["exit_price"], 4),
            "pnl_points": round(
                (trade["exit_price"] - trade["entry_price"]) * trade["direction"], 4
            ),
            "pnl_dollars": round(trade["pnl"], 2),
        }
    )
    return results


def _windowed_rows(
    store: ObservabilityStore,
    *,
    trade: dict[str, Any],
    extra_lead_minutes: int = 45,
    extra_lag_minutes: int = 15,
) -> dict[str, list[dict[str, Any]]]:
    entry_dt = trade["entry_dt"]
    exit_dt = trade["exit_dt"]
    if entry_dt is None or exit_dt is None:
        return {"decisions": [], "orders": [], "events": [], "tape": []}
    start_time = entry_dt - timedelta(minutes=extra_lead_minutes)
    end_time = exit_dt + timedelta(minutes=extra_lag_minutes)
    symbol = trade.get("payload", {}).get("symbol") or "ES"
    run_id = trade.get("run_id")
    return {
        "decisions": store.query_decision_snapshots(
            limit=500, run_id=run_id, start_time=start_time, end_time=end_time, symbol=symbol
        ),
        "orders": store.query_order_lifecycle(
            limit=500, run_id=run_id, start_time=start_time, end_time=end_time, symbol=symbol
        ),
        "events": store.query_events(
            limit=500, run_id=run_id, start_time=start_time, end_time=end_time
        ),
        "tape": store.query_market_tape(
            limit=5000, run_id=run_id, start_time=start_time, end_time=end_time, symbol=symbol
        ),
    }


def build_trade_review(
    trade_key: str | int,
    *,
    account_id: Optional[str] = None,
    store: Optional[ObservabilityStore] = None,
    config: Optional[Config] = None,
) -> dict[str, Any]:
    cfg = config or get_config()
    store = store or get_observability_store()
    effective_account = _resolve_account_id(account_id)
    trades = store.query_completed_trades(limit=300, account_id=effective_account)
    selected: Optional[dict[str, Any]] = None
    for row in trades:
        if str(row.get("id")) == str(trade_key) or str(row.get("trade_id") or "") == str(trade_key):
            selected = row
            break
    if selected is None:
        raise ValueError(f"Trade not found: {trade_key}")

    trade = _normalize_trade(selected)
    windows = _windowed_rows(store, trade=trade)
    entry_decision = _select_entry_decision(trade, windows["decisions"])
    excursions = _compute_excursions(trade, windows["tape"])
    exit_candidates = _compare_exit_candidates(trade, windows["tape"], cfg)
    return {
        "trade": {
            "id": trade.get("id"),
            "trade_id": trade.get("trade_id"),
            "run_id": trade.get("run_id"),
            "account_id": trade.get("account_id"),
            "account_name": trade.get("account_name"),
            "zone": trade.get("zone"),
            "direction": _trade_direction_label(trade),
            "contracts": trade.get("contracts"),
            "entry_time": trade["entry_dt"].isoformat() if trade["entry_dt"] else None,
            "exit_time": trade["exit_dt"].isoformat() if trade["exit_dt"] else None,
            "entry_time_pt": trade["entry_pt"].isoformat() if trade["entry_pt"] else None,
            "exit_time_pt": trade["exit_pt"].isoformat() if trade["exit_pt"] else None,
            "entry_price": trade.get("entry_price"),
            "exit_price": trade.get("exit_price"),
            "pnl": trade.get("pnl"),
            "duration_hours": _duration_hours(trade),
            "regime": trade.get("regime"),
            "event_tags": list(trade.get("event_tags") or []),
            "actual_exit_reason": _extract_exit_reason(trade, windows["events"]),
        },
        "entry_decision": entry_decision,
        "market_excursions": excursions,
        "exit_candidates": exit_candidates,
        "supporting": {
            "orders": windows["orders"][-20:],
            "events": windows["events"][-40:],
            "candles": _candles_from_tape(windows["tape"]),
            "decision_count": len(windows["decisions"]),
            "order_event_count": len(windows["orders"]),
            "market_points": len(windows["tape"]),
        },
    }


def _trade_filter(
    trades: Iterable[dict[str, Any]],
    *,
    account_id: Optional[str],
    lookback_days: int,
) -> list[dict[str, Any]]:
    cutoff = datetime.now(UTC) - timedelta(days=max(lookback_days, 1))
    results: list[dict[str, Any]] = []
    seen_dates: set[str] = set()
    for raw in trades:
        trade = _normalize_trade(raw)
        if account_id and trade.get("account_id") != account_id:
            continue
        if trade["entry_dt"] is None or trade["exit_dt"] is None:
            continue
        if trade["exit_dt"] < cutoff:
            continue
        entry_pt = trade["entry_pt"]
        if entry_pt and entry_pt.date().isoformat() == "2026-03-16":
            marker = "2026-03-16"
            if marker in seen_dates:
                continue
            seen_dates.add(marker)
        results.append(trade)
    return sorted(results, key=lambda item: item["entry_dt"] or datetime.now(UTC))


def build_regime_packet(
    *,
    account_id: Optional[str] = None,
    lookback_days: int = 14,
    store: Optional[ObservabilityStore] = None,
    config: Optional[Config] = None,
) -> dict[str, Any]:
    cfg = config or get_config()
    store = store or get_observability_store()
    effective_account = _resolve_account_id(account_id)
    trades = _trade_filter(
        store.query_completed_trades(limit=500, account_id=effective_account),
        account_id=effective_account,
        lookback_days=lookback_days,
    )

    by_hour: dict[int, list[dict[str, Any]]] = defaultdict(list)
    by_zone: dict[str, list[dict[str, Any]]] = defaultdict(list)
    reviews: list[dict[str, Any]] = []
    for trade in trades:
        entry_pt = trade["entry_pt"]
        if entry_pt is not None:
            by_hour[entry_pt.hour].append(trade)
        by_zone[str(trade.get("zone") or "Unknown")].append(trade)
        reviews.append(
            build_trade_review(
                str(trade["id"]), account_id=effective_account, store=store, config=cfg
            )
        )

    def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        pnls = [float(row.get("pnl") or 0.0) for row in rows]
        durations = [_duration_hours(row) for row in rows]
        return {
            "count": len(rows),
            "wins": sum(1 for value in pnls if value > 0),
            "losses": sum(1 for value in pnls if value < 0),
            "flat": sum(1 for value in pnls if value == 0),
            "total_pnl": round(sum(pnls), 2),
            "avg_pnl": round(mean(pnls), 2) if pnls else 0.0,
            "avg_duration_hours": round(mean(durations), 2) if durations else 0.0,
        }

    hour_summary = {
        str(hour): {
            **_summary(rows),
            "direction_mix": {
                "long": sum(1 for row in rows if row["direction"] > 0),
                "short": sum(1 for row in rows if row["direction"] < 0),
            },
        }
        for hour, rows in sorted(by_hour.items())
    }
    zone_summary = {zone: _summary(rows) for zone, rows in sorted(by_zone.items())}
    morning_rows = by_hour.get(4, [])
    overnight_rows = by_hour.get(23, [])

    promotion_recommendations: dict[str, str] = {}
    for zone_name, summary in zone_summary.items():
        if zone_name == "Pre-Open":
            promotion_recommendations[zone_name] = "live"
        elif summary["count"] == 0:
            promotion_recommendations[zone_name] = "shadow_insufficient_sample"
        elif summary["total_pnl"] > 0 and summary["wins"] >= 2:
            promotion_recommendations[zone_name] = "candidate_for_promotion"
        else:
            promotion_recommendations[zone_name] = "shadow_only"

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "account_id": effective_account,
        "lookback_days": lookback_days,
        "trade_count": len(trades),
        "morning_meta": {
            "candidate": bool(morning_rows),
            "summary": _summary(morning_rows),
            "entry_window": "04:00-04:59 America/Los_Angeles",
        },
        "overnight_negative_control": {
            "summary": _summary(overnight_rows),
            "entry_window": "23:00-23:59 America/Los_Angeles",
        },
        "entry_hour_summary": hour_summary,
        "zone_summary": zone_summary,
        "promotion_recommendations": promotion_recommendations,
        "trade_reviews": reviews,
        "launch_defaults": {
            "launch_gate_enabled": cfg.strategy.launch_gate_enabled,
            "live_entry_zones": list(cfg.strategy.live_entry_zones or []),
            "shadow_entry_zones": list(cfg.strategy.shadow_entry_zones or []),
            "session_exit_enabled": cfg.strategy.session_exit_enabled,
            "session_exit_checkpoint_time": cfg.strategy.session_exit_checkpoint_time,
            "session_exit_hard_flat_time": cfg.strategy.session_exit_hard_flat_time,
            "session_exit_timezone": cfg.strategy.session_exit_timezone,
        },
    }


def build_launch_readiness(
    *,
    account_id: Optional[str] = None,
    store: Optional[ObservabilityStore] = None,
    config: Optional[Config] = None,
) -> dict[str, Any]:
    cfg = config or get_config()
    packet = build_regime_packet(account_id=account_id, lookback_days=14, store=store, config=cfg)
    state, health, state_source = _load_runtime_state(cfg)
    morning_candidate = packet["morning_meta"]["summary"]
    account = state.get("account") if isinstance(state.get("account"), dict) else {}
    broker_truth = (
        state.get("broker_truth") if isinstance(state.get("broker_truth"), dict) else {}
    )
    current_broker_truth = (
        broker_truth.get("current") if isinstance(broker_truth.get("current"), dict) else {}
    )
    contradictions = (
        broker_truth.get("contradictions")
        if isinstance(broker_truth.get("contradictions"), dict)
        else {}
    )
    current_position = (
        current_broker_truth.get("position")
        if isinstance(current_broker_truth.get("position"), dict)
        else {}
    )
    lifecycle = state.get("lifecycle") if isinstance(state.get("lifecycle"), dict) else {}
    recovery_verified = bool(
        lifecycle.get("recovery_verified")
        or lifecycle.get("restart_verified")
        or lifecycle.get("recover_verified")
    )
    ready_checks = {
        "launch_gate_enabled": bool(cfg.strategy.launch_gate_enabled),
        "pre_open_live": "Pre-Open" in (cfg.strategy.live_entry_zones or []),
        "shadow_zones_defined": bool(cfg.strategy.shadow_entry_zones),
        "session_exit_enabled": bool(cfg.strategy.session_exit_enabled),
        "bridge_disabled_by_default": True,
        "recent_morning_sample_positive": bool(morning_candidate.get("count"))
        and morning_candidate.get("total_pnl", 0.0) > 0,
        "runtime_reachable": state_source in ("sqlite", "status_file")
        or (state_source == "in_process" and bool(state.get("running"))),
        "runtime_running": bool(state.get("running")),
        "runtime_healthy": str(health.get("status") or "").lower() == "healthy",
        "funded_account_selected": bool(account.get("id")) and account.get("is_practice") is False,
        "broker_truth_available": bool(broker_truth),
        "broker_truth_flat": bool(broker_truth)
        and int(current_position.get("quantity", 0) or 0) == 0
        and int(current_broker_truth.get("open_order_count", 0) or 0) == 0,
        "broker_truth_no_contradictions": not any(bool(v) for v in contradictions.values()),
        "recovery_verified": recovery_verified,
    }
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "checks": ready_checks,
        "ready": all(ready_checks.values()),
        "runtime_status": state.get("status"),
        "runtime_state_source": state_source,
        "current_zone": (state.get("zone") or {}).get("name"),
        "account_id": packet.get("account_id"),
        "launch_defaults": packet.get("launch_defaults"),
    }


def render_regime_packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# Regime Packet",
        "",
        f"- Generated: `{packet.get('generated_at')}`",
        f"- Account: `{packet.get('account_id') or 'unknown'}`",
        f"- Trade count: `{packet.get('trade_count', 0)}`",
        "",
        "## Morning meta",
    ]
    morning = packet.get("morning_meta", {}).get("summary", {})
    overnight = packet.get("overnight_negative_control", {}).get("summary", {})
    lines.extend(
        [
            f"- 4 AM PT trades: `{morning.get('count', 0)}`",
            f"- 4 AM PT total PnL: `${morning.get('total_pnl', 0.0):.2f}`",
            f"- 4 AM PT avg duration: `{morning.get('avg_duration_hours', 0.0):.2f}h`",
            "",
            "## Negative control",
            f"- 11 PM PT trades: `{overnight.get('count', 0)}`",
            f"- 11 PM PT total PnL: `${overnight.get('total_pnl', 0.0):.2f}`",
            "",
            "## Zone summary",
        ]
    )
    for zone, summary in (packet.get("zone_summary") or {}).items():
        lines.append(
            f"- {zone}: count `{summary['count']}`, wins `{summary['wins']}`, losses `{summary['losses']}`, total `${summary['total_pnl']:.2f}`, avg `{summary['avg_duration_hours']:.2f}h`"
        )
    lines.extend(["", "## Launch defaults"])
    defaults = packet.get("launch_defaults") or {}
    lines.extend(
        [
            f"- Launch gate enabled: `{defaults.get('launch_gate_enabled')}`",
            f"- Live entry zones: `{defaults.get('live_entry_zones')}`",
            f"- Shadow entry zones: `{defaults.get('shadow_entry_zones')}`",
            f"- Session checkpoint: `{defaults.get('session_exit_checkpoint_time')} {defaults.get('session_exit_timezone')}`",
            f"- Session hard flat: `{defaults.get('session_exit_hard_flat_time')} {defaults.get('session_exit_timezone')}`",
        ]
    )
    return "\n".join(lines) + "\n"
