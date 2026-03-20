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
- `es-trade service install|uninstall|start|stop|restart|status|logs|doctor` — manage the local `launchd` wrapper and inspect local runtime health.
- `es-trade db runs|events|snapshots|bridge-health|logs` — inspect local SQLite durability (including historical bridge-health rows from archived integrations).
- `es-trade config` — show configuration.
- `es-trade balance` — show Topstep account balance.
- `es-trade health` — health check.
- `es-trade replay <path>` — replay from file.

## Local Flask console

`es-trade start` brings up the trading engine and the local Flask console on the Mac. The console is the main browser-based operator surface for the current launch cut.

The console is local-only and serves these pages:
- `/` — console overview (status and zone in the header; live state omits duplicate status/zone; a short log teaser links to `/logs`; recent events are behind an expandable section)
- `/chart` — live chart and indicators (compact symbol/price/zone strip; recent broker fills capped with a link to `/trades`)
- `/trades` — local trade list and account-trade context
- `/trades/<id>` — trade review
- `/logs` — runtime log stream as the primary view; events and orders are behind an expandable section
- `/system` — config, health, and launch readiness
- `/health` and `/debug` — JSON compatibility endpoints for the CLI and service checks

Chart notes:
- `/chart` reads retained local `market_tape` across runs so price history does not disappear just because the current runtime restarted.
- In live mode, `/chart` can attempt a bounded historical 1-minute bar backfill from the TopstepX/ProjectX history API when the requested lookback window has an older gap and credentials are available.
- Replay writes its feed into the same local `market_tape`, so `/chart` can show replay candles and the same indicator overlays without a separate chart path.
- The plotted VWAP/band overlays are derived from stored candles, and alpha lines are carried forward from recorded decision snapshots instead of being rendered as flat current-state lines.
- The chart now defaults to a **7d** window and exposes a `24h` / `48h` / `7d` selector in the page so operators can inspect longer retained history without editing the URL by hand.
- Candlesticks are the primary price layer; the redundant close-only price overlay is suppressed so the chart does not read like indicators-only rendering.

Default local ports are pinned to a high, memorable pair so they do not collide with typical dev services:
- `31380` — `/health`
- `31381` — console UI and `/debug`

On the console overview (`/`), **Trades today** and **Losses** use the local observability **broker ledger** (`account_trades` rows with realized P&L) for the current **America/Los_Angeles calendar day**, filtered to the active account when known. They are not the engine session risk counters (`trades_today` / `consecutive_losses` in `/debug`).

## Local-only workflow

The active operator workflow is local-only:

- use the CLI for service control, analysis, and broker truth
- use the local Flask console for browser-based visibility
- use SQLite as the durable source of truth

## Launch posture

- **Live entries:** `Pre-Open` is live by default.
- **Shadow-only zones:** `Post-Open`, `Midday`, and `Outside` still score and log, but they do not place live entries in the launch cut.
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
