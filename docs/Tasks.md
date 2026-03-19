# Tasks

Checklist of migration, launch-cut, and follow-up work. Completed items are checked; open items are unchecked. Source: [TUI Sunset and Railway Data Network plan](../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md), [Current-State.md](Current-State.md), and the local-only Sunday/Monday launch cut.

---

## Plan todos (TUI Sunset and Railway)

- [x] **Compliance and boundaries** — Document Topstep/CME boundaries and add compliance gate before migration.
- [x] **Runtime freeze and reset** — Stop trader, define state-reset runbook, and enforce pre-migration freeze.
- [x] **Local hardening** — Harden local executor durability (outbox, retry, fail-open).
- [x] **TUI sunset, CLI primary** — Remove TUI; CLI no-arg shows help; add status command.
- [x] **Secure data bridge** — Implement in-process durable bridge with outbox and bearer auth.
- [x] **Railway Postgres and ingest** — Deploy Postgres and g-trade-ingest in Railway.
- [x] **Railway analytics API** — Deploy g-trade-analytics read-only API in Railway.
- [x] **Access control (single-user)** — Enforce bearer + single-user auth on ingest and analytics; private posture.
- [x] **Railway Next.js web** — Deploy g-trade-web Next.js app after backend stable.
- [x] **Railway MCP** — Deploy g-trade-mcp on Railway; remove local MCP from debug server.
- [x] **Verification and research traceability** — Add tests and research traceability for major changes.

---

## Phased execution (plan phases)

- [x] **Phase 0 — Freeze and compliance** — Stop trader, no stuck state, document Topstep/CME boundaries, operator ready.
- [x] **Phase 1 — TUI sunset and CLI primary** — Delete `src/tui/`, no-arg → help, add status, remove Textual, smoke-test.
- [x] **Phase 2 — Local bridge and outbox** — In-process bridge and outbox (config-gated), validate batching/retry/idempotency.
- [x] **Phase 3 — Railway Postgres and ingest** — Postgres + g-trade-ingest in G-Trade project; bridge pointed at live ingest.
- [x] **Phase 4 — Railway analytics API** — Deploy g-trade-analytics; read-only; single-operator auth.
- [x] **Phase 5 — Railway Next.js app** — Deploy g-trade-web; call analytics API; auth.
- [x] **Phase 6 — Railway MCP** — Deploy g-trade-mcp; remove MCP from local debug server; document Railway MCP URL.
- [ ] **Phase 7 — Hardening** — Backpressure on outbox size, alerts on queue growth, replay/consistency checks, recovery/rollback runbook (optional/future).

---

## Easy-to-miss checklist (from plan §10)

- [x] Engine default source `"tui"` → `"cli"` in operator_request handling.
- [x] Debug server: MCP removed; POST returns 404 or equivalent for MCP path.
- [x] Startup banner: no local MCP URL; use optional `railway_mcp_url` from config.
- [x] Config: `ObservabilityConfig.railway_ingest_url` (and related); optional `ServerConfig.railway_mcp_url`.
- [x] Manifest/provenance: `mcp_url` from config (Railway URL or None).
- [x] Docs: operator updates `.cursor/mcp.json` to Railway MCP URL; documented in OPERATOR.md.
- [x] Tests: no test depends on live debug server MCP route for pass.

---

## Open / future

- [x] **Trader audit P1 — fail-closed broker retry handling** — Local executor submit/cancel retry paths now fail closed on final transport failure instead of raising through safety/fallback code. Files: `es-hotzone-trader/src/execution/executor.py`. Linear: `GDG-223`.
- [x] **Trader audit P1 — bridge cursor durability** — The Mac → Railway bridge now advances local delivery cursors only after outbox enqueue succeeds, with regression coverage for enqueue failure. Files: `es-hotzone-trader/src/bridge/railway_bridge.py`. Linear: `GDG-223`.
- [x] **Trader audit P2 — observability flush resilience** — SQLite flush failures no longer permanently disable telemetry; batched writes are transactional and retries/backoff are covered by tests. Files: `es-hotzone-trader/src/observability/store.py`. Linear: `GDG-226`.
- [x] **Trader audit P2 — no-trade regression investigation (Mar 17 → Mar 18)** — Root cause was overlapping volatility gating: `Pre-Open` hard-vetoed `STRESS` before the true safety layer could decide. `Pre-Open` no longer hard-blocks `STRESS`, while `risk_circuit_breaker` remains the hard stop. Files: `es-hotzone-trader/src/config/loader.py`, `es-hotzone-trader/config/default.yaml`, `es-hotzone-trader/tests/test_matrix_engine.py`. Linear: `GDG-224`. Research note: `docs/research/Trader Research Roundup 2026-03-19.md`.
- [x] **Trader audit P2 — matrix/session correctness** — `strategy.vwap_session` was a misleading no-op. The runtime remains zone-derived (`Pre-Open` => `ETH`, other zones => `RTH`), the dead knob is removed from the default config surface, and regression coverage now locks the zone-derived session behavior. Files: `es-hotzone-trader/src/config/loader.py`, `es-hotzone-trader/config/default.yaml`, `es-hotzone-trader/tests/test_matrix_engine.py`, `es-hotzone-trader/tests/test_config_loader.py`. Linear: `GDG-225`.
- [x] **Trader audit P3 — sizing config truthfulness** — `use_volatility_sizing` and `target_daily_risk_pct` were dead knobs. They are removed from the default config surface and accepted only as deprecated ignored keys so legacy configs still load without changing runtime sizing behavior. Files: `es-hotzone-trader/src/config/loader.py`, `es-hotzone-trader/config/default.yaml`, `es-hotzone-trader/tests/test_config_loader.py`. Linear: `GDG-225`.
- [x] **Trader audit P3 — stale pending ID cleanup** — Pending decision/attempt/position/trade IDs are now cleared when the live broker-entry guard blocks an order attempt. Files: `es-hotzone-trader/src/engine/trading_engine.py`. Linear: `GDG-227`.
- [ ] **Sunday/Monday launch cut — regime proof and local operator readiness** — Prove the current winning conditions, confirm the local Flask console and CLI are the primary operator surfaces, validate the launch-gate defaults, and keep Monday launch risk bounded to the current local posture.
- [ ] **Trader investigation — optimization, durability, execution, error-free pass** — Continue deeper review of strategy thresholds, risk gates, broker-sync behavior, durability gaps, and local evidence so the trader can be trusted to keep taking good trades after recent updates.
- [x] **Data quality review — completed trade anomalies** — Unrealistic `completed_trades` rows were replay/mock artifacts amplified by timezone-string duplicate backfill. Non-live runs no longer persist into authoritative `completed_trades`, timestamps are canonicalized before dedupe, and default trade queries now hide non-authoritative replay rows. Files: `es-hotzone-trader/src/observability/store.py`, `es-hotzone-trader/tests/test_matrix_engine.py`. Linear: `GDG-228`.
- [ ] **Phase 7 hardening** — Outbox backpressure, queue-growth alerts, replay/consistency checks, recovery runbook (if desired).
- [ ] **Local launch verification** — Confirm the local Flask console, launch gate, session exit policy, and broker-truth commands are enough to operate without Railway for the Monday cut.
- [ ] **Legacy cloud verification** — If you re-enable cloud telemetry later, confirm the Mac bridge → Railway ingest → Postgres → analytics/MCP/web path before relying on it.
- [ ] **Linear cleanup** — Review the remaining GDG issues and close, archive, or reclassify the Railway-only items that are no longer required for the local launch cut.

**Plan "Deploy, Linear, and dev flow" completed:** Deployment verified via Railway CLI + MCP (see Current-State). Linear: GDG-215 confirmed In Progress. Back-to-dev flow documented in OPERATOR.md; next step is implementing GDG-215 (E2E validation).

---

When you complete an open task, check it here and update [Current-State.md](Current-State.md) if it changes what is operational or validated.
