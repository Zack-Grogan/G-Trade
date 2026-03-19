# Current State

Operational view: what is in place, what has been validated, and what is not yet done or not validated. See [Architecture-Overview.md](Architecture-Overview.md) for architecture and [.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md](../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md) for the completed migration plan. This page reflects the current local-only Sunday/Monday launch cut.

---

## What is operational

### Local (Mac) — es-hotzone-trader

| Component | Status | Notes |
|-----------|--------|--------|
| **CLI** | Operational | No TUI; `es-trade` (no args) shows help. Commands include start/stop/restart/status/debug/events/config/balance/health/replay plus `broker-truth`, `analyze ...`, `service ...`, and `db ...` for launchd and local durability operations. |
| **Trading engine** | Operational | Strategy, sync, protection, adoption, launch gating, and dynamic exit. Runs in same process as `es-trade start`. |
| **Order executor** | Operational | Orders, protection, reconciliation. Topstep API and execution stay on Mac only. |
| **Local Flask console** | Operational | Browser-based local operator surface on `127.0.0.1`. Serves `/`, `/chart`, `/trades`, `/trades/<id>`, `/logs`, `/system`, plus `/health` and `/debug` JSON. |
| **Observability store** | Operational | SQLite: events, runs, completed trades, state snapshots, decision snapshots, market tape, order lifecycle, bridge health, runtime logs, account trade history. Source of truth for replay/recovery. |
| **Data bridge + outbox** | Disabled by default | In-process; reads local observability, writes to outbox, drains to Railway ingest only when configured. Permanent auth failures are recorded locally instead of retried forever. |
| **Config** | In place | `observability.railway_ingest_url` is empty by default, `observability.internal_api_token` (or env `GTRADE_INTERNAL_API_TOKEN`) is optional for cloud re-enable, and launch-gate defaults are Pre-Open live with later zones shadow-only. |
| **Runtime artifacts** | In place | `logs/runtime/trader.pid`, `runtime_status.json`, `lifecycle_request.json`, local launchd plist/log paths, local outbox delivery cursors. |

### Railway (G-Trade, legacy / optional)

| Service | Status | Notes |
|---------|--------|--------|
| **Postgres** | Deployed | Legacy cloud store for runs, events, state snapshots, market tape, decision snapshots, order lifecycle, runtime logs, completed trades, and RLM artifacts. Not required for Monday launch. |
| **g-trade-ingest** | Deployed | FastAPI; legacy Mac → cloud telemetry receiver. Only used if the bridge is explicitly re-enabled. |
| **g-trade-analytics** | Deployed | Query-only API over Postgres. Useful for legacy cloud review, not required for the local launch cut. |
| **g-trade-mcp** | Deployed | Legacy MCP endpoint for Cursor; not part of the Monday launch workflow. |
| **g-trade-web** | Deployed | Legacy Next.js operator console; not required for the local launch cut. |

Deployment and env (e.g. `DATABASE_URL`, `GTRADE_INTERNAL_API_TOKEN`, `ANALYTICS_API_KEY`, `MCP_AUTH_TOKEN`, `RLM_SERVICE_URL`, optional `RLM_AUTH_TOKEN`) remain in the Railway project for legacy use, but the local launch cut does not depend on them.

---

## What has been validated

- **TUI removal:** No `src/tui/`, no `run_tui` or Textual in codebase; no-arg CLI shows help; `status` command present.
- **Local Flask console:** Browser-based local console serves health/debug compatibility plus the operator pages needed for the launch cut.
- **Bridge and outbox:** Implemented (`src/bridge/`); config-gated; bearer auth to ingest; outbox for durability; disabled by default in the launch cut.
- **Launch gating:** Pre-Open is live by default, later zones remain shadow-only unless explicitly promoted, and session exit is enabled with a morning hard-flat cutoff.
- **Compliance:** Topstep/CME boundaries documented; compliance gate defined for future major changes ([Compliance-Boundaries.md](Compliance-Boundaries.md)).
- **Runbook:** Live restart, state reset, and compliance steps documented ([runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md)).
- **Plan checklist:** All 11 plan todos (compliance, freeze, local hardening, TUI sunset, bridge, Railway Postgres/ingest/analytics/web/MCP, verification) marked completed in the plan file.

---

## What is not done or not validated

- **Phase 7 (Hardening):** Plan called for backpressure on outbox size, alerts on queue growth, replay/consistency checks, and a short runbook for recovery and rollback. Not tracked as completed in the plan; treat as optional/future unless explicitly implemented.
- **End-to-end cloud validation:** The Railway path is legacy/optional for the current launch cut. If you re-enable it, confirm the full Mac bridge → Railway ingest → Postgres → analytics/MCP/web path before depending on it.
- **Automated tests for bridge/deploy:** Unit tests exist (e.g. `tests/test_bridge.py`, `tests/test_matrix_engine.py`); integration or E2E tests against real Railway services are not documented here.

---

## Invariants (must remain true)

1. **Execution and Topstep on Mac only.** No order placement or broker API from Railway.
2. **Data flow one way: Mac → Railway.** Cloud never sends orders or market data back.
3. **MCP on Railway only.** Local debug server does not expose MCP.
4. **Single-operator auth** on all Railway surfaces; no public unauthenticated endpoints.
5. **Local trading resilient to cloud downtime.** Bridge fails open; outbox retries when Railway is available again.

---

## Deployment readiness

- **Repos:** All six repos created under Zack-Grogan; `main` pushed: G-Trade, es-hotzone-trader, g-trade-ingest, g-trade-analytics, g-trade-mcp, g-trade-web.
- **Naming:** Repo names as above; Railway service names g-trade-ingest, g-trade-analytics, g-trade-mcp, g-trade-web.
- **Linear:** Project G-Trade (team GDG); branch prefix GDG for issues. Current launch-cut work should stay centered on the local trader, the Flask console, and the launch-readiness items in Tasks.md.
- **Railway:** G-Trade project and services remain available for legacy/cloud use, but the current launch cut does not require them.
- **Cursor:** .cursor and MCP (Linear, GitHub, Railway, OpenViking, etc.) aligned; “repo root” for workspace scripts = G-Trade repo root.

---

## Quick reference

- **Operator workflow:** [OPERATOR.md](OPERATOR.md)
- **Architecture:** [Architecture-Overview.md](Architecture-Overview.md)
- **Plan (completed migration):** [.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md](../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md)
- **Tasks checklist:** [Tasks.md](Tasks.md)
