# Tasks

Checklist of active trader work. Historical migration tasks live in git history and the archive docs.

## Active work

- [x] **Trader audit P1 — fail-closed broker retry handling** — Local executor submit/cancel retry paths now fail closed on final transport failure instead of raising through safety/fallback code. Files: `src/execution/executor.py`. Linear: `GDG-223`.
- [x] **Trader audit P1 — bridge cursor durability** — The legacy bridge cursor no longer advances before local durability succeeds. Files: `src/bridge/railway_bridge.py`. Linear: `GDG-223`.
- [x] **Trader audit P2 — observability flush resilience** — SQLite flush failures no longer permanently disable telemetry; batched writes are transactional and retries/backoff are covered by tests. Files: `src/observability/store.py`. Linear: `GDG-226`.
- [x] **Trader audit P2 — no-trade regression investigation (Mar 17 → Mar 18)** — Root cause was overlapping volatility gating: `Pre-Open` hard-vetoed `STRESS` before the true safety layer could decide. `Pre-Open` no longer hard-blocks `STRESS`, while `risk_circuit_breaker` remains the hard stop. Files: `src/config/loader.py`, `config/default.yaml`, `tests/test_matrix_engine.py`. Linear: `GDG-224`. Research note: `docs/research/Trader Research Roundup 2026-03-19.md`.
- [x] **Trader audit P2 — matrix/session correctness** — `strategy.vwap_session` was a misleading no-op. The runtime remains zone-derived (`Pre-Open` => `ETH`, other zones => `RTH`), the dead knob is removed from the default config surface, and regression coverage now locks the zone-derived session behavior. Files: `src/config/loader.py`, `config/default.yaml`, `tests/test_matrix_engine.py`, `tests/test_config_loader.py`. Linear: `GDG-225`.
- [x] **Trader audit P3 — sizing config truthfulness** — `use_volatility_sizing` and `target_daily_risk_pct` were dead knobs. They are removed from the default config surface and accepted only as deprecated ignored keys so legacy configs still load without changing runtime sizing behavior. Files: `src/config/loader.py`, `config/default.yaml`, `tests/test_config_loader.py`. Linear: `GDG-225`.
- [x] **Trader audit P3 — stale pending ID cleanup** — Pending decision/attempt/position/trade IDs are now cleared when the live broker-entry guard blocks an order attempt. Files: `src/engine/trading_engine.py`. Linear: `GDG-227`.
- [x] **Quality target hardening — broker auth/order/query coverage, crash recovery validation, runtime dead code removal** — Expanded `tests/test_topstep_client.py` with auth/order/query/SignalR coverage, added crash-recovery tests for `src/observability/store.py`, removed the unused `src/cli/runtime_controller.py`. Historical Flask console tests were retired when the HTTP console was removed; use CLI + SQLite inspection tests instead.
- [ ] **Sunday/Monday launch cut — regime proof and local operator readiness** — Prove the current winning conditions, confirm the CLI and SQLite observability are the primary operator surfaces, validate the launch-gate defaults, and keep Monday launch risk bounded to the current local posture.
- [ ] **Trader investigation — optimization, durability, execution, error-free pass** — Continue deeper review of strategy thresholds, risk gates, broker-sync behavior, durability gaps, and local evidence so the trader can be trusted to keep taking good trades after recent updates.
- [x] **Data quality review — completed trade anomalies** — Unrealistic `completed_trades` rows were replay/mock artifacts amplified by timezone-string duplicate backfill. Non-live runs no longer persist into authoritative `completed_trades`, timestamps are canonicalized before dedupe, and default trade queries now hide non-authoritative replay rows. Files: `src/observability/store.py`, `tests/test_matrix_engine.py`. Linear: `GDG-228`.
- [ ] **Phase 7 hardening** — Queue limits, replay/consistency checks, and recovery runbook if those legacy durability paths remain useful. Queue-drop visibility is now exposed in tests; replay/rollback proof and the short runbook remain to be finished if still needed.
- [ ] **Local launch verification** — Confirm the CLI, SQLite durability, launch gate, session exit policy, and broker-truth commands are enough to operate cleanly for the Monday cut.
- [ ] **Linear cleanup** — Review the remaining GDG issues and close, archive, or reclassify old cloud-era items that no longer matter.

---

When you complete an open task, check it here and update [Current-State.md](Current-State.md) if it changes what is operational or validated.
