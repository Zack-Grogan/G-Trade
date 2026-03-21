"""Tests for CLI + SQLite runtime inspection helpers."""

from __future__ import annotations

import unittest

from src.runtime.inspection import health_dict_from_debug


class HealthDictFromDebugTests(unittest.TestCase):
    def test_maps_to_health_shape(self) -> None:
        debug = {
            "status": "healthy",
            "data_mode": "live",
            "zone": {"name": "Pre-Open", "state": "active", "semantics_version": "launch_gate_aware_v1"},
            "position": {"contracts": 2, "pnl": 12.5},
            "account": {"daily_pnl": -5.0, "is_practice": False},
            "risk": {"state": "normal"},
            "alpha": {"long_score": 1.0, "short_score": 0.5},
            "heartbeat": {"market_stream_connected": True},
        }
        health = health_dict_from_debug(debug)
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["zone"], "Pre-Open")
        self.assertEqual(health["zone_state"], "active")
        self.assertEqual(health["zone_semantics_version"], "launch_gate_aware_v1")
        self.assertEqual(health["position"], 2)
        self.assertEqual(health["daily_pnl"], -5.0)
        self.assertEqual(health["risk_state"], "normal")
        self.assertTrue(health["market_stream_connected"])

    def test_marks_legacy_zone_semantics_when_missing_version(self) -> None:
        debug = {
            "status": "healthy",
            "data_mode": "live",
            "zone": {"name": "Post-Open", "state": "shadow"},
            "position": {"contracts": 0, "pnl": 0.0},
            "account": {"daily_pnl": 0.0, "is_practice": True},
            "risk": {"state": "normal"},
            "alpha": {"long_score": 0.0, "short_score": 0.0},
            "heartbeat": {"market_stream_connected": True},
        }
        health = health_dict_from_debug(debug)
        self.assertEqual(health["zone_semantics_version"], "legacy_or_unknown")

    def test_uses_top_level_zone_semantics_version_when_nested_missing(self) -> None:
        debug = {
            "status": "healthy",
            "data_mode": "live",
            "zone": {"name": "Post-Open", "state": "shadow"},
            "zone_semantics_version": "launch_gate_aware_v1",
            "position": {"contracts": 0, "pnl": 0.0},
            "account": {"daily_pnl": 0.0, "is_practice": True},
            "risk": {"state": "normal"},
            "alpha": {"long_score": 0.0, "short_score": 0.0},
            "heartbeat": {"market_stream_connected": True},
        }
        health = health_dict_from_debug(debug)
        self.assertEqual(health["zone_semantics_version"], "launch_gate_aware_v1")
