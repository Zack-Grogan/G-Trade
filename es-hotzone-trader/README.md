# ES Hot-Zone Trader

CLI-based day trading system for ES hot zones. Execution and Topstep API run locally. The current launch cut is local-first: the CLI and local Flask console are the operator surfaces, and Railway telemetry is disabled by default unless you explicitly re-enable it.

## Operator interface

The only operator interface is the **CLI** (no TUI). From the project root:

- `es-trade` — show help and commands
- `es-trade start` — start the trading engine (live) and the local Flask console
- `es-trade stop` / `es-trade restart` — lifecycle
- `es-trade status` — one-screen status (running, zone, position, PnL, risk)
- `es-trade debug` / `es-trade events` / `es-trade config` / `es-trade balance` / `es-trade health` / `es-trade replay <path>`
- `es-trade broker-truth --focus-timestamp <iso>` — inspect selected-account broker truth, open orders, recent order history, and contradiction flags
- `es-trade analyze regime-packet|trade-review|launch-readiness` — build the local regime packet, review a single trade, or check launch defaults from SQLite and broker truth
- `es-trade service install|uninstall|start|stop|restart|status|logs|doctor` — manage the local `launchd` wrapper and inspect runtime health
- `es-trade db runs|events|snapshots|bridge-health|logs|account-trades|sync-account-trades|replay-missing` — inspect the local SQLite durability store, review broker account trade history, sync broker trades into durability, and rebuild missing outbox payloads

Default local ports:
- `31380` — health endpoint
- `31381` — local Flask console and debug JSON

See the repo **docs/** for full operator and architecture docs:

- [docs/OPERATOR.md](../docs/OPERATOR.md) — commands, local console, compliance
- [docs/Architecture-Overview.md](../docs/Architecture-Overview.md) — what runs where, data flow, Railway services
- [docs/Compliance-Boundaries.md](../docs/Compliance-Boundaries.md) — Topstep/CME boundaries and pre-migration gate

## Layout

- **`src/cli/`** — CLI commands and entrypoint
- **`src/engine/`** — Trading engine, strategy, reconciliation
- **`src/execution/`** — Order executor
- **`src/market/`** — Topstep client (market data, orders, positions)
- **`src/observability/`** — SQLite store (events, runs, completed trades, account trade history, snapshots, bridge health, runtime logs)
- **`src/bridge/`** — Data bridge and outbox (Mac → Railway ingest)
- **`src/server/`** — Local Flask operator console plus `/health` and `/debug` JSON; MCP is legacy/optional and not part of the local launch cut
- **`config/default.yaml`** — Default configuration

## Railway

Cloud services still live in the repo under **railway/** (ingest, analytics, mcp, rlm, web), but they are not required for the Monday launch cut. Keep them only if you intentionally want cloud telemetry or cloud review.

If you re-enable the bridge later, set `observability.railway_ingest_url` plus `observability.internal_api_token` (or env `GTRADE_INTERNAL_API_TOKEN`) so the local bridge can send data.

Account-aware durability is now first-class:

- local run manifests, state snapshots, and completed trades persist `account_id`, `account_name`, and practice/live mode
- broker account trade history can be synced into local SQLite and shipped to Railway as `account_trades`
- startup can optionally sync recent broker account history with `observability.sync_account_trade_history_on_startup`
- launch defaults favor `Pre-Open` live, later zones shadow-only, and a morning session exit policy with a `10:00` PT checkpoint and `11:30` PT hard-flat
