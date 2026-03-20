"""Market-hours guard helpers for entry blocking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytz

from src.config import StrategyConfig

_DAY_TO_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


@dataclass
class MarketHoursStatus:
    is_open: bool
    reason: str | None
    payload: dict[str, Any]


class MarketHoursGuard:
    """Deterministic local schedule guard for entry permissions."""

    def __init__(self, strategy_config: StrategyConfig):
        self._config = strategy_config
        self._timezone = pytz.timezone(strategy_config.market_hours_timezone)
        self._daily_start = self._parse_hhmm(strategy_config.market_hours_daily_maintenance_start)
        self._daily_end = self._parse_hhmm(strategy_config.market_hours_daily_maintenance_end)
        self._weekend_close_day = self._parse_weekday(
            strategy_config.market_hours_weekend_close_day
        )
        self._weekend_open_day = self._parse_weekday(strategy_config.market_hours_weekend_open_day)
        self._weekend_close_time = self._parse_hhmm(strategy_config.market_hours_weekend_close_time)
        self._weekend_open_time = self._parse_hhmm(strategy_config.market_hours_weekend_open_time)
        self._holiday_dates = set(strategy_config.market_hours_holiday_dates or [])

    @staticmethod
    def _parse_hhmm(value: str) -> tuple[int, int]:
        hours, minutes = value.strip().split(":", 1)
        return int(hours), int(minutes)

    @staticmethod
    def _parse_weekday(value: str) -> int:
        normalized = value.strip().lower()
        if normalized not in _DAY_TO_WEEKDAY:
            raise ValueError(f"Unsupported weekday value: {value}")
        return _DAY_TO_WEEKDAY[normalized]

    @staticmethod
    def _is_after_or_equal(now_pair: tuple[int, int], reference: tuple[int, int]) -> bool:
        return now_pair >= reference

    @staticmethod
    def _is_before(now_pair: tuple[int, int], reference: tuple[int, int]) -> bool:
        return now_pair < reference

    def evaluate(self, current_time: datetime) -> MarketHoursStatus:
        if not self._config.market_hours_guard_enabled:
            return MarketHoursStatus(
                is_open=True,
                reason=None,
                payload={"reason": "market_hours_guard_disabled"},
            )

        if current_time.tzinfo is None:
            localized = self._timezone.localize(current_time)
        else:
            localized = current_time.astimezone(self._timezone)
        weekday = localized.weekday()
        now_pair = (localized.hour, localized.minute)
        date_iso = localized.date().isoformat()

        if date_iso in self._holiday_dates:
            return MarketHoursStatus(
                is_open=False,
                reason="market_closed_holiday",
                payload={
                    "reason": "market_closed_holiday",
                    "market_time": localized.isoformat(),
                    "market_date": date_iso,
                },
            )

        if weekday == self._weekend_close_day and self._is_after_or_equal(
            now_pair, self._weekend_close_time
        ):
            return MarketHoursStatus(
                is_open=False,
                reason="market_closed_weekend",
                payload={
                    "reason": "market_closed_weekend",
                    "market_time": localized.isoformat(),
                },
            )

        if weekday == 5:
            return MarketHoursStatus(
                is_open=False,
                reason="market_closed_weekend",
                payload={
                    "reason": "market_closed_weekend",
                    "market_time": localized.isoformat(),
                },
            )

        if weekday == self._weekend_open_day and self._is_before(now_pair, self._weekend_open_time):
            return MarketHoursStatus(
                is_open=False,
                reason="market_closed_weekend",
                payload={
                    "reason": "market_closed_weekend",
                    "market_time": localized.isoformat(),
                },
            )

        if weekday in {0, 1, 2, 3} and self._daily_start <= now_pair < self._daily_end:
            return MarketHoursStatus(
                is_open=False,
                reason="market_closed_maintenance",
                payload={
                    "reason": "market_closed_maintenance",
                    "market_time": localized.isoformat(),
                    "maintenance_start": self._config.market_hours_daily_maintenance_start,
                    "maintenance_end": self._config.market_hours_daily_maintenance_end,
                },
            )

        return MarketHoursStatus(
            is_open=True,
            reason=None,
            payload={
                "reason": "market_open",
                "market_time": localized.isoformat(),
            },
        )
