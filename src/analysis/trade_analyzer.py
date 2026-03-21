"""Analyze ACTUAL TRADES from replay runs.

IMPORTANT: This module analyzes completed trades from a replay run, NOT individual
decision signals. This is critical because:

1. Trades are simulated chronologically with position tracking
2. Capital constraints are enforced (can't trade if broke)
3. Slippage and fill simulation are included
4. Risk limits (daily loss, max trades, etc.) are enforced

For valid threshold optimization, you MUST re-run the replay with different
config values - you cannot backtest threshold changes on individual signals.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from src.config import Config, get_config
from src.observability.store import ObservabilityStore, get_observability_store

logger = logging.getLogger(__name__)


@dataclass
class TradeStats:
    """Statistics for a set of trades."""

    trade_count: int
    win_count: int
    loss_count: int
    scratch_count: int
    win_rate: float
    total_pnl: float
    gross_wins: float
    gross_losses: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_hold_minutes: float
    max_win: float
    max_loss: float
    max_consecutive_wins: int
    max_consecutive_losses: int

    # Balance tracking (if available)
    starting_balance: Optional[float] = None
    ending_balance: Optional[float] = None
    max_drawdown: Optional[float] = None


@dataclass
class ZoneTradeStats:
    """Trade statistics broken down by zone."""

    zone: str
    stats: TradeStats
    trades_per_hour: float
    avg_entry_score: float
    most_common_strategy: str


@dataclass
class ThresholdSensitivity:
    """Analysis of how trades would change at different thresholds.

    This is NOT a backtest - it shows which ACTUAL trades from the replay
    would have been filtered at different threshold values.

    IMPORTANT: This does NOT account for:
    - Different entries that might have occurred at lower thresholds
    - Capital/balance changes from different trade sequences
    - Market impact of different trade timing

    For valid threshold testing, re-run the replay with different config.
    """

    threshold: float
    trades_would_pass: int
    trades_would_be_filtered: int
    win_rate_of_passing_trades: float
    pnl_of_passing_trades: float
    filtered_trades_were_winners: int
    filtered_trades_were_losers: int


@dataclass
class TradeAnalysisReport:
    """Full analysis of trades from a replay run."""

    run_id: str
    symbol: str
    generated_at: datetime

    # Overall stats
    overall_stats: TradeStats

    # By-zone breakdown
    zone_stats: list[ZoneTradeStats]

    # By-regime breakdown
    regime_stats: dict[str, TradeStats]

    # Threshold sensitivity (which trades pass at different thresholds)
    threshold_sensitivity: list[ThresholdSensitivity]

    # Hold time analysis
    hold_time_distribution: dict[str, int]  # "0-15": count, "15-60": count, etc.

    # Entry score distribution
    entry_score_distribution: dict[str, Any]

    # Time-of-day analysis
    hourly_breakdown: dict[int, dict[str, Any]]

    # Warnings
    warnings: list[str] = field(default_factory=list)


def query_completed_trades(
    store: Optional[ObservabilityStore] = None,
    run_id: Optional[str] = None,
    symbol: str = "ES",
    limit: int = 10000,
) -> list[dict[str, Any]]:
    """Query completed trades from the observability store."""
    store = store or get_observability_store()
    if not store.enabled():
        logger.warning("Observability store not enabled")
        return []

    return store.query_completed_trades(
        run_id=run_id,
        limit=limit,
        ascending=True,
    )


def compute_trade_stats(trades: list[dict[str, Any]]) -> TradeStats:
    """Compute statistics for a list of trades."""
    if not trades:
        return TradeStats(
            trade_count=0,
            win_count=0,
            loss_count=0,
            scratch_count=0,
            win_rate=0.0,
            total_pnl=0.0,
            gross_wins=0.0,
            gross_losses=0.0,
            profit_factor=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            avg_hold_minutes=0.0,
            max_win=0.0,
            max_loss=0.0,
            max_consecutive_wins=0,
            max_consecutive_losses=0,
        )

    pnls = [float(t.get("pnl", 0)) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    scratches = [p for p in pnls if p == 0]

    # Calculate hold times
    hold_times = []
    for t in trades:
        entry_time = _parse_datetime(t.get("entry_time"))
        exit_time = _parse_datetime(t.get("exit_time"))
        if entry_time and exit_time:
            hold_minutes = (exit_time - entry_time).total_seconds() / 60
            hold_times.append(hold_minutes)

    # Calculate consecutive wins/losses
    consecutive_wins = 0
    consecutive_losses = 0
    max_consec_wins = 0
    max_consec_losses = 0
    for pnl in pnls:
        if pnl > 0:
            consecutive_wins += 1
            consecutive_losses = 0
            max_consec_wins = max(max_consec_wins, consecutive_wins)
        elif pnl < 0:
            consecutive_losses += 1
            consecutive_wins = 0
            max_consec_losses = max(max_consec_losses, consecutive_losses)
        else:
            consecutive_wins = 0
            consecutive_losses = 0

    gross_wins = sum(wins)
    gross_losses = abs(sum(losses))

    return TradeStats(
        trade_count=len(trades),
        win_count=len(wins),
        loss_count=len(losses),
        scratch_count=len(scratches),
        win_rate=len(wins) / len(trades) if trades else 0.0,
        total_pnl=sum(pnls),
        gross_wins=gross_wins,
        gross_losses=gross_losses,
        profit_factor=gross_wins / gross_losses if gross_losses > 0 else float("inf") if gross_wins > 0 else 0.0,
        avg_win=sum(wins) / len(wins) if wins else 0.0,
        avg_loss=sum(losses) / len(losses) if losses else 0.0,
        avg_hold_minutes=sum(hold_times) / len(hold_times) if hold_times else 0.0,
        max_win=max(wins) if wins else 0.0,
        max_loss=min(losses) if losses else 0.0,
        max_consecutive_wins=max_consec_wins,
        max_consecutive_losses=max_consec_losses,
    )


def compute_zone_stats(
    trades: list[dict[str, Any]],
    store: Optional[ObservabilityStore] = None,
) -> list[ZoneTradeStats]:
    """Compute trade statistics broken down by zone."""
    zones: dict[str, list[dict]] = {}

    for trade in trades:
        zone = trade.get("zone") or "Unknown"
        if zone not in zones:
            zones[zone] = []
        zones[zone].append(trade)

    results: list[ZoneTradeStats] = []
    for zone, zone_trades in zones.items():
        stats = compute_trade_stats(zone_trades)

        # Calculate trades per hour
        if zone_trades:
            entry_times = [_parse_datetime(t.get("entry_time")) for t in zone_trades]
            entry_times = [t for t in entry_times if t is not None]
            if len(entry_times) >= 2:
                time_span = (max(entry_times) - min(entry_times)).total_seconds() / 3600
                trades_per_hour = len(zone_trades) / time_span if time_span > 0 else 0.0
            else:
                trades_per_hour = 0.0
        else:
            trades_per_hour = 0.0

        # Calculate average entry score
        entry_scores = []
        for t in zone_trades:
            payload = t.get("payload", {})
            if isinstance(payload, str):
                import json
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}
            score = payload.get("entry_score") or t.get("entry_score")
            if score is not None:
                entry_scores.append(float(score))

        avg_entry_score = sum(entry_scores) / len(entry_scores) if entry_scores else 0.0

        # Most common strategy
        strategies = [t.get("strategy") or "Unknown" for t in zone_trades]
        most_common = max(set(strategies), key=strategies.count) if strategies else "Unknown"

        results.append(
            ZoneTradeStats(
                zone=zone,
                stats=stats,
                trades_per_hour=round(trades_per_hour, 2),
                avg_entry_score=round(avg_entry_score, 2),
                most_common_strategy=most_common,
            )
        )

    return results


def compute_threshold_sensitivity(
    trades: list[dict[str, Any]],
    threshold_range: tuple[float, float] = (3.5, 6.5),
    step: float = 0.25,
) -> list[ThresholdSensitivity]:
    """
    Analyze which ACTUAL trades would pass at different entry thresholds.

    WARNING: This is NOT a backtest. It shows which trades from the replay
    would have been filtered at different thresholds. It does NOT account for:
    - Different entries that might have occurred at lower thresholds
    - Capital/balance changes from different trade sequences

    For valid threshold testing, re-run the replay with different config.
    """
    results: list[ThresholdSensitivity] = []

    # Extract entry scores from trades
    trade_scores: list[tuple[float, float, bool]] = []  # (score, pnl, was_winner)
    for trade in trades:
        payload = trade.get("payload", {})
        if isinstance(payload, str):
            import json
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        # Look for entry score in various places
        score = (
            payload.get("entry_score")
            or payload.get("long_score")
            or payload.get("short_score")
            or trade.get("entry_score")
        )
        if score is not None:
            pnl = float(trade.get("pnl", 0))
            was_winner = pnl > 0
            trade_scores.append((float(score), pnl, was_winner))

    if not trade_scores:
        return results

    threshold = threshold_range[0]
    while threshold <= threshold_range[1]:
        passing_trades = [(s, p, w) for s, p, w in trade_scores if s >= threshold]
        filtered_trades = [(s, p, w) for s, p, w in trade_scores if s < threshold]

        passing_pnl = sum(p for _, p, _ in passing_trades)
        passing_winners = sum(1 for _, _, w in passing_trades if w)
        filtered_winners = sum(1 for _, _, w in filtered_trades if w)
        filtered_losers = sum(1 for _, _, w in filtered_trades if not w)

        results.append(
            ThresholdSensitivity(
                threshold=threshold,
                trades_would_pass=len(passing_trades),
                trades_would_be_filtered=len(filtered_trades),
                win_rate_of_passing_trades=passing_winners / len(passing_trades) if passing_trades else 0.0,
                pnl_of_passing_trades=round(passing_pnl, 2),
                filtered_trades_were_winners=filtered_winners,
                filtered_trades_were_losers=filtered_losers,
            )
        )

        threshold += step

    return results


def compute_hold_time_distribution(trades: list[dict[str, Any]]) -> dict[str, int]:
    """Compute distribution of hold times."""
    distribution = {
        "0-5 min": 0,
        "5-15 min": 0,
        "15-30 min": 0,
        "30-60 min": 0,
        "60-120 min": 0,
        "120+ min": 0,
    }

    for trade in trades:
        entry_time = _parse_datetime(trade.get("entry_time"))
        exit_time = _parse_datetime(trade.get("exit_time"))
        if not entry_time or not exit_time:
            continue

        hold_minutes = (exit_time - entry_time).total_seconds() / 60

        if hold_minutes < 5:
            distribution["0-5 min"] += 1
        elif hold_minutes < 15:
            distribution["5-15 min"] += 1
        elif hold_minutes < 30:
            distribution["15-30 min"] += 1
        elif hold_minutes < 60:
            distribution["30-60 min"] += 1
        elif hold_minutes < 120:
            distribution["60-120 min"] += 1
        else:
            distribution["120+ min"] += 1

    return distribution


def compute_hourly_breakdown(trades: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Compute trade statistics by hour of day."""
    hourly: dict[int, dict[str, Any]] = {}

    for trade in trades:
        entry_time = _parse_datetime(trade.get("entry_time"))
        if not entry_time:
            continue

        hour = entry_time.hour
        if hour not in hourly:
            hourly[hour] = {"trades": 0, "wins": 0, "pnl": 0.0}

        hourly[hour]["trades"] += 1
        pnl = float(trade.get("pnl", 0))
        hourly[hour]["pnl"] += pnl
        if pnl > 0:
            hourly[hour]["wins"] += 1

    # Calculate win rates
    for hour, data in hourly.items():
        data["win_rate"] = data["wins"] / data["trades"] if data["trades"] > 0 else 0.0

    return hourly


def build_trade_analysis_report(
    run_id: str,
    symbol: str = "ES",
    store: Optional[ObservabilityStore] = None,
    config: Optional[Config] = None,
) -> TradeAnalysisReport:
    """Build a full trade analysis report from a replay run."""
    config = config or get_config()
    store = store or get_observability_store()

    warnings: list[str] = []

    # Query completed trades
    trades = query_completed_trades(store=store, run_id=run_id, symbol=symbol)

    if not trades:
        warnings.append(
            "No completed trades found. Run a replay that produces trades (e.g. "
            "`es-trade replay --tape-run-id …` or `es-trade replay --path …`), or trade live with observability enabled."
        )
        return TradeAnalysisReport(
            run_id=run_id,
            symbol=symbol,
            generated_at=datetime.now(UTC),
            overall_stats=compute_trade_stats([]),
            zone_stats=[],
            regime_stats={},
            threshold_sensitivity=[],
            hold_time_distribution={},
            entry_score_distribution={},
            hourly_breakdown={},
            warnings=warnings,
        )

    # Compute overall stats
    overall_stats = compute_trade_stats(trades)

    # Zone breakdown
    zone_stats = compute_zone_stats(trades, store)

    # Regime breakdown
    regime_trades: dict[str, list[dict]] = {}
    for trade in trades:
        regime = trade.get("regime") or "Unknown"
        if regime not in regime_trades:
            regime_trades[regime] = []
        regime_trades[regime].append(trade)

    regime_stats = {
        regime: compute_trade_stats(rt) for regime, rt in regime_trades.items()
    }

    # Threshold sensitivity
    threshold_sensitivity = compute_threshold_sensitivity(trades)

    # Hold time distribution
    hold_time_distribution = compute_hold_time_distribution(trades)

    # Hourly breakdown
    hourly_breakdown = compute_hourly_breakdown(trades)

    # Entry score distribution
    entry_scores: list[float] = []
    for trade in trades:
        payload = trade.get("payload", {})
        if isinstance(payload, str):
            import json
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        score = payload.get("entry_score") or trade.get("entry_score")
        if score is not None:
            entry_scores.append(float(score))

    entry_score_distribution = {}
    if entry_scores:
        sorted_scores = sorted(entry_scores)
        n = len(sorted_scores)
        entry_score_distribution = {
            "min": sorted_scores[0],
            "max": sorted_scores[-1],
            "mean": sum(entry_scores) / n,
            "median": sorted_scores[n // 2],
            "p25": sorted_scores[int(n * 0.25)],
            "p75": sorted_scores[int(n * 0.75)],
        }

    # Add warning if trade count is low
    if len(trades) < 20:
        warnings.append(
            f"Only {len(trades)} trades found. For reliable threshold optimization, "
            "run a longer replay (e.g., --days 30)."
        )

    # Check if we're in target hold range
    if overall_stats.avg_hold_minutes < 15:
        warnings.append(
            f"Average hold time ({overall_stats.avg_hold_minutes:.1f} min) is below "
            "target range (15-360 min). Consider adjusting exit thresholds."
        )
    elif overall_stats.avg_hold_minutes > 360:
        warnings.append(
            f"Average hold time ({overall_stats.avg_hold_minutes:.1f} min) is above "
            "target range (15-360 min). Consider tightening exit criteria."
        )

    return TradeAnalysisReport(
        run_id=run_id,
        symbol=symbol,
        generated_at=datetime.now(UTC),
        overall_stats=overall_stats,
        zone_stats=zone_stats,
        regime_stats=regime_stats,
        threshold_sensitivity=threshold_sensitivity,
        hold_time_distribution=hold_time_distribution,
        entry_score_distribution=entry_score_distribution,
        hourly_breakdown=hourly_breakdown,
        warnings=warnings,
    )


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse a datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except ValueError:
            return None
    return None


def render_trade_analysis_summary(report: TradeAnalysisReport) -> str:
    """Render a human-readable summary of the trade analysis."""
    lines = [
        "# Trade Analysis Report",
        f"Run ID: {report.run_id}",
        f"Symbol: {report.symbol}",
        f"Generated: {report.generated_at.isoformat()}",
        "",
        "## Overall Statistics",
        f"- Total trades: {report.overall_stats.trade_count}",
        f"- Win rate: {report.overall_stats.win_rate:.1%}",
        f"- Total P&L: ${report.overall_stats.total_pnl:.2f}",
        f"- Profit factor: {report.overall_stats.profit_factor:.2f}",
        f"- Average win: ${report.overall_stats.avg_win:.2f}",
        f"- Average loss: ${report.overall_stats.avg_loss:.2f}",
        f"- Average hold: {report.overall_stats.avg_hold_minutes:.1f} min",
        f"- Max consecutive wins: {report.overall_stats.max_consecutive_wins}",
        f"- Max consecutive losses: {report.overall_stats.max_consecutive_losses}",
        "",
        "## Zone Breakdown",
    ]

    for zs in report.zone_stats:
        lines.append(f"### {zs.zone}")
        lines.append(f"- Trades: {zs.stats.trade_count}")
        lines.append(f"- Win rate: {zs.stats.win_rate:.1%}")
        lines.append(f"- P&L: ${zs.stats.total_pnl:.2f}")
        lines.append(f"- Avg hold: {zs.stats.avg_hold_minutes:.1f} min")
        lines.append(f"- Trades/hour: {zs.trades_per_hour:.2f}")
        lines.append("")

    if report.threshold_sensitivity:
        lines.append("## Threshold Sensitivity")
        lines.append("")
        lines.append("| Threshold | Trades | Win Rate | P&L |")
        lines.append("|-----------|--------|----------|-----|")
        for ts in report.threshold_sensitivity:
            lines.append(
                f"| {ts.threshold:.2f} | {ts.trades_would_pass} | "
                f"{ts.win_rate_of_passing_trades:.1%} | ${ts.pnl_of_passing_trades:.2f} |"
            )
        lines.append("")

    if report.hold_time_distribution:
        lines.append("## Hold Time Distribution")
        for bucket, count in report.hold_time_distribution.items():
            lines.append(f"- {bucket}: {count}")
        lines.append("")

    if report.warnings:
        lines.append("## Warnings")
        for warning in report.warnings:
            lines.append(f"- ⚠️ {warning}")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.append(
        "To test different threshold values, re-run the replay with modified config:"
    )
    lines.append("")
    lines.append("```bash")
    lines.append("# Edit config/default.yaml")
    lines.append("# Then run a replay that records completed trades, e.g. tape replay:")
    lines.append("es-trade replay --tape-start <iso> --tape-end <iso> --symbol ES")
    lines.append("# (Do not use replay-topstep for validated research — see docs/replay/replay-topstep-deprecated.md)")
    lines.append("```")
    lines.append("")
    lines.append(
        "IMPORTANT: Do NOT use the threshold sensitivity table above as a backtest. "
        "It only shows which ACTUAL trades would have been filtered, not what trades "
        "would have occurred at different thresholds."
    )

    return "\n".join(lines)
