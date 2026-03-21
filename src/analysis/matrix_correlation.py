"""Matrix score-to-outcome correlation analysis."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from src.observability.store import ObservabilityStore, get_observability_store

logger = logging.getLogger(__name__)


@dataclass
class ScoreOutcomePair:
    """Matrix score at time T with price outcome at T+N bars."""

    timestamp: datetime
    zone: str
    regime: str
    long_score: float
    short_score: float
    flat_bias: float
    dominant_side: str
    price_at_decision: float
    atr_at_decision: float

    # Outcomes at multiple horizons (normalized by ATR)
    move_5_bars_atr: Optional[float] = None  # 5 min
    move_15_bars_atr: Optional[float] = None  # 15 min
    move_30_bars_atr: Optional[float] = None  # 30 min
    move_60_bars_atr: Optional[float] = None  # 60 min

    # Raw price outcomes
    price_5_bars: Optional[float] = None
    price_15_bars: Optional[float] = None
    price_30_bars: Optional[float] = None
    price_60_bars: Optional[float] = None

    # Direction prediction accuracy
    predicted_long_correct_5: Optional[bool] = None
    predicted_long_correct_15: Optional[bool] = None
    predicted_long_correct_30: Optional[bool] = None
    predicted_long_correct_60: Optional[bool] = None


@dataclass
class ThresholdResult:
    """Analysis results for a single threshold value."""

    threshold: float
    trade_count: int
    win_count: int
    loss_count: int
    win_rate: float
    avg_move_atr: float
    total_move_atr: float
    false_positive_count: int
    false_positive_rate: float
    avg_hold_minutes: Optional[float] = None
    profit_factor: Optional[float] = None

    # By-zone breakdown
    zone_stats: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class CorrelationReport:
    """Full correlation analysis report."""

    run_id: str
    symbol: str
    total_decisions: int
    score_outcome_pairs: list[ScoreOutcomePair]
    threshold_results: list[ThresholdResult]
    score_distribution: dict[str, Any]
    zone_breakdown: dict[str, dict[str, Any]]
    regime_breakdown: dict[str, dict[str, Any]]
    generated_at: datetime


def extract_score_outcome_pairs(
    store: Optional[ObservabilityStore] = None,
    run_id: Optional[str] = None,
    symbol: str = "ES",
    limit: int = 50000,
) -> list[ScoreOutcomePair]:
    """
    Query decision_snapshots and market_tape tables.
    Join each decision with subsequent prices at 5/15/30/60 bar horizons.
    Normalize moves by ATR for cross-regime comparison.
    """
    store = store or get_observability_store()
    if not store.enabled():
        logger.warning("Observability store not enabled")
        return []

    # Query decision snapshots
    decisions = store.query_decision_snapshots(
        run_id=run_id,
        symbol=symbol,
        limit=limit,
        ascending=True,
    )

    if not decisions:
        logger.warning("No decision snapshots found for run_id=%s symbol=%s", run_id, symbol)
        return []

    # Query market tape for price lookups
    market_tape = store.query_market_tape(
        run_id=run_id,
        symbol=symbol,
        limit=limit * 100,  # Much larger for price lookups
        ascending=True,
    )

    if not market_tape:
        logger.warning("No market tape data found for run_id=%s symbol=%s", run_id, symbol)
        return []

    # Build price timeline index
    price_timeline: list[tuple[datetime, float, float]] = []
    for tick in market_tape:
        ts = _parse_datetime(tick.get("captured_at"))
        if ts is None:
            continue
        last_price = tick.get("last") or tick.get("close")
        atr = tick.get("atr") or _estimate_atr_from_tick(tick)
        if last_price is not None:
            price_timeline.append((ts, float(last_price), float(atr) if atr else 2.0))

    # Sort by timestamp
    price_timeline.sort(key=lambda x: x[0])

    pairs: list[ScoreOutcomePair] = []
    for decision in decisions:
        decision_time = _parse_datetime(decision.get("decided_at"))
        if decision_time is None:
            continue

        current_price = decision.get("current_price")
        if current_price is None:
            continue

        # Find the closest price tick to get ATR
        atr = _find_atr_at_time(price_timeline, decision_time) or 2.0

        # Find prices at horizons (1-min bars, so 5/15/30/60 bars = 5/15/30/60 minutes)
        price_5 = _find_price_at_horizon(price_timeline, decision_time, timedelta(minutes=5))
        price_15 = _find_price_at_horizon(price_timeline, decision_time, timedelta(minutes=15))
        price_30 = _find_price_at_horizon(price_timeline, decision_time, timedelta(minutes=30))
        price_60 = _find_price_at_horizon(price_timeline, decision_time, timedelta(minutes=60))

        long_score = float(decision.get("long_score") or 0.0)
        short_score = float(decision.get("short_score") or 0.0)
        dominant_side = "long" if long_score >= short_score else "short"

        pair = ScoreOutcomePair(
            timestamp=decision_time,
            zone=decision.get("zone") or "Unknown",
            regime=decision.get("regime_state") or "RANGE",
            long_score=long_score,
            short_score=short_score,
            flat_bias=float(decision.get("flat_bias") or 0.0),
            dominant_side=dominant_side,
            price_at_decision=float(current_price),
            atr_at_decision=atr,
        )

        # Calculate normalized moves
        if price_5 is not None:
            pair.price_5_bars = price_5
            pair.move_5_bars_atr = (price_5 - current_price) / atr if atr > 0 else None
        if price_15 is not None:
            pair.price_15_bars = price_15
            pair.move_15_bars_atr = (price_15 - current_price) / atr if atr > 0 else None
        if price_30 is not None:
            pair.price_30_bars = price_30
            pair.move_30_bars_atr = (price_30 - current_price) / atr if atr > 0 else None
        if price_60 is not None:
            pair.price_60_bars = price_60
            pair.move_60_bars_atr = (price_60 - current_price) / atr if atr > 0 else None

        # Calculate prediction accuracy
        if pair.dominant_side == "long":
            pair.predicted_long_correct_5 = pair.move_5_bars_atr is not None and pair.move_5_bars_atr > 0
            pair.predicted_long_correct_15 = pair.move_15_bars_atr is not None and pair.move_15_bars_atr > 0
            pair.predicted_long_correct_30 = pair.move_30_bars_atr is not None and pair.move_30_bars_atr > 0
            pair.predicted_long_correct_60 = pair.move_60_bars_atr is not None and pair.move_60_bars_atr > 0
        else:
            pair.predicted_long_correct_5 = pair.move_5_bars_atr is not None and pair.move_5_bars_atr < 0
            pair.predicted_long_correct_15 = pair.move_15_bars_atr is not None and pair.move_15_bars_atr < 0
            pair.predicted_long_correct_30 = pair.move_30_bars_atr is not None and pair.move_30_bars_atr < 0
            pair.predicted_long_correct_60 = pair.move_60_bars_atr is not None and pair.move_60_bars_atr < 0

        pairs.append(pair)

    return pairs


def compute_threshold_analysis(
    pairs: list[ScoreOutcomePair],
    threshold_range: tuple[float, float] = (3.5, 6.5),
    step: float = 0.25,
    horizon: str = "15",  # Which horizon to use for win/loss
) -> list[ThresholdResult]:
    """
    For each threshold, compute:
    - Win rate (move in predicted direction)
    - Average move in ATR
    - Trade count
    - False positive rate
    """
    results: list[ThresholdResult] = []
    threshold = threshold_range[0]

    while threshold <= threshold_range[1]:
        trades_at_threshold: list[ScoreOutcomePair] = []
        wins = 0
        losses = 0
        total_move = 0.0
        false_positives = 0
        zone_stats: dict[str, dict[str, Any]] = {}

        for pair in pairs:
            dominant_score = pair.long_score if pair.dominant_side == "long" else pair.short_score
            if dominant_score < threshold:
                continue

            trades_at_threshold.append(pair)

            # Select the move based on horizon
            if horizon == "5":
                move_atr = pair.move_5_bars_atr
                correct = pair.predicted_long_correct_5
            elif horizon == "30":
                move_atr = pair.move_30_bars_atr
                correct = pair.predicted_long_correct_30
            elif horizon == "60":
                move_atr = pair.move_60_bars_atr
                correct = pair.predicted_long_correct_60
            else:  # default to 15
                move_atr = pair.move_15_bars_atr
                correct = pair.predicted_long_correct_15

            if move_atr is None or correct is None:
                continue

            if correct:
                wins += 1
                total_move += abs(move_atr)
            else:
                losses += 1
                total_move -= abs(move_atr)  # Negative contribution
                false_positives += 1

            # Zone breakdown
            zone = pair.zone or "Unknown"
            if zone not in zone_stats:
                zone_stats[zone] = {"wins": 0, "losses": 0, "total_move": 0.0}
            if correct:
                zone_stats[zone]["wins"] += 1
                zone_stats[zone]["total_move"] += abs(move_atr)
            else:
                zone_stats[zone]["losses"] += 1
                zone_stats[zone]["total_move"] -= abs(move_atr)

        trade_count = wins + losses
        win_rate = wins / trade_count if trade_count > 0 else 0.0
        avg_move = total_move / trade_count if trade_count > 0 else 0.0
        fp_rate = false_positives / trade_count if trade_count > 0 else 0.0

        # Calculate profit factor (gross wins / gross losses)
        gross_wins = sum(
            abs(pair.move_15_bars_atr or 0)
            for pair in trades_at_threshold
            if horizon == "15" and pair.predicted_long_correct_15
        )
        gross_losses = sum(
            abs(pair.move_15_bars_atr or 0)
            for pair in trades_at_threshold
            if horizon == "15" and pair.predicted_long_correct_15 is False
        )
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float("inf") if gross_wins > 0 else 0.0

        results.append(
            ThresholdResult(
                threshold=threshold,
                trade_count=trade_count,
                win_count=wins,
                loss_count=losses,
                win_rate=win_rate,
                avg_move_atr=avg_move,
                total_move_atr=total_move,
                false_positive_count=false_positives,
                false_positive_rate=fp_rate,
                profit_factor=profit_factor,
                zone_stats=zone_stats,
            )
        )

        threshold += step

    return results


def build_score_distribution(pairs: list[ScoreOutcomePair]) -> dict[str, Any]:
    """Build distribution statistics for scores."""
    if not pairs:
        return {}

    long_scores = [p.long_score for p in pairs]
    short_scores = [p.short_score for p in pairs]
    flat_biases = [p.flat_bias for p in pairs]

    def stats(values: list[float]) -> dict[str, float]:
        if not values:
            return {}
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        return {
            "min": sorted_vals[0],
            "max": sorted_vals[-1],
            "mean": sum(values) / n,
            "median": sorted_vals[n // 2],
            "p25": sorted_vals[int(n * 0.25)],
            "p75": sorted_vals[int(n * 0.75)],
            "p90": sorted_vals[int(n * 0.90)],
        }

    return {
        "long_score": stats(long_scores),
        "short_score": stats(short_scores),
        "flat_bias": stats(flat_biases),
        "total_count": len(pairs),
    }


def build_zone_breakdown(pairs: list[ScoreOutcomePair]) -> dict[str, dict[str, Any]]:
    """Build breakdown statistics by zone."""
    zones: dict[str, dict[str, Any]] = {}

    for pair in pairs:
        zone = pair.zone or "Unknown"
        if zone not in zones:
            zones[zone] = {
                "count": 0,
                "avg_long_score": 0.0,
                "avg_short_score": 0.0,
                "win_rate_15": 0.0,
                "avg_move_15_atr": 0.0,
            }
        zones[zone]["count"] += 1
        zones[zone]["avg_long_score"] += pair.long_score
        zones[zone]["avg_short_score"] += pair.short_score

        if pair.predicted_long_correct_15 is not None:
            if "wins_15" not in zones[zone]:
                zones[zone]["wins_15"] = 0
                zones[zone]["total_15"] = 0
            zones[zone]["total_15"] += 1
            if pair.predicted_long_correct_15:
                zones[zone]["wins_15"] += 1

        if pair.move_15_bars_atr is not None:
            if "total_move_15" not in zones[zone]:
                zones[zone]["total_move_15"] = 0.0
            zones[zone]["total_move_15"] += abs(pair.move_15_bars_atr)

    # Finalize averages
    for zone, stats in zones.items():
        count = stats["count"]
        if count > 0:
            stats["avg_long_score"] = round(stats["avg_long_score"] / count, 4)
            stats["avg_short_score"] = round(stats["avg_short_score"] / count, 4)
        if stats.get("total_15", 0) > 0:
            stats["win_rate_15"] = round(stats.get("wins_15", 0) / stats["total_15"], 4)
            stats["avg_move_15_atr"] = round(stats.get("total_move_15", 0) / stats["total_15"], 4)

    return zones


def build_regime_breakdown(pairs: list[ScoreOutcomePair]) -> dict[str, dict[str, Any]]:
    """Build breakdown statistics by regime."""
    regimes: dict[str, dict[str, Any]] = {}

    for pair in pairs:
        regime = pair.regime or "Unknown"
        if regime not in regimes:
            regimes[regime] = {
                "count": 0,
                "avg_long_score": 0.0,
                "avg_short_score": 0.0,
                "win_rate_15": 0.0,
            }
        regimes[regime]["count"] += 1
        regimes[regime]["avg_long_score"] += pair.long_score
        regimes[regime]["avg_short_score"] += pair.short_score

        if pair.predicted_long_correct_15 is not None:
            if "wins_15" not in regimes[regime]:
                regimes[regime]["wins_15"] = 0
                regimes[regime]["total_15"] = 0
            regimes[regime]["total_15"] += 1
            if pair.predicted_long_correct_15:
                regimes[regime]["wins_15"] += 1

    # Finalize averages
    for regime, stats in regimes.items():
        count = stats["count"]
        if count > 0:
            stats["avg_long_score"] = round(stats["avg_long_score"] / count, 4)
            stats["avg_short_score"] = round(stats["avg_short_score"] / count, 4)
        if stats.get("total_15", 0) > 0:
            stats["win_rate_15"] = round(stats.get("wins_15", 0) / stats["total_15"], 4)

    return regimes


def build_matrix_correlation_report(
    run_id: str,
    symbol: str = "ES",
    store: Optional[ObservabilityStore] = None,
) -> CorrelationReport:
    """Build a full correlation report for a run."""
    pairs = extract_score_outcome_pairs(store=store, run_id=run_id, symbol=symbol)
    threshold_results = compute_threshold_analysis(pairs)

    return CorrelationReport(
        run_id=run_id,
        symbol=symbol,
        total_decisions=len(pairs),
        score_outcome_pairs=pairs,
        threshold_results=threshold_results,
        score_distribution=build_score_distribution(pairs),
        zone_breakdown=build_zone_breakdown(pairs),
        regime_breakdown=build_regime_breakdown(pairs),
        generated_at=datetime.now(UTC),
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


def _estimate_atr_from_tick(tick: dict) -> Optional[float]:
    """Estimate ATR from tick high/low if available."""
    high = tick.get("ask") or tick.get("high")
    low = tick.get("bid") or tick.get("low")
    if high is not None and low is not None:
        return abs(float(high) - float(low))
    return None


def _find_atr_at_time(
    timeline: list[tuple[datetime, float, float]], target_time: datetime
) -> Optional[float]:
    """Find the ATR value closest to the target time."""
    for ts, _, atr in reversed(timeline):
        if ts <= target_time:
            return atr
    return None


def _find_price_at_horizon(
    timeline: list[tuple[datetime, float, float]],
    decision_time: datetime,
    horizon: timedelta,
) -> Optional[float]:
    """Find the price at decision_time + horizon."""
    target_time = decision_time + horizon

    # Binary search for efficiency
    left, right = 0, len(timeline)
    while left < right:
        mid = (left + right) // 2
        if timeline[mid][0] < target_time:
            left = mid + 1
        else:
            right = mid

    if left < len(timeline):
        return timeline[left][1]
    return None
