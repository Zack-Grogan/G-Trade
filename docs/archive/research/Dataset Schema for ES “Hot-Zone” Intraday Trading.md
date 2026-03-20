# Research Dataset Schema for ES “Hot-Zone” Intraday Trading

To support sophisticated intraday quant research (baseline strategies, regime labeling, event studies, execution modeling, etc.) on ES futures, the data model should cleanly separate raw market feeds, derived features, and trade actions. Key tables include:

- **Instrument/Reference Tables:** e.g. `instruments` (instrument_id, symbol, details like tick size, currency), `venues` (exchange info), and optionally `strategies` (strategy_id, description).  
- **Market Data Tables:** raw tick/trade data, bar/interval data, best-bid/offer snapshots, and order-book depth. These store time-stamped price/volume information.  
- **Event Tables:** e.g. `event_calendar` (macro/corporate events with date/time, type, description).  
- **Hot-Zone Definitions:** table of named time windows (`hot_zone_id`, start_time, end_time, parent_zone_id for nesting, etc.).  
- **Regime Labels:** `regimes` mapping time ranges to market regimes (regime_id, start_time, end_time, regime_label).  
- **Signals Table:** records model outputs (`signal_id`, timestamp, instrument, model_id/module, direction/size, etc.).  
- **Orders Table:** orders placed by the system (`order_id`, signal_id or strategy_id, timestamp_submitted, instrument, side, type, limit_price, quantity, etc.).  
- **Fills Table:** actual executions (`fill_id`, order_id, timestamp_filled, price, quantity, fill_type).  
- **Trades/Positions Table:** aggregated trades or position lifecycles (`trade_id`, entry_order_id, exit_order_id, entry_time/price, exit_time/price, quantity, realized_PnL, etc.).  
- **Execution Diagnostics:** e.g. `slippage_metrics` or `execution_logs` linking to orders/fills (order_id, metric_name, metric_value, timestamp) to record slippage, realized spread, or fill probabilities.  

This core schema cleanly isolates raw market data from derived signals/orders and from performance metrics, facilitating reproducibility and analysis by zone/regime/module.

## Table Schemas (Fields, Keys, Timestamps)

**Bar Data (`bar_data`):** Stores regular-interval bars (e.g. 1-min or 5-min). Columns: `(instrument_id, period_start UTC timestamp as PK, open, high, low, close, volume, trade_count, vwap, etc.)`. Primary key is (instrument_id, period_start). All times in UTC (see below).  

**Tick/Trade Data (`tick_data` or `trades_raw`):** Each row is one trade. Columns: `(instrument_id, tick_time UTC, price, quantity, trade_id, exchange_seq, side/aggressor_flag)`. PK could be (instrument_id, tick_time, trade_id). Use exchange timestamps if available, normalized to UTC【31†L188-L190】.

**Best-Bid/Offer Snapshots (`bbo_snapshots`):** Top-of-book quotes over time. Columns: `(instrument_id, snapshot_time UTC, bid_price, bid_size, ask_price, ask_size)`. PK: (instrument_id, snapshot_time). These are often captured at regular ticks or on quote updates.

**Orderbook Depth/Book Summary (`orderbook_snapshots`):** Level-N book data. For example, N=5 levels: `(instrument_id, snapshot_time UTC, bid_price1, bid_size1, … bid_priceN, bid_sizeN, ask_price1, ask_size1, … ask_priceN, ask_sizeN)`. PK: (instrument_id, snapshot_time). This lets one reconstruct liquidity and depth for execution modeling【23†L151-L159】.

**Event Calendar (`events`):** Economic or news events. Columns: `(event_id PK, event_time UTC, event_type (e.g. FOMC, NFP, holiday), description, importance, region)`. Use event_time in UTC or local market time as long as normalized. Include attributes (impact rating, data values) as needed.

**Hot-Zone Definitions (`hot_zones`):** Named time windows per trading day. Columns: `(zone_id PK, zone_name, start_time (as “time-of-day”), end_time, parent_zone_id NULLable, description)`. For example, “6:30–8:30 CT” and “12:45–1:00 CT” (with parent=“12:00–1:00”). Represent nested windows by parent_zone_id or an “is_subzone” flag. Store times relative to session or daily calendar (e.g. as offset from session start).

**Regime Labels (`regimes`):** Market regimes assigned over time. Columns: `(regime_id PK, instrument_id, regime_label (string or code), start_time UTC, end_time UTC, method, notes)`. PK: (instrument_id, start_time). These records link periods to regimes for analysis.

**Strategy Signals (`signals`):** Generated trade signals. Columns: `(signal_id PK, strategy_id/module, instrument_id, signal_time UTC (signal generation time), signal_type, side (long/short), quantity or weight, confidence, expiry_time)`. Key = signal_id (or composite (strategy_id, signal_time)). Timestamps mark when signal is first available to the system.

**Orders (`orders`):** Orders sent to market. Columns: `(order_id PK, signal_id FK, instrument_id, order_time UTC (submission time), side, order_type (market/limit), limit_price, quantity, tif (time-in-force), status, version)`. PK: order_id. Include foreign-key linking to the originating signal or strategy. 

**Fills (`fills`):** Executed fills for orders. Columns: `(fill_id PK, order_id FK, fill_time UTC, fill_price, fill_quantity)`. PK: fill_id (or composite (order_id, fill_sequence)). This captures how each order was filled (possibly multiple partial fills).

**Trades/Positions (`trades`):** Completed round-trip trades or positions. Columns: `(trade_id PK, entry_order_id FK, exit_order_id FK, instrument_id, entry_time UTC, exit_time UTC, entry_price, exit_price, quantity, pnl, realized_commission, strategy_id)`. PK: trade_id. Optionally include fields for fees, slippage metrics, and referencing the zone_id/regime_id (see below).

**Slippage/Execution Diagnostics (`execution_logs` or `slippage_metrics`):** Metrics for each order/trade. Columns: `(log_id PK, order_id or trade_id FK, log_time UTC, metric_name (e.g. “realized_spread”), metric_value, details)`. Alternatively, include slippage fields directly on fills/trades (e.g. expected_price vs actual, slippage), but a separate table allows multiple metrics per order/trade. 

All tables should include **instrument_id** and **UTC timestamps** as keys. Use consistent timestamp source across tables (e.g. exchange timestamp field) to avoid alignment issues【34†L354-L363】. Primary keys typically combine instrument and time; for events/orders/trades use surrogate IDs. For example, bar_data’s PK is (instrument, bar_start_time), tick_data’s PK (instrument, tick_time, trade_id), bbo_snapshots PK (instrument, timestamp). Foreign keys link signals→orders, orders→fills, signals→regimes/zones (via lookup).

## Timezone Handling and Session Anchors

Store all timestamps in a single normalized zone (preferably UTC) to avoid confusion【31†L188-L190】. Ingest raw data (often in exchange local time) and convert to UTC immediately. Also record the exchange’s local session date to allow grouping by trading day (e.g. ES “calendar_date” anchored at 4:00 PM CT). Define **session anchors** such as daily open/close or official start-of-day for clarity. For instance, one can define session_date (the trade day) as the date of the prior afternoon session, and record session-relative times. This ensures windows like 9:30 ET (open) are anchored correctly each day. Normalization to UTC and use of session_date prevents time-zone ambiguity and mixing of dates【31†L188-L190】.

All tables with time data should use these normalized times. For example, a trade at 10:05 CT would be stored as 15:05 UTC (assuming CDT). Use consistent timestamp fields (e.g. `timestamp_exchange` for market time, `timestamp_received` if needed for feed latency) but do analysis on `timestamp_exchange`. As CoinAPI notes, mixing different timestamp sources breaks alignment【34†L354-L363】. Use the same time reference (e.g. `timestamp_exchange`) across tick, BBO, orderbook, etc.

## Representing Nested Trading Windows

Define each hot-zone as a separate entry in `hot_zones`. To represent nested windows (e.g. 12:45–1:00 inside 12:00–1:00), include a **parent_zone_id** field. For example:
- zone_id=10: name=”Afternoon”, start=12:00, end=13:00, parent=NULL  
- zone_id=11: name=”Afternoon Peak”, start=12:45, end=13:00, parent=10.  
You can also add a Boolean flag `is_subzone`. Then, when tagging data or trades with zones, an entry at 12:50 would pick zone_id=10 and subzone=11. This relational approach avoids overlap confusion. A careful key might be (instrument, start_time, end_time) unique.

## Features: Precomputed vs On-Demand

Store **static or heavy features** offline and **compute real-time features on demand**. Precompute features that depend only on historical market data (e.g. intraday volatility, moving averages, volume imbalances, regime probabilities) and store them in a “features” table keyed by time. For example, a `features` table could have columns (instrument_id, timestamp, feature1, feature2, …). This accelerates backtests and avoids recomputation. Use columnar formats (Parquet) for such time-series feature tables【34†L331-L336】. 

On the other hand, generate features that require current tick-level or external data on the fly during simulation. These include real-time order-flow signals, live imbalance ratios, or features derived from concurrent multi-asset data. Also, ad hoc features for event studies or sentiment likely come from join queries at analysis time. In summary: **Precompute** heavy, purely historical indicators; **compute on demand** anything that depends on live event context or cross-entity correlation. This division helps prevent hidden leakage because precomputed features are fixed snapshots of history, whereas on-demand features use only data available up to the analysis timestamp.

## Minimum Viable vs Ideal Dataset

- **Minimum Viable Dataset:** At minimum, capture 1-minute bars (or tick trades) and top-of-book quotes, plus time and volume. For execution fidelity, at least store tick trades and best-bid/ask quotes. Also include the key hot-zone definitions and a simple economic calendar. This allows basic backtesting and cost-estimation. Without full depth, assume constant spread or simple VWAP fills.  

- **Ideal Dataset:** Include *both* full tick trades *and* detailed order-book snapshots (multi-level), plus a comprehensive event calendar. High-granularity features (trade-side, order IDs) enable realistic slippage modeling. The ideal set has (a) tick-level trade data, (b) full-depth LOB snapshots, (c) enriched corporate/macro event streams, and (d) reference tables (holidays, symbol mappings). As one practitioner notes: “Backtesting on 1-minute candles is fine — until you care about fills. Then it’s worthless”【34†L286-L294】. In other words, for true execution and slippage analysis, tick and book data are needed. For regime labeling and signals, finer data (tick or at least 1-min bars with sufficient history) is highly desirable. Overall, the ideal dataset is a superset of the minimum: raw trade ticks + quotes + depth + features + events.

## Data Partitioning, Walk-Forward, and Leakage Prevention

Organize data by time to facilitate walk-forward testing. Partition tables by date or hour (e.g. by trading day) to speed queries【34†L333-L339】. For example, store each day’s data in a separate partition or file. Maintain a `calendar_date` column (market date) in all tables for joining across data types on the same day. This allows sliding-window backtests: one can easily select a contiguous block of days for training and the next block for testing. Use incremental versions (e.g. month or year) for archiving old data.

To minimize lookahead and ensure realistic simulation, **use bitemporal data management**: record both *effective* (market) time and *system* (load) time, and always query features as-of the decision time. As LuxAlgo advises, “employ bitemporal data systems to ensure only data available at the time is used”【44†L204-L213】. In practice, this means:
- When generating signals or orders, restrict all feature queries to data with timestamp < current_time (use strict “less than”).  
- Ensure events or regimes are labeled only up to the lookahead cutoff.  
- Clearly separate tables: raw market prices for *day T* should not leak values from *T+1*.

For walk-forward ease, include a `test_flag` or version columns in the metadata to delineate in-sample vs out-of-sample periods. Always rebuild features per period without mixing future info. For example, when backtesting January 2025 data, do not preload any March 2025 moves into January features. Use rigorous time-based joins rather than row-number indexes.

Post-trade attribution by zone/regime/module/execution: each trade record should include foreign-keys linking to the zone (`zone_id`), regime (`regime_id`), strategy/module, and execution type (market/limit). This enables slicing PnL by hot-zone or market regime in analysis. For instance, add `entry_zone`, `exit_zone`, `entry_regime`, `exit_regime`, and `execution_type` fields to the trades table.

## Naming Conventions and Versioning

Use clear, consistent naming. We recommend **snake_case** for table and column names (e.g. `bar_data`, `tick_time`, `order_id`). Prefix tables by domain (e.g. `market_`, `strategy_`) if helpful. Include units in column names where ambiguous (e.g. `price`, `size`). Keep names meaningful and avoid cryptic codes【42†L1-L4】. For example: use `signal_id` and `order_id` rather than generic `id1`, `id2`.

Versioning: maintain a dataset or metadata table that records schema version, data date-range, and source version (e.g. vendor or code revision) for each table. When making schema changes (e.g. adding a column), either migrate in place with new version tags or create a new table suffixed with `_v2`. Document column definitions and changes in a data dictionary. Store creation/modification timestamps on each table. Also version trading signals and strategies (e.g. `strategy_version`) so you can replicate past backtests. A naming pattern like `trades_v1`, `trades_v2` or a date suffix can help trace back which schema was used. The key is consistency: once a naming scheme is chosen, use it everywhere and never rename tables without schema migration.

## Common Pitfalls to Avoid

Quant-data modeling errors often ruin research. Key anti-patterns include:
- **Timezone mismatches:** Forgetting to normalize timestamps across data sources leads to misaligned bars and orders. Always use a single timezone (UTC) for all tables【31†L188-L190】.  
- **Lookahead bias:** Including future info (e.g. using tomorrow’s open/close to compute today’s signals) will fake performance. As one analysis warns, relying on next-day prices at previous close “introduces [lookahead] bias and inflates performance”【39†L175-L183】. Prevent this by strictly filtering queries by current timestamp (bitemporal joins)【44†L204-L213】.  
- **Data gaps:** Treat missing data as market reality, not an error to be patched without consideration. “Don’t ignore data gaps – they represent real market conditions”【34†L436-L444】. If your data feed has outages or rollovers, record them (via nulls or flags) rather than silently interpolating, and reflect that in signal validity.  
- **Inconsistent schema:** Mixing raw and normalized fields, or inconsistent symbols, breaks reproducibility. As noted, maintain “unified schema across all venues” and “normalized symbol mappings”【34†L310-L315】 so queries mean the same thing day to day.  
- **Lack of unique keys:** Without proper keys (e.g. order_id, trade_id), you can’t reliably link signals→orders→fills. That destroys traceability.  
- **Ignoring execution costs:** Modeling orders without realistic slippage/spread leads to overfitting. Capture fill details and fees explicitly. As a rule, add estimated spread buffers and execution delays if market data isn’t perfect.  
- **Over-normalization of market data:** Stripping needed fields from raw feeds can hide latency or quote origin. Retain timestamps and sequence IDs from the exchange for debugging.  
- **Not versioning data:** Changing a table schema or signal logic without version control makes past results irreproducible. Always tag data with schema and strategy versions.  

In summary, a good data model for quant research is concrete and auditable: every signal must trace to source data and execution. By carefully structuring tables with clear keys, normalized times, and separate layers for raw vs derived data, we prevent hidden leakage and ensure walk-forward tests and post-trade attribution can be done by zone, regime, model, and execution type【34†L310-L315】【39†L175-L183】. 

**Sources:** Best practices from quantitative data engineering【31†L188-L190】【34†L310-L315】【39†L175-L183】【44†L204-L213】 (industry guides and trading analytics blogs) informed these schema designs.