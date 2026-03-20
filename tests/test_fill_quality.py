"""Tests for fill quality analysis."""

from datetime import UTC, datetime

from src.analysis.fill_quality import (
    FillAnalysis,
    FillQualityAnalyzer,
    FillQualityReport,
    FillScorecard,
    build_fill_quality_report,
)


def test_fill_analysis_dataclass():
    """FillAnalysis dataclass should store fill details correctly."""
    fill = FillAnalysis(
        order_id="12345",
        trade_id="T67890",
        symbol="ES",
        side="buy",
        quantity=2,
        expected_price=5900.0,
        filled_price=5900.25,
        slippage_ticks=1.0,
        slippage_dollars=12.50,
        zone="Hot-Open",
        timestamp=datetime.now(UTC),
        order_type="limit",
        is_protective=False,
    )
    assert fill.order_id == "12345"
    assert fill.slippage_ticks == 1.0
    assert fill.slippage_dollars == 12.50


def test_fill_scorecard_empty():
    """FillScorecard should handle empty fill lists."""
    scorecard = FillScorecard(
        fill_count=0,
        total_contracts=0,
        avg_slippage_ticks=0.0,
        median_slippage_ticks=0.0,
        max_slippage_ticks=0.0,
        p95_slippage_ticks=0.0,
        total_slippage_dollars=0.0,
        protective_fill_count=0,
        protective_avg_slippage_ticks=0.0,
        limit_fill_count=0,
        market_fill_count=0,
    )
    assert scorecard.fill_count == 0
    assert scorecard.avg_slippage_ticks == 0.0


def test_fill_quality_report():
    """FillQualityReport should aggregate fill analysis results."""
    report = FillQualityReport(
        generated_at=datetime.now(UTC),
        account_id="12345",
        account_name="Test Account",
        lookback_days=30,
        total_fills=10,
        overall_scorecard=FillScorecard(
            fill_count=10,
            total_contracts=20,
            avg_slippage_ticks=0.5,
            median_slippage_ticks=0.25,
            max_slippage_ticks=2.0,
            p95_slippage_ticks=1.5,
            total_slippage_dollars=125.0,
            protective_fill_count=5,
            protective_avg_slippage_ticks=0.75,
            limit_fill_count=8,
            market_fill_count=2,
        ),
        zone_scorecards={},
        order_type_breakdown={},
        slippage_distribution={"0_ticks": 5, "1_tick": 3, "2+_ticks": 2},
        correlation_with_volatility=None,
    )
    assert report.total_fills == 10
    assert report.overall_scorecard.avg_slippage_ticks == 0.5


def test_compute_slippage_ticks():
    """Slippage calculation should be correct for buy and sell orders."""
    analyzer = FillQualityAnalyzer()

    # Buy: paid more than expected = positive slippage (bad)
    slippage = analyzer._compute_slippage_ticks(
        filled_price=5900.50,
        expected_price=5900.00,
        side="buy",
    )
    assert slippage == 2.0  # 0.50 / 0.25 = 2 ticks adverse

    # Sell: received less than expected = positive slippage (bad)
    slippage = analyzer._compute_slippage_ticks(
        filled_price=5899.50,
        expected_price=5900.00,
        side="sell",
    )
    assert slippage == 2.0  # 0.50 / 0.25 = 2 ticks adverse


def test_normalize_side():
    """Side normalization should handle various formats."""
    analyzer = FillQualityAnalyzer()

    assert analyzer._normalize_side("BUY") == "buy"
    assert analyzer._normalize_side("Sell") == "sell"
    assert analyzer._normalize_side("0") == "buy"
    assert analyzer._normalize_side("1") == "sell"
    assert analyzer._normalize_side("long") == "buy"
    assert analyzer._normalize_side("short") == "sell"
    assert analyzer._normalize_side(None) == "unknown"


def test_build_slippage_distribution():
    """Slippage distribution should bucket fills correctly."""
    analyzer = FillQualityAnalyzer()

    fills = [
        FillAnalysis(
            order_id=str(i),
            trade_id=None,
            symbol="ES",
            side="buy",
            quantity=1,
            expected_price=5900.0,
            filled_price=5900.0 + (slip * 0.25),
            slippage_ticks=slip,
            slippage_dollars=abs(slip) * 12.50,
            zone=None,
            timestamp=datetime.now(UTC),
            order_type="market",
            is_protective=False,
        )
        for i, slip in enumerate([0, 0.1, 0.3, 0.6, 0.8, 1.0, 1.2, 1.4, 2.5, 3.0])
    ]

    distribution = analyzer._build_slippage_distribution(fills)

    assert distribution["0_ticks"] == 1  # 0
    assert distribution["0.25_ticks"] == 1  # 0.1
    assert distribution["0.5_ticks"] == 1  # 0.3
    assert distribution["0.75_ticks"] == 1  # 0.6
    assert distribution["1_tick"] == 2  # 0.8, 1.0
    assert distribution["1.25_ticks"] == 1  # 1.2
    assert distribution["1.5_ticks"] == 1  # 1.4
    assert distribution["2+_ticks"] == 2  # 2.5, 3.0


def test_build_fill_quality_report():
    """build_fill_quality_report should return a valid report."""
    report = build_fill_quality_report(
        account_id="test",
        days_back=7,
        source="observability",  # Use observability only to avoid API calls
    )

    assert "generated_at" in report
    assert "lookback_days" in report
    assert report["lookback_days"] == 7
    assert "overall_scorecard" in report
    assert "zone_scorecards" in report
    assert "order_type_breakdown" in report
    assert "slippage_distribution" in report
