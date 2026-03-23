# Operator guide — CLI and local SQLite

The primary operator interface is the **CLI**. There is no TUI and no local HTTP console. Runtime truth for a running trader is available via CLI commands and SQLite (`logs/observability.db`, `logs/runtime/runtime_status.json`). For a high-level picture of what runs where and how data flows, see [Architecture-Overview.md](Architecture-Overview.md).

## Commands

- `es-trade` (no args) — shows help and available commands.
- `es-trade start` — start the trading engine (practice by default; add `--live` to select the live account).
- `es-trade stop` — request clean stop.
- `es-trade emergency-halt` — create/refresh the file-backed emergency halt flag (`event_provider.emergency_halt_path`); the running engine treats it as blackout on the next calendar refresh (see `event_provider.refresh_seconds`) and will flatten open risk per `RiskManager` rules. Remove the file or let it age past `emergency_halt_max_age_minutes` to clear. Prefer this plus `es-trade stop` and a broker-side position check over relying on the flag alone.
- `es-trade restart` — clean restart.
- `es-trade status` — one-screen status (running, tenant, zone, position, PnL, risk). Uses SQLite state snapshots when inspecting a **separate** trader process.
- `es-trade debug` — full debug state (JSON), with `_runtime_state_source` indicating `in_process`, `sqlite`, or `status_file`, and `tenant_id` included in the payload.
- `es-trade broker-truth --focus-timestamp <iso>` — selected-account broker truth, recent broker order/trade history, and contradiction diagnostics.
- `es-trade analyze regime-packet|trade-review|launch-readiness` — local research, broker-truth checks, and launch-readiness output from SQLite plus runtime context.
- `es-trade events` — query observability events (same SQLite `events` table as `es-trade db events`; use `--run-id` to scope one process run).
- `es-trade service install|uninstall|start|stop|restart|status|logs|doctor` — manage the local `launchd` wrapper and inspect local runtime health.
- `es-trade db runs|events|snapshots|export-tape|bridge-health|logs` — inspect local SQLite durability (including historical bridge-health rows from archived integrations). `export-tape` writes `market_tape` rows as JSONL for cold backup (use `--out`; long archives may require raising `observability.retention_days` in config).
- `es-trade config` — show configuration, including the active `tenant_id`.
- `es-trade balance` — show Topstep account balance.
- `es-trade health` — health check (same sources as `status`).
- `es-trade replay` — replay through the engine: **file:** `--path` (CSV/JSONL); **captured market tape:** `--tape-run-id` (replay ticks from a prior live run’s `market_tape` rows) or `--tape-start` / `--tape-end` (ISO range) with optional `--tape-symbol` / `--tape-source` (comma-separated, e.g. `GatewayQuote,GatewayTrade`). Optional `--paired-live-run-id` loads practice execution telemetry from that run’s state snapshots for promotion gates. **Preferred** for realistic microstructure vs minute bars.
- `es-trade replay-topstep` — **deprecated** (stale): minute OHLCV from the Topstep history API only; synthetic BBO; **not** a validated backtest path. Prefer tape or file replay. See [replay/replay-topstep-deprecated.md](replay/replay-topstep-deprecated.md).

## Runtime inspection (no HTTP)

- **Same process:** `status` / `health` / `debug` read in-process `TradingState`.
- **Another process:** use the same commands; the CLI loads the latest **state snapshot** from SQLite for the run id in `logs/runtime/runtime_status.json`, or falls back to fields from that JSON if the snapshot has not been written yet.

The CLI output is tenant-aware: `status`, `health`, `debug`, and `config` surface the active `tenant_id` so multiple local lanes can share the same repo without ambiguity.

## Local text-to-speech (optional)

On macOS, the engine can announce order lifecycle events using the system `say` command (fully local, no network). Enable in `config/default.yaml` or your override under `operator_tts` (`enabled: true`). Configure `voice` / `rate` per `man say`, limit the queue with `max_queue`, and restrict which events speak via `events` (`filled`, `partially_filled`, `rejected`, `cancelled`, `submit_failed`, `realized_pnl`). When `realized_pnl` is enabled, closing a position (risk-manager completed trade) speaks realized profit or loss in dollars and, if `include_trade_time_in_speech` is true, the exit time in your configured hot-zone timezone (e.g. “A profit of 1,200 dollars at 3:45 PM.”). By default TTS is off and does not run in replay/mock mode unless `speak_in_mock_mode` is true.

## Observability contract

Canonical rules for categories, decision outcomes, correlation IDs, and streams: [Observability-Contract.md](Observability-Contract.md). Code constants live in `src/observability/taxonomy.py`.

## Watchdog (`watchdog` in config)

- **`stale_order_seconds`:** Age-based cancellation applies to **non-protective** working orders (for example a stuck entry). **Protective** stop-loss and take-profit orders are **not** cancelled just because they are older than this threshold; they remain working until filled or replaced by the execution layer.
- **`protection_ack_seconds`:** If the engine requested protection but no protective orders are tracked locally for longer than this interval, the watchdog may trigger fail-safe. Keep it consistent with normal attach latency after fills.

## Local-only workflow

The active operator workflow is local-only:

- use the CLI for service control, analysis, and broker truth
- use SQLite as the durable source of truth

## Launch posture

- **Live entries:** Whichever zones are listed under `strategy.live_entry_zones` (default repo config is **Pre-Open** only).
- **Shadow-only zones:** Zones in `strategy.shadow_entry_zones` score and log without live entries until promoted to live. The default morning-first profile keeps `Post-Open`, `Midday`, and `Outside` shadow-only. Launch-gate behavior is config-driven: `PREFERRED_ACCOUNT_ID` selects the exact account, `--live` / `safety.prac_only: false` opt into the live account, and the shipped default sets `strategy.practice_shadow_trading_enabled: true` so the practice account keeps trading in shadow zones for mirror-style research.
- **Market-hours guard:** signal evaluation and logging keep running, but new entry submission is blocked during configured closed windows (daily maintenance/weekend/holiday overrides). Broker outside-hours rejections remain as fallback telemetry.
- **Session exit:** the configured morning session policy caps **live-zone positions** with a checkpoint flatten beginning at `10:00` PT and a hard-flat time at `11:30` PT. If a checkpoint flatten request is accepted but the position remains open, the engine may retry before hard-flat. Adopted or unknown-origin positions are also included as a safety fallback after restarts/broker adoption; “unknown” includes empty/missing `entry_zone` metadata. Explicitly non-live-tagged positions without adoption metadata are **not** forcibly session-flattened by this policy.
- **Contracts:** shipped `account.max_contracts` is `5` (hard cap); live size still follows risk manager, zone sizing, and `default_contracts`.

## Development flow (back to coding)

Linear is the source of "what to do next" (G-Trade project, issues GDG-214–221). To resume development:

1. **Pick an issue** — Start with the one In Progress (e.g. GDG-215 E2E validation) or move another from Backlog to In Progress via Linear.
2. **Branch** — Work from this repo (`G-Trade`) for runtime, docs, and tooling changes: e.g. `feat/GDG-215-e2e-validation`. Use GDG prefix; see [engineering-system/linear-workflow.md](engineering-system/linear-workflow.md).
3. **Implement** — Follow [.cursor/skills/issue-to-pr/SKILL.md](../.cursor/skills/issue-to-pr/SKILL.md): read issue and AGENTS.md, implement, run tests, update docs if behavior or config changed.
4. **Commit and PR** — Commit with issue ref in message; open PR with template and link to Linear issue. See [engineering-system/github-workflow.md](engineering-system/github-workflow.md).
5. **Close the loop** — When PR is merged, move the Linear issue to Done; optionally update [Tasks.md](Tasks.md) if that item is listed there.

## Emergency stop sequence

1. **`es-trade emergency-halt`** (optional `--reason`) — refreshes the halt file so the engine sees `manual_emergency_halt` on the next provider refresh.
2. **`es-trade stop`** — shut down the local process cleanly.
3. **Verify** — confirm flat position and working orders in Topstep (dashboard or `es-trade broker-truth`) if anything still looks open.

Implementation detail: [`src/engine/event_provider.py`](../src/engine/event_provider.py) (`LocalEventProvider.get_context`). Config: `event_provider.emergency_halt_path`, `emergency_halt_max_age_minutes`.

## Compliance

See [Compliance-Boundaries.md](Compliance-Boundaries.md), optional evaluation mirror notes in [risk/topstep-evaluation-mirror.md](risk/topstep-evaluation-mirror.md), and the state-reset section in [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md).
