# Current State

Operational view: what is in place, what has been validated, and what is not yet done or not validated. See [Architecture-Overview.md](Architecture-Overview.md) for the active local-only architecture.

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
| **Data bridge + outbox** | Removed | Railway bridge/outbox runtime code has been removed from the active codebase; historical context remains in `docs/archive/railway-sunset/`. |
| **Config** | In place | Launch-gate defaults are Pre-Open live with later zones shadow-only. SQLite and local runtime config are the active contract. |
| **Runtime artifacts** | In place | `logs/runtime/trader.pid`, `runtime_status.json`, `lifecycle_request.json`, local launchd plist/log paths, local outbox delivery cursors. |

---

## What has been validated

- **TUI removal:** No `src/tui/`, no `run_tui` or Textual in codebase; no-arg CLI shows help; `status` command present.
- **Local Flask console:** Browser-based local console serves health/debug compatibility plus the operator pages needed for the launch cut.
- **Launch gating:** Pre-Open is live by default, later zones remain shadow-only unless explicitly promoted, and session exit is enabled with a morning hard-flat cutoff.
- **Compliance:** Topstep/CME boundaries documented; compliance gate defined for future major changes ([Compliance-Boundaries.md](Compliance-Boundaries.md)).
- **Runbook:** Live restart, state reset, and compliance steps documented ([runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md)).
- **Plan checklist:** The local trader launch cut is implemented and documented. Remaining tasks are trader-facing, not cloud-facing.

---

## What is not done or not validated

- **Phase 7 (Hardening):** Plan called for backpressure on outbox size, alerts on queue growth, replay/consistency checks, and a short runbook for recovery and rollback. Not tracked as completed in the plan; treat as optional/future unless explicitly implemented.
- **Morning edge proof:** The current morning regime packet is still a candidate edge, not a permanent truth. Ongoing validation is still required.
- **Trade management:** Contract scaling and longer-horizon exit policy tuning remain intentionally conservative.

---

## Invariants (must remain true)

1. **Execution and Topstep stay on the Mac.**
2. **SQLite is authoritative.**
3. **CLI and local Flask console are the operator surfaces.**
4. **No cloud dependency is required to trade, debug, or review runs.**
5. **Historical cloud notes are archival only.**

---

## Deployment readiness

- **Repo:** `G-Trade` is the canonical monorepo.
- **Linear:** Project G-Trade (team GDG); current work should stay centered on the local trader and launch-readiness items in [Tasks.md](Tasks.md).
- **Cursor/Codex:** project-local assets are committed with safe example configs; live credentials stay local-only.

---

## Quick reference

- **Operator workflow:** [OPERATOR.md](OPERATOR.md)
- **Architecture:** [Architecture-Overview.md](Architecture-Overview.md)
- **Plan (completed migration):** [.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md](../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md)
- **Tasks checklist:** [Tasks.md](Tasks.md)
