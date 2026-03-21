"""Tests for observability decision recording (contract: one snapshot per successful submit)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from src.cli.commands import cli
from src.config import set_config
from src.engine import TradingEngine
from src.engine.decision_matrix import FeatureSnapshot, MatrixDecision
from src.engine.market_context import OrderFlowSnapshot
from src.market import MarketData
from src.observability.taxonomy import OUTCOME_ORDER_SUBMITTED

from tests.test_matrix_engine import bars_from_prices, build_config, zone


def _long_decision(price: float) -> MatrixDecision:
    fs = FeatureSnapshot(
        zone_name="Post-Open",
        current_price=price,
        atr_value=1.0,
        long_features={"trend_state": 1.0},
        short_features={"trend_state": 0.1},
        flat_features={"event_state": 0.0},
        signed_features={},
    )
    return MatrixDecision(
        zone_name="Post-Open",
        action="LONG",
        reason="test_long",
        long_score=5.0,
        short_score=1.0,
        flat_bias=0.0,
        active_vetoes=[],
        feature_snapshot=fs,
        execution_tradeable=True,
        size_fraction=1.0,
        side="buy",
        stop_loss=price - 10.0,
        take_profit=price + 10.0,
        max_hold_minutes=60,
    )


class ObservabilityDecisionTelemetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = build_config()
        set_config(self.config)
        self.engine = TradingEngine(self.config)
        self.engine.reset_runtime_state()

    def test_successful_entry_emits_single_order_submitted_snapshot(self) -> None:
        """Contract: one record_decision_snapshot with outcome order_submitted per place_order success."""
        self.engine._mock_mode = True
        self.engine.executor.enable_mock_mode()
        self.engine._bars = bars_from_prices(
            "2026-03-13 09:00", [100.0 + (i * 0.2) for i in range(30)]
        )
        self.engine._last_price = float(self.engine._bars["close"].iloc[-1])
        self.engine._latest_market_data = MarketData(
            symbol="ES",
            bid=self.engine._last_price - 0.25,
            ask=self.engine._last_price + 0.25,
            last=self.engine._last_price,
            volume=1000,
            timestamp=self.engine._bars.index[-1].tz_convert("UTC").to_pydatetime(),
        )
        self.engine._latest_flow_snapshot = OrderFlowSnapshot(
            ofi=12.0,
            ofi_zscore=1.2,
            quote_rate_per_minute=30.0,
            quote_rate_state=0.8,
            spread_regime=1.4,
            volume_pace=1.0,
        )
        dec = _long_decision(self.engine._last_price)
        obs = MagicMock()
        obs.get_run_id.return_value = "run-test"
        self.engine.observability = obs

        z = zone("Post-Open", self.engine._bars.index[-1], start_time=self.engine._bars.index[0])

        with patch.object(
            self.engine.scheduler,
            "get_current_zone",
            return_value=z,
        ):
            with patch.object(self.engine.risk_manager, "can_trade", return_value=(True, "")):
                with patch.object(
                    self.engine.risk_manager,
                    "should_flatten_position",
                    return_value=(False, ""),
                ):
                    with patch.object(
                        self.engine,
                        "_should_flatten_for_session_policy",
                        return_value=(False, None),
                    ):
                        with patch.object(
                            self.engine.matrix,
                            "evaluate",
                            return_value=dec,
                        ):
                            with patch.object(
                                self.engine,
                                "_market_hours_entry_allowed",
                                return_value=(True, None, {}),
                            ):
                                self.engine._evaluate_current_state(allow_entries=True)

        submitted = [
            c
            for c in obs.record_decision_snapshot.call_args_list
            if c[0][0].get("outcome") == OUTCOME_ORDER_SUBMITTED
        ]
        self.assertEqual(len(submitted), 1)
        payload = submitted[0][0][0]
        self.assertIsNotNone(payload.get("decision_id"))
        self.assertIsNotNone(payload.get("attempt_id"))

    def test_events_cli_passes_run_id_to_query(self) -> None:
        store = MagicMock()
        store.query_events.return_value = []
        with patch("src.cli.commands.get_observability_store", return_value=store):
            runner = CliRunner()
            result = runner.invoke(cli, ["events", "--run-id", "run-xyz", "--limit", "3"])
        self.assertEqual(result.exit_code, 0, result.output)
        store.query_events.assert_called_once()
        self.assertEqual(store.query_events.call_args.kwargs.get("run_id"), "run-xyz")

    def test_shadow_outside_decision_snapshot_records_zone_state_shadow(self) -> None:
        self.engine._mock_mode = True
        self.engine.executor.enable_mock_mode()
        self.engine.config.strategy.trade_outside_hotzones = True
        self.engine.config.strategy.launch_gate_enabled = True
        self.engine.config.strategy.live_entry_zones = ["Pre-Open"]
        self.engine.config.strategy.shadow_entry_zones = ["Post-Open", "Midday", "Outside"]
        self.engine._last_price = 100.0
        self.engine._latest_market_data = MarketData(
            symbol="ES",
            bid=99.75,
            ask=100.25,
            last=100.0,
            volume=1000,
            timestamp=bars_from_prices("2026-03-13 17:05", [100.0]).index[-1]
            .tz_convert("UTC")
            .to_pydatetime(),
        )
        self.engine._latest_flow_snapshot = OrderFlowSnapshot()
        obs = MagicMock()
        obs.get_run_id.return_value = "run-test"
        self.engine.observability = obs
        decision = MatrixDecision(
            zone_name="Outside",
            action="LONG",
            reason="test_shadow_outside",
            long_score=4.0,
            short_score=1.0,
            flat_bias=0.0,
            active_vetoes=[],
            feature_snapshot=FeatureSnapshot(
                zone_name="Outside",
                current_price=100.0,
                atr_value=1.0,
                long_features={},
                short_features={},
                flat_features={},
                signed_features={},
            ),
            execution_tradeable=True,
            size_fraction=1.0,
            side="buy",
            stop_loss=99.0,
            take_profit=102.0,
            max_hold_minutes=30,
        )

        self.engine._record_decision_event(
            decision,
            zone=None,
            current_time=self.engine._latest_market_data.timestamp,
            current_price=100.0,
            allow_entries=True,
            outcome="shadow_only_zone",
            outcome_reason="shadow_only_zone",
        )

        payload = obs.record_decision_snapshot.call_args.args[0]
        self.assertEqual(payload["zone_state"], "shadow")
        self.assertEqual(payload["zone_semantics_version"], "launch_gate_aware_v1")

    def test_named_shadow_zone_decision_snapshot_records_zone_state_shadow(self) -> None:
        self.engine._mock_mode = True
        self.engine.executor.enable_mock_mode()
        self.engine.config.strategy.launch_gate_enabled = True
        self.engine.config.strategy.live_entry_zones = ["Pre-Open"]
        self.engine.config.strategy.shadow_entry_zones = ["Post-Open", "Midday", "Outside"]
        obs = MagicMock()
        obs.get_run_id.return_value = "run-test"
        self.engine.observability = obs
        decision = _long_decision(100.0)
        decision.zone_name = "Post-Open"
        decision.feature_snapshot.zone_name = "Post-Open"

        shadow_zone = zone("Post-Open", bars_from_prices("2026-03-13 09:00", [100.0]).index[-1])
        self.engine._record_decision_event(
            decision,
            zone=shadow_zone,
            current_time=bars_from_prices("2026-03-13 09:00", [100.0]).index[-1],
            current_price=100.0,
            allow_entries=True,
            outcome="shadow_only_zone",
            outcome_reason="shadow_only_zone",
        )

        payload = obs.record_decision_snapshot.call_args.args[0]
        self.assertEqual(payload["zone_state"], "shadow")
        self.assertEqual(payload["zone_semantics_version"], "launch_gate_aware_v1")

    def test_blocked_outside_decision_snapshot_records_zone_state_blocked(self) -> None:
        self.engine._mock_mode = True
        self.engine.executor.enable_mock_mode()
        self.engine.config.strategy.trade_outside_hotzones = True
        self.engine.config.strategy.launch_gate_enabled = True
        self.engine.config.strategy.live_entry_zones = ["Pre-Open"]
        self.engine.config.strategy.shadow_entry_zones = ["Post-Open", "Midday"]
        obs = MagicMock()
        obs.get_run_id.return_value = "run-test"
        self.engine.observability = obs
        decision = _long_decision(100.0)
        decision.zone_name = "Outside"
        decision.feature_snapshot.zone_name = "Outside"

        self.engine._record_decision_event(
            decision,
            zone=None,
            current_time=bars_from_prices("2026-03-13 17:05", [100.0]).index[-1],
            current_price=100.0,
            allow_entries=True,
            outcome="launch_gate_blocked",
            outcome_reason="launch_gate_blocked",
        )

        payload = obs.record_decision_snapshot.call_args.args[0]
        self.assertEqual(payload["zone_state"], "blocked")
        self.assertEqual(payload["zone_semantics_version"], "launch_gate_aware_v1")

    def test_launch_gate_config_invalid_records_blocked_decision_outcome(self) -> None:
        self.engine._mock_mode = True
        self.engine.executor.enable_mock_mode()
        self.engine.config.strategy.launch_gate_enabled = True
        self.engine.config.strategy.live_entry_zones = ["Pre-Open", "Outside"]
        self.engine.config.strategy.shadow_entry_zones = ["Outside"]
        self.engine._bars = bars_from_prices(
            "2026-03-13 17:05", [100.0 + (i * 0.15) for i in range(30)]
        )
        self.engine._last_price = float(self.engine._bars["close"].iloc[-1])
        self.engine._latest_market_data = MarketData(
            symbol="ES",
            bid=self.engine._last_price - 0.25,
            ask=self.engine._last_price + 0.25,
            last=self.engine._last_price,
            volume=1000,
            timestamp=self.engine._bars.index[-1].tz_convert("UTC").to_pydatetime(),
        )
        self.engine._latest_flow_snapshot = OrderFlowSnapshot()
        obs = MagicMock()
        obs.get_run_id.return_value = "run-test"
        self.engine.observability = obs
        decision = MatrixDecision(
            zone_name="Outside",
            action="LONG",
            reason="test_invalid_gate",
            long_score=4.0,
            short_score=1.0,
            flat_bias=0.0,
            active_vetoes=[],
            feature_snapshot=FeatureSnapshot(
                zone_name="Outside",
                current_price=self.engine._last_price,
                atr_value=1.0,
                long_features={},
                short_features={},
                flat_features={},
                signed_features={},
            ),
            execution_tradeable=True,
            size_fraction=1.0,
            side="buy",
            stop_loss=self.engine._last_price - 4.0,
            take_profit=self.engine._last_price + 8.0,
            max_hold_minutes=30,
        )

        with patch.object(
            self.engine.scheduler,
            "get_current_zone",
            return_value=None,
        ):
            with patch.object(self.engine.matrix, "evaluate", return_value=decision):
                with patch.object(self.engine.risk_manager, "can_trade", return_value=(True, "")):
                    with patch.object(self.engine, "_determine_contracts", return_value=1):
                        with patch.object(self.engine.executor, "place_order") as place_order:
                            self.engine._evaluate_current_state(allow_entries=True)

        place_order.assert_not_called()
        payload = obs.record_decision_snapshot.call_args.args[0]
        self.assertEqual(payload["outcome"], "shadow_only_zone")
        self.assertEqual(payload["outcome_reason"], "launch_gate_config_invalid")
        self.assertEqual(payload["zone_state"], "blocked")


if __name__ == "__main__":
    unittest.main()
