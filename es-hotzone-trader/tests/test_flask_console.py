from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.config import load_config, set_config
from src.observability import get_observability_store
from src.server.debug_server import create_app, set_state


class FlaskConsoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.config = load_config()
        self.config.observability.enabled = True
        self.config.observability.sqlite_path = str(Path(self._temp_dir.name) / "observability.db")
        self.config.server.health_port = 0
        self.config.server.debug_port = 0
        set_config(self.config)
        self.store = get_observability_store(force_recreate=True, config=self.config)
        self.run_id = "test-run"
        now = datetime.now(UTC)
        started = now - timedelta(hours=6)
        ended = now - timedelta(hours=5, minutes=15)

        set_state(
            running=True,
            status="running",
            data_mode="live",
            current_zone="Pre-Open",
            zone_state="active",
            position=1,
            position_pnl=125.5,
            daily_pnl=842.25,
            account_balance=51250,
            account_open_pnl=45.5,
            account_realized_pnl=796.75,
            account_id="PRAC-V2-546557-70802903",
            account_name="PRAC-V2-546557-70802903",
            account_is_practice=True,
            long_score=7.5,
            short_score=2.25,
            flat_bias=0.1,
            active_vetoes=["event_blackout"],
            matrix_version="hotzone-v3",
            last_entry_reason="pre-open_short_matrix",
            last_exit_reason="dynamic_exit",
            active_session="ETH",
            anchored_vwaps={"ETH": 6622.5},
            vwap_bands={"upper": 6636.5, "lower": 6629.4},
            volume_profile={"value_area_high": 6638.0, "value_area_low": 6618.0},
            regime={"state": "TREND", "reason": "session_open"},
            execution={"decision_id": "decision-1", "attempt_id": "attempt-1", "trade_id": "trade-1"},
            broker_truth={"status": "adopted", "summary": "Selected account short open"},
            heartbeat={"market_stream_connected": True},
            event_context={"zone": "Pre-Open"},
            last_signal={"symbol": "ES"},
            last_price=6623.75,
            trades_today=1,
            trades_this_hour=1,
            trades_this_zone=1,
            risk_state="normal",
            run_id=self.run_id,
            observability_db_path=self.config.observability.sqlite_path,
        )

        self.store.record_run_manifest(
            {
                "run_id": self.run_id,
                "started_at": started,
                "data_mode": "live",
                "symbols": ["ES"],
                "account_id": "PRAC-V2-546557-70802903",
                "account_name": "PRAC-V2-546557-70802903",
                "account_is_practice": True,
                "config_path": "config/default.yaml",
                "config_hash": "abc123",
                "log_path": "logs/trading.log",
                "sqlite_path": self.config.observability.sqlite_path,
                "git_commit": "deadbeef",
                "git_branch": "main",
                "git_dirty": False,
                "git_available": True,
                "app_version": "test",
            }
        )
        self.store.record_state_snapshot(
            {
                "run_id": self.run_id,
                "status": "running",
                "data_mode": "live",
                "zone": {"name": "Pre-Open", "state": "active"},
                "position": {"contracts": 1, "pnl": 125.5},
                "account": {"daily_pnl": 842.25},
                "risk": {"state": "normal"},
                "account_id": "PRAC-V2-546557-70802903",
                "account_name": "PRAC-V2-546557-70802903",
                "account_is_practice": True,
                "execution": {"decision_id": "decision-1", "attempt_id": "attempt-1", "trade_id": "trade-1"},
            },
            event_time=now,
        )
        self.store.record_market_tick(
            {
                "run_id": self.run_id,
                "symbol": "ES",
                "captured_at": started + timedelta(minutes=1),
                "last": 6620.0,
                "volume": 10,
            }
        )
        self.store.record_market_tick(
            {
                "run_id": self.run_id,
                "symbol": "ES",
                "captured_at": started + timedelta(minutes=2),
                "last": 6624.0,
                "volume": 12,
            }
        )
        self.store.record_decision_snapshot(
            {
                "run_id": self.run_id,
                "decision_id": "decision-1",
                "decided_at": started + timedelta(minutes=1),
                "symbol": "ES",
                "zone": "Pre-Open",
                "action": "enter_long",
                "reason": "pre-open_short_matrix",
                "outcome": "submit_order",
                "outcome_reason": "matrix_not_decisive",
                "long_score": 7.5,
                "short_score": 2.25,
                "flat_bias": 0.1,
                "score_gap": 5.25,
                "dominant_side": "long",
                "current_price": 6620.0,
                "allow_entries": True,
                "execution_tradeable": True,
                "contracts": 1,
                "order_type": "limit",
                "limit_price": 6620.0,
                "decision_price": 6620.0,
                "side": "buy",
                "stop_loss": 6614.0,
                "take_profit": 6632.0,
                "max_hold_minutes": 40,
                "regime_state": "TREND",
                "regime_reason": "session_open",
                "active_session": "ETH",
                "active_vetoes": ["event_blackout"],
                "feature_snapshot": {"atr": 1.2},
                "entry_guard": {"allowed": True},
                "unresolved_entry": {},
                "event_context": {"zone": "Pre-Open"},
                "order_flow": {"ofi": 1.5},
            }
        )
        self.store.record_order_lifecycle(
            {
                "run_id": self.run_id,
                "order_id": "order-1",
                "decision_id": "decision-1",
                "attempt_id": "attempt-1",
                "observed_at": started + timedelta(minutes=2),
                "symbol": "ES",
                "event_type": "order_submitted",
                "status": "working",
                "side": "buy",
                "role": "entry",
                "is_protective": False,
                "order_type": "limit",
                "quantity": 1,
                "contracts": 1,
                "limit_price": 6620.0,
                "zone": "Pre-Open",
                "reason": "pre-open_short_matrix",
                "lifecycle_state": "working",
            }
        )
        self.store.record_runtime_log(
            {
                "run_id": self.run_id,
                "logged_at": now,
                "logger_name": "src.engine.trading_engine",
                "level": "INFO",
                "source": "local-runtime",
                "service_name": "es-hotzone-trader",
                "process_id": 1234,
                "line_hash": "abc123",
                "thread_name": "MainThread",
                "message": "Placed trade for test",
                "exception_text": None,
            }
        )
        self.store.record_runtime_log(
            {
                "run_id": self.run_id,
                "logged_at": now,
                "logger_name": "werkzeug",
                "level": "INFO",
                "source": "local-runtime",
                "service_name": "es-hotzone-trader",
                "process_id": 1234,
                "line_hash": "noise123",
                "thread_name": "Thread-1",
                "message": '127.0.0.1 - - [19/Mar/2026 13:11:13] "GET /api/state HTTP/1.1" 200 -',
                "exception_text": None,
            }
        )
        self.store.record_bridge_health(
            {
                "run_id": self.run_id,
                "observed_at": now,
                "bridge_status": "running",
                "queue_depth": 1,
                "last_error": None,
            }
        )
        self.store.record_completed_trade(
            {
                "run_id": self.run_id,
                "entry_time": started + timedelta(minutes=1),
                "exit_time": ended,
                "direction": 1,
                "contracts": 1,
                "entry_price": 6620.0,
                "exit_price": 6625.5,
                "pnl": 275.0,
                "zone": "Pre-Open",
                "strategy": "morning",
                "regime": "TREND",
                "event_tags": ["morning"],
                "trade_id": "trade-1",
                "position_id": "position-1",
                "decision_id": "decision-1",
                "attempt_id": "attempt-1",
                "account_id": "PRAC-V2-546557-70802903",
                "account_name": "PRAC-V2-546557-70802903",
                "account_is_practice": True,
            },
            run_id=self.run_id,
        )
        self.store.record_account_trade(
            {
                "run_id": self.run_id,
                # Align with Pacific "today" in the console (see flask_console._ledger_calendar_day_trade_stats).
                "occurred_at": now,
                "account_id": "PRAC-V2-546557-70802903",
                "account_name": "PRAC-V2-546557-70802903",
                "account_is_practice": True,
                "broker_trade_id": "broker-trade-1",
                "broker_order_id": "order-1",
                "contract_id": "CON.F.US.EP.M26",
                "side": 1,
                "size": 1,
                "price": 6625.5,
                "profit_and_loss": 275.0,
                "fees": 1.25,
                "voided": False,
            },
            run_id=self.run_id,
        )
        self.store.force_flush()
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.store.stop()
        set_state(running=False, status="stopped")
        self._temp_dir.cleanup()

    def test_health_and_debug_routes_return_json(self) -> None:
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json()["status"], "healthy")

        debug = self.client.get("/debug")
        self.assertEqual(debug.status_code, 200)
        payload = debug.get_json()
        self.assertEqual(payload["run_id"], self.run_id)
        self.assertTrue(payload["running"])

    def test_required_html_routes_render(self) -> None:
        for path, marker in [
            ("/", "Live state"),
            ("/chart", "Price"),
            ("/trades", "Broker fill journal"),
            ("/trades/1", "Trade review"),
            ("/logs", "Runtime activity"),
            ("/system", "System"),
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(marker, response.get_data(as_text=True))
        trades_page = self.client.get("/trades").get_data(as_text=True)
        logs_page = self.client.get("/logs").get_data(as_text=True)
        self.assertTrue("PDT" in trades_page or "PST" in trades_page)
        self.assertNotIn("GET /api/state", logs_page)
        home = self.client.get("/").get_data(as_text=True)
        self.assertIn("Trades today 1", home)
        self.assertIn("Losses 0", home)

    def test_chart_api_exposes_candles_and_levels(self) -> None:
        response = self.client.get("/api/chart")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(len(payload["candles"]), 1)
        self.assertIn("series", payload)
        self.assertIn("levels", payload)

    def test_trades_and_logs_apis_are_filtered_for_operator_use(self) -> None:
        trades = self.client.get("/api/trades")
        logs = self.client.get("/api/logs")
        self.assertEqual(trades.status_code, 200)
        self.assertEqual(logs.status_code, 200)
        trade_payload = trades.get_json()
        log_payload = logs.get_json()
        self.assertEqual(trade_payload["account_trades"][0]["side_label"], "Sell")
        self.assertNotIn("werkzeug", [row["logger_name"] for row in log_payload["logs"]])

    def test_stream_state_smoke(self) -> None:
        response = self.client.get("/stream/state")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/event-stream", response.headers.get("Content-Type", ""))
        first_chunk = next(response.response)
        self.assertIn(b": connected", first_chunk)

    def test_console_risk_panel_counts_losing_ledger_rows_today(self) -> None:
        now = datetime.now(UTC)
        self.store.record_account_trade(
            {
                "run_id": self.run_id,
                "occurred_at": now,
                "account_id": "PRAC-V2-546557-70802903",
                "account_name": "PRAC-V2-546557-70802903",
                "account_is_practice": True,
                "broker_trade_id": "broker-trade-loss-1",
                "broker_order_id": "order-loss-1",
                "contract_id": "CON.F.US.EP.M26",
                "side": 1,
                "size": 1,
                "price": 6600.0,
                "profit_and_loss": -42.0,
                "fees": 1.0,
                "voided": False,
            },
            run_id=self.run_id,
        )
        self.store.force_flush()
        home = self.client.get("/").get_data(as_text=True)
        self.assertIn("Trades today 2", home)
        self.assertIn("Losses 1", home)


if __name__ == "__main__":
    unittest.main()
