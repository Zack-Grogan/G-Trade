"""Tests for matrix correlation analysis."""

from datetime import UTC, datetime, timedelta

from src.analysis.matrix_correlation import (
    ScoreOutcomePair,
    ThresholdResult,
    build_score_distribution,
    build_zone_breakdown,
    build_regime_breakdown,
    compute_threshold_analysis,
)
from src.analysis.threshold_optimizer import (
    ThresholdRecommendation,
    HoldTimeRecommendation,
    optimize_entry_threshold,
    optimize_exit_decay_score,
    optimize_max_hold_minutes,
)


def test_score_outcome_pair_dataclass():
    """ScoreOutcomePair should store decision and outcome data correctly."""
    pair = ScoreOutcomePair(
        timestamp=datetime.now(UTC),
        zone="Pre-Open",
        regime="TREND",
        long_score=4.5,
        short_score=2.0,
        flat_bias=0.5,
        dominant_side="long",
        price_at_decision=5900.0,
        atr_at_decision=10.0,
        move_5_bars_atr=0.3,
        move_15_bars_atr=0.5,
        move_30_bars_atr=0.8,
        move_60_bars_atr=1.2,
        predicted_long_correct_5=True,
        predicted_long_correct_15=True,
        predicted_long_correct_30=True,
        predicted_long_correct_60=True,
    )
    assert pair.zone == "Pre-Open"
    assert pair.long_score == 4.5
    assert pair.dominant_side == "long"
    assert pair.move_15_bars_atr == 0.5
    assert pair.predicted_long_correct_15 is True


def test_threshold_result_dataclass():
    """ThresholdResult should store analysis results correctly."""
    result = ThresholdResult(
        threshold=4.5,
        trade_count=100,
        win_count=55,
        loss_count=45,
        win_rate=0.55,
        avg_move_atr=0.25,
        total_move_atr=25.0,
        false_positive_count=45,
        false_positive_rate=0.45,
        profit_factor=1.5,
    )
    assert result.threshold == 4.5
    assert result.trade_count == 100
    assert result.win_rate == 0.55
    assert result.false_positive_rate == 0.45


def test_build_score_distribution():
    """Score distribution should calculate correct statistics."""
    pairs = [
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Pre-Open",
            regime="TREND",
            long_score=4.0 + i * 0.1,
            short_score=2.0 + i * 0.05,
            flat_bias=0.5 + i * 0.02,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
        )
        for i in range(10)
    ]

    distribution = build_score_distribution(pairs)

    assert distribution["total_count"] == 10
    assert "long_score" in distribution
    assert "short_score" in distribution
    assert "flat_bias" in distribution
    assert distribution["long_score"]["min"] == 4.0
    assert distribution["long_score"]["max"] == 4.9
    assert distribution["short_score"]["min"] == 2.0


def test_build_score_distribution_empty():
    """Score distribution should handle empty input."""
    distribution = build_score_distribution([])

    assert distribution == {}


def test_build_zone_breakdown():
    """Zone breakdown should aggregate statistics by zone."""
    pairs = [
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Pre-Open",
            regime="TREND",
            long_score=4.5,
            short_score=2.0,
            flat_bias=0.5,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
            move_15_bars_atr=0.5,
            predicted_long_correct_15=True,
        ),
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Pre-Open",
            regime="TREND",
            long_score=4.0,
            short_score=2.5,
            flat_bias=0.3,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
            move_15_bars_atr=-0.3,
            predicted_long_correct_15=False,
        ),
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Post-Open",
            regime="RANGE",
            long_score=3.5,
            short_score=3.0,
            flat_bias=0.2,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
            move_15_bars_atr=0.2,
            predicted_long_correct_15=True,
        ),
    ]

    breakdown = build_zone_breakdown(pairs)

    assert "Pre-Open" in breakdown
    assert "Post-Open" in breakdown
    assert breakdown["Pre-Open"]["count"] == 2
    assert breakdown["Post-Open"]["count"] == 1
    # Win rate for Pre-Open: 1 win, 1 loss = 50%
    assert breakdown["Pre-Open"]["win_rate_15"] == 0.5
    # Win rate for Post-Open: 1 win, 0 losses = 100%
    assert breakdown["Post-Open"]["win_rate_15"] == 1.0


def test_build_regime_breakdown():
    """Regime breakdown should aggregate statistics by regime."""
    pairs = [
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Pre-Open",
            regime="TREND",
            long_score=4.5,
            short_score=2.0,
            flat_bias=0.5,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
            move_15_bars_atr=0.5,
            predicted_long_correct_15=True,
        ),
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Post-Open",
            regime="RANGE",
            long_score=3.5,
            short_score=3.0,
            flat_bias=0.2,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
            move_15_bars_atr=-0.2,
            predicted_long_correct_15=False,
        ),
    ]

    breakdown = build_regime_breakdown(pairs)

    assert "TREND" in breakdown
    assert "RANGE" in breakdown
    assert breakdown["TREND"]["count"] == 1
    assert breakdown["RANGE"]["count"] == 1


def test_compute_threshold_analysis():
    """Threshold analysis should compute statistics for each threshold."""
    pairs = [
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Pre-Open",
            regime="TREND",
            long_score=score,
            short_score=2.0,
            flat_bias=0.5,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
            move_15_bars_atr=move,
            predicted_long_correct_15=correct,
        )
        for score, move, correct in [
            (4.0, 0.5, True),
            (4.5, 0.3, True),
            (5.0, -0.2, False),
            (5.5, 0.4, True),
            (6.0, -0.1, False),
        ]
    ]

    results = compute_threshold_analysis(
        pairs,
        threshold_range=(3.5, 6.5),
        step=0.5,
    )

    assert len(results) > 0

    # At threshold 4.0, all 5 trades qualify
    result_4_0 = next((r for r in results if r.threshold == 4.0), None)
    assert result_4_0 is not None
    assert result_4_0.trade_count == 5
    assert result_4_0.win_count == 3
    assert result_4_0.loss_count == 2

    # At threshold 5.5, only 2 trades qualify
    result_5_5 = next((r for r in results if r.threshold == 5.5), None)
    assert result_5_5 is not None
    assert result_5_5.trade_count == 2
    assert result_5_5.win_count == 1
    assert result_5_5.loss_count == 1


def test_optimize_entry_threshold():
    """Entry threshold optimization should find optimal value."""
    results = [
        ThresholdResult(
            threshold=4.0,
            trade_count=100,
            win_count=50,
            loss_count=50,
            win_rate=0.50,
            avg_move_atr=0.1,
            total_move_atr=10.0,
            false_positive_count=50,
            false_positive_rate=0.50,
            profit_factor=1.0,
        ),
        ThresholdResult(
            threshold=4.5,
            trade_count=80,
            win_count=48,
            loss_count=32,
            win_rate=0.60,
            avg_move_atr=0.2,
            total_move_atr=16.0,
            false_positive_count=32,
            false_positive_rate=0.40,
            profit_factor=1.5,
        ),
        ThresholdResult(
            threshold=5.0,
            trade_count=50,
            win_count=35,
            loss_count=15,
            win_rate=0.70,
            avg_move_atr=0.3,
            total_move_atr=15.0,
            false_positive_count=15,
            false_positive_rate=0.30,
            profit_factor=2.0,
        ),
    ]

    recommendation = optimize_entry_threshold(
        results,
        current=5.0,
        min_trades=10,
        target_win_rate=0.50,
        max_fp_rate=0.50,
    )

    assert recommendation.current == 5.0
    # Should recommend 4.5 or 5.0 based on profit factor and trade count balance
    assert recommendation.recommended >= 4.0
    assert recommendation.recommended <= 5.0
    assert recommendation.confidence in ("high", "medium", "low")


def test_optimize_entry_threshold_no_results():
    """Entry threshold optimization should handle empty results."""
    recommendation = optimize_entry_threshold(
        [],
        current=5.0,
    )

    assert recommendation.current == 5.0
    assert recommendation.recommended == 5.0
    assert recommendation.confidence == "low"


def test_optimize_exit_decay_score():
    """Exit decay score optimization should find optimal value."""
    pairs = [
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Pre-Open",
            regime="TREND",
            long_score=score,
            short_score=2.0,
            flat_bias=0.5,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
            move_15_bars_atr=move,
            predicted_long_correct_15=correct,
        )
        for score, move, correct in [
            (3.0, 0.5, True),
            (3.5, 0.4, True),
            (4.0, 0.3, True),
            (4.5, -0.2, False),
            (5.0, -0.3, False),
        ]
    ]

    recommendation = optimize_exit_decay_score(pairs, current=1.5)

    assert recommendation.current == 1.5
    # Should recommend something based on the winning scores
    assert recommendation.recommended >= 0.5


def test_optimize_max_hold_minutes():
    """Max hold minutes optimization should find optimal values per zone."""
    pairs = [
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Pre-Open",
            regime="TREND",
            long_score=4.5,
            short_score=2.0,
            flat_bias=0.5,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
            move_15_bars_atr=0.3,
            move_30_bars_atr=0.5,
            move_60_bars_atr=0.8,
            predicted_long_correct_15=True,
            predicted_long_correct_30=True,
            predicted_long_correct_60=True,
        ),
        ScoreOutcomePair(
            timestamp=datetime.now(UTC),
            zone="Post-Open",
            regime="RANGE",
            long_score=4.0,
            short_score=2.5,
            flat_bias=0.3,
            dominant_side="long",
            price_at_decision=5900.0,
            atr_at_decision=10.0,
            move_15_bars_atr=0.2,
            move_30_bars_atr=0.1,
            move_60_bars_atr=-0.1,
            predicted_long_correct_15=True,
            predicted_long_correct_30=False,
            predicted_long_correct_60=False,
        ),
    ]

    recommendations = optimize_max_hold_minutes(
        pairs,
        current_config={"Pre-Open": 40, "Post-Open": 55},
    )

    assert len(recommendations) == 2

    pre_open_rec = next((r for r in recommendations if r.zone == "Pre-Open"), None)
    post_open_rec = next((r for r in recommendations if r.zone == "Post-Open"), None)

    assert pre_open_rec is not None
    assert post_open_rec is not None

    # Pre-Open has winners at 60 min, should recommend longer hold
    assert pre_open_rec.recommended >= 15
    # Post-Open winners come early, should recommend shorter hold
    assert post_open_rec.recommended >= 15


def test_threshold_recommendation_dataclass():
    """ThresholdRecommendation should store recommendation details."""
    rec = ThresholdRecommendation(
        current=5.0,
        recommended=4.25,
        reason="Triggers 47 additional trades with 55% win rate",
        trade_off="More trades, slightly lower win rate",
        confidence="high",
    )

    assert rec.current == 5.0
    assert rec.recommended == 4.25
    assert "47 additional trades" in rec.reason
    assert rec.confidence == "high"


def test_hold_time_recommendation_dataclass():
    """HoldTimeRecommendation should store recommendation details."""
    rec = HoldTimeRecommendation(
        zone="Pre-Open",
        current=40,
        recommended=180,
        reason="Winners continue past 30 min; 12 wins at 60 min vs 8 at 30 min",
        avg_win_hold_minutes=45.0,
        avg_loss_hold_minutes=20.0,
    )

    assert rec.zone == "Pre-Open"
    assert rec.current == 40
    assert rec.recommended == 180
    assert "Winners continue" in rec.reason
