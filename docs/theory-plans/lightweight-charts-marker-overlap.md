# Lightweight Charts Marker Overlap Bug Report

## Overview
The local `flask_console` chart (`http://localhost:31381/chart`) is currently experiencing severe rendering issues, specifically:
1. **Vertical Market Stacking**: "Broker fill" annotations (both green and red) are stacked directly on top of each other at the far-left edge of the chart (e.g., at index 0 / 21:00 UTC).
2. **Extreme Y-Axis Distortion**: Because the markers are stacked vertically, the chart attempts to keep all their labels visible, resulting in an artificially ballooned Y-Axis spanning from roughly `-2000` to `10000`, compressing actual price movement into a flat line.

## Root Causes

The core reason behind this issue stems from the interaction between G-Trade's data hydration methods and Native TradingView `Lightweight Charts` timeline enforcement.

### 1. Unordered Concatenation
In `src/server/flask_console.py`, the chart model constructs a list of markers by concatenating `completed_trades` and `account_trades`:
```python
markers = _trade_markers(list(reversed(completed_trades))) + _account_trade_markers(list(reversed(account_trades)))
```
Even if `completed_trades` and `account_trades` are individually reversed and sorted, concatenating them end-to-end creates an unsorted list where an `account_trade` from 10:00 AM may follow a `completed_trade` from 11:30 AM. **Lightweight Charts strictly requires the markers array to be perfectly sorted chronologically by `time`.**

### 2. Resolution alignment
`_trade_markers` and `_account_trade_markers` were extracting raw entry/exit seconds as the precise mathematical timestamp. Because the current charting instance groups market ticks into robust 1-minute `candles`, marker timestamps that deviate into individual intra-minute seconds occasionally fail to anchor properly against the unified TimeScale indices.

### 3. Out-Of-Bounds Snapping (Primary UI Destructor)
The `_build_chart_model` method uses dynamic scoping, meaning the `candles` array is bounded based on the `market_rows` query, which limits returned ticks:
```python
market_rows = _recent_market_rows(store, run_id=run_id, symbol=None, hours=8, limit=25000)
candles = _build_candles(market_rows)
```
Simultaneously, `account_trades` runs a generic limit loop that may reach out beyond the 8-hour window depending on how sparse the recent dataset is:
```python
account_trades = _canonical_account_trades(store.query_account_trades(limit=50, ascending=False, run_id=run_id))
```
**Vendor Constraint**: According to official issue trackers (#1459, #1874), Lightweight Charts markers *must* associate with an exact existing `candle` node on the timeline. If the array of `markers` includes historical fills whose timestamps are mathematically *before* the first available `candle[0].time` in the buffer, the engine natively collapses all of those orphaned markers onto `index 0`. To prevent the text collision that inherently incurs, it forcibly stacks their labels vertically, skyrocketing the Y-Axis ranges simply to make geographical UI room for the labels.

## Required Implementation Fix

To resolve this reliably in `src/server/flask_console.py`, three synchronous steps must occur right before the chart payload is returned:

1. **Bucket Align Timestamps:**
   Force all individual historical entry/exit timestamps to snap cleanly into 1-minute bucket times matching the base candles via module integer division.
   ```python
   # Inside _trade_markers & _account_trade_markers
   entry_time = _seconds(trade.get("entry_time"))
   bucket_time = (entry_time // 60) * 60
   ```

2. **Inline Array Sort:**
   Force an absolute chronological sort after concatenation.
   ```python
   markers.sort(key=lambda m: m.get("time", 0) if m.get("time") is not None else 0)
   ```

3. **Pre-Index Pruning:**
   Explicitly slice off any out-of-bounds historical trade markers that fall before the loaded `candles` buffer to prevent the library from defaulting their positions onto the 0-node.
   ```python
   if candles:
       first_candle_time = candles[0].get("time", 0)
       markers = [m for m in markers if m.get("time", 0) >= first_candle_time]
   ```

Applying the above directly resolves both the visual stacking anomaly and guarantees standard scaling compliance.
