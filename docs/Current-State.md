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
| **Runtime inspection** | Operational | CLI (`es-trade status`, `health`, `debug`) plus SQLite state snapshots; no local HTTP console. Optional local macOS `operator_tts` speaks order lifecycle events via `say` when enabled. |
| **Observability store** | Operational | SQLite: events, runs, completed trades, state snapshots, decision snapshots, market tape, order lifecycle, bridge health, runtime logs, account trade history. Source of truth for replay/recovery. |
| **Data bridge + outbox** | Removed | Railway bridge/outbox runtime code has been removed from the active codebase; historical context remains in `docs/archive/railway-sunset/`. |
| **Config** | In place | Launch-gate defaults are `Pre-Open` and `Outside` live with `Post-Open`/`Midday` shadow-only unless promoted. SQLite and local runtime config are the active contract. |
| **Runtime artifacts** | In place | `logs/runtime/trader.pid`, `runtime_status.json`, `lifecycle_request.json`, local launchd plist/log paths, local outbox delivery cursors. |

---

## What has been validated

- **TUI removal:** No `src/tui/`, no `run_tui` or Textual in codebase; no-arg CLI shows help; `status` command present.
- **Broker hardening:** `topstep_client.py` now has expanded auth, order lifecycle, broker-truth, query, and SignalR helper coverage; the runtime no longer carries the unused `runtime_controller.py` abstraction.
- **Crash recovery:** SQLite observability durability now has dedicated crash-recovery tests covering WAL mode, unclean restart, atomic batches, concurrent writes, and restart persistence.
- **Validation pass:** Full `pytest` suite passes from repo root; coverage targets remain documented in test tooling.
- **CLI + SQLite:** Operator visibility is CLI and SQLite only (no Flask).
- **Launch gating:** Pre-Open and Outside are live by default; later zones remain shadow-only unless explicitly promoted in config. Zone policy does not branch on practice vs live—only `strategy.live_entry_zones` / `shadow_entry_zones` and `PREFERRED_ACCOUNT_ID` matter at runtime, session exit is enabled with a morning hard-flat cutoff, market-hours guard blocks new entries during configured closed windows while leaving signal evaluation active, and launch-readiness still requires a funded account, flat broker truth, contradiction-free broker state, and recovery proof before it returns green.
- **Compliance:** Topstep/CME boundaries documented; the compliance gate is now fail-closed unless `COMPLIANCE_GATE_ACK` is explicitly set ([Compliance-Boundaries.md](Compliance-Boundaries.md)).
- **Runbook:** Live restart, state reset, and compliance steps documented ([runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md)).
- **Plan checklist:** The local trader launch cut is implemented and documented. Remaining tasks are trader-facing, not cloud-facing.

---

## What is not done or not validated

- **Coverage targets:** The suite is substantially stronger, but the aspirational per-file coverage targets are still not fully reached yet.
- **Phase 7 (Hardening):** Queue-drop visibility and recovery consistency coverage are improved, but the short recovery/rollback runbook and any remaining replay-proof gaps are still future work unless explicitly completed.
- **Morning edge proof:** The current morning regime packet is still a candidate edge, not a permanent truth. Ongoing validation is still required.
- **Trade management:** Contract scaling and longer-horizon exit policy tuning remain intentionally conservative.

---

## Invariants (must remain true)

1. **Execution and Topstep stay on the Mac.**
2. **SQLite is authoritative.**
3. **CLI and SQLite-backed observability are the operator surfaces.**
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
