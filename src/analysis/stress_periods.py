"""Stress period detection from market bars and observability data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from statistics import mean, stdev
from typing import Any, Optional

import pandas as pd

from src.market import get_client
from src.observability import get_observability_store


@dataclass
class StressPeriod:
    """A detected period of market stress."""

    start_time: datetime
    end_time: datetime
    duration_minutes: int
    atr_multiplier: float
    spread_ticks: float
    bar_count: int
    avg_range: float
    max_range: float
    total_volume: int
    stress_score: float
    tags: list[str] = field(default_factory=list)


@dataclass
class StressReport:
    """Report of detected stress periods."""

    generated_at: datetime
    symbol: str
    lookback_days: int
    total_periods: int
    total_stress_minutes: int
    avg_stress_score: float
    max_stress_score: float
    periods: list[StressPeriod]
    summary: dict[str, Any]


def detect_stress_periods(
    bars: list[dict],
    atr_threshold: float = 2.0,
    spread_threshold: float = 5.0,
    min_consecutive_bars: int = 3,
    lookback_for_atr: int = 20,
) -> list[StressPeriod]:
    """Identify high-volatility periods from bar data.

    Args:
        bars: List of bar dicts with 'time', 'open', 'high', 'low', 'close', 'volume'
        atr_threshold: Multiplier of ATR to consider stressed
        spread_threshold: Maximum spread in ticks to consider stressed
        min_consecutive_bars: Minimum consecutive stressed bars to form a period
        lookback_for_atr: Bars to look back for ATR calculation

    Returns:
        List of detected StressPeriod objects
    """
    if len(bars) < lookback_for_atr + min_consecutive_bars:
        return []

    # Convert to DataFrame for easier calculation
    df = pd.DataFrame(bars)
    if "time" not in df.columns:
        return []

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values("time").reset_index(drop=True)

    # Calculate True Range and ATR
    df["tr"] = df["high"] - df["low"]
    df["atr"] = df["tr"].rolling(window=lookback_for_atr, min_periods=1).mean()

    # Calculate range as multiple of ATR
    df["range_multiplier"] = df["tr"] / df["atr"].replace(0, 1)

    # Calculate spread (using high-low as proxy)
    tick_size = 0.25  # ES
    df["spread_ticks"] = (df["high"] - df["low"]) / tick_size

    # Identify stressed bars
    df["is_stressed"] = (df["range_multiplier"] >= atr_threshold) | (
        df["spread_ticks"] >= spread_threshold
    )

    # Find consecutive stressed periods
    periods: list[StressPeriod] = []
    stress_start: Optional[int] = None

    for i, row in df.iterrows():
        if row["is_stressed"]:
            if stress_start is None:
                stress_start = i
        else:
            if stress_start is not None:
                stressed_bars = df.iloc[stress_start:i]
                if len(stressed_bars) >= min_consecutive_bars:
                    periods.append(_build_stress_period(stressed_bars))
                stress_start = None

    # Handle trailing period
    if stress_start is not None:
        stressed_bars = df.iloc[stress_start:]
        if len(stressed_bars) >= min_consecutive_bars:
            periods.append(_build_stress_period(stressed_bars))

    return periods


def detect_stress_periods_from_topstep(
    symbol: str = "ES",
    days_back: int = 30,
    atr_threshold: float = 2.0,
    spread_threshold: float = 5.0,
) -> list[StressPeriod]:
    """Fetch bars from Topstep and detect stress periods."""
    client = get_client()
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=max(int(days_back), 1))

    if not client._access_token and not client.authenticate():
        return []

    bars = client.retrieve_bars(
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        unit="minute",
        unit_number=1,
        limit=50000,
    )

    if not bars:
        return []

    return detect_stress_periods(
        bars,
        atr_threshold=atr_threshold,
        spread_threshold=spread_threshold,
    )


def detect_stress_periods_from_observability(
    db_path: str = "logs/observability.db",
    days_back: int = 30,
    atr_threshold: float = 2.0,
    spread_threshold: float = 5.0,
) -> list[StressPeriod]:
    """Query observability DB for market tape and detect stress periods."""
    observability = get_observability_store()
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(days=max(int(days_back), 1))

    tape = observability.query_market_tape(
        limit=50000,
        start_time=start_time,
        end_time=end_time,
    )

    if not tape:
        return []

    # Group tape entries by minute to form bars
    bars_by_minute: dict[str, dict[str, Any]] = {}
    for entry in tape:
        ts = entry.get("captured_at") or entry.get("timestamp")
        if ts is None:
            continue

        if isinstance(ts, str):
            ts = pd.Timestamp(ts)
        minute_key = ts.strftime("%Y-%m-%d %H:%M")

        if minute_key not in bars_by_minute:
            bars_by_minute[minute_key] = {
                "time": ts,
                "open": entry.get("last", 0),
                "high": entry.get("last", 0),
                "low": entry.get("last", 0),
                "close": entry.get("last", 0),
                "volume": 0,
            }

        bar = bars_by_minute[minute_key]
        price = float(entry.get("last", 0) or bar["close"])
        volume = int(entry.get("volume", 0) or 0)

        bar["high"] = max(bar["high"], price)
        bar["low"] = min(bar["low"], price)
        bar["close"] = price
        bar["volume"] += volume

    bars = list(bars_by_minute.values())
    return detect_stress_periods(
        bars,
        atr_threshold=atr_threshold,
        spread_threshold=spread_threshold,
    )


def build_stress_report(
    periods: list[StressPeriod],
    *,
    symbol: str = "ES",
    lookback_days: int = 30,
) -> StressReport:
    """Build a comprehensive stress report from detected periods."""
    total_stress_minutes = sum(p.duration_minutes for p in periods)
    stress_scores = [p.stress_score for p in periods] if periods else [0]

    return StressReport(
        generated_at=datetime.now(UTC),
        symbol=symbol,
        lookback_days=lookback_days,
        total_periods=len(periods),
        total_stress_minutes=total_stress_minutes,
        avg_stress_score=round(mean(stress_scores), 4),
        max_stress_score=round(max(stress_scores), 4),
        periods=periods,
        summary={
            "total_stress_hours": round(total_stress_minutes / 60, 2),
            "pct_time_in_stress": round(
                total_stress_minutes / (lookback_days * 24 * 60) * 100, 2
            ),
            "avg_duration_minutes": (
                round(mean([p.duration_minutes for p in periods]), 1) if periods else 0
            ),
            "max_duration_minutes": max((p.duration_minutes for p in periods), default=0),
            "avg_atr_multiplier": (
                round(mean([p.atr_multiplier for p in periods]), 2) if periods else 0
            ),
            "avg_spread_ticks": (
                round(mean([p.spread_ticks for p in periods]), 2) if periods else 0
            ),
        },
    )


def _build_stress_period(stressed_bars: pd.DataFrame) -> StressPeriod:
    """Build a StressPeriod from a DataFrame of stressed bars."""
    start_time = stressed_bars.iloc[0]["time"]
    end_time = stressed_bars.iloc[-1]["time"]

    if isinstance(start_time, pd.Timestamp):
        start_time = start_time.to_pydatetime()
    if isinstance(end_time, pd.Timestamp):
        end_time = end_time.to_pydatetime()

    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=UTC)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=UTC)

    duration_minutes = int((end_time - start_time).total_seconds() / 60) + 1
    avg_range = float(stressed_bars["tr"].mean())
    max_range = float(stressed_bars["tr"].max())
    avg_atr_mult = float(stressed_bars["range_multiplier"].mean())
    avg_spread = float(stressed_bars["spread_ticks"].mean())
    total_volume = int(stressed_bars["volume"].sum())

    # Compute stress score (0-100)
    # Weighted combination of ATR multiplier, spread, and duration
    atr_score = min(avg_atr_mult / 4.0 * 40, 40)  # Max 40 points
    spread_score = min(avg_spread / 10.0 * 30, 30)  # Max 30 points
    duration_score = min(duration_minutes / 60.0 * 30, 30)  # Max 30 points
    stress_score = atr_score + spread_score + duration_score

    # Generate tags based on characteristics
    tags: list[str] = []
    if avg_atr_mult >= 3.0:
        tags.append("high_volatility")
    if avg_spread >= 8:
        tags.append("wide_spreads")
    if duration_minutes >= 30:
        tags.append("extended_stress")
    if total_volume >= 100000:
        tags.append("high_volume")

    return StressPeriod(
        start_time=start_time,
        end_time=end_time,
        duration_minutes=duration_minutes,
        atr_multiplier=round(avg_atr_mult, 2),
        spread_ticks=round(avg_spread, 2),
        bar_count=len(stressed_bars),
        avg_range=round(avg_range, 2),
        max_range=round(max_range, 2),
        total_volume=total_volume,
        stress_score=round(stress_score, 2),
        tags=tags,
    )


def build_stress_periods_dict(
    *,
    symbol: str = "ES",
    days_back: int = 30,
    source: str = "topstep",
    atr_threshold: float = 2.0,
    spread_threshold: float = 5.0,
) -> dict[str, Any]:
    """Build a stress periods report for CLI consumption."""
    periods: list[StressPeriod] = []

    if source == "topstep":
        periods = detect_stress_periods_from_topstep(
            symbol=symbol,
            days_back=days_back,
            atr_threshold=atr_threshold,
            spread_threshold=spread_threshold,
        )
    elif source == "observability":
        periods = detect_stress_periods_from_observability(
            days_back=days_back,
            atr_threshold=atr_threshold,
            spread_threshold=spread_threshold,
        )

    report = build_stress_report(periods, symbol=symbol, lookback_days=days_back)

    return {
        "generated_at": report.generated_at.isoformat(),
        "symbol": report.symbol,
        "lookback_days": report.lookback_days,
        "total_periods": report.total_periods,
        "total_stress_minutes": report.total_stress_minutes,
        "avg_stress_score": report.avg_stress_score,
        "max_stress_score": report.max_stress_score,
        "summary": report.summary,
        "periods": [
            {
                "start_time": p.start_time.isoformat(),
                "end_time": p.end_time.isoformat(),
                "duration_minutes": p.duration_minutes,
                "atr_multiplier": p.atr_multiplier,
                "spread_ticks": p.spread_ticks,
                "bar_count": p.bar_count,
                "avg_range": p.avg_range,
                "max_range": p.max_range,
                "total_volume": p.total_volume,
                "stress_score": p.stress_score,
                "tags": p.tags,
            }
            for p in report.periods[:50]  # Limit output
        ],
    }
