"""Aggregate market_tape ticks into OHLCV candles for charting.

Provides two data paths:

1. **Local tape** -- reads tick-level rows from the
   :class:`~src.observability.store.ObservabilityStore` ``market_tape``
   table, then resamples them into OHLCV candles using pandas.

2. **API bars** -- fetches historical bars directly from the TopstepX
   history endpoint via
   :meth:`~src.market.topstep_client.TopstepClient.retrieve_bars`.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd
from PySide6.QtCore import QObject, Signal

from src.observability.store import ObservabilityStore

logger = logging.getLogger(__name__)

# Maximum number of ticks to pull from the store in a single query when
# aggregating candles from the local tape.
_MAX_TAPE_TICKS = 50_000


class ChartDataProvider(QObject):
    """Aggregates market_tape ticks into OHLCV candles.

    All ``load_*`` methods are **synchronous** and should be called from a
    worker / background thread.  Results are delivered via Qt signals that
    are safe to connect to main-thread widgets.
    """

    candles_ready = Signal(object)   # pandas.DataFrame with OHLCV columns
    candles_error = Signal(str)      # human-readable error message

    def __init__(self, store: ObservabilityStore) -> None:
        super().__init__()
        self._store = store
        # Simple in-memory cache keyed by (symbol, tf_minutes, start, end, run_id)
        self._cache: dict[tuple, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # From local observability tape
    # ------------------------------------------------------------------

    def load_candles(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        timeframe_minutes: int = 5,
        run_id: Optional[str] = None,
    ) -> None:
        """Query ``market_tape`` and resample into OHLCV candles.

        Parameters
        ----------
        symbol:
            Contract symbol (e.g. ``"ES"``).
        start_time, end_time:
            UTC-aware time range to query.
        timeframe_minutes:
            Candle period in minutes (default 5).
        run_id:
            Optional run_id filter for the tape query.
        """
        cache_key = (symbol, timeframe_minutes, start_time, end_time, run_id)
        if cache_key in self._cache:
            self.candles_ready.emit(self._cache[cache_key].copy())
            return

        try:
            ticks = self._store.query_market_tape(
                limit=_MAX_TAPE_TICKS,
                run_id=run_id,
                symbol=symbol,
                ascending=True,
                start_time=start_time,
                end_time=end_time,
            )

            if not ticks:
                self.candles_ready.emit(pd.DataFrame())
                return

            df = self._ticks_to_candles(ticks, timeframe_minutes)
            self._cache[cache_key] = df
            self.candles_ready.emit(df.copy())

        except Exception as exc:
            msg = f"Failed to build candles from tape: {exc}"
            logger.exception(msg)
            self.candles_error.emit(msg)

    # ------------------------------------------------------------------
    # From TopstepX history API
    # ------------------------------------------------------------------

    def load_candles_from_api(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        unit_number: int = 5,
    ) -> None:
        """Fetch OHLCV bars from the TopstepX history API.

        Parameters
        ----------
        symbol:
            Contract symbol (e.g. ``"ES"``).
        start_time, end_time:
            UTC-aware time range.
        unit_number:
            Bar granularity in minutes (default 5).
        """
        try:
            from src.market import get_client

            client = get_client()
            raw_bars: list[dict[str, Any]] = client.retrieve_bars(
                symbol,
                start_time=start_time,
                end_time=end_time,
                unit="minute",
                unit_number=max(int(unit_number), 1),
            )

            if not raw_bars:
                self.candles_ready.emit(pd.DataFrame())
                return

            df = self._bars_to_dataframe(raw_bars)
            self.candles_ready.emit(df)

        except Exception as exc:
            msg = f"Failed to fetch bars from API: {exc}"
            logger.exception(msg)
            self.candles_error.emit(msg)

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def clear_cache(self) -> None:
        """Drop the in-memory candle cache."""
        self._cache.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ticks_to_candles(
        ticks: list[dict[str, Any]],
        timeframe_minutes: int,
    ) -> pd.DataFrame:
        """Resample tick-level rows into OHLCV candles.

        Each tick dict is expected to contain at least ``captured_at``
        (or ``timestamp``) and ``last`` (trade price).  ``volume`` is
        used when present.
        """
        records: list[dict[str, Any]] = []
        for tick in ticks:
            # Determine timestamp -- the store returns ``captured_at``
            ts_raw = tick.get("captured_at") or tick.get("timestamp")
            if ts_raw is None:
                continue
            if isinstance(ts_raw, str):
                ts = pd.Timestamp(ts_raw, tz="UTC")
            elif isinstance(ts_raw, datetime):
                ts = pd.Timestamp(ts_raw, tz=ts_raw.tzinfo or timezone.utc)
            else:
                ts = pd.Timestamp(ts_raw)

            price = tick.get("last") or tick.get("close") or tick.get("bid") or 0.0
            if not price or float(price) <= 0:
                continue

            records.append({
                "timestamp": ts,
                "price": float(price),
                "volume": int(tick.get("volume") or tick.get("last_size") or 0),
            })

        if not records:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.set_index("timestamp").sort_index()

        freq = f"{max(int(timeframe_minutes), 1)}min"
        ohlcv = df["price"].resample(freq).agg(
            open="first",
            high="max",
            low="min",
            close="last",
        )
        vol = df["volume"].resample(freq).sum()
        ohlcv["volume"] = vol
        ohlcv = ohlcv.dropna(subset=["open"])
        return ohlcv

    @staticmethod
    def _bars_to_dataframe(bars: list[dict[str, Any]]) -> pd.DataFrame:
        """Convert normalised API bar dicts to a pandas DataFrame.

        The bar dicts are produced by
        :meth:`TopstepClient.retrieve_bars` and have keys
        ``time``, ``open``, ``high``, ``low``, ``close``, ``volume``.
        """
        if not bars:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])

        df = pd.DataFrame(bars)

        # Normalise the time column
        time_col = "time" if "time" in df.columns else "timestamp"
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
        df = df.set_index(time_col).sort_index()

        # Keep only canonical OHLCV columns
        for col in ("open", "high", "low", "close", "volume"):
            if col not in df.columns:
                df[col] = 0.0
        df = df[["open", "high", "low", "close", "volume"]]
        df = df.astype({
            "open": float,
            "high": float,
            "low": float,
            "close": float,
            "volume": int,
        })
        return df
