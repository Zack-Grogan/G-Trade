"""Shared launch-gate-aware zone-state helpers for operator/runtime surfaces."""

from __future__ import annotations

from typing import Optional

from src.config import StrategyConfig
from src.observability.taxonomy import (
    ZONE_STATE_ACTIVE,
    ZONE_STATE_BLOCKED,
    ZONE_STATE_INACTIVE,
    ZONE_STATE_SHADOW,
)

ZONE_SEMANTICS_VERSION = "launch_gate_aware_v1"


def resolve_launch_gate_zone_state(
    strategy: StrategyConfig,
    *,
    zone_name: Optional[str],
    scheduled_zone_state: Optional[str] = None,
) -> str:
    """Return the operator-facing zone state after launch-gate policy is applied."""
    if zone_name is None:
        return ZONE_STATE_INACTIVE
    if scheduled_zone_state and scheduled_zone_state != ZONE_STATE_ACTIVE:
        return scheduled_zone_state

    live_zones = set(strategy.live_entry_zones or [])
    shadow_zones = set(strategy.shadow_entry_zones or [])
    if strategy.launch_gate_enabled and zone_name in live_zones and zone_name in shadow_zones:
        return ZONE_STATE_BLOCKED
    if not strategy.launch_gate_enabled or zone_name in live_zones:
        return ZONE_STATE_ACTIVE
    if zone_name in shadow_zones:
        return ZONE_STATE_SHADOW
    return ZONE_STATE_BLOCKED
