"""Tests for optional evaluation drawdown mirror in RiskManager."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime
from unittest.mock import Mock, patch

from src.config import RiskConfig
from src.engine.risk_manager import RiskManager


class TestEvaluationDrawdownMirror(unittest.TestCase):
    def _make_manager(self, **risk_kwargs) -> RiskManager:
        cfg = Mock()
        cfg.symbols = ["ES"]
        cfg.watchdog = Mock()
        cfg.watchdog.feed_stale_seconds = 15
        cfg.observability = Mock()
        cfg.observability.persist_completed_trades = False
        base = RiskConfig(
            max_daily_loss=10_000,
            max_position_loss=50_000,
            evaluation_drawdown_mirror_enabled=True,
            evaluation_starting_equity=50_000.0,
            evaluation_trailing_drawdown_dollars=2_000.0,
            evaluation_mirror_buffer_dollars=0.0,
        )
        merged = {**base.__dict__, **risk_kwargs}
        cfg.risk = RiskConfig(**merged)
        cfg.account = Mock()
        cfg.account.default_contracts = 1
        cfg.account.max_contracts = 5
        cfg.account.risk_per_contract = 500.0
        with patch("src.engine.risk_manager.get_observability_store") as p_obs:
            p_obs.return_value = Mock(record_event=Mock(), record_completed_trade=Mock())
            return RiskManager(config=cfg)

    def test_mirror_trips_on_open_loss_before_daily_pnl_would(self) -> None:
        rm = self._make_manager()
        t0 = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)
        rm.observe_time(t0)
        rm.open_position(
            contracts=1,
            entry_price=5000.0,
            direction=1,
            zone="Midday",
            current_time=t0,
        )
        rm.observe_market_price(4960.0, t0)
        self.assertTrue(rm.is_evaluation_mirror_breached())
        allowed, reason = rm.can_trade("Midday", current_time=t0)
        self.assertFalse(allowed)
        self.assertEqual(reason, "evaluation_drawdown_mirror")
        flat, why = rm.should_flatten_position(4960.0, t0)
        self.assertTrue(flat)
        self.assertEqual(why, "evaluation_drawdown_mirror")

    def test_hwm_trails_up_then_tighter_floor(self) -> None:
        rm = self._make_manager()
        t0 = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)
        rm.observe_time(t0)
        rm.open_position(
            contracts=1,
            entry_price=5000.0,
            direction=1,
            zone="Midday",
            current_time=t0,
        )
        rm.observe_market_price(5020.0, t0)
        self.assertFalse(rm.is_evaluation_mirror_breached())
        rm.observe_market_price(5010.0, t0)
        self.assertFalse(rm.is_evaluation_mirror_breached())
        rm.observe_market_price(4980.0, t0)
        self.assertTrue(rm.is_evaluation_mirror_breached())

    def test_reset_state_clears_mirror(self) -> None:
        rm = self._make_manager()
        t0 = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)
        rm.observe_time(t0)
        rm.open_position(
            contracts=1,
            entry_price=5000.0,
            direction=1,
            zone="Midday",
            current_time=t0,
        )
        rm.observe_market_price(4960.0, t0)
        self.assertTrue(rm.is_evaluation_mirror_breached())
        rm.reset_state(clear_history=True)
        self.assertFalse(rm.is_evaluation_mirror_breached())
