# G-Trade workspace

Docs, .cursor rules/skills, scripts, and the AI operating layer for the G-Trade project. Application code lives in separate repositories.

## Repositories (Zack-Grogan)

| Repo | Purpose |
|------|---------|
| **G-Trade** (this repo) | Workspace: docs, .cursor, scripts, AGENTS.md, .github. Run workspace scripts (e.g. `python scripts/onboard_openviking.py`) from this repo root. |
| [es-hotzone-trader](https://github.com/Zack-Grogan/es-hotzone-trader) | Trading CLI, engine, bridge, observability. |
| [g-trade-ingest](https://github.com/Zack-Grogan/g-trade-ingest) | Ingest API (state/events/trades → Postgres). |
| [g-trade-analytics](https://github.com/Zack-Grogan/g-trade-analytics) | Read-only analytics API. |
| [g-trade-mcp](https://github.com/Zack-Grogan/g-trade-mcp) | MCP server for Cursor (Railway). |
| [g-trade-web](https://github.com/Zack-Grogan/g-trade-web) | Next.js analytics UI. |

## Full workspace layout

To get the full tree (this repo + app repos), clone this repo, then clone the five app repos into the same directory so you have:

- `G-Trade/` (this repo) → `docs/`, `.cursor/`, `scripts/`, `AGENTS.md`, etc.
- `es-hotzone-trader/` → from Zack-Grogan/es-hotzone-trader
- `railway/ingest/` → from Zack-Grogan/g-trade-ingest
- `railway/analytics/` → from Zack-Grogan/g-trade-analytics
- `railway/mcp/` → from Zack-Grogan/g-trade-mcp
- `railway/web/` → from Zack-Grogan/g-trade-web

Start with [docs/README.md](docs/README.md) and [AGENTS.md](AGENTS.md).
