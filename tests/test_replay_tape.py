"""Tests for SQLite market_tape → replay mapping."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from src.engine.replay_tape import market_data_from_tape_row


class ReplayTapeMappingTests(unittest.TestCase):
    def test_market_data_from_tape_row_uses_columns(self) -> None:
        row = {
            "id": 1,
            "captured_at": "2026-03-20T14:30:00+00:00",
            "symbol": "ES",
            "bid": 6000.0,
            "ask": 6000.25,
            "last": 6000.1,
            "volume": 100,
            "bid_size": 10.0,
            "ask_size": 12.0,
            "last_size": 1.0,
            "volume_is_cumulative": True,
            "quote_is_synthetic": False,
            "trade_side": "buy",
            "latency_ms": 5,
            "source": "GatewayTrade",
            "payload": {},
        }
        md = market_data_from_tape_row(row)
        self.assertEqual(md.symbol, "ES")
        self.assertEqual(md.bid, 6000.0)
        self.assertEqual(md.ask, 6000.25)
        self.assertEqual(md.last, 6000.1)
        self.assertTrue(md.volume_is_cumulative)
        self.assertFalse(md.quote_is_synthetic)
        self.assertEqual(md.trade_side, "buy")

    def test_market_data_from_tape_row_falls_back_to_payload_symbol(self) -> None:
        row = {
            "captured_at": datetime(2026, 3, 20, 14, 30, tzinfo=UTC),
            "symbol": None,
            "bid": 1.0,
            "ask": 2.0,
            "last": 1.5,
            "volume": 0,
            "volume_is_cumulative": None,
            "quote_is_synthetic": None,
            "payload": {"symbol": "MES", "volume_is_cumulative": False},
        }
        md = market_data_from_tape_row(row)
        self.assertEqual(md.symbol, "MES")
        self.assertFalse(md.volume_is_cumulative)
