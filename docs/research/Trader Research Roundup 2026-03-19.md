# Trader Research Roundup — 2026-03-19

Research-first roundup for `es-hotzone-trader` after the March 19 audit. This note converts the current findings into evidence-backed packets and records the first ranked memo for the March 17 -> March 18 no-trade regression.

## Resolution status (updated 2026-03-19)

- `GDG-223` completed:
  - executor submit/cancel retries now fail closed on final transport failure
  - bridge delivery cursors advance only after outbox durability succeeds
- `GDG-224` completed:
  - the March 17 -> March 18 no-trade regression was an overlapping volatility-gating problem
  - `Pre-Open` no longer hard-vetoes `STRESS`; `risk_circuit_breaker` remains the actual hard stop
- `GDG-225` completed:
  - `strategy.vwap_session` was removed from the active config surface because runtime session routing is zone-derived, not config-driven
  - `use_volatility_sizing` and `target_daily_risk_pct` were converted into deprecated ignored legacy keys so old configs still load without changing behavior
- `GDG-226` completed:
  - observability flush failures no longer poison telemetry for the rest of the process lifetime
- `GDG-227` completed:
  - broker entry-guard blocks now clear pending decision/attempt/position/trade IDs
- `GDG-228` completed:
  - unrealistic `completed_trades` rows were replay/mock artifacts plus timezone-string duplicate backfill
  - non-live runs no longer persist into authoritative completed-trade history and completed-trade timestamps are canonicalized before dedupe

## Linear tracking

- Umbrella: `GDG-222` — Trader research-first issue roundup and investigation wave
- `GDG-223` — Fix executor retry safety and bridge cursor durability
- `GDG-224` — Investigate March 17 -> March 18 no-trade regression
- `GDG-225` — Align matrix/session routing and sizing config with runtime truth
- `GDG-226` — Harden observability flush recovery
- `GDG-227` — Clear stale pending IDs on broker entry-guard blocks
- `GDG-228` — Investigate completed-trade anomalies and accounting drift

## Issue packets

### 1. Executor retry fail-closed

- Observed symptom: final broker submit/cancel transport failures can still raise through the safety path instead of failing closed.
- Local evidence source: targeted executor tests plus runtime logs around submit/cancel failures.
- Primary code paths:
  - `es-hotzone-trader/src/execution/executor.py`
- External dependency:
  - official Topstep broker/API behavior docs only if retry semantics depend on transport vs. business error classes.
- Acceptance test:
  - force final-attempt transport failure on submit and cancel; verify the executor returns a safe failure result, records the failure, and does not unwind fallback/safety code.

### 2. Bridge cursor durability

- Observed symptom: delivery cursors can advance before outbox durability is confirmed.
- Local evidence source:
  - `logs/railway_outbox.db`
  - `logs/observability.db`
  - bridge runtime logs
- Primary code paths:
  - `es-hotzone-trader/src/bridge/railway_bridge.py`
- External dependency: none.
- Acceptance test:
  - force `outbox.enqueue()` failure during replay/drain; verify cursor state does not advance and the item remains recoverable after restart.

### 3. Observability flush resilience

- Observed symptom: one SQLite flush error can suppress telemetry for the rest of the run.
- Local evidence source:
  - `logs/observability.db`
  - `logs/trading.log`
  - forced flush-failure test
- Primary code paths:
  - `es-hotzone-trader/src/observability/store.py`
- External dependency: none.
- Acceptance test:
  - inject a write/flush error, then verify later telemetry can still persist after recovery.

### 4. March 17 -> March 18 no-trade regression

- Observed symptom:
  - March 17 live run produced real Pre-Open LONG/SHORT decisions and entries.
  - March 18 live run produced meaningful Pre-Open score gaps but no entries.
- Local evidence source:
  - `run_manifests`
  - `events`
  - `decision_snapshots`
  - `completed_trades`
  - `runtime_logs`
- Primary code paths:
  - `es-hotzone-trader/src/engine/decision_matrix.py`
  - `es-hotzone-trader/src/engine/risk_manager.py`
  - `es-hotzone-trader/src/engine/trading_engine.py`
  - `es-hotzone-trader/src/engine/regime.py`
- External dependency:
  - official CME Globex hours/session reference for ES session context
  - official Topstep account/order/streaming docs only where broker semantics need to be separated from signal logic
- Acceptance test:
  - reconstruct the March 17 vs. March 18 window, prove whether the lockout was intended risk gating or an overtuned regression, and add regression coverage before any threshold change lands.
- Resolution:
  - implemented the minimum-risk fix: `Pre-Open` no longer blocks `STRESS` at the matrix-veto layer, but `risk_circuit_breaker` remains a hard entry stop
  - regression tests now prove `Pre-Open` can still act on a strong signal under `STRESS` when risk is `NORMAL`, and still blocks when risk is `CIRCUIT_BREAKER`

### 5. Matrix/session routing correctness

- Observed symptom: `vwap_session` and `trade_outside_hotzones` appear configurable, but session routing is still effectively hard-coded in the matrix.
- Local evidence source:
  - config loader
  - default config
  - matrix decision payloads
- Primary code paths:
  - `es-hotzone-trader/src/engine/decision_matrix.py`
  - `es-hotzone-trader/src/config/loader.py`
  - `es-hotzone-trader/config/default.yaml`
- External dependency:
  - none unless session naming needs to be aligned to an official market-hours reference.
- Acceptance test:
  - prove that config semantics match runtime behavior, or remove/simplify the misleading knobs.
- Resolution:
  - `strategy.vwap_session` was confirmed to be a misleading no-op and removed from the active config surface
  - runtime session routing remains zone-derived and is now locked by regression coverage (`Pre-Open` => `ETH`, other in-zone trading => `RTH`)

### 6. Sizing config truthfulness

- Observed symptom: `use_volatility_sizing` and `target_daily_risk_pct` exist in config but do not drive live sizing.
- Local evidence source:
  - config files
  - sizing telemetry in decisions/risk logs
- Primary code paths:
  - `es-hotzone-trader/src/config/loader.py`
  - `es-hotzone-trader/src/engine/risk_manager.py`
  - `es-hotzone-trader/config/default.yaml`
- External dependency: none.
- Acceptance test:
  - either implement the knobs and prove the effect, or remove them and document the runtime truth.
- Resolution:
  - `use_volatility_sizing` and `target_daily_risk_pct` were confirmed dead and removed from the default config surface
  - the loader now accepts them only as deprecated ignored keys so older configs remain loadable without changing sizing behavior

### 7. Stale pending ID cleanup

- Observed symptom: pending decision/attempt/position/trade IDs can remain stale when the broker entry guard blocks an order attempt.
- Local evidence source:
  - live decision events
  - guard-block traces in engine logs/snapshots
- Primary code paths:
  - `es-hotzone-trader/src/engine/trading_engine.py`
- External dependency: none.
- Acceptance test:
  - force each guard-block branch and verify pending IDs and unresolved metadata are cleared.

### 8. Completed trade anomaly review

- Observed symptom: local `completed_trades` contains unrealistic PnL outliers.
- Local evidence source:
  - `logs/observability.db` tables `completed_trades`, `account_trades`, `events`
- Primary code paths:
  - `es-hotzone-trader/src/observability/store.py`
- External dependency:
  - broker-history semantics only if local accounting turns out to be interpreting broker rows incorrectly.
- Acceptance test:
  - trace one representative outlier from broker/history input through local durability and classify the fault as replay duplication, write-path inflation, or accounting semantics.
- Resolution:
  - the representative outliers came from `replay` runs, not live broker truth
  - replay/mock runs no longer persist into authoritative `completed_trades`
  - completed-trade timestamps are canonicalized to UTC before insert/backfill so runtime and event-backfill rows dedupe correctly

## March 17 -> March 18 regression memo

### Evidence

- March 17 run `1773741810-84492` (`git_commit=2247b1e`) produced real Pre-Open entry decisions, including:
  - `2026-03-17T11:35:00+00:00` — `pre-open_long_matrix`
  - `2026-03-17T11:53:00+00:00` — `pre-open_short_matrix`
- March 18 run `1773828331-38310` (`git_commit=905362a`) produced `NO_TRADE` throughout the same session even when the score gap remained large.
- The critical March 18 decision row:
  - `2026-03-18T11:30:00+00:00`
  - `short_score=5.5896`
  - `score_gap=11.6066`
  - `regime_state=STRESS`
  - `active_vetoes=["regime_stress"]`
- One minute later, the risk manager escalated to circuit breaker:
  - `2026-03-18T11:31:00+00:00`
  - `reason=volatility_spike`
  - `atr_value=2.7732358599`
  - `baseline=1.5828660351`
  - `threshold=2.7700155614`

### Ranked root-cause categories

1. Overlapping volatility gates are the leading suspect.
   - The regime classifier marks `STRESS` on volatility spikes.
   - The matrix blocks stressed regimes.
   - The risk manager can then escalate the same condition into `risk_circuit_breaker`.
2. Circuit-breaker hysteresis looks too sticky.
   - The trip happened on a tiny overshoot above threshold.
   - The clear path requires ATR to fall below a stricter normalization rule, which can pin the engine in lockout.
3. Session/config drift is real but secondary.
   - `vwap_session` still looks user-configurable even though the matrix continues to hard-code the active session path.
4. Entry guard behavior is not the cause of the regression.
   - March 18 never reached the live-entry path; the guard was not the blocking mechanism.
5. Broker sync/execution issues are secondary.
   - A later `503` exists in the March 18 runtime, but it happens after the no-trade wall begins.

### What should not change without stronger evidence

- Do not disable circuit breakers just to recover missed trades.
- Do not use the entry guard as the tactical scapegoat for the March 18 wall.
- Do not treat `vwap_session` as the regression fix; that is a config-correctness issue, not the primary lockout.
- Do not widen outside-hot-zone trading as a workaround.

### Research references

- CME Globex trading-hours reference:
  - [CME Group Holiday and Trading Hours](https://www.cmegroup.com/trading-hours.html)
- Repo research context:
  - `docs/research/Separated Signal and Execution Research Architecture.md`
  - `docs/research/Rigorous Validation Philosophy.md`
  - `docs/research/Regime Labeling Framework.md`

### Remaining evidence gaps

- The exact local config diff between the last good live run and the first bad live run is still incomplete because historical run manifests persisted the config hash, not the full config body.
- The old March 18 theory-plan notes under `docs/theory-plans/` were written before the richer current SQLite evidence existed, so they should not be treated as final.
