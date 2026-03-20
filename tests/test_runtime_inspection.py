"""Tests for CLI + SQLite runtime inspection helpers."""

from __future__ import annotations

import unittest

from src.runtime.inspection import health_dict_from_debug


class HealthDictFromDebugTests(unittest.TestCase):
    def test_maps_to_health_shape(self) -> None:
        debug = {
            "status": "healthy",
            "data_mode": "live",
            "zone": {"name": "Pre-Open", "state": "active"},
            "position": {"contracts": 2, "pnl": 12.5},
            "account": {"daily_pnl": -5.0, "is_practice": False},
            "risk": {"state": "normal"},
            "alpha": {"long_score": 1.0, "short_score": 0.5},
            "heartbeat": {"market_stream_connected": True},
        }
        health = health_dict_from_debug(debug)
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["zone"], "Pre-Open")
        self.assertEqual(health["position"], 2)
        self.assertEqual(health["daily_pnl"], -5.0)
        self.assertEqual(health["risk_state"], "normal")
        self.assertTrue(health["market_stream_connected"])
