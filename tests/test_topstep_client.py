from __future__ import annotations

import tempfile
import time
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from src.config import load_config, set_config
from src.market.topstep_client import Account, TopstepClient
from src.observability import get_observability_store


class TopstepClientHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.config = load_config()
        self.config.observability.enabled = True
        self.config.observability.sqlite_path = str(Path(self._temp_dir.name) / "observability.db")
        set_config(self.config)
        self.store = get_observability_store(force_recreate=True, config=self.config)
        self.client = TopstepClient(self.config.api)
        self.client.observability = self.store
        self.client._access_token = "token"
        self.client._token_expires = time.time() + 3600

    def tearDown(self) -> None:
        self.store.stop()
        self._temp_dir.cleanup()

    @patch("src.market.topstep_client.requests.post")
    def test_retrieve_bars_normalizes_history_payload(self, mock_post) -> None:
        start_time = datetime(2026, 3, 20, 14, 30, tzinfo=UTC)
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "bars": [
                {"t": "2026-03-20T14:30:00Z", "o": 6000.25, "h": 6001.0, "l": 5999.5, "c": 6000.75, "v": 18}
            ]
        }
        mock_post.return_value = response
        self.client.get_account = Mock(
            return_value=Account(account_id="1", name="Practice", is_practice=True)
        )
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        bars = self.client.retrieve_bars(
            "ES",
            start_time=start_time,
            end_time=start_time + timedelta(minutes=1),
        )

        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0]["symbol"], "ES")
        self.assertEqual(bars[0]["contract_id"], "CON.F.US.EP.M26")
        self.assertEqual(bars[0]["open"], 6000.25)
        self.assertEqual(bars[0]["close"], 6000.75)
        request_payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(request_payload["unit"], 2)
        self.assertFalse(request_payload["live"])

    def test_backfill_market_history_writes_history_bars_to_market_tape(self) -> None:
        start_time = datetime(2026, 3, 20, 14, 30, tzinfo=UTC)
        self.client.has_credentials = Mock(return_value=True)
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")
        self.client.retrieve_bars = Mock(
            return_value=[
                {
                    "time": start_time,
                    "open": 6000.0,
                    "high": 6001.5,
                    "low": 5999.75,
                    "close": 6001.0,
                    "volume": 11,
                    "contract_id": "CON.F.US.EP.M26",
                    "symbol": "ES",
                },
                {
                    "time": start_time + timedelta(minutes=1),
                    "open": 6001.0,
                    "high": 6002.0,
                    "low": 6000.5,
                    "close": 6001.25,
                    "volume": 9,
                    "contract_id": "CON.F.US.EP.M26",
                    "symbol": "ES",
                },
            ]
        )

        result = self.client.backfill_market_history(
            "ES",
            start_time=start_time,
            end_time=start_time + timedelta(minutes=2),
        )

        self.assertTrue(result["attempted"])
        self.assertEqual(result["bars_imported"], 2)
        rows = self.store.query_market_tape(limit=10, ascending=True, symbol="ES")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["source"], "HistoryBar")
        self.assertTrue(rows[0]["quote_is_synthetic"])
        self.assertEqual(rows[0]["payload"]["open"], 6000.0)
        self.assertEqual(rows[0]["payload"]["close"], 6001.0)


if __name__ == "__main__":
    unittest.main()
