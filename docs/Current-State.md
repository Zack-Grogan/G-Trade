# Current State

Operational view: what is in place, what has been validated, and what is not yet done or not validated. See [Architecture-Overview.md](Architecture-Overview.md) for architecture and [.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md](../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md) for the full migration plan.

---

## What is operational

### Local (Mac) — es-hotzone-trader

| Component | Status | Notes |
|-----------|--------|--------|
| **CLI** | Operational | No TUI; `es-trade` (no args) shows help. Commands: start, stop, restart, status, debug, events, config, balance, health, replay. |
| **Trading engine** | Operational | Strategy, sync, protection, adoption, dynamic exit. Runs in same process as `es-trade start`. |
| **Order executor** | Operational | Orders, protection, reconciliation. Topstep API and execution stay on Mac only. |
| **Debug server** | Operational | Health and `/debug` HTTP only. No MCP on this process. Used by CLI and data bridge. |
| **Observability store** | Operational | SQLite: events, runs, completed trades. Source for bridge. |
| **Data bridge + outbox** | Operational when configured | In-process; reads state + observability, writes to outbox, drains to Railway ingest. Gated by `observability.railway_ingest_url` and API key. Fail-open if Railway is down. |
| **Config** | In place | `observability.railway_ingest_url`, `railway_ingest_api_key` (or env `RAILWAY_INGEST_API_KEY`); optional `server.railway_mcp_url`. |
| **Runtime artifacts** | In place | `logs/runtime/trader.pid`, `runtime_status.json`, `lifecycle_request.json`. |

### Railway (G-Trade)

| Service | Status | Notes |
|---------|--------|--------|
| **Postgres** | Deployed | Single DB for runs, events, state_snapshots, completed_trades. |
| **g-trade-ingest** | Deployed | FastAPI; `POST /ingest/state`, `/ingest/events`, `/ingest/trades`; Bearer auth. |
| **g-trade-analytics** | Deployed | Read-only API over Postgres; single-operator auth. |
| **g-trade-mcp** | Deployed | MCP endpoint for Cursor; tools/resources from Postgres/analytics. |
| **g-trade-web** | Deployed | Next.js app; calls analytics API only. |

Deployment and env (e.g. `DATABASE_URL`, `INGEST_API_KEY`, `ANALYTICS_API_KEY`) are set in the Railway project. Operator configures local bridge and Cursor MCP to point at these services.

**Compatibility:** Existing Railway services may still be named `grogan-trade-ingest` etc.; URLs and env (e.g. `server.railway_mcp_url`) continue to work. When creating new environments or renaming in Railway, prefer project "G-Trade" and service names `g-trade-ingest`, `g-trade-analytics`, `g-trade-mcp`, `g-trade-web`.

---

## What has been validated

- **TUI removal:** No `src/tui/`, no `run_tui` or Textual in codebase; no-arg CLI shows help; `status` command present.
- **Local MCP removal:** Debug server serves health and debug only; MCP route removed. Cursor uses Railway MCP URL.
- **Bridge and outbox:** Implemented (`src/bridge/`); config-gated; bearer auth to ingest; outbox for durability.
- **Compliance:** Topstep/CME boundaries documented; compliance gate defined for future major changes ([Compliance-Boundaries.md](Compliance-Boundaries.md)).
- **Runbook:** Live restart, state reset, and compliance steps documented ([runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md)).
- **Plan checklist:** All 11 plan todos (compliance, freeze, local hardening, TUI sunset, bridge, Railway Postgres/ingest/analytics/web/MCP, verification) marked completed in the plan file.

---

## What is not done or not validated

- **Phase 7 (Hardening):** Plan called for backpressure on outbox size, alerts on queue growth, replay/consistency checks, and a short runbook for recovery and rollback. Not tracked as completed in the plan; treat as optional/future unless explicitly implemented.
- **End-to-end live validation:** No guarantee that a full live run (Mac bridge → Railway ingest → Postgres → analytics/MCP/web) has been exercised end-to-end in production; operator should confirm with a test run when changing env or deploy.
- **Automated tests for bridge/deploy:** Unit tests exist (e.g. `tests/test_bridge.py`, `tests/test_matrix_engine.py`); integration or E2E tests against real Railway services are not documented here.

---

## Invariants (must remain true)

1. **Execution and Topstep on Mac only.** No order placement or broker API from Railway.
2. **Data flow one way: Mac → Railway.** Cloud never sends orders or market data back.
3. **MCP on Railway only.** Local debug server does not expose MCP.
4. **Single-operator auth** on all Railway surfaces; no public unauthenticated endpoints.
5. **Local trading resilient to cloud downtime.** Bridge fails open; outbox retries when Railway is available again.

---

## Quick reference

- **Operator workflow:** [OPERATOR.md](OPERATOR.md)
- **Architecture:** [Architecture-Overview.md](Architecture-Overview.md)
- **Plan (completed migration):** [.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md](../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md)
- **Tasks checklist:** [Tasks.md](Tasks.md)
