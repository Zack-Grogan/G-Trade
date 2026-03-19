# Operator guide — CLI and local Flask console

The primary operator interfaces are the **CLI** and the **local Flask console**. There is no TUI. For a high-level picture of what runs where and how data flows, see [Architecture-Overview.md](Architecture-Overview.md).

## Commands

- `es-trade` (no args) — shows help and available commands.
- `es-trade start` — start the trading engine (live).
- `es-trade stop` — request clean stop.
- `es-trade restart` — clean restart.
- `es-trade status` — one-screen status (running, zone, position, PnL, risk).
- `es-trade debug` — full debug state (JSON).
- `es-trade broker-truth --focus-timestamp <iso>` — selected-account broker truth, recent broker order/trade history, and contradiction diagnostics.
- `es-trade analyze regime-packet|trade-review|launch-readiness` — local research and launch checks from SQLite plus broker-truth context.
- `es-trade events` — query observability events.
- `es-trade service install|uninstall|start|stop|restart|status|logs|doctor` — manage the local `launchd` wrapper and inspect local runtime/bridge health.
- `es-trade db runs|events|snapshots|bridge-health|logs|replay-missing` — inspect local SQLite durability and rebuild outbox work from local observability state.
- `es-trade config` — show configuration.
- `es-trade balance` — show Topstep account balance.
- `es-trade health` — health check.
- `es-trade replay <path>` — replay from file.

## Local Flask console

`es-trade start` brings up the trading engine and the local Flask console on the Mac. The console is the main browser-based operator surface for the current launch cut.

The console is local-only and serves these pages:
- `/` — console overview
- `/chart` — live chart and indicators
- `/trades` — local trade list and account-trade context
- `/trades/<id>` — trade review
- `/logs` — runtime and broker/order events
- `/system` — config, health, and launch readiness
- `/health` and `/debug` — JSON compatibility endpoints for the CLI and service checks

Default local ports are pinned to a high, memorable pair so they do not collide with typical dev services:
- `31380` — `/health`
- `31381` — console UI and `/debug`

On the console overview (`/`), **Trades today** and **Losses** use the local observability **broker ledger** (`account_trades` rows with realized P&L) for the current **America/Los_Angeles calendar day**, filtered to the active account when known. They are not the engine session risk counters (`trades_today` / `consecutive_losses` in `/debug`).

## Railway and MCP (legacy / optional)

Railway services still exist in the repository, but they are not required for the current Monday launch.

- The local bridge is disabled by default when `observability.railway_ingest_url` is empty.
- If you intentionally re-enable cloud telemetry later, set `observability.railway_ingest_url` and `observability.internal_api_token` (or `GTRADE_INTERNAL_API_TOKEN`) before starting the bridge.
- MCP remains a Railway-only path if you explicitly use it later; it is not part of the local launch workflow.
- The Railway web console, analytics, and MCP remain legacy tooling for archived or future cloud workflows, not the operator path for this cut.

## Launch posture

- **Live entries:** `Pre-Open` is live by default.
- **Shadow-only zones:** `Post-Open`, `Midday`, and `Outside` still score and log, but they do not place live entries in the launch cut.
- **Session exit:** morning entries are capped by the configured session exit policy, with a checkpoint at `10:00` PT and a hard-flat time at `11:30` PT.
- **Bridge:** disabled by default unless you explicitly configure Railway ingestion.
- **Contracts:** the live launch posture remains `1` contract until the morning edge is reviewed forward and the trade tracking is clean.

## Development flow (back to coding)

Linear is the source of "what to do next" (G-Trade project, issues GDG-214–221). To resume development:

1. **Pick an issue** — Start with the one In Progress (e.g. GDG-215 E2E validation) or move another from Backlog to In Progress via Linear.
2. **Branch** — From the repo that owns the work (es-hotzone-trader for bridge/engine; G-Trade for docs): e.g. `feat/GDG-215-e2e-validation`. Use GDG prefix; see [engineering-system/linear-workflow.md](engineering-system/linear-workflow.md).
3. **Implement** — Follow [.cursor/skills/issue-to-pr/SKILL.md](../.cursor/skills/issue-to-pr/SKILL.md): read issue and AGENTS.md, implement, run tests, update docs if behavior or config changed.
4. **Commit and PR** — Commit with issue ref in message; open PR with template and link to Linear issue. See [engineering-system/github-workflow.md](engineering-system/github-workflow.md).
5. **Close the loop** — When PR is merged, move the Linear issue to Done; optionally update [Tasks.md](Tasks.md) if that item is listed there.

## Legacy Railway verification

Use this only if you intentionally re-enable cloud telemetry or cloud tooling later:

1. Confirm the G-Trade Railway project still has the expected services and env vars.
2. Confirm the bridge is configured with a non-empty ingest URL and token.
3. Run a short live or replay session and verify data lands in Railway as expected.

## Compliance

See [Compliance-Boundaries.md](Compliance-Boundaries.md) and the state-reset section in [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md).
