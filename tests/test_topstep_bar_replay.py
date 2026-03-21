"""Regression tests for Topstep minute-bar replay (deprecated CLI path; code kept for smoke tests)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import pandas as pd

from src.config import Config, HotZoneConfig, set_config
from src.engine.replay_runner import ReplayRunner
from src.engine.trading_engine import TradingEngine
from src.market import MarketData, get_client


def _topstep_replay_test_config() -> Config:
    """Minimal config for replay tests (mirrors tests.test_matrix_engine.build_config)."""
    config = Config(
        hot_zones=[
            HotZoneConfig(name="Pre-Open", start="06:30", end="08:30", timezone="America/Chicago"),
            HotZoneConfig(name="Post-Open", start="09:00", end="11:00", timezone="America/Chicago"),
            HotZoneConfig(name="Midday", start="12:00", end="13:00", timezone="America/Chicago"),
            HotZoneConfig(
                name="Close-Scalp",
                start="12:45",
                end="13:00",
                timezone="America/Chicago",
                mode="flatten_only",
            ),
        ]
    )
    config.alpha.min_entry_score = 1.25
    config.alpha.full_size_score = 3.5
    config.alpha.min_score_gap = 0.25
    config.alpha.flat_bias_buffer = 0.0
    config.alpha.zone_vetoes["Midday"]["max_atr_percentile"] = 1.0
    config.regime.stress_quote_rate = 0.0
    config.regime.trend_slope_threshold = 0.05
    config.regime.trend_ofi_threshold = 0.2
    config.replay.segment_size = 2
    config.validation.walk_forward_train_bars = 2
    config.validation.walk_forward_test_bars = 2
    config.validation.synthetic_quote_policy = "reject"
    config.event_provider.calendar_path = "config/does-not-exist.yaml"
    config.event_provider.emergency_halt_path = "config/does-not-exist.flag"
    config.observability.enabled = False
    return config


class TopstepBarReplayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = _topstep_replay_test_config()
        set_config(self.config)
        get_client(force_recreate=True)
        self.engine = TradingEngine(self.config)

    def test_bar_to_market_data_uses_tick_spread_not_bar_range(self) -> None:
        runner = ReplayRunner(config=self.config, engine=self.engine)
        bar = {
            "time": pd.Timestamp("2026-03-13 15:00:00Z"),
            "open": 5000.0,
            "high": 5010.0,
            "low": 4990.0,
            "close": 5005.0,
            "volume": 1000,
        }
        md = runner._bar_to_market_data(bar, "ES")
        tick = float(self.config.volume_profile.tick_size)
        self.assertAlmostEqual(md.ask - md.bid, tick, places=6)
        self.assertAlmostEqual((md.bid + md.ask) / 2.0, 5005.0, places=6)
        self.assertTrue(md.quote_is_synthetic)

    def test_on_topstep_history_bar_preserves_api_high_low(self) -> None:
        self.engine.reset_runtime_state(clear_history=True)
        self.engine.enable_mock_mode()
        api_bar = {
            "time": pd.Timestamp("2026-03-13 15:00:00Z"),
            "open": 100.0,
            "high": 105.0,
            "low": 99.0,
            "close": 103.0,
            "volume": 50,
        }
        tick = float(self.config.volume_profile.tick_size)
        md = MarketData(
            symbol="ES",
            bid=103.0 - tick / 2.0,
            ask=103.0 + tick / 2.0,
            last=103.0,
            volume=50,
            volume_is_cumulative=False,
            quote_is_synthetic=True,
            timestamp=pd.Timestamp("2026-03-13 15:00:00Z").to_pydatetime(),
        )
        with patch.object(self.engine, "_evaluate_current_state"):
            self.engine.on_topstep_history_bar(api_bar, md)
        self.assertFalse(self.engine._bars.empty)
        row = self.engine._bars.iloc[-1]
        self.assertEqual(row["high"], 105.0)
        self.assertEqual(row["low"], 99.0)
        self.assertEqual(row["close"], 103.0)
        self.assertEqual(row["open"], 100.0)

    def test_bar_aggregator_reset_after_history_bar(self) -> None:
        self.engine.reset_runtime_state(clear_history=True)
        self.engine.enable_mock_mode()
        api_bar = {
            "time": pd.Timestamp("2026-03-13 15:00:00Z"),
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 10,
        }
        tick = float(self.config.volume_profile.tick_size)
        md = MarketData(
            symbol="ES",
            bid=100.5 - tick / 2.0,
            ask=100.5 + tick / 2.0,
            last=100.5,
            volume=10,
            volume_is_cumulative=False,
            quote_is_synthetic=True,
            timestamp=pd.Timestamp("2026-03-13 15:00:00Z").to_pydatetime(),
        )
        with patch.object(self.engine, "_evaluate_current_state"):
            self.engine.on_topstep_history_bar(api_bar, md)
        self.assertIsNone(self.engine.bar_aggregator._bucket_start)
        self.assertIsNone(self.engine.bar_aggregator._bar)

    def test_run_from_topstep_appends_api_ohlc_to_bars(self) -> None:
        fake_bars = [
            {
                "time": pd.Timestamp("2026-03-13 15:00:00Z"),
                "open": 100.0,
                "high": 110.0,
                "low": 95.0,
                "close": 108.0,
                "volume": 10,
            },
            {
                "time": pd.Timestamp("2026-03-13 15:01:00Z"),
                "open": 108.0,
                "high": 109.0,
                "low": 100.0,
                "close": 101.0,
                "volume": 20,
            },
        ]
        with patch.object(
            self.engine.client,
            "retrieve_bars_covering_range",
            return_value=(fake_bars, {"bars_returned": 2}),
        ):
            with patch.object(self.engine, "_evaluate_current_state"):
                result = ReplayRunner(config=self.config, engine=self.engine).run_from_topstep(
                    symbol="ES",
                    start_date="2026-03-13",
                    end_date="2026-03-14",
                )
        self.assertEqual(result.events, 2)
        self.assertEqual(len(self.engine._bars), 2)
        self.assertEqual(float(self.engine._bars.iloc[0]["high"]), 110.0)
        self.assertEqual(float(self.engine._bars.iloc[0]["low"]), 95.0)
        self.assertEqual(float(self.engine._bars.iloc[1]["high"]), 109.0)
        self.assertEqual(float(self.engine._bars.iloc[1]["low"]), 100.0)
        self.assertIsNone(self.engine.bar_aggregator._bucket_start)


if __name__ == "__main__":
    unittest.main()
