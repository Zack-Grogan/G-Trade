# Architecture overview — Post–TUI Sunset and Railway

Canonical architecture doc (lowercase path). This document summarizes the current architecture after the TUI Sunset and Railway Data Network migration. For the full execution plan and checklist, see [.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md](../../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md).

## One-line summary

**Execution and Topstep stay on the Mac (CLI-only operator surface).** Telemetry flows one-way to Railway (Postgres, ingest, analytics, MCP, Next.js). MCP and analytics run in the cloud so tooling works even when the trading process is stopped.

## What runs where

| Where | What |
|-------|------|
| **Local (Mac)** | Trading engine, order executor, Topstep client, debug server (health + debug HTTP), observability SQLite, CLI, data bridge + outbox. All execution and broker access. |
| **Railway (G-Trade)** | Postgres, g-trade-ingest, g-trade-analytics, g-trade-mcp, g-trade-web. Storage, read-only APIs, MCP for Cursor, internal analytics UI. |

## Data flow

- **Mac → Railway:** The in-process bridge reads debug state and observability (events, runs, trades), writes to a local outbox, and POSTs batches to the ingest API over HTTPS with Bearer auth. Data flows one way only.
- **Railway → Mac:** None. Cloud never sends orders or market data back.
- **Cursor / IDE:** MCP clients connect to the Railway MCP service URL (not localhost). Same tool names and resources; backend is Postgres/analytics.

## Railway services (summary)

| Service | Purpose |
|--------|--------|
| **Postgres** | Single database for runs, events, state_snapshots, completed_trades. |
| **g-trade-ingest** | Accepts POSTs from the Mac bridge (state, events, trades); writes to Postgres; Bearer auth. |
| **g-trade-analytics** | Read-only API (runs, events, trades, summary). Used by web app and MCP. Single-operator auth. |
| **g-trade-mcp** | MCP endpoint for Cursor; tools backed by analytics/Postgres. Single-operator auth. |
| **g-trade-web** | Next.js app for analytics and tooling; calls analytics API only. |

Details (purpose, why, what, how, why that way) are in the plan file, Section 4.

## Key docs

- **[docs/README.md](../README.md)** — Documentation index.
- **[OPERATOR.md](../OPERATOR.md)** — CLI commands, MCP setup, compliance pointer.
- **[Current-State.md](../Current-State.md)** — What is operational, validated, and not done.
- **[Tasks.md](../Tasks.md)** — Task checklist (completed and open).
- **[Compliance-Boundaries.md](../Compliance-Boundaries.md)** — Topstep/CME boundaries and compliance gate.
- **[runbooks/ES Hot Zone Trader Live Restart Runbook.md](../runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md)** — Stop/restart, state reset.
- **[Current_Plan.md](../Current_Plan.md)** — Plan reference (this architecture is complete).

## Config (local)

- **Bridge:** `observability.railway_ingest_url`, `observability.railway_ingest_api_key` (or env `RAILWAY_INGEST_API_KEY`), outbox path, retry settings. Bridge runs only when ingest URL and key are set.
- **MCP URL for Cursor:** `server.railway_mcp_url` (optional); shown in startup banner and manifest when set.
