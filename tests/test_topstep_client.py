from __future__ import annotations

import asyncio
import os
import tempfile
import time
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import requests

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
                {
                    "t": "2026-03-20T14:30:00Z",
                    "o": 6000.25,
                    "h": 6001.0,
                    "l": 5999.5,
                    "c": 6000.75,
                    "v": 18,
                }
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

    def test_retrieve_bars_covering_range_merges_chunks(self) -> None:
        start_time = datetime(2026, 3, 20, 14, 30, tzinfo=UTC)
        end_time = start_time + timedelta(days=8)
        self.client.get_account = Mock(
            return_value=Account(account_id="1", name="Practice", is_practice=True)
        )
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        bars_by_chunk: list[list] = [
            [
                {
                    "time": start_time,
                    "open": 1.0,
                    "high": 1.0,
                    "low": 1.0,
                    "close": 1.0,
                    "volume": 1,
                    "symbol": "ES",
                    "contract_id": "CON.F.US.EP.M26",
                }
            ],
            [
                {
                    "time": start_time + timedelta(days=7, minutes=1),
                    "open": 2.0,
                    "high": 2.0,
                    "low": 2.0,
                    "close": 2.0,
                    "volume": 1,
                    "symbol": "ES",
                    "contract_id": "CON.F.US.EP.M26",
                }
            ],
        ]

        def fake_retrieve(symbol, *args, start_time, end_time, **kwargs):
            return bars_by_chunk.pop(0)

        self.client.retrieve_bars = Mock(side_effect=fake_retrieve)

        merged, meta = self.client.retrieve_bars_covering_range(
            "ES",
            start_time=start_time,
            end_time=end_time,
        )
        self.assertEqual(len(merged), 2)
        self.assertEqual(meta["chunks_fetched"], 2)
        self.assertTrue(meta["coverage_complete"])
        self.assertFalse(meta["truncated_chunk"])

    def test_retrieve_bars_covering_range_marks_truncated_chunk(self) -> None:
        start_time = datetime(2026, 3, 20, 14, 30, tzinfo=UTC)
        self.client.get_account = Mock(
            return_value=Account(account_id="1", name="Practice", is_practice=True)
        )
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")
        huge = [
            {
                "time": start_time + timedelta(minutes=i),
                "open": 1.0,
                "high": 1.0,
                "low": 1.0,
                "close": 1.0,
                "volume": 1,
                "symbol": "ES",
                "contract_id": "CON.F.US.EP.M26",
            }
            for i in range(20000)
        ]
        self.client.retrieve_bars = Mock(return_value=huge)

        merged, meta = self.client.retrieve_bars_covering_range(
            "ES",
            start_time=start_time,
            end_time=start_time + timedelta(days=7),
        )
        self.assertEqual(len(merged), 20000)
        self.assertTrue(meta["truncated_chunk"])
        self.assertFalse(meta["coverage_complete"])


class TopstepClientAuthTests(unittest.TestCase):
    """Tests for authentication and session management in TopstepClient."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.config = load_config()
        self.config.observability.enabled = True
        self.config.observability.sqlite_path = str(Path(self._temp_dir.name) / "observability.db")
        set_config(self.config)
        self.store = get_observability_store(force_recreate=True, config=self.config)
        self.client = TopstepClient(self.config.api)
        self.client.observability = self.store

    def tearDown(self) -> None:
        self.store.stop()
        self._temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # authenticate() with invalid credentials - LoginErrorCode tests
    # -------------------------------------------------------------------------

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_user_not_found_returns_false(self, mock_post) -> None:
        """Test authenticate returns False when API returns UserNotFound (1)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "token": None,
            "errorCode": 1,
            "errorMessage": "User not found",
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)
        self.assertIsNone(self.client._access_token)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_password_verification_failed_returns_false(self, mock_post) -> None:
        """Test authenticate returns False when API returns PasswordVerificationFailed (2)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "token": None,
            "errorCode": 2,
            "errorMessage": "Password verification failed",
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)
        self.assertIsNone(self.client._access_token)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_invalid_credentials_returns_false(self, mock_post) -> None:
        """Test authenticate returns False when API returns InvalidCredentials (3)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "token": None,
            "errorCode": 3,
            "errorMessage": "Invalid credentials",
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)
        self.assertIsNone(self.client._access_token)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_api_key_disabled_returns_false(self, mock_post) -> None:
        """Test authenticate returns False when API returns ApiKeyAuthenticationDisabled (10)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "token": None,
            "errorCode": 10,
            "errorMessage": "API key authentication disabled",
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)
        self.assertIsNone(self.client._access_token)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_app_not_found_returns_false(self, mock_post) -> None:
        """Test authenticate returns False when API returns AppNotFound (4)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "token": None,
            "errorCode": 4,
            "errorMessage": "App not found",
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_api_subscription_not_found_returns_false(self, mock_post) -> None:
        """Test authenticate returns False when API returns ApiSubscriptionNotFound (9)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "token": None,
            "errorCode": 9,
            "errorMessage": "API subscription not found",
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # authenticate() with missing credentials
    # -------------------------------------------------------------------------

    @patch.dict(os.environ, {}, clear=True)
    def test_authenticate_missing_credentials_returns_false(self) -> None:
        """Test authenticate returns False when EMAIL and TOPSTEP_API_KEY are missing."""
        result = self.client.authenticate()

        self.assertFalse(result)
        self.assertIsNone(self.client._access_token)

    @patch.dict(os.environ, {"EMAIL": "test@example.com"}, clear=True)
    def test_authenticate_missing_api_key_returns_false(self) -> None:
        """Test authenticate returns False when TOPSTEP_API_KEY is missing."""
        result = self.client.authenticate()

        self.assertFalse(result)

    @patch.dict(os.environ, {"TOPSTEP_API_KEY": "test-key"}, clear=True)
    def test_authenticate_missing_email_returns_false(self) -> None:
        """Test authenticate returns False when EMAIL is missing."""
        result = self.client.authenticate()

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # authenticate() with successful response
    # -------------------------------------------------------------------------

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_success_sets_token(self, mock_post) -> None:
        """Test authenticate sets token and expiration on successful response."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": True,
            "token": "test-jwt-token-12345",
            "errorCode": 0,
            "errorMessage": None,
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertTrue(result)
        self.assertEqual(self.client._access_token, "test-jwt-token-12345")
        self.assertGreater(self.client._token_expires, time.time())

    # -------------------------------------------------------------------------
    # authenticate() with network errors
    # -------------------------------------------------------------------------

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_network_error_returns_false(self, mock_post) -> None:
        """Test authenticate returns False on network error."""
        mock_post.side_effect = requests.ConnectionError("Network unreachable")

        result = self.client.authenticate()

        self.assertFalse(result)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_timeout_returns_false(self, mock_post) -> None:
        """Test authenticate returns False on timeout."""
        mock_post.side_effect = requests.Timeout("Request timed out")

        result = self.client.authenticate()

        self.assertFalse(result)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_http_error_returns_false(self, mock_post) -> None:
        """Test authenticate returns False on HTTP error (e.g., 500)."""
        response = Mock()
        response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # _ensure_auth() token refresh logic
    # -------------------------------------------------------------------------

    def test_ensure_auth_returns_true_when_token_valid(self) -> None:
        """Test _ensure_auth returns True when token is valid and not expired."""
        self.client._access_token = "valid-token"
        self.client._token_expires = time.time() + 3600  # 1 hour from now

        result = self.client._ensure_auth()

        self.assertTrue(result)

    def test_ensure_auth_returns_false_when_token_missing(self) -> None:
        """Test _ensure_auth returns False when access token is missing."""
        self.client._access_token = None
        self.client._token_expires = time.time() + 3600

        result = self.client._ensure_auth()

        self.assertFalse(result)

    def test_ensure_auth_returns_false_when_token_expired(self) -> None:
        """Test _ensure_auth returns False when token is expired."""
        self.client._access_token = "expired-token"
        self.client._token_expires = time.time() - 60  # Expired 1 minute ago

        result = self.client._ensure_auth()

        self.assertFalse(result)

    def test_ensure_auth_returns_false_when_token_near_expiry(self) -> None:
        """Test _ensure_auth returns False when token expires within 60 seconds."""
        self.client._access_token = "almost-expired-token"
        self.client._token_expires = time.time() + 30  # Expires in 30 seconds

        result = self.client._ensure_auth()

        self.assertFalse(result)

    def test_ensure_auth_returns_true_when_token_has_sixty_one_seconds(self) -> None:
        """Test _ensure_auth returns True when token has just over 60 seconds left."""
        self.client._access_token = "valid-token"
        self.client._token_expires = time.time() + 61  # 61 seconds from now

        result = self.client._ensure_auth()

        self.assertTrue(result)

    # -------------------------------------------------------------------------
    # _headers() generation
    # -------------------------------------------------------------------------

    def test_headers_includes_authorization_bearer(self) -> None:
        """Test _headers returns dict with Authorization Bearer token."""
        self.client._access_token = "my-test-token"

        headers = self.client._headers()

        self.assertEqual(headers["Authorization"], "Bearer my-test-token")

    def test_headers_includes_content_type(self) -> None:
        """Test _headers returns dict with Content-Type application/json."""
        self.client._access_token = "test-token"

        headers = self.client._headers()

        self.assertEqual(headers["Content-Type"], "application/json")

    def test_headers_returns_both_required_headers(self) -> None:
        """Test _headers returns both Authorization and Content-Type headers."""
        self.client._access_token = "complete-token"

        headers = self.client._headers()

        self.assertIn("Authorization", headers)
        self.assertIn("Content-Type", headers)
        self.assertEqual(len(headers), 2)

    def test_headers_with_none_token(self) -> None:
        """Test _headers handles None token gracefully."""
        self.client._access_token = None

        headers = self.client._headers()

        self.assertEqual(headers["Authorization"], "Bearer None")

    # -------------------------------------------------------------------------
    # Token expiration edge cases
    # -------------------------------------------------------------------------

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_sets_seven_day_expiration(self, mock_post) -> None:
        """Test that authenticate sets token expiration to 7 days."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": True,
            "token": "long-lived-token",
            "errorCode": 0,
        }
        mock_post.return_value = response

        before_auth = time.time()
        result = self.client.authenticate()
        after_auth = time.time()

        self.assertTrue(result)
        # Should be approximately 7 days (86400 * 7 = 604800 seconds)
        expected_min = before_auth + 86400 * 7
        expected_max = after_auth + 86400 * 7
        self.assertGreaterEqual(self.client._token_expires, expected_min)
        self.assertLessEqual(self.client._token_expires, expected_max)

    def test_ensure_auth_with_zero_expiration(self) -> None:
        """Test _ensure_auth returns False when token_expires is 0 (default)."""
        self.client._access_token = "some-token"
        self.client._token_expires = 0

        result = self.client._ensure_auth()

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # Unknown error code handling
    # -------------------------------------------------------------------------

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_unknown_error_code_returns_false(self, mock_post) -> None:
        """Test authenticate returns False for unknown error codes."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "token": None,
            "errorCode": 999,  # Unknown error code
            "errorMessage": "Unknown error",
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_missing_error_code_returns_false(self, mock_post) -> None:
        """Test authenticate returns False when errorCode is missing from response."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "token": None,
            # No errorCode field
            "errorMessage": "Some error",
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_missing_success_field_returns_false(self, mock_post) -> None:
        """Test authenticate returns False when success field is missing."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            # No success field
            "token": None,
            "errorCode": 0,
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)

    @patch.dict(os.environ, {"EMAIL": "test@example.com", "TOPSTEP_API_KEY": "test-key"})
    @patch("src.market.topstep_client.requests.post")
    def test_authenticate_success_false_no_token_returns_false(self, mock_post) -> None:
        """Test authenticate returns False when success=False even with token."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "token": "some-token",  # Token present but success=False
            "errorCode": 1,
        }
        mock_post.return_value = response

        result = self.client.authenticate()

        self.assertFalse(result)


class TopstepClientOrderTests(unittest.TestCase):
    """Tests for order placement, modification, and cancellation error paths in TopstepClient."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.config = load_config()
        self.config.observability.enabled = True
        self.config.observability.sqlite_path = str(Path(self._temp_dir.name) / "observability.db")
        set_config(self.config)
        self.store = get_observability_store(force_recreate=True, config=self.config)
        self.client = TopstepClient(self.config.api)
        self.client.observability = self.store
        self.client._access_token = "test-token"
        self.client._token_expires = time.time() + 3600
        self.client._account_id = 12345

    def tearDown(self) -> None:
        self.store.stop()
        self._temp_dir.cleanup()

    # -------------------------------------------------------------------------
    # place_order() error paths - PlaceOrderErrorCode values 1-10
    # -------------------------------------------------------------------------

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_account_not_found_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns AccountNotFound (1)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 1,
            "errorMessage": "Account not found",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_rejected_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns OrderRejected (2)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 2,
            "errorMessage": "Order rejected",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_insufficient_funds_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns InsufficientFunds (3)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 3,
            "errorMessage": "Insufficient funds",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_account_violation_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns AccountViolation (4)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 4,
            "errorMessage": "Account violation",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_outside_trading_hours_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns OutsideTradingHours (5)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 5,
            "errorMessage": "Outside trading hours",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        with patch.object(self.client, "_record_event") as record_event:
            result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)
        self.assertTrue(
            any(
                call.kwargs.get("event_type") == "broker_order_outside_trading_hours"
                and call.kwargs.get("reason") == "broker_outside_trading_hours"
                for call in record_event.call_args_list
            )
        )

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_pending_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns OrderPending (6)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 6,
            "errorMessage": "Order pending",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_unknown_error_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns UnknownError (7)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 7,
            "errorMessage": "Unknown error",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_contract_not_found_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns ContractNotFound (8)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 8,
            "errorMessage": "Contract not found",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_contract_not_active_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns ContractNotActive (9)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 9,
            "errorMessage": "Contract not active",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_account_rejected_returns_none(self, mock_post) -> None:
        """Test place_order returns None when API returns AccountRejected (10)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 10,
            "errorMessage": "Account rejected",
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_success_returns_order_id(self, mock_post) -> None:
        """Test place_order returns order ID on successful response."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": True,
            "orderId": 123456,
            "errorCode": 0,
        }
        mock_post.return_value = response
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertEqual(result, "123456")

    def test_place_order_no_account_id_returns_none(self) -> None:
        """Test place_order returns None when account_id is not set."""
        self.client._account_id = None
        self.client.get_account = Mock(return_value=None)

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    def test_place_order_contract_resolution_fails_returns_none(self) -> None:
        """Test place_order returns None when contract resolution fails."""
        self.client._resolve_contract_id = Mock(return_value=None)

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_network_error_returns_none(self, mock_post) -> None:
        """Test place_order returns None on network error."""
        mock_post.side_effect = requests.ConnectionError("Network unreachable")
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    @patch("src.market.topstep_client.requests.post")
    def test_place_order_timeout_returns_none(self, mock_post) -> None:
        """Test place_order returns None on timeout."""
        mock_post.side_effect = requests.Timeout("Request timed out")
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")

        result = self.client.place_order("ES", 1, "buy", order_type="market")

        self.assertIsNone(result)

    # -------------------------------------------------------------------------
    # modify_order() error paths - ModifyOrderErrorCode values 1-7
    # -------------------------------------------------------------------------

    @patch("src.market.topstep_client.requests.post")
    def test_modify_order_account_not_found_returns_false(self, mock_post) -> None:
        """Test modify_order returns False when API returns AccountNotFound (1)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 1,
            "errorMessage": "Account not found",
        }
        mock_post.return_value = response

        result = self.client.modify_order("12345", size=2)

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_modify_order_not_found_returns_false(self, mock_post) -> None:
        """Test modify_order returns False when API returns OrderNotFound (2)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 2,
            "errorMessage": "Order not found",
        }
        mock_post.return_value = response

        result = self.client.modify_order("12345", size=2)

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_modify_order_rejected_returns_false(self, mock_post) -> None:
        """Test modify_order returns False when API returns Rejected (3)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 3,
            "errorMessage": "Order modification rejected",
        }
        mock_post.return_value = response

        result = self.client.modify_order("12345", size=2)

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_modify_order_pending_returns_false(self, mock_post) -> None:
        """Test modify_order returns False when API returns Pending (4)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 4,
            "errorMessage": "Order modification pending",
        }
        mock_post.return_value = response

        result = self.client.modify_order("12345", size=2)

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_modify_order_unknown_error_returns_false(self, mock_post) -> None:
        """Test modify_order returns False when API returns UnknownError (5)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 5,
            "errorMessage": "Unknown error",
        }
        mock_post.return_value = response

        result = self.client.modify_order("12345", size=2)

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_modify_order_account_rejected_returns_false(self, mock_post) -> None:
        """Test modify_order returns False when API returns AccountRejected (6)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 6,
            "errorMessage": "Account rejected",
        }
        mock_post.return_value = response

        result = self.client.modify_order("12345", size=2)

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_modify_order_contract_not_found_returns_false(self, mock_post) -> None:
        """Test modify_order returns False when API returns ContractNotFound (7)."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 7,
            "errorMessage": "Contract not found",
        }
        mock_post.return_value = response

        result = self.client.modify_order("12345", size=2)

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_modify_order_success_returns_true(self, mock_post) -> None:
        """Test modify_order returns True on successful response."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": True,
            "errorCode": 0,
        }
        mock_post.return_value = response

        result = self.client.modify_order("12345", size=2, limit_price=6000.0)

        self.assertTrue(result)

    def test_modify_order_no_account_id_returns_false(self) -> None:
        """Test modify_order returns False when account_id is not set."""
        self.client._account_id = None

        result = self.client.modify_order("12345", size=2)

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_modify_order_network_error_returns_false(self, mock_post) -> None:
        """Test modify_order returns False on network error."""
        mock_post.side_effect = requests.ConnectionError("Network unreachable")

        result = self.client.modify_order("12345", size=2)

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # cancel_order() error paths - CancelOrderErrorCode values 1-6
    # -------------------------------------------------------------------------

    @patch("src.market.topstep_client.requests.post")
    def test_cancel_order_account_not_found_returns_false(self, mock_post) -> None:
        """Test cancel_order returns False when API reports AccountNotFound."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 1,
            "errorMessage": "Account not found",
        }
        mock_post.return_value = response

        result = self.client.cancel_order("12345")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_cancel_order_not_found_returns_false(self, mock_post) -> None:
        """Test cancel_order returns False when API reports OrderNotFound."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 2,
            "errorMessage": "Order not found",
        }
        mock_post.return_value = response

        result = self.client.cancel_order("12345")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_cancel_order_rejected_returns_false(self, mock_post) -> None:
        """Test cancel_order returns False when API reports Rejected."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 3,
            "errorMessage": "Cancel rejected",
        }
        mock_post.return_value = response

        result = self.client.cancel_order("12345")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_cancel_order_pending_returns_false(self, mock_post) -> None:
        """Test cancel_order returns False when API reports Pending."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 4,
            "errorMessage": "Cancel pending",
        }
        mock_post.return_value = response

        result = self.client.cancel_order("12345")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_cancel_order_unknown_error_returns_false(self, mock_post) -> None:
        """Test cancel_order returns False when API reports UnknownError."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 5,
            "errorMessage": "Unknown error",
        }
        mock_post.return_value = response

        result = self.client.cancel_order("12345")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_cancel_order_account_rejected_returns_false(self, mock_post) -> None:
        """Test cancel_order returns False when API reports AccountRejected."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 6,
            "errorMessage": "Account rejected",
        }
        mock_post.return_value = response

        result = self.client.cancel_order("12345")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_cancel_order_success_returns_true(self, mock_post) -> None:
        """Test cancel_order returns True on successful response."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": True,
            "errorCode": 0,
        }
        mock_post.return_value = response

        result = self.client.cancel_order("12345")

        self.assertTrue(result)

    def test_cancel_order_invalid_order_id_returns_false(self) -> None:
        """Non-numeric order_id returns False before any HTTP call."""
        result = self.client.cancel_order("not-a-number")
        self.assertFalse(result)


class TopstepClientQueryStreamingTests(unittest.TestCase):
    """Tests for broker-truth, query, and SignalR helper paths."""

    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.config = load_config()
        self.config.observability.enabled = True
        self.config.observability.sqlite_path = str(Path(self._temp_dir.name) / "observability.db")
        set_config(self.config)
        self.store = get_observability_store(force_recreate=True, config=self.config)
        self.client = TopstepClient(self.config.api)
        self.client.observability = self.store
        self.client._access_token = "test-token"
        self.client._token_expires = time.time() + 3600
        self.client._account_id = 12345
        self.client._account = Account(account_id="12345", name="Practice", is_practice=True)

    def tearDown(self) -> None:
        self.store.stop()
        self._temp_dir.cleanup()

    @patch("src.market.topstep_client.requests.post")
    def test_search_orders_returns_empty_list_on_empty_payload(self, mock_post) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"orders": []}
        mock_post.return_value = response

        result = self.client.search_orders(start_timestamp="2026-03-20T00:00:00Z")

        self.assertEqual(result, [])

    @patch("src.market.topstep_client.requests.post")
    def test_search_orders_returns_empty_list_on_request_error(self, mock_post) -> None:
        mock_post.side_effect = requests.RequestException("account lookup failed")

        result = self.client.search_orders(start_timestamp="2026-03-20T00:00:00Z")

        self.assertEqual(result, [])

    @patch("src.market.topstep_client.requests.post")
    def test_search_trades_returns_empty_list_on_empty_payload(self, mock_post) -> None:
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"trades": []}
        mock_post.return_value = response

        result = self.client.search_trades(start_timestamp="2026-03-20T00:00:00Z")

        self.assertEqual(result, [])

    @patch("src.market.topstep_client.requests.post")
    def test_search_trades_returns_empty_list_on_request_error(self, mock_post) -> None:
        mock_post.side_effect = requests.RequestException("trade lookup failed")

        result = self.client.search_trades(start_timestamp="2026-03-20T00:00:00Z")

        self.assertEqual(result, [])

    def test_parse_datetime_handles_common_inputs(self) -> None:
        naive = datetime(2026, 3, 20, 14, 30)
        aware = datetime(2026, 3, 20, 14, 30, tzinfo=UTC)

        self.assertIsNone(self.client._parse_datetime(None))
        self.assertIsNone(self.client._parse_datetime(""))
        self.assertEqual(self.client._parse_datetime(naive).tzinfo, UTC)
        self.assertEqual(self.client._parse_datetime(aware), aware)
        self.assertIsNone(self.client._parse_datetime("not-a-date"))

    def test_normalize_symbol_strips_prefix_and_whitespace(self) -> None:
        self.assertEqual(self.client._normalize_symbol(" /es "), "ES")
        self.assertEqual(self.client._normalize_symbol("mes"), "MES")
        self.assertEqual(self.client._normalize_symbol(""), "")

    def test_decode_signalr_frames_skips_invalid_json_and_non_dicts(self) -> None:
        payload = '{"type":1}\x1e["not-a-dict"]\x1enot-json\x1e{"error":"bad"}\x1e'

        frames = self.client._decode_signalr_frames(payload)

        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0]["type"], 1)
        self.assertEqual(frames[1]["error"], "bad")

    def test_coerce_signalr_payload_prefers_first_dict(self) -> None:
        self.assertEqual(self.client._coerce_signalr_payload({"a": 1}), {"a": 1})
        self.assertEqual(self.client._coerce_signalr_payload([1, {"b": 2}]), {"b": 2})
        self.assertEqual(self.client._coerce_signalr_payload("nope"), {})

    def test_signalr_send_raises_without_socket(self) -> None:
        with self.assertRaises(RuntimeError):
            asyncio.run(self.client._signalr_send("SubscribeOrders", 12345))

    def test_signalr_send_writes_invocation_frame(self) -> None:
        ws = AsyncMock()
        self.client._ws = ws

        asyncio.run(self.client._signalr_send("SubscribeOrders", 12345))

        sent = ws.send.call_args.args[0]
        self.assertIn('"target": "SubscribeOrders"', sent)
        self.assertIn('"arguments": [12345]', sent)

    def test_signalr_handshake_raises_without_socket(self) -> None:
        with self.assertRaises(RuntimeError):
            asyncio.run(self.client._signalr_handshake())

    def test_get_positions_snapshot_normalizes_signed_size_and_prices(self) -> None:
        market_snapshot = Mock()
        market_snapshot.last = 5000.25
        self.client._lookup_market_snapshot = Mock(return_value=market_snapshot)

        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "positions": [
                {
                    "contractId": "CON.F.US.EP.M26",
                    "type": 2,
                    "size": 3,
                    "averagePrice": 5000.0,
                    "profitAndLoss": -25.5,
                }
            ]
        }
        self.client._post_with_retry = Mock(return_value=response)

        positions, error = self.client.get_positions_snapshot()

        self.assertIsNone(error)
        self.assertIsNotNone(positions)
        position = positions["CON.F.US.EP.M26"]
        self.assertEqual(position.quantity, -3)
        self.assertEqual(position.current_price, 5000.25)

    def test_get_open_orders_snapshot_filters_by_symbol(self) -> None:
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "orders": [
                {
                    "id": 1,
                    "contractId": "CON.F.US.EP.M26",
                    "symbol": "ES",
                    "status": "working",
                },
                {
                    "id": 2,
                    "contractId": "CON.F.US.NQ.M26",
                    "symbol": "NQ",
                    "status": "working",
                },
            ]
        }
        self.client._post_with_retry = Mock(return_value=response)

        orders, error = self.client.get_open_orders_snapshot("ES")

        self.assertIsNone(error)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["contractId"], "CON.F.US.EP.M26")

    def test_get_broker_truth_bundle_tracks_recent_activity_and_errors(self) -> None:
        focus = datetime(2026, 3, 20, 14, 30, tzinfo=UTC)
        self.client.get_positions_snapshot = Mock(return_value=(None, "position_error"))
        self.client.get_open_orders_snapshot = Mock(return_value=([], "open_orders_error"))
        self.client._resolve_contract_id = Mock(return_value="CON.F.US.EP.M26")
        self.client.search_orders = Mock(
            return_value=[
                {
                    "id": 111,
                    "contractId": "CON.F.US.EP.M26",
                    "creationTimestamp": "2026-03-20T14:29:30Z",
                    "status": "working",
                    "side": "buy",
                    "size": 1,
                    "filledQuantity": 0,
                    "limitPrice": 5000.0,
                    "stopPrice": None,
                }
            ]
        )
        self.client.search_trades = Mock(
            return_value=[
                {
                    "id": 222,
                    "contractId": "CON.F.US.EP.M26",
                    "creationTimestamp": "2026-03-20T14:30:10Z",
                    "side": "sell",
                    "size": 1,
                    "price": 5001.0,
                    "profitAndLoss": 2.5,
                    "fees": 0.5,
                    "voided": False,
                    "orderId": 111,
                }
            ]
        )

        bundle = self.client.get_broker_truth_bundle(
            "ES", focus_timestamp=focus, lookback_minutes=5, include_history=True
        )

        self.assertEqual(bundle["error"], None)
        self.assertEqual(bundle["current"]["position_error"], "position_error")
        self.assertEqual(bundle["current"]["open_orders_error"], "open_orders_error")
        self.assertEqual(bundle["history"]["recent_order_count"], 1)
        self.assertEqual(bundle["history"]["recent_trade_count"], 1)
        self.assertTrue(bundle["contradictions"]["focus_timestamp_activity_detected"])

    def test_get_broker_truth_bundle_without_history_skips_history_queries(self) -> None:
        self.client.get_positions_snapshot = Mock(return_value=({}, None))
        self.client.get_open_orders_snapshot = Mock(return_value=([], None))
        self.client.search_orders = Mock()
        self.client.search_trades = Mock()

        bundle = self.client.get_broker_truth_bundle("ES", include_history=False)

        self.assertEqual(bundle["error"], None)
        self.assertEqual(bundle["history"]["recent_order_count"], 0)
        self.assertEqual(bundle["history"]["recent_trade_count"], 0)
        self.client.search_orders.assert_not_called()
        self.client.search_trades.assert_not_called()

    @patch("src.market.topstep_client.requests.post")
    def test_cancel_order_network_error_returns_false(self, mock_post) -> None:
        """Test cancel_order returns False on network error."""
        mock_post.side_effect = requests.ConnectionError("Network unreachable")

        result = self.client.cancel_order("12345")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_cancel_order_timeout_returns_false(self, mock_post) -> None:
        """Test cancel_order returns False on timeout."""
        mock_post.side_effect = requests.Timeout("Request timed out")

        result = self.client.cancel_order("12345")

        self.assertFalse(result)

    # -------------------------------------------------------------------------
    # close_position() error paths
    # -------------------------------------------------------------------------

    @patch("src.market.topstep_client.requests.post")
    def test_close_position_account_not_found_returns_false(self, mock_post) -> None:
        """Test close_position returns False when API returns AccountNotFound."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 1,
            "errorMessage": "Account not found",
        }
        mock_post.return_value = response

        result = self.client.close_position("CON.F.US.EP.M26")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_close_position_rejected_returns_false(self, mock_post) -> None:
        """Test close_position returns False when API returns rejection."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": False,
            "errorCode": 3,
            "errorMessage": "Position close rejected",
        }
        mock_post.return_value = response

        result = self.client.close_position("CON.F.US.EP.M26")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_close_position_success_returns_true(self, mock_post) -> None:
        """Test close_position returns True on successful response."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": True,
            "errorCode": 0,
        }
        mock_post.return_value = response

        result = self.client.close_position("CON.F.US.EP.M26")

        self.assertTrue(result)

    def test_close_position_no_account_id_returns_false(self) -> None:
        """Test close_position returns False when account_id is not set."""
        self.client._account_id = None

        result = self.client.close_position("CON.F.US.EP.M26")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_close_position_network_error_returns_false(self, mock_post) -> None:
        """Test close_position returns False on network error."""
        mock_post.side_effect = requests.ConnectionError("Network unreachable")

        result = self.client.close_position("CON.F.US.EP.M26")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_close_position_timeout_returns_false(self, mock_post) -> None:
        """Test close_position returns False on timeout."""
        mock_post.side_effect = requests.Timeout("Request timed out")

        result = self.client.close_position("CON.F.US.EP.M26")

        self.assertFalse(result)

    @patch("src.market.topstep_client.requests.post")
    def test_close_position_with_explicit_account_id(self, mock_post) -> None:
        """Test close_position uses explicit account_id when provided."""
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "success": True,
            "errorCode": 0,
        }
        mock_post.return_value = response

        result = self.client.close_position("CON.F.US.EP.M26", account_id=99999)

        self.assertTrue(result)
        # Verify the correct account_id was used in the request
        call_payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(call_payload["accountId"], 99999)


if __name__ == "__main__":
    unittest.main()
