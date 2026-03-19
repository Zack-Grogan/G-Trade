# Tasks

Checklist of active trader work. Historical migration tasks live in git history and the archive docs.

## Active work

- [x] **Trader audit P1 — fail-closed broker retry handling** — Local executor submit/cancel retry paths now fail closed on final transport failure instead of raising through safety/fallback code. Files: `es-hotzone-trader/src/execution/executor.py`. Linear: `GDG-223`.
- [x] **Trader audit P1 — bridge cursor durability** — The legacy bridge cursor no longer advances before local durability succeeds. Files: `es-hotzone-trader/src/bridge/railway_bridge.py`. Linear: `GDG-223`.
- [x] **Trader audit P2 — observability flush resilience** — SQLite flush failures no longer permanently disable telemetry; batched writes are transactional and retries/backoff are covered by tests. Files: `es-hotzone-trader/src/observability/store.py`. Linear: `GDG-226`.
- [x] **Trader audit P2 — no-trade regression investigation (Mar 17 → Mar 18)** — Root cause was overlapping volatility gating: `Pre-Open` hard-vetoed `STRESS` before the true safety layer could decide. `Pre-Open` no longer hard-blocks `STRESS`, while `risk_circuit_breaker` remains the hard stop. Files: `es-hotzone-trader/src/config/loader.py`, `es-hotzone-trader/config/default.yaml`, `es-hotzone-trader/tests/test_matrix_engine.py`. Linear: `GDG-224`. Research note: `docs/research/Trader Research Roundup 2026-03-19.md`.
- [x] **Trader audit P2 — matrix/session correctness** — `strategy.vwap_session` was a misleading no-op. The runtime remains zone-derived (`Pre-Open` => `ETH`, other zones => `RTH`), the dead knob is removed from the default config surface, and regression coverage now locks the zone-derived session behavior. Files: `es-hotzone-trader/src/config/loader.py`, `es-hotzone-trader/config/default.yaml`, `es-hotzone-trader/tests/test_matrix_engine.py`, `es-hotzone-trader/tests/test_config_loader.py`. Linear: `GDG-225`.
- [x] **Trader audit P3 — sizing config truthfulness** — `use_volatility_sizing` and `target_daily_risk_pct` were dead knobs. They are removed from the default config surface and accepted only as deprecated ignored keys so legacy configs still load without changing runtime sizing behavior. Files: `es-hotzone-trader/src/config/loader.py`, `es-hotzone-trader/config/default.yaml`, `es-hotzone-trader/tests/test_config_loader.py`. Linear: `GDG-225`.
- [x] **Trader audit P3 — stale pending ID cleanup** — Pending decision/attempt/position/trade IDs are now cleared when the live broker-entry guard blocks an order attempt. Files: `es-hotzone-trader/src/engine/trading_engine.py`. Linear: `GDG-227`.
- [ ] **Sunday/Monday launch cut — regime proof and local operator readiness** — Prove the current winning conditions, confirm the local Flask console and CLI are the primary operator surfaces, validate the launch-gate defaults, and keep Monday launch risk bounded to the current local posture.
- [ ] **Trader investigation — optimization, durability, execution, error-free pass** — Continue deeper review of strategy thresholds, risk gates, broker-sync behavior, durability gaps, and local evidence so the trader can be trusted to keep taking good trades after recent updates.
- [x] **Data quality review — completed trade anomalies** — Unrealistic `completed_trades` rows were replay/mock artifacts amplified by timezone-string duplicate backfill. Non-live runs no longer persist into authoritative `completed_trades`, timestamps are canonicalized before dedupe, and default trade queries now hide non-authoritative replay rows. Files: `es-hotzone-trader/src/observability/store.py`, `es-hotzone-trader/tests/test_matrix_engine.py`. Linear: `GDG-228`.
- [ ] **Phase 7 hardening** — Queue limits, replay/consistency checks, and recovery runbook if those legacy durability paths remain useful.
- [ ] **Local launch verification** — Confirm the local Flask console, launch gate, session exit policy, and broker-truth commands are enough to operate cleanly for the Monday cut.
- [ ] **Linear cleanup** — Review the remaining GDG issues and close, archive, or reclassify old cloud-era items that no longer matter.

---

When you complete an open task, check it here and update [Current-State.md](Current-State.md) if it changes what is operational or validated.
