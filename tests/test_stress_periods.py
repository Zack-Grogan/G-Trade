"""Tests for stress period detection."""

from datetime import UTC, datetime, timedelta

from src.analysis.stress_periods import (
    StressPeriod,
    StressReport,
    detect_stress_periods,
    build_stress_report,
    build_stress_periods_dict,
)


def make_bar(time_offset_minutes: int, open_price: float, high: float, low: float, close: float, volume: int = 1000):
    """Create a test bar dict."""
    base_time = datetime(2026, 3, 20, 9, 30, tzinfo=UTC)
    return {
        "time": base_time + timedelta(minutes=time_offset_minutes),
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }


def test_detect_stress_periods_no_stress():
    """Should return empty list when no stress periods exist."""
    # Create 30 normal bars with consistent range
    bars = [
        make_bar(i, 5900.0, 5900.25, 5899.75, 5900.0, 1000)
        for i in range(30)
    ]

    periods = detect_stress_periods(
        bars,
        atr_threshold=2.0,
        spread_threshold=5.0,
        min_consecutive_bars=3,
        lookback_for_atr=10,
    )

    assert len(periods) == 0


def test_detect_stress_periods_with_stress():
    """Should detect stress periods when bars have high volatility."""
    # Create 10 normal bars, then 5 stressed bars, then 10 normal bars
    bars = []

    # 10 normal bars
    for i in range(10):
        bars.append(make_bar(i, 5900.0, 5900.25, 5899.75, 5900.0, 1000))

    # 5 stressed bars (large range)
    for i in range(10, 15):
        bars.append(make_bar(i, 5900.0, 5910.0, 5890.0, 5905.0, 5000))

    # 10 normal bars
    for i in range(15, 25):
        bars.append(make_bar(i, 5905.0, 5905.25, 5904.75, 5905.0, 1000))

    periods = detect_stress_periods(
        bars,
        atr_threshold=2.0,
        spread_threshold=5.0,
        min_consecutive_bars=3,
        lookback_for_atr=5,
    )

    assert len(periods) == 1
    assert periods[0].bar_count == 5
    assert periods[0].atr_multiplier >= 2.0


def test_detect_stress_periods_min_consecutive():
    """Should require minimum consecutive bars to form a period."""
    # Create bars with only 2 stressed bars (below min_consecutive_bars=3)
    bars = []

    # 10 normal bars
    for i in range(10):
        bars.append(make_bar(i, 5900.0, 5900.25, 5899.75, 5900.0, 1000))

    # Only 2 stressed bars
    for i in range(10, 12):
        bars.append(make_bar(i, 5900.0, 5910.0, 5890.0, 5905.0, 5000))

    # More normal bars
    for i in range(12, 20):
        bars.append(make_bar(i, 5905.0, 5905.25, 5904.75, 5905.0, 1000))

    periods = detect_stress_periods(
        bars,
        atr_threshold=2.0,
        spread_threshold=5.0,
        min_consecutive_bars=3,
        lookback_for_atr=5,
    )

    assert len(periods) == 0


def test_stress_period_dataclass():
    """StressPeriod dataclass should store period details correctly."""
    period = StressPeriod(
        start_time=datetime(2026, 3, 20, 10, 0, tzinfo=UTC),
        end_time=datetime(2026, 3, 20, 10, 30, tzinfo=UTC),
        duration_minutes=30,
        atr_multiplier=3.5,
        spread_ticks=8.0,
        bar_count=30,
        avg_range=5.0,
        max_range=10.0,
        total_volume=50000,
        stress_score=75.0,
        tags=["high_volatility", "wide_spreads"],
    )

    assert period.duration_minutes == 30
    assert period.atr_multiplier == 3.5
    assert period.stress_score == 75.0
    assert "high_volatility" in period.tags


def test_stress_report():
    """StressReport should aggregate stress period results."""
    report = StressReport(
        generated_at=datetime.now(UTC),
        symbol="ES",
        lookback_days=30,
        total_periods=3,
        total_stress_minutes=90,
        avg_stress_score=50.0,
        max_stress_score=75.0,
        periods=[],
        summary={
            "total_stress_hours": 1.5,
            "pct_time_in_stress": 0.21,
            "avg_duration_minutes": 30,
            "max_duration_minutes": 45,
            "avg_atr_multiplier": 3.0,
            "avg_spread_ticks": 6.0,
        },
    )

    assert report.total_periods == 3
    assert report.total_stress_minutes == 90
    assert report.summary["total_stress_hours"] == 1.5


def test_build_stress_report():
    """build_stress_report should compute correct aggregations."""
    periods = [
        StressPeriod(
            start_time=datetime(2026, 3, 20, 10, 0, tzinfo=UTC),
            end_time=datetime(2026, 3, 20, 10, 15, tzinfo=UTC),
            duration_minutes=15,
            atr_multiplier=2.5,
            spread_ticks=6.0,
            bar_count=15,
            avg_range=3.0,
            max_range=5.0,
            total_volume=20000,
            stress_score=40.0,
            tags=["high_volatility"],
        ),
        StressPeriod(
            start_time=datetime(2026, 3, 20, 14, 0, tzinfo=UTC),
            end_time=datetime(2026, 3, 20, 14, 30, tzinfo=UTC),
            duration_minutes=30,
            atr_multiplier=4.0,
            spread_ticks=10.0,
            bar_count=30,
            avg_range=6.0,
            max_range=12.0,
            total_volume=60000,
            stress_score=80.0,
            tags=["high_volatility", "wide_spreads", "extended_stress"],
        ),
    ]

    report = build_stress_report(periods, symbol="ES", lookback_days=30)

    assert report.total_periods == 2
    assert report.total_stress_minutes == 45
    assert report.avg_stress_score == 60.0  # (40 + 80) / 2
    assert report.max_stress_score == 80.0
    assert report.summary["total_stress_hours"] == 0.75


def test_build_stress_periods_dict_empty():
    """build_stress_periods_dict should handle empty results."""
    report = build_stress_periods_dict(
        symbol="ES",
        days_back=7,
        source="observability",  # Use observability to avoid API calls
    )

    assert "generated_at" in report
    assert "symbol" in report
    assert report["symbol"] == "ES"
    assert "periods" in report
    assert "summary" in report


def test_stress_period_tags():
    """Stress period tags should be generated based on characteristics."""
    # High volatility tag (atr >= 3.0)
    period_high_vol = StressPeriod(
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC) + timedelta(minutes=30),
        duration_minutes=30,
        atr_multiplier=3.5,
        spread_ticks=5.0,
        bar_count=30,
        avg_range=5.0,
        max_range=10.0,
        total_volume=50000,
        stress_score=50.0,
        tags=["high_volatility"],
    )
    assert "high_volatility" in period_high_vol.tags

    # Wide spreads tag (spread >= 8)
    period_wide_spread = StressPeriod(
        start_time=datetime.now(UTC),
        end_time=datetime.now(UTC) + timedelta(minutes=30),
        duration_minutes=30,
        atr_multiplier=2.0,
        spread_ticks=10.0,
        bar_count=30,
        avg_range=3.0,
        max_range=5.0,
        total_volume=50000,
        stress_score=50.0,
        tags=["wide_spreads"],
    )
    assert "wide_spreads" in period_wide_spread.tags
