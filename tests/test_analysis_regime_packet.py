from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.analysis.regime_packet import build_launch_readiness
from src.config import load_config, set_config
from src.observability import get_observability_store


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


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

    def test_launch_readiness_prefers_remote_runtime_state_when_available(self) -> None:
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
        }
        remote_health = {"status": "healthy"}

        with patch("src.analysis.regime_packet.build_regime_packet", return_value=packet):
            with patch(
                "src.analysis.regime_packet.urlopen",
                side_effect=[_FakeResponse(remote_debug), _FakeResponse(remote_health)],
            ):
                readiness = build_launch_readiness(store=self.store, config=self.config)

        self.assertTrue(readiness["checks"]["runtime_reachable"])
        self.assertTrue(readiness["checks"]["runtime_running"])
        self.assertTrue(readiness["checks"]["runtime_healthy"])
        self.assertEqual(readiness["runtime_state_source"], "remote")
        self.assertEqual(readiness["runtime_status"], "healthy")
