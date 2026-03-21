# `es-trade replay-topstep` — deprecated / not validated

**Status:** **Stale.** Kept in the codebase for occasional smoke tests only. **Do not use** this path to justify strategy changes, thresholds, or “production readiness.”

## Why

- Historical data from the Topstep/ProjectX **bar** API is **OHLCV aggregates only**. There is **no** historical best bid/offer or tick stream through this integration.
- The engine therefore uses **synthetic** BBO (minimal spread around the close) and **coarse** microstructure updates (effectively once per minute). That is **not** comparable to live `GatewayQuote` + trade flow.
- **Validated research** for hold times, edge around Pre-Open, and execution realism should use:
  - **`es-trade replay`** with SQLite **`market_tape`** (captured live BBO/trades), or
  - **`es-trade replay --path`** with a file you trust,  
  until/unless **paid** historical tick or L2 data is integrated.

## What still runs

The CLI command `replay-topstep` and `ReplayRunner.run_from_topstep()` remain **callable**. They emit **deprecation warnings** in logs and on stderr. Observability events (`replay_topstep_completed` / `replay_topstep_failed`) are unchanged for continuity.

## For AI agents and contributors

- Treat **`replay-topstep` as non-authoritative** for backtests and tuning.
- Do **not** recommend it as the default way to “generate trades for analysis” — prefer tape replay after a live or paper session that recorded `market_tape`.
- If you change the implementation, keep warnings and this doc in sync.

## Related

- [../Current-State.md](../Current-State.md) — replay fidelity notes  
- [../OPERATOR.md](../OPERATOR.md) — supported replay modes  
