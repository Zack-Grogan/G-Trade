"""Read-only data access for GUI panels.

Wraps :class:`~src.observability.store.ObservabilityStore` query methods
with a stable, GUI-friendly API.  All methods are synchronous and safe to
call from a worker thread; none of them mutate the store.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from PySide6.QtCore import QObject, Signal

from src.observability.store import ObservabilityStore

logger = logging.getLogger(__name__)


class DataProvider(QObject):
    """Read-only data access for GUI panels.

    Each public method delegates to the corresponding
    ``ObservabilityStore.query_*`` call, forwarding the keyword arguments
    that the store supports.  The return type is always ``list[dict]`` --
    a list of row dictionaries exactly as returned by the store.
    """

    def __init__(self, store: ObservabilityStore) -> None:
        super().__init__()
        self._store = store

    # ------------------------------------------------------------------
    # Completed trades
    # ------------------------------------------------------------------

    def get_completed_trades(
        self,
        *,
        limit: int = 100,
        run_id: Optional[str] = None,
        account_id: Optional[str] = None,
        zone: Optional[str] = None,
        strategy: Optional[str] = None,
        min_pnl: Optional[float] = None,
        max_pnl: Optional[float] = None,
        ascending: bool = False,
        search: Optional[str] = None,
        start_time: Optional[datetime | str] = None,
        end_time: Optional[datetime | str] = None,
        include_non_authoritative: bool = False,
    ) -> list[dict[str, Any]]:
        """Query completed trades from the observability store."""
        return self._store.query_completed_trades(
            limit=limit,
            run_id=run_id,
            account_id=account_id,
            zone=zone,
            strategy=strategy,
            min_pnl=min_pnl,
            max_pnl=max_pnl,
            ascending=ascending,
            search=search,
            start_time=start_time,
            end_time=end_time,
            include_non_authoritative=include_non_authoritative,
        )

    # ------------------------------------------------------------------
    # Market tape (raw ticks / quotes)
    # ------------------------------------------------------------------

    def get_market_tape(
        self,
        *,
        limit: int = 100,
        run_id: Optional[str] = None,
        symbol: Optional[str] = None,
        source: Optional[str] = None,
        sources: Optional[list[str]] = None,
        ascending: bool = False,
        search: Optional[str] = None,
        start_time: Optional[datetime | str] = None,
        end_time: Optional[datetime | str] = None,
    ) -> list[dict[str, Any]]:
        """Query the market_tape table."""
        return self._store.query_market_tape(
            limit=limit,
            run_id=run_id,
            symbol=symbol,
            source=source,
            sources=sources,
            ascending=ascending,
            search=search,
            start_time=start_time,
            end_time=end_time,
        )

    # ------------------------------------------------------------------
    # State snapshots
    # ------------------------------------------------------------------

    def get_state_snapshots(
        self,
        *,
        limit: int = 100,
        run_id: Optional[str] = None,
        symbol: Optional[str] = None,
        ascending: bool = False,
        search: Optional[str] = None,
        start_time: Optional[datetime | str] = None,
        end_time: Optional[datetime | str] = None,
    ) -> list[dict[str, Any]]:
        """Query state snapshots."""
        return self._store.query_state_snapshots(
            limit=limit,
            run_id=run_id,
            symbol=symbol,
            ascending=ascending,
            search=search,
            start_time=start_time,
            end_time=end_time,
        )

    # ------------------------------------------------------------------
    # Order lifecycle
    # ------------------------------------------------------------------

    def get_order_lifecycle(
        self,
        *,
        limit: int = 100,
        order_id: Optional[str] = None,
        run_id: Optional[str] = None,
        symbol: Optional[str] = None,
        ascending: bool = False,
        search: Optional[str] = None,
        start_time: Optional[datetime | str] = None,
        end_time: Optional[datetime | str] = None,
    ) -> list[dict[str, Any]]:
        """Query order lifecycle events."""
        return self._store.query_order_lifecycle(
            limit=limit,
            order_id=order_id,
            run_id=run_id,
            symbol=symbol,
            ascending=ascending,
            search=search,
            start_time=start_time,
            end_time=end_time,
        )

    # ------------------------------------------------------------------
    # Runtime logs
    # ------------------------------------------------------------------

    def get_runtime_logs(
        self,
        *,
        limit: int = 100,
        run_id: Optional[str] = None,
        level: Optional[str] = None,
        ascending: bool = False,
        search: Optional[str] = None,
        start_time: Optional[datetime | str] = None,
        end_time: Optional[datetime | str] = None,
    ) -> list[dict[str, Any]]:
        """Query runtime logs."""
        return self._store.query_runtime_logs(
            limit=limit,
            run_id=run_id,
            level=level,
            ascending=ascending,
            search=search,
            start_time=start_time,
            end_time=end_time,
        )

    # ------------------------------------------------------------------
    # Run manifests
    # ------------------------------------------------------------------

    def get_run_manifests(
        self,
        *,
        limit: int = 25,
        search: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Query run manifests (provenance records)."""
        return self._store.query_run_manifests(limit=limit, search=search)

    # ------------------------------------------------------------------
    # Decision snapshots
    # ------------------------------------------------------------------

    def get_decision_snapshots(
        self,
        *,
        limit: int = 100,
        run_id: Optional[str] = None,
        symbol: Optional[str] = None,
        ascending: bool = False,
        search: Optional[str] = None,
        start_time: Optional[datetime | str] = None,
        end_time: Optional[datetime | str] = None,
    ) -> list[dict[str, Any]]:
        """Query decision snapshots."""
        return self._store.query_decision_snapshots(
            limit=limit,
            run_id=run_id,
            symbol=symbol,
            ascending=ascending,
            search=search,
            start_time=start_time,
            end_time=end_time,
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def get_events(
        self,
        *,
        limit: int = 100,
        category: Optional[str] = None,
        event_type: Optional[str] = None,
        run_id: Optional[str] = None,
        order_id: Optional[str] = None,
        ascending: bool = False,
        search: Optional[str] = None,
        since_minutes: Optional[int] = None,
        start_time: Optional[datetime | str] = None,
        end_time: Optional[datetime | str] = None,
    ) -> list[dict[str, Any]]:
        """Query observability events."""
        return self._store.query_events(
            limit=limit,
            category=category,
            event_type=event_type,
            run_id=run_id,
            order_id=order_id,
            ascending=ascending,
            search=search,
            since_minutes=since_minutes,
            start_time=start_time,
            end_time=end_time,
        )

    # ------------------------------------------------------------------
    # Account trades (broker-reported fills)
    # ------------------------------------------------------------------

    def get_account_trades(
        self,
        *,
        limit: int = 100,
        run_id: Optional[str] = None,
        account_id: Optional[str] = None,
        ascending: bool = False,
        search: Optional[str] = None,
        start_time: Optional[datetime | str] = None,
        end_time: Optional[datetime | str] = None,
    ) -> list[dict[str, Any]]:
        """Query broker-reported account trades."""
        return self._store.query_account_trades(
            limit=limit,
            run_id=run_id,
            account_id=account_id,
            ascending=ascending,
            search=search,
            start_time=start_time,
            end_time=end_time,
        )
