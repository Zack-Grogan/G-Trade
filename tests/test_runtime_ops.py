from __future__ import annotations

import plistlib
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from src.cli.commands import (
    _fetch_broker_truth,
    _startup_zone_surface,
    _sync_account_trade_history,
    cli,
)
from src.cli.launchd import LAUNCHD_LABEL, render_launchd_plist
from src.config import get_config, load_config, set_config
from src.observability import get_observability_store
from src.runtime.inspection import fetch_runtime_health_dict, runtime_status_path
from src.runtime.zone_surface import resolve_launch_gate_zone_state


class RuntimeOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_config = get_config()

    def tearDown(self) -> None:
        set_config(self.previous_config)

    def _build_config(self, temp_dir: str):
        config = load_config()
        config.observability.enabled = True
        config.observability.sqlite_path = str(Path(temp_dir) / "observability.db")
        config.logging.file = str(Path(temp_dir) / "trading.log")
        set_config(config)
        return config

    def test_observability_store_persists_runtime_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._build_config(temp_dir)
            store = get_observability_store(force_recreate=True, config=config)
            store.start()
            store.record_runtime_log(
                {
                    "logger_name": "tests.runtime",
                    "level": "ERROR",
                    "process_id": 42,
                    "service_name": "es-hotzone-trader",
                    "source": "local-runtime",
                    "line_hash": "abc123",
                    "thread_name": "MainThread",
                    "message": "bridge auth failed",
                    "exception_text": "HTTP 401",
                }
            )
            store.force_flush()

            rows = store.query_runtime_logs(limit=10, level="ERROR", search="auth")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["message"], "bridge auth failed")
            self.assertEqual(rows[0]["payload"]["exception_text"], "HTTP 401")
            store.stop()

    def test_observability_store_filters_rows_by_tenant_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            alpha_config = self._build_config(temp_dir)
            alpha_config.tenant_id = "tenant-alpha"
            alpha_store = get_observability_store(force_recreate=True, config=alpha_config)
            alpha_store.start()
            alpha_store.record_event(
                category="system",
                event_type="tenant_scoped_event",
                source="tests.runtime",
                payload={"tenant": "alpha"},
                action="record",
                reason="tenant_alpha",
            )
            alpha_store.force_flush()

            alpha_rows = alpha_store.query_events(
                limit=10, category="system", event_type="tenant_scoped_event"
            )
            self.assertEqual(len(alpha_rows), 1)
            self.assertEqual(alpha_rows[0]["tenant_id"], "tenant-alpha")

            alpha_store.stop()

            beta_config = self._build_config(temp_dir)
            beta_config.tenant_id = "tenant-beta"
            beta_store = get_observability_store(force_recreate=True, config=beta_config)
            beta_store.start()

            beta_rows = beta_store.query_events(
                limit=10, category="system", event_type="tenant_scoped_event"
            )

            self.assertEqual(beta_rows, [])
            beta_store.stop()

    def test_start_command_help_exposes_live_flag(self) -> None:
        runner = CliRunner()

        result = runner.invoke(cli, ["start", "--help"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("--live", result.output)

    def test_config_command_reports_tenant_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._build_config(temp_dir)
            config.tenant_id = "tenant-report"
            set_config(config)

            runner = CliRunner()
            result = runner.invoke(cli, ["config"])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("Tenant ID:", result.output)
            self.assertIn("tenant-report", result.output)

    def test_observability_store_recovers_after_flush_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._build_config(temp_dir)
            config.observability.flush_interval_ms = 10
            config.observability.batch_size = 1
            store = get_observability_store(force_recreate=True, config=config)
            store.start()

            original_write = store._write_records_locked
            attempts = {"count": 0}

            def flaky_write(records):
                attempts["count"] += 1
                if attempts["count"] == 1:
                    raise sqlite3.OperationalError("simulated flush failure")
                return original_write(records)

            with patch.object(store, "_write_records_locked", side_effect=flaky_write):
                store.record_event(
                    category="system",
                    event_type="flush_test",
                    source="tests.runtime",
                    payload={"value": 1},
                    action="record",
                    reason="flush_recovery_test",
                )
                store.record_runtime_log(
                    {
                        "logger_name": "tests.runtime",
                        "level": "INFO",
                        "process_id": 42,
                        "service_name": "es-hotzone-trader",
                        "source": "local-runtime",
                        "line_hash": "recover123",
                        "thread_name": "MainThread",
                        "message": "after recovery",
                    }
                )

                deadline = time.time() + 5.0
                runtime_rows = []
                event_rows = []
                while time.time() < deadline:
                    runtime_rows = store.query_runtime_logs(limit=10, search="after recovery")
                    event_rows = store.query_events(limit=10, search="flush_recovery_test")
                    if runtime_rows and event_rows and attempts["count"] >= 2:
                        break
                    time.sleep(0.05)

            self.assertTrue(store.enabled())
            self.assertGreaterEqual(attempts["count"], 2)
            self.assertEqual(len(event_rows), 1)
            self.assertEqual(event_rows[0]["event_type"], "flush_test")
            self.assertEqual(len(runtime_rows), 1)
            self.assertEqual(runtime_rows[0]["message"], "after recovery")
            store.stop()

    def test_observability_store_upgrades_existing_completed_trades_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._build_config(temp_dir)
            db_path = Path(config.observability.sqlite_path)
            with sqlite3.connect(db_path) as conn:
                conn.execute("""
                    CREATE TABLE completed_trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_id TEXT NOT NULL,
                        inserted_at TEXT NOT NULL,
                        entry_time TEXT,
                        exit_time TEXT NOT NULL,
                        direction INTEGER NOT NULL,
                        contracts INTEGER NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL NOT NULL,
                        pnl REAL NOT NULL,
                        zone TEXT,
                        strategy TEXT,
                        regime TEXT,
                        event_tags_json TEXT NOT NULL,
                        source TEXT NOT NULL,
                        backfilled INTEGER NOT NULL DEFAULT 0,
                        trade_id TEXT,
                        position_id TEXT,
                        decision_id TEXT,
                        attempt_id TEXT,
                        payload_json TEXT NOT NULL,
                        UNIQUE(run_id, exit_time, direction, contracts, entry_price, exit_price, pnl, zone, strategy)
                    )
                    """)
                conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
                conn.execute(
                    "INSERT INTO metadata(key, value) VALUES (?, ?)",
                    ("schema_version", "4"),
                )
                conn.commit()

            store = get_observability_store(force_recreate=True, config=config)
            store.start()
            store.stop()

            with sqlite3.connect(db_path) as conn:
                columns = [
                    row[1] for row in conn.execute("PRAGMA table_info(completed_trades)").fetchall()
                ]
            self.assertIn("account_id", columns)
            self.assertIn("account_name", columns)
            self.assertIn("account_mode", columns)
            self.assertIn("account_is_practice", columns)

    def test_startup_account_trade_sync_authenticates_before_reading_account(self) -> None:
        class FakeAccount:
            account_id = "20139389"
            name = "PRAC-V2-546557-70802903"
            is_practice = True

        class FakeClient:
            def __init__(self) -> None:
                self._access_token = None
                self.authenticate_calls = 0
                self.search_trades_calls = 0

            def authenticate(self) -> bool:
                self.authenticate_calls += 1
                self._access_token = "token"
                return True

            def get_account(self):
                if not self._access_token:
                    return None
                return FakeAccount()

            def search_trades(self, *, start_timestamp: str, end_timestamp: str, account_id: int):
                self.search_trades_calls += 1
                self.last_account_id = account_id
                return [
                    {
                        "id": "trade-1",
                        "accountId": account_id,
                        "side": 1,
                        "size": 1,
                        "price": 6789.25,
                        "profitAndLoss": 42.5,
                        "creationTimestamp": "2026-03-18T14:30:00Z",
                    }
                ]

        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._build_config(temp_dir)
            store = get_observability_store(force_recreate=True, config=config)
            store.start()
            fake_client = FakeClient()
            with patch("src.cli.commands.get_client", return_value=fake_client):
                result = _sync_account_trade_history(
                    config,
                    store,
                    source="startup_account_history_sync",
                    lookback_hours=1,
                )
            self.assertEqual(result["error"] if "error" in result else None, None)
            self.assertEqual(result["checked"], 1)
            self.assertEqual(result["imported"], 1)
            self.assertEqual(fake_client.authenticate_calls, 1)
            self.assertEqual(fake_client.search_trades_calls, 1)
            self.assertEqual(fake_client.last_account_id, 20139389)

            rows = store.query_account_trades(limit=10)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["broker_trade_id"], "trade-1")
            self.assertEqual(rows[0]["account_id"], "20139389")
            store.stop()

    def test_fetch_broker_truth_authenticates_before_requesting_bundle(self) -> None:
        class FakeClient:
            def __init__(self) -> None:
                self.authenticate_calls = 0
                self.last_args = None

            def authenticate(self) -> bool:
                self.authenticate_calls += 1
                return True

            def get_broker_truth_bundle(
                self,
                symbol: str,
                *,
                lookback_minutes: int,
                focus_timestamp: str | None,
                include_history: bool,
            ):
                self.last_args = {
                    "symbol": symbol,
                    "lookback_minutes": lookback_minutes,
                    "focus_timestamp": focus_timestamp,
                    "include_history": include_history,
                }
                return {"symbol": symbol, "account": {"id": "20139389"}}

        with tempfile.TemporaryDirectory() as temp_dir:
            config = self._build_config(temp_dir)
            fake_client = FakeClient()
            with patch("src.cli.commands.get_client", return_value=fake_client):
                payload = _fetch_broker_truth(
                    config,
                    symbol="ES",
                    lookback_minutes=30,
                    focus_timestamp="2026-03-19T11:35:01Z",
                )

        self.assertEqual(payload["symbol"], "ES")
        self.assertEqual(fake_client.authenticate_calls, 1)
        self.assertEqual(
            fake_client.last_args,
            {
                "symbol": "ES",
                "lookback_minutes": 30,
                "focus_timestamp": "2026-03-19T11:35:01Z",
                "include_history": True,
            },
        )

    def test_render_launchd_plist_embeds_cli_start(self) -> None:
        payload = render_launchd_plist("/tmp/gtrade-config.yaml")
        parsed = plistlib.loads(payload)
        self.assertEqual(parsed["Label"], LAUNCHD_LABEL)
        self.assertIn("src.cli", parsed["ProgramArguments"])
        self.assertIn("--config", parsed["ProgramArguments"])

    def test_render_launchd_plist_sets_python_unbuffered_env(self) -> None:
        payload = render_launchd_plist()
        parsed = plistlib.loads(payload)
        self.assertEqual(parsed["EnvironmentVariables"]["PYTHONUNBUFFERED"], "1")

    def test_startup_zone_surface_marks_outside_as_shadow_in_default_profile(self) -> None:
        cfg = load_config()

        current_zone, zone_state, message = _startup_zone_surface(cfg, None)

        self.assertEqual(current_zone, "Outside")
        self.assertEqual(zone_state, "shadow")
        self.assertEqual(message, "Current zone: Outside (shadow)")

    def test_startup_zone_surface_marks_outside_as_blocked_when_not_live_or_shadow(self) -> None:
        cfg = load_config()
        cfg.strategy.shadow_entry_zones = ["Post-Open", "Midday"]

        current_zone, zone_state, message = _startup_zone_surface(cfg, None)

        self.assertEqual(current_zone, "Outside")
        self.assertEqual(zone_state, "blocked")
        self.assertEqual(message, "Current zone: Outside (blocked)")

    def test_startup_zone_surface_marks_named_shadow_zone_as_shadow(self) -> None:
        cfg = load_config()

        class ShadowZone:
            name = "Post-Open"

            class state:
                value = "active"

        current_zone, zone_state, message = _startup_zone_surface(cfg, ShadowZone())

        self.assertEqual(current_zone, "Post-Open")
        self.assertEqual(zone_state, "shadow")
        self.assertEqual(message, "Current zone: Post-Open (shadow)")

    def test_resolve_launch_gate_zone_state_marks_named_shadow_zone_as_shadow(self) -> None:
        cfg = load_config()

        zone_state = resolve_launch_gate_zone_state(
            cfg.strategy,
            zone_name="Post-Open",
            scheduled_zone_state="active",
        )

        self.assertEqual(zone_state, "shadow")

    def test_resolve_launch_gate_zone_state_blocks_overlap_when_gate_enabled(self) -> None:
        cfg = load_config()
        cfg.strategy.live_entry_zones = ["Pre-Open", "Outside"]
        cfg.strategy.shadow_entry_zones = ["Outside"]

        zone_state = resolve_launch_gate_zone_state(
            cfg.strategy,
            zone_name="Outside",
            scheduled_zone_state="active",
        )

        self.assertEqual(zone_state, "blocked")

    def test_resolve_launch_gate_zone_state_uses_scheduler_active_when_gate_disabled(self) -> None:
        cfg = load_config()
        cfg.strategy.launch_gate_enabled = False
        cfg.strategy.live_entry_zones = []
        cfg.strategy.shadow_entry_zones = []

        zone_state = resolve_launch_gate_zone_state(
            cfg.strategy,
            zone_name="Post-Open",
            scheduled_zone_state="active",
        )

        self.assertEqual(zone_state, "active")

    def test_resolve_launch_gate_zone_state_preserves_flatten_only_scheduler_state(self) -> None:
        cfg = load_config()

        zone_state = resolve_launch_gate_zone_state(
            cfg.strategy,
            zone_name="Close-Scalp",
            scheduled_zone_state="flatten_only",
        )

        self.assertEqual(zone_state, "flatten_only")

    def test_resolve_launch_gate_zone_state_marks_missing_live_and_shadow_as_blocked(self) -> None:
        cfg = load_config()
        cfg.strategy.live_entry_zones = ["Pre-Open"]
        cfg.strategy.shadow_entry_zones = ["Post-Open", "Midday"]

        zone_state = resolve_launch_gate_zone_state(
            cfg.strategy,
            zone_name="Outside",
            scheduled_zone_state="active",
        )

        self.assertEqual(zone_state, "blocked")

    def test_fetch_runtime_health_dict_preserves_sqlite_zone_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cfg = self._build_config(temp_dir)
            store = get_observability_store(force_recreate=True, config=cfg)
            store.start()
            run_id = "run-shadow-health"
            store.record_state_snapshot(
                {
                    "run_id": run_id,
                    "status": "healthy",
                    "data_mode": "live",
                    "zone": {
                        "name": "Post-Open",
                        "state": "shadow",
                        "semantics_version": "launch_gate_aware_v1",
                    },
                    "position": {"contracts": 0, "pnl": 0.0},
                    "account": {"daily_pnl": 0.0, "is_practice": True},
                    "risk": {"state": "normal"},
                    "alpha": {"long_score": 0.0, "short_score": 0.0},
                    "heartbeat": {"market_stream_connected": True},
                },
            )
            store.force_flush()

            status_path = runtime_status_path(cfg)
            status_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.write_text(
                '{"running": true, "pid": 999999, "run_id": "run-shadow-health", "data_mode": "live"}',
                encoding="utf-8",
            )

            health, source = fetch_runtime_health_dict(cfg)
            snapshot_rows = store.query_state_snapshots(limit=1, run_id=run_id)

            self.assertEqual(source, "sqlite")
            self.assertEqual(health["zone"], "Post-Open")
            self.assertEqual(health["zone_state"], "shadow")
            self.assertEqual(health["zone_semantics_version"], "launch_gate_aware_v1")
            self.assertEqual(snapshot_rows[0]["zone_semantics_version"], "launch_gate_aware_v1")
            store.stop()

    def test_engine_update_server_state_persists_zone_semantics_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cfg = self._build_config(temp_dir)
            store = get_observability_store(force_recreate=True, config=cfg)
            store.start()
            with patch("src.engine.trading_engine.get_observability_store", return_value=store):
                from src.engine.trading_engine import TradingEngine

                engine = TradingEngine(cfg)
                engine.reset_runtime_state(clear_history=True)
                set_config(cfg)
                engine._update_server_state()
                store.force_flush()

            rows = store.query_state_snapshots(limit=1)
            self.assertEqual(rows[0]["zone_semantics_version"], "launch_gate_aware_v1")
            self.assertEqual(
                rows[0]["payload"]["zone"]["semantics_version"], "launch_gate_aware_v1"
            )
            store.stop()

    def test_status_warns_when_zone_semantics_are_legacy_or_unknown(self) -> None:
        remote = {
            "status": "healthy",
            "running": True,
            "data_mode": "live",
            "zone": {"name": "Post-Open", "state": "active"},
            "strategy": "WEIGHTED_SCORE_MATRIX",
            "position": {"contracts": 0, "pnl": 0.0},
            "account": {"daily_pnl": 0.0},
            "risk": {"state": "normal"},
        }
        runner = CliRunner()
        with patch("src.cli.commands.fetch_runtime_debug_state", return_value=(remote, "sqlite")):
            result = runner.invoke(cli, ["status"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("legacy/unknown snapshot", result.output)
