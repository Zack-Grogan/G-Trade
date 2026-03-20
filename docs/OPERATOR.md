# Operator guide — CLI and local SQLite

The primary operator interface is the **CLI**. There is no TUI and no local HTTP console. Runtime truth for a running trader is available via CLI commands and SQLite (`logs/observability.db`, `logs/runtime/runtime_status.json`). For a high-level picture of what runs where and how data flows, see [Architecture-Overview.md](Architecture-Overview.md).

## Commands

- `es-trade` (no args) — shows help and available commands.
- `es-trade start` — start the trading engine (live).
- `es-trade stop` — request clean stop.
- `es-trade restart` — clean restart.
- `es-trade status` — one-screen status (running, zone, position, PnL, risk). Uses SQLite state snapshots when inspecting a **separate** trader process.
- `es-trade debug` — full debug state (JSON), with `_runtime_state_source` indicating `in_process`, `sqlite`, or `status_file`.
- `es-trade broker-truth --focus-timestamp <iso>` — selected-account broker truth, recent broker order/trade history, and contradiction diagnostics.
- `es-trade analyze regime-packet|trade-review|launch-readiness` — local research, broker-truth checks, and launch-readiness output from SQLite plus runtime context.
- `es-trade events` — query observability events (same SQLite `events` table as `es-trade db events`; use `--run-id` to scope one process run).
- `es-trade service install|uninstall|start|stop|restart|status|logs|doctor` — manage the local `launchd` wrapper and inspect local runtime health.
- `es-trade db runs|events|snapshots|bridge-health|logs` — inspect local SQLite durability (including historical bridge-health rows from archived integrations).
- `es-trade config` — show configuration.
- `es-trade balance` — show Topstep account balance.
- `es-trade health` — health check (same sources as `status`).
- `es-trade replay <path>` — replay from file.

## Runtime inspection (no HTTP)

- **Same process:** `status` / `health` / `debug` read in-process `TradingState`.
- **Another process:** use the same commands; the CLI loads the latest **state snapshot** from SQLite for the run id in `logs/runtime/runtime_status.json`, or falls back to fields from that JSON if the snapshot has not been written yet.

## Local text-to-speech (optional)

On macOS, the engine can announce order lifecycle events using the system `say` command (fully local, no network). Enable in `config/default.yaml` or your override under `operator_tts` (`enabled: true`). Configure `voice` / `rate` per `man say`, limit the queue with `max_queue`, and restrict which events speak via `events` (`filled`, `partially_filled`, `rejected`, `cancelled`, `submit_failed`, `realized_pnl`). When `realized_pnl` is enabled, closing a position (risk-manager completed trade) speaks realized profit or loss in dollars and, if `include_trade_time_in_speech` is true, the exit time in your configured hot-zone timezone (e.g. “A profit of 1,200 dollars at 3:45 PM.”). By default TTS is off and does not run in replay/mock mode unless `speak_in_mock_mode` is true.

## Observability contract

Canonical rules for categories, decision outcomes, correlation IDs, and streams: [Observability-Contract.md](Observability-Contract.md). Code constants live in `src/observability/taxonomy.py`.

## Local-only workflow

The active operator workflow is local-only:

- use the CLI for service control, analysis, and broker truth
- use SQLite as the durable source of truth

## Launch posture

- **Live entries:** `Pre-Open` and `Outside` are live by default (see `strategy.live_entry_zones` in config).
- **Shadow-only zones:** `Post-Open` and `Midday` still score and log without live entries until promoted. Launch-gate behavior is config-driven only (not tied to practice vs live); set `PREFERRED_ACCOUNT_ID` to the account you intend to trade.
- **Market-hours guard:** signal evaluation and logging keep running, but new entry submission is blocked during configured closed windows (daily maintenance/weekend/holiday overrides). Broker outside-hours rejections remain as fallback telemetry.
- **Session exit:** morning entries are capped by the configured session exit policy, with a checkpoint at `10:00` PT and a hard-flat time at `11:30` PT.
- **Contracts:** the live launch posture remains `1` contract until the morning edge is reviewed forward and the trade tracking is clean.

## Development flow (back to coding)

Linear is the source of "what to do next" (G-Trade project, issues GDG-214–221). To resume development:

1. **Pick an issue** — Start with the one In Progress (e.g. GDG-215 E2E validation) or move another from Backlog to In Progress via Linear.
2. **Branch** — Work from this repo (`G-Trade`) for runtime, docs, and tooling changes: e.g. `feat/GDG-215-e2e-validation`. Use GDG prefix; see [engineering-system/linear-workflow.md](engineering-system/linear-workflow.md).
3. **Implement** — Follow [.cursor/skills/issue-to-pr/SKILL.md](../.cursor/skills/issue-to-pr/SKILL.md): read issue and AGENTS.md, implement, run tests, update docs if behavior or config changed.
4. **Commit and PR** — Commit with issue ref in message; open PR with template and link to Linear issue. See [engineering-system/github-workflow.md](engineering-system/github-workflow.md).
5. **Close the loop** — When PR is merged, move the Linear issue to Done; optionally update [Tasks.md](Tasks.md) if that item is listed there.

## Compliance

See [Compliance-Boundaries.md](Compliance-Boundaries.md) and the state-reset section in [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md).
