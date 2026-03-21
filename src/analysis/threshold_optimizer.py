"""Threshold optimization for matrix scoring."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Optional

from src.analysis.matrix_correlation import (
    CorrelationReport,
    ScoreOutcomePair,
    ThresholdResult,
    build_matrix_correlation_report,
    extract_score_outcome_pairs,
)
from src.config import Config, get_config

logger = logging.getLogger(__name__)


@dataclass
class ThresholdRecommendation:
    """Recommendation for a single threshold."""

    current: float
    recommended: float
    reason: str
    trade_off: str  # e.g., "more trades, lower win rate"
    confidence: str  # "high", "medium", "low"


@dataclass
class TrailingStopRecommendation:
    """Recommendation for trailing stop ATR multiplier."""

    current: float
    recommended: float
    reason: str
    pct_trades_reaching_target: float
    avg_hold_minutes: float


@dataclass
class HoldTimeRecommendation:
    """Recommendation for max hold time by zone."""

    zone: str
    current: int
    recommended: int
    reason: str
    avg_win_hold_minutes: Optional[float] = None
    avg_loss_hold_minutes: Optional[float] = None


@dataclass
class OptimizationReport:
    """Full optimization recommendations report."""

    run_id: str
    symbol: str
    generated_at: datetime

    # Entry/exit threshold recommendations
    min_entry_score: ThresholdRecommendation
    exit_decay_score: ThresholdRecommendation
    reverse_score_gap: ThresholdRecommendation
    full_size_score: ThresholdRecommendation

    # Strategy parameter recommendations
    trailing_stop_atr: Optional[TrailingStopRecommendation] = None
    breakeven_trigger_atr: Optional[ThresholdRecommendation] = None
    profit_lock_atr: Optional[ThresholdRecommendation] = None

    # Hold time recommendations by zone
    max_hold_minutes: list[HoldTimeRecommendation] = field(default_factory=list)

    # Summary metrics
    current_threshold_trades: int = 0
    recommended_threshold_trades: int = 0
    expected_win_rate_change: float = 0.0

    # Raw analysis data
    threshold_results: list[ThresholdResult] = field(default_factory=list)


def optimize_entry_threshold(
    results: list[ThresholdResult],
    current: float = 5.0,
    min_trades: int = 20,
    target_win_rate: float = 0.50,
    max_fp_rate: float = 0.50,
) -> ThresholdRecommendation:
    """
    Find threshold that maximizes profit factor while keeping FP rate < 50%.
    """
    if not results:
        return ThresholdRecommendation(
            current=current,
            recommended=current,
            reason="No threshold results available",
            trade_off="N/A",
            confidence="low",
        )

    # Filter results with enough trades
    valid_results = [r for r in results if r.trade_count >= min_trades]

    if not valid_results:
        # Fall back to closest threshold with any trades
        valid_results = [r for r in results if r.trade_count > 0]
        if not valid_results:
            return ThresholdRecommendation(
                current=current,
                recommended=current,
                reason="No trades at any threshold",
                trade_off="N/A",
                confidence="low",
            )

    # Find the best threshold meeting criteria
    best: Optional[ThresholdResult] = None
    best_score = -1.0

    for r in valid_results:
        # Skip if FP rate too high
        if r.false_positive_rate > max_fp_rate:
            continue
        # Skip if win rate too low
        if r.win_rate < target_win_rate:
            continue

        # Score: profit factor * trade count (favor more trades with good PF)
        score = (r.profit_factor or 0) * min(r.trade_count / 100, 1.0)

        if score > best_score:
            best_score = score
            best = r

    if best is None:
        # Relax constraints - just find lowest FP rate with decent win rate
        for r in sorted(valid_results, key=lambda x: x.false_positive_rate):
            if r.win_rate >= 0.45:
                best = r
                break

    if best is None:
        return ThresholdRecommendation(
            current=current,
            recommended=current,
            reason="No threshold meets minimum criteria",
            trade_off="N/A",
            confidence="low",
        )

    # Build recommendation
    delta = best.threshold - current
    if abs(delta) < 0.1:
        reason = "Current threshold is already optimal"
        trade_off = "No change needed"
    elif delta < 0:
        reason = f"Lower threshold triggers {best.trade_count} trades with {best.win_rate:.0%} win rate"
        trade_off = f"More trades (+{best.trade_count - _estimate_trades_at(results, current)}), "
        trade_off += f"win rate: {best.win_rate:.0%}, FP rate: {best.false_positive_rate:.0%}"
    else:
        reason = f"Higher threshold improves win rate to {best.win_rate:.0%}"
        trade_off = f"Fewer trades, higher win rate, FP rate: {best.false_positive_rate:.0%}"

    confidence = "high" if best.trade_count >= 50 else ("medium" if best.trade_count >= 20 else "low")

    return ThresholdRecommendation(
        current=current,
        recommended=round(best.threshold, 2),
        reason=reason,
        trade_off=trade_off,
        confidence=confidence,
    )


def _estimate_trades_at(results: list[ThresholdResult], threshold: float) -> int:
    """Estimate trade count at a specific threshold."""
    for r in results:
        if abs(r.threshold - threshold) < 0.1:
            return r.trade_count
    return 0


def optimize_exit_decay_score(
    pairs: list[ScoreOutcomePair],
    current: float = 1.5,
) -> ThresholdRecommendation:
    """
    Find optimal exit decay score for extending hold times.
    """
    if not pairs:
        return ThresholdRecommendation(
            current=current,
            recommended=current,
            reason="No score-outcome pairs available",
            trade_off="N/A",
            confidence="low",
        )

    # Analyze how scores decay over time for winning vs losing trades
    # Lower exit_decay_score = hold longer (exit when score drops below threshold)

    # For now, recommend based on score distribution at 15-minute horizon
    winning_scores: list[float] = []
    losing_scores: list[float] = []

    for pair in pairs:
        if pair.move_15_bars_atr is None:
            continue
        dominant_score = pair.long_score if pair.dominant_side == "long" else pair.short_score

        if pair.predicted_long_correct_15:
            winning_scores.append(dominant_score)
        else:
            losing_scores.append(dominant_score)

    if not winning_scores:
        return ThresholdRecommendation(
            current=current,
            recommended=current,
            reason="No winning trades to analyze",
            trade_off="N/A",
            confidence="low",
        )

    # Find score level where most winners are still above
    winning_scores.sort()
    p25 = winning_scores[int(len(winning_scores) * 0.25)]

    # Recommend exit decay slightly below p25 of winning scores
    recommended = max(1.0, round(p25 - 0.5, 2))

    if abs(recommended - current) < 0.25:
        reason = "Current exit decay score is well-calibrated"
        trade_off = "No change needed"
    elif recommended < current:
        reason = f"Lower exit decay extends avg hold; {len(winning_scores)} winners still above {recommended:.2f}"
        trade_off = "Longer holds, more time for winners to run"
    else:
        reason = f"Higher exit decay exits faster; reduces exposure to reversals"
        trade_off = "Shorter holds, less profit potential per trade"

    confidence = "high" if len(winning_scores) >= 50 else ("medium" if len(winning_scores) >= 20 else "low")

    return ThresholdRecommendation(
        current=current,
        recommended=recommended,
        reason=reason,
        trade_off=trade_off,
        confidence=confidence,
    )


def optimize_trailing_stop(
    pairs: list[ScoreOutcomePair],
    current: float = 1.0,
    target_min_hold: int = 15,
    target_max_hold: int = 360,
) -> TrailingStopRecommendation:
    """
    Find trailing_stop_atr that maximizes trades in 15-360 min hold range.
    """
    if not pairs:
        return TrailingStopRecommendation(
            current=current,
            recommended=current,
            reason="No pairs available for analysis",
            pct_trades_reaching_target=0.0,
            avg_hold_minutes=0.0,
        )

    # Analyze max adverse excursion for winning trades
    # (In a full implementation, we'd need actual trade data with MAE)

    # For now, use the move at 15-minute horizon as a proxy
    trades_reaching_target = 0
    total_move = 0.0

    for pair in pairs:
        if pair.move_15_bars_atr is None:
            continue
        # A trade "reaches target" if it moves at least 0.5 ATR in predicted direction
        if pair.predicted_long_correct_15 and pair.move_15_bars_atr >= 0.5:
            trades_reaching_target += 1
            total_move += pair.move_15_bars_atr

    pct_reaching = trades_reaching_target / len(pairs) if pairs else 0.0
    avg_move = total_move / trades_reaching_target if trades_reaching_target > 0 else 0.0

    # Recommend based on typical ES volatility
    # Tighter stops (0.75-1.0 ATR) for high win rate
    # Wider stops (1.5-2.0 ATR) for more profit capture
    if pct_reaching < 0.4:
        recommended = 1.5  # Wider stop to let trades breathe
        reason = "Wider trailing stop allows more trades to reach profit targets"
    elif pct_reaching > 0.7:
        recommended = 0.75  # Tighter stop to lock in profits
        reason = "Tighter trailing stop locks in profits more aggressively"
    else:
        recommended = 1.0  # Keep current
        reason = "Current trailing stop is well-calibrated"

    return TrailingStopRecommendation(
        current=current,
        recommended=recommended,
        reason=reason,
        pct_trades_reaching_target=round(pct_reaching, 2),
        avg_hold_minutes=15.0,  # Placeholder - would need actual trade data
    )


def optimize_max_hold_minutes(
    pairs: list[ScoreOutcomePair],
    current_config: dict[str, int],
) -> list[HoldTimeRecommendation]:
    """
    Optimize max hold time by zone for 15-360 minute target range.
    """
    recommendations: list[HoldTimeRecommendation] = []

    # Group pairs by zone
    zone_pairs: dict[str, list[ScoreOutcomePair]] = {}
    for pair in pairs:
        zone = pair.zone or "Unknown"
        if zone not in zone_pairs:
            zone_pairs[zone] = []
        zone_pairs[zone].append(pair)

    for zone, zone_data in zone_pairs.items():
        current_hold = current_config.get(zone, 30)

        # Analyze winning trade horizons
        wins_at_15 = sum(1 for p in zone_data if p.predicted_long_correct_15)
        wins_at_30 = sum(1 for p in zone_data if p.predicted_long_correct_30)
        wins_at_60 = sum(1 for p in zone_data if p.predicted_long_correct_60)

        total_with_15 = sum(1 for p in zone_data if p.move_15_bars_atr is not None)

        if total_with_15 == 0:
            continue

        win_rate_15 = wins_at_15 / total_with_15

        # Recommend based on when winners materialize
        if wins_at_60 > wins_at_30 * 1.2:
            # Winners keep coming after 30 min - extend hold time
            recommended = min(240, current_hold * 2)
            reason = f"Winners continue past 30 min; {wins_at_60} wins at 60 min vs {wins_at_30} at 30 min"
        elif wins_at_30 > wins_at_15 * 1.2:
            # Winners materialize around 30 min
            recommended = max(60, current_hold)
            reason = f"Winners materialize around 30 min; {wins_at_30} wins at 30 min"
        else:
            # Winners come early or not at all
            recommended = min(30, current_hold)
            reason = f"Most winners come early; keep hold time short"

        # Ensure within target range
        recommended = max(15, min(360, recommended))

        recommendations.append(
            HoldTimeRecommendation(
                zone=zone,
                current=current_hold,
                recommended=recommended,
                reason=reason,
                avg_win_hold_minutes=None,  # Would need actual trade data
                avg_loss_hold_minutes=None,
            )
        )

    return recommendations


def recommend_config_updates(
    report: CorrelationReport,
    config: Optional[Config] = None,
) -> OptimizationReport:
    """
    Generate config/default.yaml patch with recommended values.
    """
    config = config or get_config()
    pairs = report.score_outcome_pairs
    results = report.threshold_results

    # Optimize each threshold
    min_entry_rec = optimize_entry_threshold(
        results,
        current=config.alpha.min_entry_score,
    )

    exit_decay_rec = optimize_exit_decay_score(
        pairs,
        current=config.alpha.exit_decay_score,
    )

    reverse_gap_rec = ThresholdRecommendation(
        current=config.alpha.reverse_score_gap,
        recommended=config.alpha.reverse_score_gap,
        reason="Reverse score gap rarely triggers; analyze manually",
        trade_off="N/A",
        confidence="low",
    )

    full_size_rec = ThresholdRecommendation(
        current=config.alpha.full_size_score,
        recommended=config.alpha.full_size_score,
        reason="Full size score should be 1.5+ above min_entry for scaling",
        trade_off="N/A",
        confidence="low",
    )

    # Optimize trailing stop
    trailing_rec = optimize_trailing_stop(
        pairs,
        current=config.strategy.trailing_stop_atr,
    )

    # Optimize hold times
    hold_recs = optimize_max_hold_minutes(
        pairs,
        dict(config.alpha.max_hold_minutes),
    )

    # Count trades at current vs recommended thresholds
    current_trades = _estimate_trades_at(results, config.alpha.min_entry_score)
    recommended_trades = _estimate_trades_at(results, min_entry_rec.recommended)

    # Calculate expected win rate change
    current_wr = 0.0
    recommended_wr = 0.0
    for r in results:
        if abs(r.threshold - config.alpha.min_entry_score) < 0.1:
            current_wr = r.win_rate
        if abs(r.threshold - min_entry_rec.recommended) < 0.1:
            recommended_wr = r.win_rate

    return OptimizationReport(
        run_id=report.run_id,
        symbol=report.symbol,
        generated_at=datetime.now(UTC),
        min_entry_score=min_entry_rec,
        exit_decay_score=exit_decay_rec,
        reverse_score_gap=reverse_gap_rec,
        full_size_score=full_size_rec,
        trailing_stop_atr=trailing_rec,
        breakeven_trigger_atr=ThresholdRecommendation(
            current=config.strategy.breakeven_trigger_atr,
            recommended=config.strategy.breakeven_trigger_atr,
            reason="Breakeven trigger should trail profit lock",
            trade_off="N/A",
            confidence="low",
        ),
        profit_lock_atr=ThresholdRecommendation(
            current=config.strategy.profit_lock_atr,
            recommended=config.strategy.profit_lock_atr,
            reason="Profit lock should be 0.5 ATR below trailing stop",
            trade_off="N/A",
            confidence="low",
        ),
        max_hold_minutes=hold_recs,
        current_threshold_trades=current_trades,
        recommended_threshold_trades=recommended_trades,
        expected_win_rate_change=round(recommended_wr - current_wr, 4),
        threshold_results=results,
    )


def build_optimization_report(
    run_id: str,
    symbol: str = "ES",
    config: Optional[Config] = None,
) -> OptimizationReport:
    """Build a full optimization report for a run."""
    correlation = build_matrix_correlation_report(run_id=run_id, symbol=symbol)
    return recommend_config_updates(correlation, config=config)


def render_optimization_yaml_patch(report: OptimizationReport) -> str:
    """Render the optimization as a YAML patch for manual application."""
    lines = [
        "# Matrix threshold optimization recommendations",
        f"# Generated: {report.generated_at.isoformat()}",
        f"# Run ID: {report.run_id}",
        f"# Symbol: {report.symbol}",
        "",
        "alpha:",
    ]

    rec = report.min_entry_score
    lines.append(f"  min_entry_score: {rec.recommended}  # was {rec.current}")
    lines.append(f"    # {rec.reason}")
    lines.append(f"    # Trade-off: {rec.trade_off}")

    rec = report.exit_decay_score
    lines.append(f"  exit_decay_score: {rec.recommended}  # was {rec.current}")
    lines.append(f"    # {rec.reason}")

    rec = report.reverse_score_gap
    if abs(rec.recommended - rec.current) >= 0.1:
        lines.append(f"  reverse_score_gap: {rec.recommended}  # was {rec.current}")

    rec = report.full_size_score
    if abs(rec.recommended - rec.current) >= 0.1:
        lines.append(f"  full_size_score: {rec.recommended}  # was {rec.current}")

    # Hold times
    if report.max_hold_minutes:
        lines.append("")
        lines.append("  max_hold_minutes:")
        for hold_rec in report.max_hold_minutes:
            lines.append(f"    {hold_rec.zone}: {hold_rec.recommended}  # was {hold_rec.current}")
            lines.append(f"      # {hold_rec.reason}")

    # Strategy params
    lines.append("")
    lines.append("strategy:")

    if report.trailing_stop_atr:
        ts = report.trailing_stop_atr
        lines.append(f"  trailing_stop_atr: {ts.recommended}  # was {ts.current}")
        lines.append(f"    # {ts.reason}")

    return "\n".join(lines)
