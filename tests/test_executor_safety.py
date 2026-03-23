from __future__ import annotations

from datetime import UTC, datetime, timedelta
import unittest
from unittest.mock import MagicMock, patch

import requests

from src.config import load_config
from src.execution.executor import Order, OrderExecutor, OrderStatus
from src.market import MarketData
from src.market.topstep_client import TopstepClient


class _FakeObservability:
    def __init__(self) -> None:
        self.events: list[dict] = []
        self.lifecycle: list[dict] = []

    def record_event(self, **kwargs) -> None:
        self.events.append(kwargs)

    def record_order_lifecycle(self, payload: dict) -> None:
        self.lifecycle.append(payload)

    def get_run_id(self) -> str:
        return "test-run"


class _FailingClient:
    def get_market_data(self, symbol: str):
        return None

    def place_order(self, **kwargs):
        raise requests.RequestException("submit transport failure")

    def cancel_order(self, order_id: str) -> bool:
        raise requests.RequestException("cancel transport failure")


class _LiveClient:
    def __init__(self, *, market_timestamp: datetime) -> None:
        self.market_timestamp = market_timestamp

    def get_market_data(self, symbol: str):
        return MarketData(
            symbol=symbol,
            bid=6654.0,
            ask=6654.25,
            last=6654.25,
            volume=1,
            timestamp=self.market_timestamp,
        )

    def place_order(self, **kwargs):
        return "live-order-1"

    def cancel_order(self, order_id: str) -> bool:
        return True

    def enable_mock_mode(self) -> None:
        return None


class _TrackingCancelClient(_LiveClient):
    """Records cancel_order calls; returns True so local state can be cleared."""

    def __init__(self, *, market_timestamp: datetime) -> None:
        super().__init__(market_timestamp=market_timestamp)
        self.cancelled_ids: list[str] = []

    def cancel_order(self, order_id: str) -> bool:
        self.cancelled_ids.append(order_id)
        return True


class TestExecutorFailClosed(unittest.TestCase):
    def _make_executor(self) -> tuple[OrderExecutor, _FakeObservability]:
        config = load_config()
        config.order_execution.retry_attempts = 2
        config.order_execution.retry_delay_seconds = 0.0
        observability = _FakeObservability()
        with (
            patch("src.execution.executor.get_client", return_value=_FailingClient()),
            patch(
                "src.execution.executor.get_observability_store",
                return_value=observability,
            ),
        ):
            executor = OrderExecutor(config=config)
        return executor, observability

    def test_place_order_transport_failure_returns_none(self) -> None:
        executor, observability = self._make_executor()

        order = executor.place_order(
            "ES",
            1,
            "buy",
            order_type="market",
            use_limit_fallback=False,
        )

        self.assertIsNone(order)
        failure_events = [
            event
            for event in observability.events
            if event["event_type"] == "order_submission_failed"
        ]
        self.assertEqual(len(failure_events), 1)
        self.assertEqual(failure_events[0]["payload"]["error"], "submit transport failure")

    def test_cancel_order_transport_failure_returns_false(self) -> None:
        executor, observability = self._make_executor()
        now = datetime.now(UTC)
        executor._pending_orders["ord-1"] = Order(
            order_id="ord-1",
            symbol="ES",
            side="buy",
            quantity=1,
            order_type="limit",
            status=OrderStatus.OPEN,
            created_time=now,
            updated_time=now,
        )

        cancelled = executor.cancel_order("ord-1")

        self.assertFalse(cancelled)
        failure_events = [
            event for event in observability.events if event["event_type"] == "order_cancel_failed"
        ]
        self.assertEqual(len(failure_events), 1)
        self.assertEqual(failure_events[0]["payload"]["error"], "cancel transport failure")


class TestExecutorBrokerTruthReconciliation(unittest.TestCase):
    def _make_executor(
        self, *, market_timestamp: datetime | None = None
    ) -> tuple[OrderExecutor, _FakeObservability]:
        config = load_config()
        observability = _FakeObservability()
        client = _LiveClient(market_timestamp=market_timestamp or datetime.now(UTC))
        with (
            patch("src.execution.executor.get_client", return_value=client),
            patch(
                "src.execution.executor.get_observability_store",
                return_value=observability,
            ),
        ):
            executor = OrderExecutor(config=config)
        executor.reset_state(mock_mode=False)
        return executor, observability

    def test_live_order_timestamps_use_wall_clock_not_market_data_time(self) -> None:
        stale_market_time = datetime.now(UTC) - timedelta(hours=12)
        executor, _ = self._make_executor(market_timestamp=stale_market_time)

        before = datetime.now(UTC) - timedelta(seconds=2)
        order = executor.place_order("ES", 1, "sell", order_type="limit", limit_price=6654.25)
        after = datetime.now(UTC) + timedelta(seconds=2)

        self.assertIsNotNone(order)
        assert order is not None
        self.assertGreaterEqual(order.created_time, before)
        self.assertLessEqual(order.created_time, after)
        self.assertGreater(order.created_time, stale_market_time + timedelta(hours=1))

    def test_reconcile_broker_open_orders_clears_missing_local_entry(self) -> None:
        executor, _ = self._make_executor()
        now = datetime.now(UTC)
        executor._pending_orders["ghost-entry-1"] = Order(
            order_id="ghost-entry-1",
            symbol="ES",
            side="sell",
            quantity=1,
            order_type="limit",
            limit_price=6654.25,
            status=OrderStatus.OPEN,
            created_time=now,
            updated_time=now,
            is_protective=False,
            role="entry",
        )

        result = executor.reconcile_broker_open_orders("ES", [], event_time=now, broker_position=0)

        self.assertEqual(result["cleared_order_ids"], ["ghost-entry-1"])
        self.assertFalse(executor.has_active_entry_order("ES"))

    def test_reconcile_broker_open_orders_adopts_live_entry_when_flat(self) -> None:
        executor, _ = self._make_executor()
        now = datetime.now(UTC)

        result = executor.reconcile_broker_open_orders(
            "ES",
            [
                {
                    "id": "broker-open-1",
                    "side": "buy",
                    "size": 1,
                    "type": "limit",
                    "limitPrice": 6654.25,
                }
            ],
            event_time=now,
            broker_position=0,
        )

        self.assertEqual(result["adopted_order_ids"], ["broker-open-1"])
        self.assertTrue(executor.has_active_entry_order("ES"))
        self.assertIn(
            "broker-open-1", executor.get_watchdog_snapshot("ES")["active_entry_order_ids"]
        )


class TestReconcileStaleOrders(unittest.TestCase):
    """Stale order reconciliation must not cancel working protective orders by age."""

    def _make_executor(self, *, client: _LiveClient) -> OrderExecutor:
        config = load_config()
        config.watchdog.stale_order_seconds = 1
        observability = _FakeObservability()
        with (
            patch("src.execution.executor.get_client", return_value=client),
            patch(
                "src.execution.executor.get_observability_store",
                return_value=observability,
            ),
        ):
            executor = OrderExecutor(config=config)
        executor.reset_state(mock_mode=False)
        return executor

    def test_reconcile_pending_orders_skips_protective_orders(self) -> None:
        ts = datetime.now(UTC)
        old = ts - timedelta(seconds=120)
        client = _TrackingCancelClient(market_timestamp=ts)
        executor = self._make_executor(client=client)

        executor._pending_orders["stop-1"] = Order(
            order_id="stop-1",
            symbol="ES",
            side="sell",
            quantity=1,
            order_type="stop",
            stop_price=6500.0,
            status=OrderStatus.OPEN,
            created_time=old,
            updated_time=old,
            is_protective=True,
            role="stop_loss",
        )
        executor._pending_orders["entry-1"] = Order(
            order_id="entry-1",
            symbol="ES",
            side="buy",
            quantity=1,
            order_type="limit",
            limit_price=6654.25,
            status=OrderStatus.OPEN,
            created_time=old,
            updated_time=old,
            is_protective=False,
            role="entry",
        )

        cancelled = executor.reconcile_pending_orders()

        self.assertEqual(cancelled, 1)
        self.assertEqual(client.cancelled_ids, ["entry-1"])
        self.assertIn("stop-1", executor._pending_orders)
        self.assertNotIn("entry-1", executor._pending_orders)


class TestTopstepCancelNonCancellable(unittest.TestCase):
    def test_cancel_order_returns_true_for_error_code_5_empty_message(self) -> None:
        client = TopstepClient()
        client._account_id = 1
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "success": False,
            "errorCode": 5,
            "errorMessage": None,
        }
        with (
            patch.object(client, "_ensure_auth", return_value=True),
            patch.object(client, "_post_with_retry", return_value=mock_resp),
            patch.object(client, "_record_event"),
        ):
            self.assertTrue(client.cancel_order("12345"))


class TestMockLimitTouchFillRatio(unittest.TestCase):
    def test_limit_touch_fill_ratio_zero_never_fills_on_touch(self) -> None:
        config = load_config()
        config.replay_execution.limit_touch_fill_ratio = 0.0
        observability = _FakeObservability()
        with (
            patch(
                "src.execution.executor.get_client",
                return_value=_LiveClient(market_timestamp=datetime.now(UTC)),
            ),
            patch("src.execution.executor.get_observability_store", return_value=observability),
        ):
            executor = OrderExecutor(config=config)
        executor.enable_mock_mode()
        ts = datetime(2025, 3, 1, 16, 0, tzinfo=UTC)
        order = executor.place_order(
            "ES",
            1,
            "buy",
            "limit",
            limit_price=6655.0,
            use_limit_fallback=False,
        )
        self.assertIsNotNone(order)
        md = MarketData(
            symbol="ES",
            bid=6654.0,
            ask=6654.25,
            last=6654.25,
            volume=1,
            timestamp=ts,
        )
        executor.process_market_data(md)
        self.assertEqual(executor.get_position("ES"), 0)

    def test_limit_touch_fill_ratio_one_fills_on_touch(self) -> None:
        config = load_config()
        config.replay_execution.limit_touch_fill_ratio = 1.0
        observability = _FakeObservability()
        with (
            patch(
                "src.execution.executor.get_client",
                return_value=_LiveClient(market_timestamp=datetime.now(UTC)),
            ),
            patch("src.execution.executor.get_observability_store", return_value=observability),
        ):
            executor = OrderExecutor(config=config)
        executor.enable_mock_mode()
        ts = datetime(2025, 3, 1, 16, 0, tzinfo=UTC)
        order = executor.place_order(
            "ES",
            1,
            "buy",
            "limit",
            limit_price=6655.0,
            use_limit_fallback=False,
        )
        self.assertIsNotNone(order)
        md = MarketData(
            symbol="ES",
            bid=6654.0,
            ask=6654.25,
            last=6654.25,
            volume=1,
            timestamp=ts,
        )
        executor.process_market_data(md)
        self.assertEqual(executor.get_position("ES"), 1)
