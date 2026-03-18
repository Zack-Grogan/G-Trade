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

## Compliance

See [Compliance-Boundaries.md](Compliance-Boundaries.md) and the state-reset section in [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md).
