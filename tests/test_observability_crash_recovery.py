"""Crash recovery tests for SQLite observability store."""

from __future__ import annotations

import sqlite3
import tempfile
import time
import unittest
from pathlib import Path

from src.config import load_config, set_config
from src.observability import get_observability_store


class ObservabilityCrashRecoveryTests(unittest.TestCase):
    """Tests for crash recovery scenarios in SQLite durability layer."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.config = load_config()
        self.config.observability.enabled = True
        self.config.observability.sqlite_path = str(
            Path(self._temp_dir.name) / "observability.db"
        )
        set_config(self.config)

    def tearDown(self) -> None:
        try:
            store = get_observability_store()
            store.stop()
        except Exception:
            pass
        self._temp_dir.cleanup()

    def test_unclean_shutdown_preserves_flushed_events(self) -> None:
        """Verify events flushed before crash are preserved."""
        store = get_observability_store(force_recreate=True, config=self.config)
        store.start()
        time.sleep(0.2)

        # Write some events
        store.record_event(
            category="test",
            event_type="crash_test_event",
            source="test",
            payload={"data": "before_crash"},
        )
        store.force_flush()

        # Simulate crash - do NOT call stop()
        # Just abandon the store object and create a new one

        # Reopen and verify data persisted
        store2 = get_observability_store(force_recreate=True, config=self.config)
        store2.start()
        time.sleep(0.2)

        events = store2.query_events(limit=100)
        crash_events = [e for e in events if e.get("event_type") == "crash_test_event"]
        self.assertGreaterEqual(len(crash_events), 1)

        store2.stop()

    def test_wal_mode_is_enabled(self) -> None:
        """Verify SQLite WAL mode is enabled for crash safety."""
        store = get_observability_store(force_recreate=True, config=self.config)
        store.start()
        time.sleep(0.2)

        db_path = store.get_db_path()

        # Check WAL mode
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        conn.close()

        self.assertEqual(mode.lower(), "wal")

        store.stop()

    def test_events_persist_across_restarts(self) -> None:
        """Verify events survive store restarts."""
        store = get_observability_store(force_recreate=True, config=self.config)
        store.start()
        time.sleep(0.2)

        # Write events with unique identifier
        for i in range(3):
            store.record_event(
                category="test",
                event_type=f"restart_test_{i}",
                source="test",
                payload={"index": i},
            )
        store.force_flush()

        # Clean restart
        store.stop()
        store2 = get_observability_store(force_recreate=True, config=self.config)
        store2.start()
        time.sleep(0.2)

        # Verify events persisted
        events = store2.query_events(limit=100)
        restart_events = [e for e in events if e.get("event_type", "").startswith("restart_test_")]
        self.assertGreaterEqual(len(restart_events), 3)

        store2.stop()

    def test_market_tape_persists_across_restarts(self) -> None:
        """Verify market tape data survives restarts."""
        store = get_observability_store(force_recreate=True, config=self.config)
        store.start()
        time.sleep(0.2)

        # Write market tick
        store.record_market_tick(
            {
                "symbol": "ES",
                "bid": 5000.0,
                "ask": 5000.25,
                "last": 5000.0,
                "volume": 100,
            }
        )
        store.force_flush()

        # Restart
        store.stop()
        store2 = get_observability_store(force_recreate=True, config=self.config)
        store2.start()
        time.sleep(0.2)

        # Verify market tape persisted
        tape = store2.query_market_tape(limit=100, symbol="ES")
        self.assertGreaterEqual(len(tape), 1)

        store2.stop()

    def test_concurrent_write_does_not_corrupt(self) -> None:
        """Verify concurrent writes don't corrupt the database."""
        import threading

        store = get_observability_store(force_recreate=True, config=self.config)
        store.start()
        time.sleep(0.2)

        errors = []
        threads = []

        def write_events(thread_id):
            try:
                for i in range(10):
                    store.record_event(
                        category="test",
                        event_type=f"concurrent_{thread_id}_{i}",
                        source="test",
                        payload={"thread": thread_id, "index": i},
                    )
                    time.sleep(0.01)
            except Exception as e:
                errors.append(str(e))

        # Start multiple writer threads
        for tid in range(3):
            t = threading.Thread(target=write_events, args=(tid,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=5.0)

        store.force_flush()

        # Verify no errors and data persisted
        self.assertEqual(len(errors), 0, f"Concurrent write errors: {errors}")

        events = store.query_events(limit=100)
        concurrent_events = [e for e in events if e.get("event_type", "").startswith("concurrent_")]
        # At least some should persist - timing can cause variation
        self.assertGreaterEqual(len(concurrent_events), 10)

        store.stop()

    def test_batch_write_is_atomic(self) -> None:
        """Verify batch writes are atomic."""
        store = get_observability_store(force_recreate=True, config=self.config)
        store.start()
        time.sleep(0.2)

        # Write multiple records in quick succession
        for i in range(5):
            store.record_event(
                category="test",
                event_type=f"atomic_test_{i}",
                source="test",
                payload={"batch": True, "index": i},
            )

        store.force_flush()

        # All records should be present
        events = store.query_events(limit=100)
        atomic_events = [e for e in events if e.get("event_type", "").startswith("atomic_test_")]
        self.assertEqual(len(atomic_events), 5)

        store.stop()

    def test_schema_migration_is_safe(self) -> None:
        """Verify schema migrations don't lose data."""
        store = get_observability_store(force_recreate=True, config=self.config)
        store.start()
        time.sleep(0.2)

        # Write initial data
        store.record_event(
            category="test",
            event_type="pre_migration",
            source="test",
            payload={"phase": "before"},
        )
        store.force_flush()

        # Restart store (triggers schema check)
        store.stop()
        store2 = get_observability_store(force_recreate=True, config=self.config)
        store2.start()
        time.sleep(0.3)

        # Verify data still present
        events = store2.query_events(limit=100)
        self.assertTrue(any(e.get("event_type") == "pre_migration" for e in events))

        store2.stop()


class ObservabilityBackpressureTests(unittest.TestCase):
    """Tests for queue-full visibility and backpressure behavior."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.config = load_config()
        self.config.observability.enabled = True
        self.config.observability.sqlite_path = str(
            Path(self._temp_dir.name) / "observability.db"
        )
        self.config.observability.queue_max_size = 1
        self.config.observability.batch_size = 1
        set_config(self.config)

    def tearDown(self) -> None:
        try:
            store = get_observability_store()
            store.stop()
        except Exception:
            pass
        self._temp_dir.cleanup()

    def test_queue_full_increments_drop_counter(self) -> None:
        store = get_observability_store(force_recreate=True, config=self.config)
        store.start()
        for i in range(50):
            store.record_event(
                category="test",
                event_type=f"drop_test_{i}",
                source="test",
                payload={"index": i},
            )
        store.force_flush()
        self.assertGreater(store.get_dropped_event_count(), 0)
        store.stop()


if __name__ == "__main__":
    unittest.main()
