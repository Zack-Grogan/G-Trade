"""PRAC-gated TopstepX / ProjectX integration smoke tests.

These tests are intentionally opt-in and require live broker credentials plus a
practice-account selector. They exercise the real TopstepX REST surface so we can
catch regressions that mock-based unit tests cannot see.
"""

from __future__ import annotations

from dataclasses import asdict
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.config import load_config, set_config
from src.market.topstep_client import TopstepClient
from src.observability import get_observability_store
from src.runtime.inspection import (
    fetch_runtime_health_dict,
    read_runtime_status,
    runtime_status_path,
)
import yaml


def _is_truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _require_prac_only_account(client: TopstepClient) -> None:
    account = client.get_account()
    if account is None:
        raise unittest.SkipTest("TopstepX account lookup failed")

    preferred_account_id = os.getenv("PREFERRED_ACCOUNT_ID", "").strip()
    if not preferred_account_id:
        raise unittest.SkipTest(
            "Set PREFERRED_ACCOUNT_ID to the PRAC account before running TopstepX integration tests"
        )

    if not account.is_practice:
        raise unittest.SkipTest(
            "Selected TopstepX account is not practice; set PREFERRED_ACCOUNT_ID to the PRAC account"
        )

    if account.account_id != preferred_account_id:
        raise unittest.SkipTest(
            f"PREFERRED_ACCOUNT_ID={preferred_account_id} did not resolve to the selected PRAC account"
        )


def _write_yaml_config(config: object, path: Path) -> None:
    path.write_text(yaml.safe_dump(asdict(config), sort_keys=False), encoding="utf-8")


def _runtime_control_paths_for_config(config) -> dict[str, Path]:
    status_file = runtime_status_path(config)
    runtime_dir = status_file.parent
    return {
        "runtime_dir": runtime_dir,
        "pid_file": runtime_dir / "trader.pid",
        "request_file": runtime_dir / "lifecycle_request.json",
        "status_file": status_file,
    }


def _wait_for_condition(
    predicate,
    *,
    timeout_seconds: float,
    label: str,
    poll_seconds: float = 0.25,
):
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            result = predicate()
            if result:
                return result
        except Exception as exc:  # pragma: no cover - surfaced in assertion below
            last_error = exc
        time.sleep(poll_seconds)
    if last_error is not None:
        raise AssertionError(f"Timed out waiting for {label}: {last_error}")
    raise AssertionError(f"Timed out waiting for {label}")


@unittest.skipUnless(
    _is_truthy_env("TOPSTEPX_INTEGRATION"),
    "Set TOPSTEPX_INTEGRATION=1 to run live TopstepX integration tests",
)
@unittest.skipUnless(
    _is_truthy_env("TOPSTEPX_LIVE_STARTUP_SMOKE"),
    "Set TOPSTEPX_LIVE_STARTUP_SMOKE=1 to run the live startup smoke test",
)
class TopstepXLiveStartupSmokeTests(unittest.TestCase):
    """PRAC-gated end-to-end smoke tests for live startup, status, and shutdown."""

    @classmethod
    def setUpClass(cls) -> None:
        required_env = {
            "EMAIL": os.getenv("EMAIL", "").strip(),
            "TOPSTEP_API_KEY": os.getenv("TOPSTEP_API_KEY", "").strip(),
            "PREFERRED_ACCOUNT_ID": os.getenv("PREFERRED_ACCOUNT_ID", "").strip(),
        }
        missing = [name for name, value in required_env.items() if not value]
        if missing:
            raise unittest.SkipTest(
                "Missing required environment variables for live startup smoke tests: "
                + ", ".join(missing)
            )

        cls._temp_dir = tempfile.TemporaryDirectory()
        cls.repo_root = Path(__file__).resolve().parent.parent
        cls.config = load_config()
        cls.config.observability.enabled = True
        cls.config.observability.sqlite_path = str(Path(cls._temp_dir.name) / "observability.db")
        cls.config.logging.file = str(Path(cls._temp_dir.name) / "trading.log")
        cls.config.observability.sync_account_trade_history_on_startup = False
        zone_names = [zone.name for zone in cls.config.hot_zones] or [
            "Pre-Open",
            "Post-Open",
            "Midday",
            "Close-Scalp",
            "Outside",
        ]
        cls.config.strategy.live_entry_zones = []
        cls.config.strategy.shadow_entry_zones = zone_names
        cls.config_path = Path(cls._temp_dir.name) / "live-startup-smoke.yaml"
        _write_yaml_config(cls.config, cls.config_path)
        set_config(cls.config)
        cls.store = get_observability_store(force_recreate=True, config=cls.config)
        cls.store.start()
        cls.client = TopstepClient(cls.config.api)
        cls.client.observability = cls.store

        if not cls.client.authenticate():
            raise unittest.SkipTest("TopstepX authentication failed for live startup smoke tests")

        _require_prac_only_account(cls.client)
        cls.account = cls.client.get_account()
        if cls.account is None:
            raise unittest.SkipTest(
                "TopstepX PRAC account lookup failed for live startup smoke tests"
            )

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.store.stop()
        finally:
            cls._temp_dir.cleanup()

    def _cli_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["TOPSTEPX_INTEGRATION"] = "1"
        env["TOPSTEPX_LIVE_STARTUP_SMOKE"] = "1"
        return env

    def _run_cli(self, *args: str, timeout_seconds: int = 120) -> subprocess.CompletedProcess[str]:
        script = (
            "from src.cli.commands import main\n"
            "from src.config import load_config, set_config\n"
            f"set_config(load_config({json.dumps(str(self.config_path))}))\n"
            f"main({json.dumps(list(args))})\n"
        )
        return subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(self.repo_root),
            env=self._cli_env(),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

    def _start_runtime(self) -> subprocess.Popen[str]:
        stdout_path = Path(self._temp_dir.name) / "startup.stdout.log"
        stderr_path = Path(self._temp_dir.name) / "startup.stderr.log"
        stdout_handle = stdout_path.open("w", encoding="utf-8")
        stderr_handle = stderr_path.open("w", encoding="utf-8")
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "src.cli.commands",
                "start",
                "--config",
                str(self.config_path),
            ],
            cwd=str(self.repo_root),
            env=self._cli_env(),
            stdout=stdout_handle,
            stderr=stderr_handle,
            text=True,
        )
        proc._startup_stdout_handle = stdout_handle  # type: ignore[attr-defined]
        proc._startup_stderr_handle = stderr_handle  # type: ignore[attr-defined]
        proc._startup_stdout_path = stdout_path  # type: ignore[attr-defined]
        proc._startup_stderr_path = stderr_path  # type: ignore[attr-defined]
        return proc

    def _stop_runtime_process(self, proc: subprocess.Popen[str]) -> None:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
        stdout_handle = getattr(proc, "_startup_stdout_handle", None)
        stderr_handle = getattr(proc, "_startup_stderr_handle", None)
        if stdout_handle is not None:
            stdout_handle.close()
        if stderr_handle is not None:
            stderr_handle.close()

    def _read_runtime_logs(self, proc: subprocess.Popen[str]) -> str:
        stdout_path = getattr(proc, "_startup_stdout_path", None)
        stderr_path = getattr(proc, "_startup_stderr_path", None)
        parts = []
        if stdout_path and Path(stdout_path).exists():
            parts.append(Path(stdout_path).read_text(encoding="utf-8"))
        if stderr_path and Path(stderr_path).exists():
            parts.append(Path(stderr_path).read_text(encoding="utf-8"))
        return "\n".join(part for part in parts if part)

    def _wait_for_event(self, run_id: str, event_type: str, *, timeout_seconds: float = 60.0):
        def _predicate():
            rows = self.store.query_events(limit=20, run_id=run_id, event_type=event_type)
            return rows[0] if rows else None

        return _wait_for_condition(_predicate, timeout_seconds=timeout_seconds, label=event_type)

    def _wait_for_state_snapshot(self, run_id: str, *, timeout_seconds: float = 60.0):
        def _predicate():
            rows = self.store.query_state_snapshots(limit=5, run_id=run_id)
            return rows[0] if rows else None

        return _wait_for_condition(
            _predicate, timeout_seconds=timeout_seconds, label="state snapshot"
        )

    def _wait_for_runtime_running(self, proc: subprocess.Popen[str]):
        log_path = Path(self.config.logging.file)

        def _predicate():
            if proc.poll() is not None:
                raise AssertionError(
                    f"Live runtime exited early with code {proc.returncode}\n{self._read_runtime_logs(proc)}"
                )
            status = read_runtime_status(self.config, log_path)
            if status and status.get("running") and status.get("run_id"):
                return status
            return None

        return _wait_for_condition(_predicate, timeout_seconds=120.0, label="runtime startup")

    def test_live_startup_reports_status_health_streams_and_shutdown_cleanup(self) -> None:
        proc = self._start_runtime()
        try:
            runtime_status = self._wait_for_runtime_running(proc)
            run_id = str(runtime_status["run_id"])
            self.assertEqual(runtime_status.get("running"), True)
            self.assertEqual(runtime_status.get("data_mode"), "live")
            self.assertEqual(runtime_status.get("phase"), "running")

            startup_event = self._wait_for_event(run_id, "startup")
            self.assertEqual(startup_event["event_type"], "startup")

            market_event = self._wait_for_event(run_id, "market_stream_started")
            self.assertEqual(market_event["event_type"], "market_stream_started")

            user_hub_event = self._wait_for_event(run_id, "user_hub_connected")
            self.assertEqual(user_hub_event["event_type"], "user_hub_connected")

            snapshot = self._wait_for_state_snapshot(run_id)
            self.assertIn(snapshot["status"], {"running", "healthy"})
            self.assertEqual(snapshot["data_mode"], "live")
            self.assertEqual(snapshot["zone_semantics_version"], "launch_gate_aware_v1")

            health, source = fetch_runtime_health_dict(self.config)
            self.assertEqual(source, "sqlite")
            self.assertIn(health["status"], {"running", "healthy"})
            self.assertEqual(health["data_mode"], "live")
            self.assertTrue(health["market_stream_connected"])

            status_result = self._run_cli("status")
            self.assertEqual(
                status_result.returncode, 0, status_result.stdout + status_result.stderr
            )
            self.assertIn("Status:", status_result.stdout)
            self.assertIn("Running:   True", status_result.stdout)
            self.assertIn("Data Mode: live", status_result.stdout)

            health_result = self._run_cli("health")
            self.assertEqual(
                health_result.returncode, 0, health_result.stdout + health_result.stderr
            )
            self.assertIn("Status:", health_result.stdout)
            self.assertIn("Data Mode:   live", health_result.stdout)
            self.assertIn("Source:      sqlite", health_result.stdout)

            stop_result = self._run_cli("stop", "--reason", "live_startup_smoke")
            self.assertEqual(stop_result.returncode, 0, stop_result.stdout + stop_result.stderr)

            self._stop_runtime_process(proc)
            proc = None

            paths = _runtime_control_paths_for_config(self.config)
            runtime_after_stop = _wait_for_condition(
                lambda: (lambda status: status if status and not status.get("running") else None)(
                    read_runtime_status(self.config, Path(self.config.logging.file))
                ),
                timeout_seconds=30.0,
                label="runtime shutdown status",
            )
            self.assertFalse(runtime_after_stop.get("running"))
            self.assertEqual(runtime_after_stop.get("phase"), "stopped")
            self.assertEqual(runtime_after_stop.get("status"), "stopped")
            self.assertFalse(paths["pid_file"].exists())
            self.assertFalse(paths["request_file"].exists())

            shutdown_requested = self._wait_for_event(run_id, "shutdown_requested")
            self.assertEqual(shutdown_requested["event_type"], "shutdown_requested")
            shutdown_event = self._wait_for_event(run_id, "shutdown")
            self.assertEqual(shutdown_event["event_type"], "shutdown")
            self.assertFalse(shutdown_event["payload"].get("shutdown_error"))
            self.assertTrue(shutdown_event["payload"].get("startup_completed"))

            market_stopped = self._wait_for_event(run_id, "market_stream_stopped")
            self.assertEqual(market_stopped["event_type"], "market_stream_stopped")

            stopped_status = self._run_cli("status")
            self.assertEqual(
                stopped_status.returncode, 0, stopped_status.stdout + stopped_status.stderr
            )
            self.assertIn("Running:   False", stopped_status.stdout)
            self.assertIn("Status:    stopped", stopped_status.stdout)

            stopped_health = self._run_cli("health")
            self.assertEqual(
                stopped_health.returncode, 0, stopped_health.stdout + stopped_health.stderr
            )
            self.assertIn("Status:      stopped", stopped_health.stdout)
        finally:
            if proc is not None:
                self._stop_runtime_process(proc)


@unittest.skipUnless(
    _is_truthy_env("TOPSTEPX_INTEGRATION"),
    "Set TOPSTEPX_INTEGRATION=1 to run live TopstepX integration tests",
)
class TopstepXPracIntegrationTests(unittest.TestCase):
    """Live, read-only PRAC smoke tests for TopstepX / ProjectX paths."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._temp_dir = tempfile.TemporaryDirectory()
        cls.config = load_config()
        cls.config.observability.enabled = True
        cls.config.observability.sqlite_path = str(Path(cls._temp_dir.name) / "observability.db")
        set_config(cls.config)
        cls.store = get_observability_store(force_recreate=True, config=cls.config)
        cls.client = TopstepClient(cls.config.api)
        cls.client.observability = cls.store

        if not cls.client.authenticate():
            raise unittest.SkipTest("TopstepX authentication failed for integration tests")

        _require_prac_only_account(cls.client)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.store.stop()
        cls._temp_dir.cleanup()

    def test_prac_account_is_selected_and_visible(self) -> None:
        account = self.client.get_account()
        self.assertIsNotNone(account)
        assert account is not None
        self.assertTrue(account.is_practice)
        self.assertEqual(account.account_id, os.getenv("PREFERRED_ACCOUNT_ID", "").strip())
        self.assertGreaterEqual(account.balance, 0)

        accounts = self.client.list_accounts(only_active_accounts=False)
        self.assertTrue(accounts)
        self.assertTrue(any(str(acc.get("id")) == account.account_id for acc in accounts))

    def test_prac_broker_truth_bundle_is_consistent(self) -> None:
        bundle = self.client.get_broker_truth_bundle(
            "ES", lookback_minutes=60, include_history=True
        )

        self.assertIsNone(bundle.get("error"))
        self.assertEqual(bundle["account"]["id"], os.getenv("PREFERRED_ACCOUNT_ID", "").strip())
        self.assertTrue(bundle["account"]["is_practice"])
        self.assertIn("current", bundle)
        self.assertIn("history", bundle)
        self.assertIn("contradictions", bundle)
        self.assertIn("position", bundle["current"])
        self.assertIn("open_orders", bundle["current"])
        self.assertIn("recent_orders", bundle["history"])
        self.assertIn("recent_trades", bundle["history"])

    def test_prac_positions_and_history_queries_are_callable(self) -> None:
        positions, position_error = self.client.get_positions_snapshot()
        open_orders, open_orders_error = self.client.get_open_orders_snapshot("ES")

        start_time = datetime.now(UTC) - timedelta(hours=24)
        end_time = datetime.now(UTC)
        orders = self.client.search_orders(
            start_timestamp=start_time.isoformat(),
            end_timestamp=end_time.isoformat(),
        )
        trades = self.client.search_trades(
            start_timestamp=start_time.isoformat(),
            end_timestamp=end_time.isoformat(),
        )

        self.assertIsNone(position_error)
        self.assertIsNone(open_orders_error)
        self.assertIsNotNone(positions)
        self.assertIsNotNone(open_orders)
        self.assertIsInstance(orders, list)
        self.assertIsInstance(trades, list)

    def test_prac_history_bars_can_be_retrieved(self) -> None:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=7)

        bars = self.client.retrieve_bars("ES", start_time=start_time, end_time=end_time)

        self.assertIsInstance(bars, list)
        self.assertTrue(bars, "Expected at least one historical ES bar from the PRAC account")
        self.assertTrue(all(bar["symbol"] == "ES" for bar in bars))
        self.assertTrue(all("contract_id" in bar for bar in bars))

    @unittest.skipUnless(
        _is_truthy_env("TOPSTEPX_ALLOW_MUTATING_TESTS"),
        "Set TOPSTEPX_ALLOW_MUTATING_TESTS=1 to run the order-placement smoke test",
    )
    def test_prac_limit_order_smoke_can_submit_and_cancel(self) -> None:
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=3)
        bars = self.client.retrieve_bars("ES", start_time=start_time, end_time=end_time)
        self.assertTrue(bars, "Need at least one historical bar to derive a safe PRAC order price")

        last_close = float(bars[-1]["close"])
        limit_price = round(max(last_close - 100.0, 1.0), 2)

        order_id = None
        canceled = False
        try:
            order_id = self.client.place_order(
                "ES",
                1,
                "buy",
                order_type="limit",
                limit_price=limit_price,
            )

            self.assertIsNotNone(order_id)
            assert order_id is not None
            canceled = self.client.cancel_order(order_id)
            self.assertTrue(canceled)
        finally:
            if order_id and not canceled:
                self.client.cancel_order(order_id)
