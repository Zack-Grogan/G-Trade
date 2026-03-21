# Observability contract

Authoritative rules for logging, SQLite durability, and operator debugging. **Do not** hand-edit `docs/generated/`; use this doc and code in [`src/observability/`](../src/observability/).

## Streams

| Stream | What | When |
|--------|------|------|
| **Rotating file** (`config.logging.file`, default `logs/trading.log`) | Human-readable lines; same records mirrored to SQLite `runtime_logs` when observability is enabled | Process lifetime; level from `config.logging.level` |
| **SQLite `events`** | Structured `category` + `event_type` + JSON payload | `ObservabilityStore.record_event` |
| **SQLite `decision_snapshots`** (and related rows) | Full matrix decision snapshot including `feature_snapshot`; optional `latency_ms_market_to_decision` / `latency_ms_decision_to_submit` when `observability.record_decision_latency` is true | `record_decision_snapshot` from `TradingEngine._record_decision_event` |
| **SQLite `state_snapshots`** | Periodic `TradingState.to_dict()` | Engine `_update_server_state` |
| **SQLite `order_lifecycle`** | Order/protection lifecycle | Executor + engine |
| **SQLite `market_tape`** | Tick/bar telemetry | Market client / replay |
| **SQLite `runtime_logs`** | Every root log line (except observability store recursion) | CLI `_ObservabilityLogHandler` |

Canonical string constants live in [`src/observability/taxonomy.py`](../src/observability/taxonomy.py).

## ID rules

- **One `decision_id` per evaluation chain** for a given entry attempt. Do not emit a second `record_decision_snapshot` for the same successful `place_order` with a newly minted `decision_id`.
- **`attempt_id` / `position_id` / `trade_id`** are allocated before submit and passed through `_record_decision_event` so SQLite rows correlate with executor lifecycle events.
- Executor lifecycle uses **`order_submitted`**; align engine decision **`outcome`** with `OUTCOME_ORDER_SUBMITTED` (`order_submitted`) for successful entry.

## Decision outcomes

Use only values defined in `taxonomy.py` (`OUTCOME_*`). Examples:

- `order_submitted` — entry order placed; single snapshot per submit.
- `order_submit_failed` — `place_order` returned `None`.
- `risk_blocked`, `broker_entry_guard_blocked`, `market_closed_entry_block`, etc. — terminal reasons without a submit.

## Event taxonomy

- **`category`**: `system|decision|execution|market|risk` (see `taxonomy.py`).
- **`event_type`**: free-form but stable; decision events use `decision_evaluated` (`EVENT_DECISION_EVALUATED`).

## Cross-process debug

`fetch_runtime_debug_state` ([`src/runtime/inspection.py`](../src/runtime/inspection.py)) returns:

- `in_process` — same PID as CLI.
- `sqlite` — latest state snapshot for `run_id` from `runtime_status.json`.
- `status_file` — control-plane only until SQLite has a snapshot.

See [OPERATOR.md](OPERATOR.md).

## Observability store failure mode

If `ObservabilityStore` hits an unexpected error, it may set **`_failed`** and stop accepting new records for the process. Failures in **executor** observability are fail-open and logged; failures in **log mirroring** must surface to stderr or the file log (see implementation). Full per-subsystem isolation is not implemented; treat global disable as a follow-up.

## Replay / mock execution fill model

- **Market orders** in mock mode use `replay_execution.market_slippage_ticks` (see `OrderExecutor._mock_market_fill_price`).
- **Limit orders** use touch-based fills; `replay_execution.limit_touch_fill_ratio` (0–1) is the probability that a given quote update fills a working limit when price has crossed (`1.0` = legacy always-fill). When `mock_fill_random_seed` is set, draws use a fixed `random.Random` stream; when null, draws are deterministic from `SHA-256(order_id + tick timestamp)` so replays are repeatable.
- **`limit_fill_penalty_ticks`** in `replay_execution` is applied in **replay benchmark summaries** (`ReplayRunner._costed_trade_summary`) as a conservative dollar haircut per trade, not as an extra tick adjustment inside the executor fill price (avoids double-counting).

## CLI

- `es-trade events` and `es-trade db events` both query `events`; both support `run_id` filtering when you need to scope to one process run.
- `es-trade db export-tape` exports `market_tape` rows as JSONL for backup or offline analysis.
- Replay CLI emits **system** `replay_completed` / `replay_failed` (file or tape mode) and `replay_topstep_completed` / `replay_topstep_failed` as structured events. **`replay-topstep` is deprecated** as a research path (see `docs/replay/replay-topstep-deprecated.md`); events are retained for continuity. Replay JSON summaries include `observability_drops` (store queue drop count) when relevant; under load, the observability queue may drop tape rows—see `ObservabilityStore.get_dropped_event_count()`.

## Related

- [OPERATOR.md](OPERATOR.md) — commands and workflow.
- [`src/observability/taxonomy.py`](../src/observability/taxonomy.py) — constants.
- [`es-hotzone-debug`](../.cursor/skills/es-hotzone-debug/SKILL.md) skill — operational triage.
