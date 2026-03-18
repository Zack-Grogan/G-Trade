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

1. Set `server.railway_mcp_url` in config (or in `config/default.yaml`) to your Railway MCP service URL (e.g. `https://g-trade-mcp-production.up.railway.app/mcp`).
2. In Cursor, configure the `g_trade` MCP server in `.cursor/mcp.json`:
   - **url:** `https://g-trade-mcp-production.up.railway.app/mcp`
   - **headers:** `{ "Authorization": "Bearer <token>" }` where `<token>` is the value of `MCP_AUTH_TOKEN` from Railway (run `railway variable list --service g-trade-mcp` to see it).
3. Restart Cursor or reload the MCP server to pick up the new config.

Execution and Topstep stay on the Mac; MCP and analytics run on Railway so the IDE can inspect runs and state without the local process.
The remote MCP server now includes run timelines, state snapshots, blocker stories, and order-event reconstruction so remote investigation can answer "why did it not trade?" without reading raw tables.

## Railway and bridge (single-operator)

- **Ingest:** The local bridge (started with `es-trade start` when configured) sends state snapshots, run manifests, events, and trades to the Railway ingest API. Set `observability.railway_ingest_url` and `observability.railway_ingest_api_key` (or env `RAILWAY_INGEST_API_KEY`) in config so the bridge can authenticate. All Railway surfaces use single-operator auth; no public or commercial use.
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

1. **Railway dashboard (G-Trade project):** Confirm Postgres and all four services (g-trade-ingest, g-trade-analytics, g-trade-mcp, g-trade-web) exist and are healthy. If any were deployed from an old path or single repo, reconnect each service to its GitHub repo: Zack-Grogan/g-trade-ingest, Zack-Grogan/g-trade-analytics, Zack-Grogan/g-trade-mcp, Zack-Grogan/g-trade-web. Agent can run `railway project list --json` and Railway MCP `list-projects` / `list-services` (with linked workspace) to verify; if no project is linked, link with `railway link --project <id-or-name>` from the relevant repo root.
2. **Env and URLs:** In Railway, ensure `DATABASE_URL`, `INGEST_API_KEY`, `ANALYTICS_API_KEY` (and any MCP auth) are set per each service README. Locally (es-hotzone-trader config): set `observability.railway_ingest_url` and `observability.railway_ingest_api_key` (or env `RAILWAY_INGEST_API_KEY`) so the bridge can reach ingest.
3. **Optional E2E smoke check:** Run a short `es-trade start` (or replay) with the bridge configured; confirm data appears in Railway (Postgres or via analytics/MCP). This is E2E validation (Linear GDG-215).

**G-Trade project created from zero (agent-executed):** Project **G-Trade** was created via Railway MCP and CLI. Postgres + four services exist; repos were connected in the dashboard. **API keys (agent-set via CLI):** `INGEST_API_KEY` and `ANALYTICS_API_KEY` are set on g-trade-ingest and g-trade-analytics (and ANALYTICS_API_KEY on g-trade-mcp); `MCP_AUTH_TOKEN` set on g-trade-mcp for Cursor MCP auth. To use the bridge locally, get the ingest key: from G-Trade repo root run `railway link --project G-Trade` then `railway variable list --service g-trade-ingest` and set `observability.railway_ingest_api_key` (or `RAILWAY_INGEST_API_KEY`) in es-hotzone-trader config. **Deploy fixes applied:** Ingest and analytics were crashing with "Could not import module 'main'"; start command was set to `uvicorn app:app --host 0.0.0.0 --port $PORT` for both (via `railway environment edit --json`). **g-trade-web:** Clerk added; Next 16 + Bun in this repo's `railway/web/`. Railway still builds from Zack-Grogan/g-trade-web; that repo must be updated to match (Next 16, Clerk, proxy.ts, bun.lockb, build/start commands). Then set in Railway: `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` for production auth.

## Compliance

See [Compliance-Boundaries.md](Compliance-Boundaries.md) and the state-reset section in [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md).
