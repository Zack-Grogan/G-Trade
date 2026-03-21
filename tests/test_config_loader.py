from __future__ import annotations

import tempfile
import textwrap
import unittest
import warnings
from pathlib import Path

from src.config import Config, set_config
from src.config.loader import load_config


class TestConfigLoaderCompatibility(unittest.TestCase):
    def test_load_config_ignores_deprecated_noop_keys_with_warning(self) -> None:
        config_text = textwrap.dedent("""
            strategy:
              vwap_session: "RTH"
            risk:
              use_volatility_sizing: true
              target_daily_risk_pct: 1.0
            """)
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(config_text, encoding="utf-8")
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                config = load_config(str(config_path))

        self.assertFalse(hasattr(config.strategy, "vwap_session"))
        self.assertFalse(hasattr(config.risk, "use_volatility_sizing"))
        self.assertFalse(hasattr(config.risk, "target_daily_risk_pct"))
        messages = [str(item.message) for item in caught]
        self.assertTrue(any("vwap_session" in message for message in messages))
        self.assertTrue(any("use_volatility_sizing" in message for message in messages))
        self.assertTrue(any("target_daily_risk_pct" in message for message in messages))

    def test_load_config_ignores_removed_min_dominant_feature_score(self) -> None:
        config_text = textwrap.dedent("""
            alpha:
              min_dominant_feature_score: 1.0
            """)
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(config_text, encoding="utf-8")
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                config = load_config(str(config_path))

        self.assertFalse(hasattr(config.alpha, "min_dominant_feature_score"))
        messages = [str(item.message) for item in caught]
        self.assertTrue(any("min_dominant_feature_score" in message for message in messages))

    def test_default_config_is_morning_first_profile(self) -> None:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            config = load_config()

        self.assertTrue(config.strategy.launch_gate_enabled)
        self.assertEqual(config.strategy.live_entry_zones, ["Pre-Open"])
        self.assertEqual(config.strategy.shadow_entry_zones, ["Post-Open", "Midday", "Outside"])
        self.assertTrue(config.strategy.trade_outside_hotzones)
        self.assertTrue(config.strategy.session_exit_enabled)
        self.assertEqual(config.strategy.session_exit_checkpoint_time, "10:00")
        self.assertEqual(config.strategy.session_exit_hard_flat_time, "11:30")
        self.assertEqual(config.alpha.zone_min_entry_score["Pre-Open"], 5.0)
        self.assertEqual(config.alpha.zone_exit_decay_score["Pre-Open"], 1.5)
        self.assertEqual(config.alpha.regime_multipliers["STRESS"]["long"], 0.3)
        self.assertEqual(config.alpha.zone_weights["Outside"]["long"]["trend_state"], 1.6)
        self.assertEqual(config.alpha.zone_weights["Outside"]["flat"]["regime_stress"], 1.0)
        self.assertEqual(config.account.max_contracts, 1)
        self.assertEqual(config.risk.max_trades_per_zone, 3)
        self.assertEqual(config.risk.max_daily_trades, 10)
        self.assertEqual(caught, [])

    def test_bare_config_defaults_are_neutral_library_shape(self) -> None:
        config = Config()

        self.assertFalse(config.strategy.launch_gate_enabled)
        self.assertEqual(config.strategy.live_entry_zones, [])
        self.assertEqual(config.strategy.shadow_entry_zones, [])
        self.assertTrue(config.strategy.trade_outside_hotzones)
        self.assertFalse(config.strategy.session_exit_enabled)
        self.assertEqual(config.alpha.regime_multipliers["STRESS"]["long"], 0.3)
        self.assertEqual(config.alpha.zone_weights["Outside"]["long"]["trend_state"], 1.6)
        self.assertEqual(config.alpha.zone_weights["Outside"]["flat"]["regime_stress"], 1.0)
        self.assertEqual(config.account.max_contracts, 5)
        self.assertEqual(config.risk.max_trades_per_zone, 3)
        self.assertEqual(config.risk.max_daily_trades, 10)

    def test_load_config_rejects_zone_in_both_live_and_shadow_lists(self) -> None:
        config_text = textwrap.dedent("""
            strategy:
              launch_gate_enabled: true
              live_entry_zones: ["Pre-Open", "Outside"]
              shadow_entry_zones: ["Outside"]
            """)
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(config_text, encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(str(config_path))

    def test_load_config_allows_launch_gate_without_live_zones_for_stand_down(self) -> None:
        config_text = textwrap.dedent("""
            strategy:
              launch_gate_enabled: true
              live_entry_zones: []
            """)
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(config_text, encoding="utf-8")
            config = load_config(str(config_path))

        self.assertTrue(config.strategy.launch_gate_enabled)
        self.assertEqual(config.strategy.live_entry_zones, [])

    def test_load_config_allows_overlap_when_launch_gate_disabled(self) -> None:
        config_text = textwrap.dedent("""
            strategy:
              launch_gate_enabled: false
              live_entry_zones: ["Outside"]
              shadow_entry_zones: ["Outside"]
            """)
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.yaml"
            config_path.write_text(config_text, encoding="utf-8")
            config = load_config(str(config_path))

        self.assertFalse(config.strategy.launch_gate_enabled)

    def test_set_config_rejects_overlap_when_launch_gate_enabled(self) -> None:
        config = Config()
        config.strategy.launch_gate_enabled = True
        config.strategy.live_entry_zones = ["Pre-Open", "Outside"]
        config.strategy.shadow_entry_zones = ["Outside"]

        with self.assertRaises(ValueError):
            set_config(config)
