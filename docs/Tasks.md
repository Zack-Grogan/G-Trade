# Tasks

Checklist of migration and follow-up work. Completed items are checked; open items are unchecked. Source: [TUI Sunset and Railway Data Network plan](../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md) and [Current-State.md](Current-State.md).

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

- [ ] **Phase 7 hardening** — Outbox backpressure, queue-growth alerts, replay/consistency checks, recovery runbook (if desired).
- [ ] **E2E validation** — Confirm full path (Mac bridge → ingest → Postgres → analytics/MCP/web) in your environment with a test run. Tracked in Linear as GDG-215; when done, check here and add to Current-State "What has been validated."
- [ ] **Linear or new plan** — Track any new features or ops work in Linear or a new plan file; keep this checklist for the completed migration only.

---

When you complete an open task, check it here and update [Current-State.md](Current-State.md) if it changes what is operational or validated.
