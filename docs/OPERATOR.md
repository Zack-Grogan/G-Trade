# Operator guide — CLI and Railway

The primary operator interface is the **CLI**. There is no TUI. For a high-level picture of what runs where and how data flows, see [Architecture-Overview.md](Architecture-Overview.md).

## Commands

- `es-trade` (no args) — shows help and available commands.
- `es-trade start` — start the trading engine (live).
- `es-trade stop` — request clean stop.
- `es-trade restart` — clean restart.
- `es-trade status` — one-screen status (running, zone, position, PnL, risk).
- `es-trade debug` — full debug state (JSON).
- `es-trade events` — query observability events.
- `es-trade config` — show configuration.
- `es-trade balance` — show Topstep account balance.
- `es-trade health` — health check.
- `es-trade replay <path>` — replay from file.

## MCP (Cursor / IDE)

MCP runs on **Railway**, not locally. After deploying g-trade-mcp (or legacy grogan-trade-mcp):

1. Set `server.railway_mcp_url` in config (or in `config/default.yaml`) to your Railway MCP service URL (e.g. `https://g-trade-mcp.up.railway.app/mcp` or `https://grogan-trade-mcp.up.railway.app/mcp` if still using legacy names).
2. In Cursor, point the `g_trade` MCP server at that URL (e.g. in `.cursor/mcp.json` or Cursor settings): use the same URL and add Bearer token if your MCP service requires it.

Execution and Topstep stay on the Mac; MCP and analytics run on Railway so the IDE can inspect runs and state without the local process.

## Railway and bridge (single-operator)

- **Ingest:** The local bridge (started with `es-trade start` when configured) sends state, events, and trades to the Railway ingest API. Set `observability.railway_ingest_url` and `observability.railway_ingest_api_key` (or env `RAILWAY_INGEST_API_KEY`) in config so the bridge can authenticate. All Railway surfaces use single-operator auth; no public or commercial use.
- **Analytics / MCP / Web:** Use the same single-operator model (e.g. Bearer token or allowlist). See [Architecture-Overview.md](Architecture-Overview.md) and the plan file for service details.

## Development flow (back to coding)

Linear is the source of "what to do next" (G-Trade project, issues GDG-214–221). To resume development:

1. **Pick an issue** — Start with the one In Progress (e.g. GDG-215 E2E validation) or move another from Backlog to In Progress via Linear.
2. **Branch** — From the repo that owns the work (es-hotzone-trader for bridge/engine; G-Trade for docs): e.g. `feat/GDG-215-e2e-validation`. Use GDG prefix; see [engineering-system/linear-workflow.md](engineering-system/linear-workflow.md).
3. **Implement** — Follow [.cursor/skills/issue-to-pr/SKILL.md](../.cursor/skills/issue-to-pr/SKILL.md): read issue and AGENTS.md, implement, run tests, update docs if behavior or config changed.
4. **Commit and PR** — Commit with issue ref in message; open PR with template and link to Linear issue. See [engineering-system/github-workflow.md](engineering-system/github-workflow.md).
5. **Close the loop** — When PR is merged, move the Linear issue to Done; optionally update [Tasks.md](Tasks.md) if that item is listed there.

## Deployment verification (after repo split)

Use this checklist when confirming Railway and local config are aligned with the six-repo layout:

1. **Railway dashboard (G-Trade project):** Confirm Postgres and all four services (g-trade-ingest, g-trade-analytics, g-trade-mcp, g-trade-web) exist and are healthy. If any were deployed from an old path or single repo, reconnect each service to its GitHub repo: Zack-Grogan/g-trade-ingest, Zack-Grogan/g-trade-analytics, Zack-Grogan/g-trade-mcp, Zack-Grogan/g-trade-web.
2. **Env and URLs:** In Railway, ensure `DATABASE_URL`, `INGEST_API_KEY`, `ANALYTICS_API_KEY` (and any MCP auth) are set per each service README. Locally (es-hotzone-trader config): set `observability.railway_ingest_url` and `observability.railway_ingest_api_key` (or env `RAILWAY_INGEST_API_KEY`) so the bridge can reach ingest.
3. **Optional E2E smoke check:** Run a short `es-trade start` (or replay) with the bridge configured; confirm data appears in Railway (Postgres or via analytics/MCP). This is E2E validation (Linear GDG-215).

## Compliance

See [Compliance-Boundaries.md](Compliance-Boundaries.md) and the state-reset section in [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md).
