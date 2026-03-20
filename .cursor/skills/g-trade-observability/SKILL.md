---
name: g-trade-observability
description: Applies the G-Trade observability contract for logging, SQLite durability, decision snapshots, and CLI debugging. Use when changing src/observability, decision or event recording, es-trade db/events commands, runtime log mirroring, or debugging local trader traces.
---

# G-Trade observability

Use this skill when **changing** how the trader records or queries state. For **operational** triage (service down, broker mismatch, tailing logs), use [`es-hotzone-debug`](../es-hotzone-debug/SKILL.md) first.

## Authority

1. Read [`docs/Observability-Contract.md`](../../../docs/Observability-Contract.md) before editing emit paths or query behavior.
2. Use [`src/observability/taxonomy.py`](../../../src/observability/taxonomy.py) for `category`, `event_type`, and decision `outcome` strings — do not invent parallel spellings.
3. Do not hand-edit `docs/generated/`; refresh generated indexes with the repo’s scripts if needed.

## Invariants

- **One `decision_id` per entry attempt chain** — do not emit a second `record_decision_snapshot` after a successful `place_order` with a newly minted id.
- Successful entry outcome is **`order_submitted`** (`OUTCOME_ORDER_SUBMITTED`), aligned with executor lifecycle naming.
- **SQLite** is the durable query surface; the rotating file log is the human-readable stream. Runtime log mirroring failures must remain visible (stderr mirror logger in `src/cli.commands`).

## Verification

- After behavioral changes, run `pytest` for affected tests (including `tests/test_observability_decision_telemetry.py` when touching decision recording).
- Confirm `es-trade events --help` and `es-trade db events --help` stay aligned when adding query flags.

## Related

- [`docs/OPERATOR.md`](../../../docs/OPERATOR.md) — operator commands.
- [`es-hotzone-debug`](../es-hotzone-debug/SKILL.md) — live debugging workflow.
