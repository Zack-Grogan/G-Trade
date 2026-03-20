from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
from src.config import load_config, set_config
from src.indicators import session_vwap_bands
from src.observability import get_observability_store
from src.server.flask_console import _decision_markers
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
            execution={
                "decision_id": "decision-1",
                "attempt_id": "attempt-1",
                "trade_id": "trade-1",
            },
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
                "execution": {
                    "decision_id": "decision-1",
                    "attempt_id": "attempt-1",
                    "trade_id": "trade-1",
                },
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
        chart_page = self.client.get("/chart").get_data(as_text=True)
        self.assertIn("Window", chart_page)
        self.assertIn(">7d<", chart_page)

    def test_chart_api_exposes_candles_and_levels(self) -> None:
        response = self.client.get("/api/chart")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(len(payload["candles"]), 1)
        self.assertIn("series", payload)
        self.assertIn("levels", payload)
        self.assertEqual(payload["summary"]["lookback_hours"], 168)
        self.assertEqual(payload["series"]["price"], [])
        self.assertEqual(len(payload["series"]["vwap"]), len(payload["candles"]))
        if len(payload["candles"]) > 1:
            self.assertNotEqual(
                payload["candles"][0]["close"],
                payload["candles"][-1]["close"],
            )

    def test_decision_markers_accept_legacy_action_names(self) -> None:
        markers = _decision_markers(
            [
                {
                    "decided_at": datetime.now(UTC),
                    "action": "enter_long",
                    "reason": "legacy_action",
                    "outcome": "submit_order",
                }
            ]
        )
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]["shape"], "arrowUp")

    def test_chart_api_keeps_market_history_across_runs(self) -> None:
        earlier = datetime.now(UTC) - timedelta(hours=10)
        self.store.record_market_tick(
            {
                "run_id": "older-run",
                "symbol": "ES",
                "captured_at": earlier,
                "last": 6601.25,
                "volume": 4,
            }
        )
        self.store.force_flush()
        response = self.client.get("/api/chart?lookback_hours=12")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["candles"][0]["time"], int(earlier.timestamp() // 60) * 60)

    def test_chart_api_supports_week_window(self) -> None:
        week_old = datetime.now(UTC) - timedelta(days=6, hours=12)
        self.store.record_market_tick(
            {
                "run_id": "history-run",
                "symbol": "ES",
                "captured_at": week_old,
                "last": 6598.5,
                "volume": 9,
                "source": "HistoryBar",
                "open": 6597.0,
                "high": 6600.0,
                "low": 6596.5,
                "close": 6598.5,
                "historical": True,
            }
        )
        self.store.force_flush()
        payload = self.client.get("/api/chart?lookback_hours=168").get_json()
        self.assertLessEqual(
            datetime.fromisoformat(payload["history"]["coverage_start"]),
            week_old + timedelta(minutes=1),
        )
        self.assertEqual(payload["summary"]["lookback_hours"], 168)

    def test_chart_api_builds_candle_from_history_bar_payload(self) -> None:
        historical_time = datetime.now(UTC) - timedelta(hours=9, minutes=30)
        self.store.record_market_tick(
            {
                "run_id": "history-run",
                "symbol": "ES",
                "captured_at": historical_time,
                "last": 6611.0,
                "volume": 21,
                "source": "HistoryBar",
                "open": 6610.0,
                "high": 6614.5,
                "low": 6608.25,
                "close": 6611.0,
                "historical": True,
            }
        )
        self.store.force_flush()
        response = self.client.get("/api/chart?lookback_hours=12")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        bucket_time = int(historical_time.timestamp() // 60) * 60
        candle = next(item for item in payload["candles"] if item["time"] == bucket_time)
        self.assertEqual(candle["open"], 6610.0)
        self.assertEqual(candle["high"], 6614.5)
        self.assertEqual(candle["low"], 6608.25)
        self.assertEqual(candle["close"], 6611.0)

    def test_history_bar_overrides_same_bucket_tick_candle(self) -> None:
        bucket_time = datetime.now(UTC) - timedelta(hours=4)
        self.store.record_market_tick(
            {
                "run_id": self.run_id,
                "symbol": "ES",
                "captured_at": bucket_time,
                "last": 6612.0,
                "volume": 3,
            }
        )
        self.store.record_market_tick(
            {
                "run_id": "history-run",
                "symbol": "ES",
                "captured_at": bucket_time,
                "last": 6613.0,
                "volume": 17,
                "source": "HistoryBar",
                "open": 6611.0,
                "high": 6615.0,
                "low": 6610.5,
                "close": 6613.0,
                "historical": True,
            }
        )
        self.store.force_flush()
        payload = self.client.get("/api/chart?lookback_hours=168").get_json()
        candle_bucket = int(bucket_time.timestamp() // 60) * 60
        candle = next(item for item in payload["candles"] if item["time"] == candle_bucket)
        self.assertEqual(candle["open"], 6611.0)
        self.assertEqual(candle["high"], 6615.0)
        self.assertEqual(candle["low"], 6610.5)
        self.assertEqual(candle["close"], 6613.0)

    def test_chart_vwap_series_matches_session_math(self) -> None:
        start = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(hours=2)
        rows = [
            (6620.0, 6622.0, 6619.5, 6621.0, 10),
            (6621.0, 6623.5, 6620.5, 6623.0, 14),
            (6623.0, 6625.0, 6622.5, 6624.5, 16),
        ]
        for idx, (o, h, low, c, v) in enumerate(rows):
            self.store.record_market_tick(
                {
                    "run_id": "history-run",
                    "symbol": "ES",
                    "captured_at": start + timedelta(minutes=idx),
                    "last": c,
                    "volume": v,
                    "source": "HistoryBar",
                    "open": o,
                    "high": h,
                    "low": low,
                    "close": c,
                    "historical": True,
                }
            )
        self.store.force_flush()
        payload = self.client.get("/api/chart?lookback_hours=168").get_json()
        target_candles = payload["candles"][-3:]
        frame = pd.DataFrame(
            {
                "open": [row["open"] for row in target_candles],
                "high": [row["high"] for row in target_candles],
                "low": [row["low"] for row in target_candles],
                "close": [row["close"] for row in target_candles],
                "volume": [row["volume"] for row in target_candles],
            },
            index=pd.to_datetime(
                [row["time"] for row in target_candles], unit="s", utc=True
            ).tz_convert(self.config.sessions.timezone),
        )
        expected = session_vwap_bands(
            frame,
            self.config.sessions.eth_reset_hour,
            self.config.sessions.eth_reset_minute,
            self.config.strategy.vwap_source,
        )
        actual_last = payload["series"]["vwap"][-1]["value"]
        self.assertAlmostEqual(actual_last, float(expected.vwap.iloc[-1]), places=6)

    def test_chart_alpha_series_carries_forward_between_decisions(self) -> None:
        base = datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(hours=3)
        for idx in range(4):
            self.store.record_market_tick(
                {
                    "run_id": "history-run",
                    "symbol": "ES",
                    "captured_at": base + timedelta(minutes=idx),
                    "last": 6610.0 + idx,
                    "volume": 5 + idx,
                    "source": "HistoryBar",
                    "open": 6610.0 + idx,
                    "high": 6610.5 + idx,
                    "low": 6609.75 + idx,
                    "close": 6610.25 + idx,
                    "historical": True,
                }
            )
        self.store.record_decision_snapshot(
            {
                "run_id": self.run_id,
                "decision_id": "carry-1",
                "decided_at": base,
                "symbol": "ES",
                "zone": "Pre-Open",
                "action": "LONG",
                "reason": "carry_forward",
                "outcome": "submit_order",
                "outcome_reason": "carry_forward",
                "long_score": 5.5,
                "short_score": 1.5,
                "flat_bias": 0.4,
            }
        )
        self.store.force_flush()
        payload = self.client.get("/api/chart?lookback_hours=168").get_json()
        alpha_points = [
            point
            for point in payload["series"]["alpha_long"]
            if point["time"] >= int(base.timestamp())
        ]
        self.assertGreaterEqual(len(alpha_points), 4)
        self.assertTrue(all(point["value"] == 5.5 for point in alpha_points[:4]))

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
