"""Canonical strings for observability categories, event types, and decision outcomes.

Keep in sync with docs/Observability-Contract.md. Use these constants at emit sites
to avoid typos and drift from SQLite queries.
"""

from __future__ import annotations

from typing import Final

# --- Event categories (observability.events.category) ---

CATEGORY_SYSTEM: Final = "system"
CATEGORY_DECISION: Final = "decision"
CATEGORY_EXECUTION: Final = "execution"
CATEGORY_MARKET: Final = "market"
CATEGORY_RISK: Final = "risk"

# CLI / process hooks (src.cli.commands)
EVENT_UNCAUGHT_EXCEPTION: Final = "uncaught_exception"
EVENT_THREAD_EXCEPTION: Final = "thread_exception"

# --- Event types (decision path and related) ---

EVENT_DECISION_EVALUATED: Final = "decision_evaluated"

# --- Engine / trading_engine event_type values ---

EVENT_OUT_OF_ORDER_TICK: Final = "out_of_order_tick"
EVENT_ENGINE_STARTING: Final = "engine_starting"
EVENT_ENGINE_START_FAILED: Final = "engine_start_failed"
EVENT_STREAM_NOT_READY: Final = "stream_not_ready"
EVENT_ENGINE_STARTED: Final = "engine_started"
EVENT_ENGINE_STOPPING: Final = "engine_stopping"
EVENT_ENGINE_STOPPED: Final = "engine_stopped"
EVENT_BROKER_ORDER_UPDATE: Final = "broker_order_update"
EVENT_BROKER_POSITION_UPDATE: Final = "broker_position_update"
EVENT_OPERATOR_FORCE_RECONCILE: Final = "operator_force_reconcile"
EVENT_OPERATOR_CLEAR_UNRESOLVED: Final = "operator_clear_unresolved"
EVENT_ENGINE_LOOP_ERROR: Final = "engine_loop_error"
EVENT_UNRESOLVED_ENTRY_CLEARED: Final = "unresolved_entry_cleared"
EVENT_UNRESOLVED_ENTRY_TRACKED: Final = "unresolved_entry_tracked"
EVENT_BROKER_TRUTH_CONTRADICTION: Final = "broker_truth_contradiction"
EVENT_BROKER_ORDERS_ADOPTED: Final = "broker_orders_adopted"
EVENT_BROKER_POSITION_ADOPTED: Final = "broker_position_adopted"
EVENT_MARKET_CLOSED_ENTRY_BLOCK: Final = "market_closed_entry_block"
EVENT_DUPLICATE_UNRESOLVED_ENTRY_DETECTED: Final = "duplicate_unresolved_entry_detected"
EVENT_ZONE_TRANSITION: Final = "zone_transition"
EVENT_FLATTEN_REQUESTED: Final = "flatten_requested"
EVENT_POSITION_SYNC_SKIPPED_UNAVAILABLE: Final = "position_sync_skipped_unavailable"
EVENT_RECONCILIATION_BROKER_TRUTH: Final = "reconciliation_broker_truth"
EVENT_POSITION_OPENED: Final = "position_opened"
EVENT_POSITION_CLOSED: Final = "position_closed"
EVENT_POSITION_ADJUSTED: Final = "position_adjusted"
EVENT_DYNAMIC_EXIT_UPDATED: Final = "dynamic_exit_updated"
EVENT_WATCHDOG_TRIGGERED: Final = "watchdog_triggered"
EVENT_FAIL_SAFE_ACTIVATED: Final = "fail_safe_activated"

# --- Decision outcomes (decision_snapshot.payload / outcome field) ---
# One terminal outcome per matrix evaluation path; successful entry uses ORDER_SUBMITTED.

OUTCOME_FLATTEN_REQUEST: Final = "flatten_request"
OUTCOME_ALREADY_FLAT: Final = "already_flat"
OUTCOME_NO_TRADE: Final = "no_trade"
OUTCOME_HOLD: Final = "hold"
OUTCOME_SHADOW_ONLY_ZONE: Final = "shadow_only_zone"
OUTCOME_ENTRIES_DISABLED: Final = "entries_disabled"
OUTCOME_POSITION_OPEN: Final = "position_open"
OUTCOME_FAIL_SAFE_LOCKOUT: Final = "fail_safe_lockout"
OUTCOME_ACTIVE_ENTRY_ORDER: Final = "active_entry_order"
OUTCOME_RISK_BLOCKED: Final = "risk_blocked"
OUTCOME_SIZE_ZERO: Final = "size_zero"
OUTCOME_MISSING_SIDE: Final = "missing_side"
OUTCOME_MARKET_CLOSED_ENTRY_BLOCK: Final = "market_closed_entry_block"
OUTCOME_BROKER_ENTRY_GUARD_BLOCKED: Final = "broker_entry_guard_blocked"
OUTCOME_ORDER_SUBMIT_FAILED: Final = "order_submit_failed"
OUTCOME_ORDER_SUBMITTED: Final = "order_submitted"

# --- Payload keys (decision_evaluated / decision_snapshot) ---

PAYLOAD_KEY_DECISION_ID: Final = "decision_id"
PAYLOAD_KEY_ATTEMPT_ID: Final = "attempt_id"
PAYLOAD_KEY_POSITION_ID: Final = "position_id"
PAYLOAD_KEY_TRADE_ID: Final = "trade_id"
PAYLOAD_KEY_OUTCOME: Final = "outcome"
PAYLOAD_KEY_OUTCOME_REASON: Final = "outcome_reason"
