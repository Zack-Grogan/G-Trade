"""Load persisted SQLite market_tape rows for historical replay."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterator, Optional

import pandas as pd

from src.market import MarketData


def _coerce_ts(value: Any) -> datetime:
    if value is None:
        return datetime.now(UTC)
    if isinstance(value, datetime):
        return value
    return pd.Timestamp(value).to_pydatetime(warn=False)


def market_data_from_tape_row(row: dict[str, Any]) -> MarketData:
    """Map a row from `ObservabilityStore.query_market_tape` to `MarketData`."""
    payload = row.get("payload") or {}
    ts = _coerce_ts(row.get("captured_at") or row.get("inserted_at") or payload.get("timestamp"))

    bid = float(row["bid"]) if row.get("bid") is not None else 0.0
    ask = float(row["ask"]) if row.get("ask") is not None else 0.0
    last = float(row["last"]) if row.get("last") is not None else 0.0

    vol = row.get("volume")
    volume = int(vol) if vol is not None else int(payload.get("volume") or 0)

    vic = row.get("volume_is_cumulative")
    if vic is None:
        vic = bool(payload.get("volume_is_cumulative", True))
    else:
        vic = bool(vic)

    qsyn = row.get("quote_is_synthetic")
    if qsyn is None:
        qsyn = bool(payload.get("quote_is_synthetic", False))
    else:
        qsyn = bool(qsyn)

    symbol = str(row.get("symbol") or payload.get("symbol") or "ES")

    return MarketData(
        symbol=symbol,
        bid=bid,
        ask=ask,
        last=last,
        volume=volume,
        volume_is_cumulative=vic,
        quote_is_synthetic=qsyn,
        bid_size=float(row.get("bid_size") or 0.0),
        ask_size=float(row.get("ask_size") or 0.0),
        last_size=float(row.get("last_size") or 0.0),
        trade_side=str(row.get("trade_side") or payload.get("trade_side") or ""),
        latency_ms=int(row.get("latency_ms") or 0),
        timestamp=ts,
    )


def iter_tape_rows(
    store: Any,
    *,
    batch_size: int,
    run_id: Optional[str] = None,
    start_time: Optional[datetime | str] = None,
    end_time: Optional[datetime | str] = None,
    symbol: Optional[str] = None,
    sources: Optional[list[str]] = None,
) -> Iterator[dict[str, Any]]:
    """Yield market_tape rows in `id` order using keyset pagination."""
    after_id: Optional[int] = None
    while True:
        rows = store.query_market_tape(
            limit=max(int(batch_size), 1),
            after_id=after_id,
            ascending=True,
            run_id=run_id,
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
            sources=sources,
        )
        if not rows:
            break
        for row in rows:
            rid = row.get("id")
            if rid is not None:
                after_id = int(rid)
            yield row
        if len(rows) < batch_size:
            break
