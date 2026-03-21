"""Tests for trade analyzer (analyzes ACTUAL TRADES from replay)."""

from datetime import UTC, datetime, timedelta

from src.analysis.trade_analyzer import (
    TradeStats,
    ZoneTradeStats,
    ThresholdSensitivity,
    TradeAnalysisReport,
    compute_trade_stats,
    compute_threshold_sensitivity,
    compute_hold_time_distribution,
    compute_hourly_breakdown,
)


def test_trade_stats_dataclass():
    """TradeStats should store trade statistics correctly."""
    stats = TradeStats(
        trade_count=100,
        win_count=55,
        loss_count=40,
        scratch_count=5,
        win_rate=0.55,
        total_pnl=1250.0,
        gross_wins=2500.0,
        gross_losses=1250.0,
        profit_factor=2.0,
        avg_win=45.45,
        avg_loss=-31.25,
        avg_hold_minutes=45.0,
        max_win=200.0,
        max_loss=-150.0,
        max_consecutive_wins=5,
        max_consecutive_losses=4,
    )

    assert stats.trade_count == 100
    assert stats.win_rate == 0.55
    assert stats.profit_factor == 2.0
    assert stats.max_consecutive_wins == 5


def test_zone_trade_stats_dataclass():
    """ZoneTradeStats should store zone-specific statistics."""
    stats = TradeStats(
        trade_count=30,
        win_count=18,
        loss_count=12,
        scratch_count=0,
        win_rate=0.60,
        total_pnl=500.0,
        gross_wins=800.0,
        gross_losses=300.0,
        profit_factor=2.67,
        avg_win=44.44,
        avg_loss=-25.0,
        avg_hold_minutes=60.0,
        max_win=100.0,
        max_loss=-50.0,
        max_consecutive_wins=3,
        max_consecutive_losses=2,
    )

    zone_stats = ZoneTradeStats(
        zone="Pre-Open",
        stats=stats,
        trades_per_hour=2.5,
        avg_entry_score=4.75,
        most_common_strategy="momentum",
    )

    assert zone_stats.zone == "Pre-Open"
    assert zone_stats.trades_per_hour == 2.5
    assert zone_stats.avg_entry_score == 4.75
    assert zone_stats.most_common_strategy == "momentum"


def test_threshold_sensitivity_dataclass():
    """ThresholdSensitivity should store filter analysis correctly."""
    sensitivity = ThresholdSensitivity(
        threshold=4.5,
        trades_would_pass=80,
        trades_would_be_filtered=20,
        win_rate_of_passing_trades=0.625,
        pnl_of_passing_trades=1200.0,
        filtered_trades_were_winners=8,
        filtered_trades_were_losers=12,
    )

    assert sensitivity.threshold == 4.5
    assert sensitivity.trades_would_pass == 80
    assert sensitivity.trades_would_be_filtered == 20
    assert sensitivity.win_rate_of_passing_trades == 0.625


def test_compute_trade_stats_empty():
    """compute_trade_stats should handle empty input."""
    stats = compute_trade_stats([])

    assert stats.trade_count == 0
    assert stats.win_rate == 0.0
    assert stats.total_pnl == 0.0
    assert stats.profit_factor == 0.0
    assert stats.avg_hold_minutes == 0.0


def test_compute_trade_stats_basic():
    """compute_trade_stats should compute correct statistics."""
    base_time = datetime.now(UTC)
    trades = [
        {
            "pnl": 100.0,
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=30)).isoformat(),
        },
        {
            "pnl": -50.0,
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=15)).isoformat(),
        },
        {
            "pnl": 75.0,
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=45)).isoformat(),
        },
        {
            "pnl": 0.0,  # scratch
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=5)).isoformat(),
        },
    ]

    stats = compute_trade_stats(trades)

    assert stats.trade_count == 4
    assert stats.win_count == 2
    assert stats.loss_count == 1
    assert stats.scratch_count == 1
    assert stats.win_rate == 0.5  # 2/4
    assert stats.total_pnl == 125.0  # 100 - 50 + 75 + 0
    assert stats.gross_wins == 175.0  # 100 + 75
    assert stats.gross_losses == 50.0  # abs(-50)
    assert stats.avg_hold_minutes == 23.75  # (30 + 15 + 45 + 5) / 4


def test_compute_trade_stats_consecutive():
    """compute_trade_stats should track consecutive wins/losses."""
    trades = [
        {"pnl": 10.0, "entry_time": None, "exit_time": None},  # W
        {"pnl": 20.0, "entry_time": None, "exit_time": None},  # W
        {"pnl": 30.0, "entry_time": None, "exit_time": None},  # W
        {"pnl": -10.0, "entry_time": None, "exit_time": None},  # L
        {"pnl": -20.0, "entry_time": None, "exit_time": None},  # L
        {"pnl": 40.0, "entry_time": None, "exit_time": None},  # W
        {"pnl": -30.0, "entry_time": None, "exit_time": None},  # L
    ]

    stats = compute_trade_stats(trades)

    assert stats.max_consecutive_wins == 3
    assert stats.max_consecutive_losses == 2


def test_compute_threshold_sensitivity_empty():
    """compute_threshold_sensitivity should handle empty input."""
    results = compute_threshold_sensitivity([])

    assert results == []


def test_compute_threshold_sensitivity_basic():
    """compute_threshold_sensitivity should compute filter analysis."""
    trades = [
        {"pnl": 100.0, "entry_score": 5.0, "payload": {}},
        {"pnl": -50.0, "entry_score": 4.0, "payload": {}},
        {"pnl": 75.0, "entry_score": 5.5, "payload": {}},
        {"pnl": -25.0, "entry_score": 3.5, "payload": {}},
        {"pnl": 50.0, "entry_score": 6.0, "payload": {}},
    ]

    results = compute_threshold_sensitivity(
        trades,
        threshold_range=(3.5, 6.0),
        step=0.5,
    )

    assert len(results) > 0

    # At threshold 3.5, all 5 trades pass
    result_3_5 = next((r for r in results if r.threshold == 3.5), None)
    assert result_3_5 is not None
    assert result_3_5.trades_would_pass == 5
    assert result_3_5.trades_would_be_filtered == 0

    # At threshold 5.0, only 3 trades pass (5.0, 5.5, 6.0)
    result_5_0 = next((r for r in results if r.threshold == 5.0), None)
    assert result_5_0 is not None
    assert result_5_0.trades_would_pass == 3
    assert result_5_0.trades_would_be_filtered == 2


def test_compute_hold_time_distribution():
    """compute_hold_time_distribution should bucket hold times correctly."""
    base_time = datetime.now(UTC)
    trades = [
        {
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=3)).isoformat(),  # 0-5
        },
        {
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=10)).isoformat(),  # 5-15
        },
        {
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=20)).isoformat(),  # 15-30
        },
        {
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=45)).isoformat(),  # 30-60
        },
        {
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=90)).isoformat(),  # 60-120
        },
        {
            "entry_time": base_time.isoformat(),
            "exit_time": (base_time + timedelta(minutes=180)).isoformat(),  # 120+
        },
    ]

    distribution = compute_hold_time_distribution(trades)

    assert distribution["0-5 min"] == 1
    assert distribution["5-15 min"] == 1
    assert distribution["15-30 min"] == 1
    assert distribution["30-60 min"] == 1
    assert distribution["60-120 min"] == 1
    assert distribution["120+ min"] == 1


def test_compute_hourly_breakdown():
    """compute_hourly_breakdown should group trades by hour."""
    trades = []
    base_time = datetime.now(UTC)

    # Create trades at different hours
    for hour in [9, 9, 10, 14, 14, 14]:
        entry_time = base_time.replace(hour=hour, minute=30)
        trades.append({
            "entry_time": entry_time.isoformat(),
            "pnl": 50.0 if hour == 9 else (-25.0 if hour == 10 else 100.0),
        })

    breakdown = compute_hourly_breakdown(trades)

    assert 9 in breakdown
    assert 10 in breakdown
    assert 14 in breakdown
    assert breakdown[9]["trades"] == 2
    assert breakdown[10]["trades"] == 1
    assert breakdown[14]["trades"] == 3
    # Hour 9: 2 trades, 2 wins (both pnl=50)
    assert breakdown[9]["wins"] == 2
    # Hour 10: 1 trade, 0 wins (pnl=-25)
    assert breakdown[10]["wins"] == 0
    # Hour 14: 3 trades, 3 wins (all pnl=100)
    assert breakdown[14]["wins"] == 3


def test_trade_analysis_report_dataclass():
    """TradeAnalysisReport should store full analysis correctly."""
    stats = TradeStats(
        trade_count=50,
        win_count=28,
        loss_count=20,
        scratch_count=2,
        win_rate=0.56,
        total_pnl=750.0,
        gross_wins=1200.0,
        gross_losses=450.0,
        profit_factor=2.67,
        avg_win=42.86,
        avg_loss=-22.5,
        avg_hold_minutes=45.0,
        max_win=150.0,
        max_loss=-75.0,
        max_consecutive_wins=4,
        max_consecutive_losses=3,
    )

    report = TradeAnalysisReport(
        run_id="test-run-123",
        symbol="ES",
        generated_at=datetime.now(UTC),
        overall_stats=stats,
        zone_stats=[],
        regime_stats={},
        threshold_sensitivity=[],
        hold_time_distribution={},
        entry_score_distribution={},
        hourly_breakdown={},
        warnings=["Only 50 trades found"],
    )

    assert report.run_id == "test-run-123"
    assert report.symbol == "ES"
    assert report.overall_stats.trade_count == 50
    assert len(report.warnings) == 1
