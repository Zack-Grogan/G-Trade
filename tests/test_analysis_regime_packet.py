from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis.regime_packet import build_launch_readiness, render_regime_packet_markdown
from src.config import load_config, set_config
from src.observability import get_observability_store


class LaunchReadinessTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.config = load_config()
        self.config.observability.enabled = True
        self.config.observability.sqlite_path = str(Path(self._temp_dir.name) / "observability.db")
        self.config.strategy.launch_gate_enabled = True
        self.config.strategy.live_entry_zones = ["Pre-Open"]
        self.config.strategy.shadow_entry_zones = ["Post-Open", "Midday", "Outside"]
        self.config.strategy.session_exit_enabled = True
        set_config(self.config)
        self.store = get_observability_store(force_recreate=True, config=self.config)

    def tearDown(self) -> None:
        self.store.stop()
        self._temp_dir.cleanup()

    def test_launch_readiness_prefers_sqlite_runtime_state_when_available(self) -> None:
        packet = {
            "account_id": "20139389",
            "morning_meta": {"summary": {"count": 3, "total_pnl": 4225.0}},
            "launch_defaults": {
                "launch_gate_enabled": True,
                "live_entry_zones": ["Pre-Open"],
                "shadow_entry_zones": ["Post-Open", "Midday", "Outside"],
                "session_exit_enabled": True,
                "session_exit_checkpoint_time": "10:00",
                "session_exit_hard_flat_time": "11:30",
                "session_exit_timezone": "America/Los_Angeles",
            },
        }
        remote_debug = {
            "status": "healthy",
            "running": True,
            "zone": {"name": "Pre-Open"},
            "account": {"id": "20139389", "is_practice": False},
            "broker_truth": {
                "current": {"position": {"quantity": 0}, "open_order_count": 0},
                "contradictions": {
                    "api_flat_with_recent_activity": False,
                    "api_flat_with_working_history": False,
                    "focus_timestamp_activity_detected": False,
                    "focus_timestamp_without_current_open_state": False,
                },
            },
            "lifecycle": {"recovery_verified": True},
        }
        with patch("src.analysis.regime_packet.build_regime_packet", return_value=packet):
            with patch(
                "src.analysis.regime_packet.fetch_runtime_debug_state",
                return_value=(remote_debug, "sqlite"),
            ):
                readiness = build_launch_readiness(store=self.store, config=self.config)

        self.assertTrue(readiness["checks"]["runtime_reachable"])
        self.assertTrue(readiness["checks"]["runtime_running"])
        self.assertTrue(readiness["checks"]["runtime_healthy"])
        self.assertTrue(readiness["checks"]["funded_account_selected"])
        self.assertTrue(readiness["checks"]["broker_truth_flat"])
        self.assertTrue(readiness["checks"]["broker_truth_no_contradictions"])
        self.assertTrue(readiness["checks"]["recovery_verified"])
        self.assertEqual(readiness["runtime_state_source"], "sqlite")
        self.assertEqual(readiness["runtime_status"], "healthy")

    def test_render_regime_packet_markdown_includes_session_checkpoint_and_hard_flat(self) -> None:
        packet = {
            "generated_at": "2026-03-20T00:00:00Z",
            "account_id": "acct-1",
            "trade_count": 3,
            "morning_meta": {"summary": {"count": 3, "total_pnl": 4225.0, "avg_duration_hours": 7.39}},
            "overnight_negative_control": {"summary": {"count": 8, "total_pnl": -1850.0}},
            "zone_summary": {},
            "launch_defaults": {
                "launch_gate_enabled": True,
                "live_entry_zones": ["Pre-Open"],
                "shadow_entry_zones": ["Post-Open", "Midday", "Outside"],
                "session_exit_checkpoint_time": "10:00",
                "session_exit_hard_flat_time": "11:30",
                "session_exit_timezone": "America/Los_Angeles",
            },
        }

        rendered = render_regime_packet_markdown(packet)

        self.assertIn("Session checkpoint: `10:00 America/Los_Angeles`", rendered)
        self.assertIn("Session hard flat: `11:30 America/Los_Angeles`", rendered)
