"""Fill quality analysis from Topstep broker trades and observability data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from statistics import mean, median
from typing import Any, Optional

from src.market import get_client
from src.observability import get_observability_store


@dataclass
class FillAnalysis:
    """Analysis of a single fill."""

    order_id: str
    trade_id: Optional[str]
    symbol: str
    side: str
    quantity: int
    expected_price: float
    filled_price: float
    slippage_ticks: float
    slippage_dollars: float
    zone: Optional[str]
    timestamp: Optional[datetime]
    order_type: str
    is_protective: bool


@dataclass
class FillScorecard:
    """Aggregated fill quality metrics."""

    fill_count: int
    total_contracts: int
    avg_slippage_ticks: float
    median_slippage_ticks: float
    max_slippage_ticks: float
    p95_slippage_ticks: float
    total_slippage_dollars: float
    protective_fill_count: int
    protective_avg_slippage_ticks: float
    limit_fill_count: int
    market_fill_count: int


@dataclass
class FillQualityReport:
    """Complete fill quality report."""

    generated_at: datetime
    account_id: Optional[str]
    account_name: Optional[str]
    lookback_days: int
    total_fills: int
    overall_scorecard: FillScorecard
    zone_scorecards: dict[str, FillScorecard]
    order_type_breakdown: dict[str, FillScorecard]
    slippage_distribution: dict[str, int]
    correlation_with_volatility: Optional[float]


class FillQualityAnalyzer:
    """Analyze fill quality from Topstep trades and observability data."""

    TICK_VALUE = 12.50  # ES tick value in dollars

    def __init__(self):
        self.observability = get_observability_store()
        self.client = get_client()

    def analyze_fills_from_topstep(
        self,
        account_id: Optional[str] = None,
        days_back: int = 30,
    ) -> list[FillAnalysis]:
        """Pull recent trades from Topstep and analyze fill quality."""
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=max(int(days_back), 1))

        if not self.client._access_token and not self.client.authenticate():
            return []

        account = self.client.get_account()
        if account is None:
            return []

        effective_account_id = account_id or account.account_id

        broker_trades = self.client.search_trades(
            start_timestamp=start_time.isoformat(),
            end_timestamp=end_time.isoformat(),
            account_id=int(effective_account_id),
        )

        # Get order lifecycle data from observability for expected prices
        order_lifecycles = self.observability.query_order_lifecycle(
            limit=5000,
            start_time=start_time,
            end_time=end_time,
        )

        # Build lookup for expected fill prices
        expected_prices: dict[str, float] = {}
        for lifecycle in order_lifecycles:
            order_id = lifecycle.get("order_id")
            if order_id and lifecycle.get("expected_fill_price"):
                expected_prices[order_id] = float(lifecycle.get("expected_fill_price", 0))

        fills: list[FillAnalysis] = []
        for trade in broker_trades:
            order_id = str(trade.get("orderId", trade.get("order_id", "")))
            filled_price = float(trade.get("price", 0))
            expected_price = expected_prices.get(order_id, filled_price)
            slippage_ticks = self._compute_slippage_ticks(
                filled_price=filled_price,
                expected_price=expected_price,
                side=str(trade.get("side", "")),
            )

            fills.append(
                FillAnalysis(
                    order_id=order_id,
                    trade_id=str(trade.get("id", trade.get("tradeId", ""))),
                    symbol=str(trade.get("symbol", "ES")),
                    side=self._normalize_side(trade.get("side")),
                    quantity=int(trade.get("size", trade.get("quantity", 1))),
                    expected_price=expected_price,
                    filled_price=filled_price,
                    slippage_ticks=slippage_ticks,
                    slippage_dollars=abs(slippage_ticks) * self.TICK_VALUE,
                    zone=None,  # Zone not available from broker trade history
                    timestamp=self._parse_timestamp(trade.get("timestamp", trade.get("creationTimestamp"))),
                    order_type="unknown",
                    is_protective=False,
                )
            )

        return fills

    def analyze_fills_from_observability(
        self,
        days_back: int = 30,
        run_id: Optional[str] = None,
    ) -> list[FillAnalysis]:
        """Analyze fills from local observability data."""
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=max(int(days_back), 1))

        # Query order lifecycle events for fills
        lifecycles = self.observability.query_order_lifecycle(
            limit=5000,
            start_time=start_time,
            end_time=end_time,
            run_id=run_id,
        )

        fills: list[FillAnalysis] = []
        for lifecycle in lifecycles:
            filled_price = lifecycle.get("filled_price")
            expected_price = lifecycle.get("expected_fill_price")
            if filled_price is None:
                continue

            filled_price = float(filled_price)
            expected_price = float(expected_price) if expected_price else filled_price

            slippage_ticks = self._compute_slippage_ticks(
                filled_price=filled_price,
                expected_price=expected_price,
                side=str(lifecycle.get("side", "")),
            )

            fills.append(
                FillAnalysis(
                    order_id=str(lifecycle.get("order_id", "")),
                    trade_id=lifecycle.get("trade_id"),
                    symbol=str(lifecycle.get("symbol", "ES")),
                    side=self._normalize_side(lifecycle.get("side")),
                    quantity=int(lifecycle.get("filled_quantity", lifecycle.get("quantity", 1))),
                    expected_price=expected_price,
                    filled_price=filled_price,
                    slippage_ticks=slippage_ticks,
                    slippage_dollars=abs(slippage_ticks) * self.TICK_VALUE,
                    zone=lifecycle.get("zone"),
                    timestamp=self._parse_timestamp(lifecycle.get("observed_at")),
                    order_type=str(lifecycle.get("order_type", "unknown")),
                    is_protective=bool(lifecycle.get("is_protective")),
                )
            )

        return fills

    def build_zone_scorecard(self, fills: list[FillAnalysis]) -> dict[str, FillScorecard]:
        """Build fill scorecards grouped by zone."""
        zone_fills: dict[str, list[FillAnalysis]] = {}
        for fill in fills:
            zone = fill.zone or "Unknown"
            zone_fills.setdefault(zone, []).append(fill)

        return {
            zone: self._build_scorecard(zone_fill_list)
            for zone, zone_fill_list in zone_fills.items()
        }

    def build_order_type_scorecard(self, fills: list[FillAnalysis]) -> dict[str, FillScorecard]:
        """Build fill scorecards grouped by order type."""
        type_fills: dict[str, list[FillAnalysis]] = {}
        for fill in fills:
            order_type = fill.order_type or "unknown"
            type_fills.setdefault(order_type, []).append(fill)

        return {
            order_type: self._build_scorecard(type_fill_list)
            for order_type, type_fill_list in type_fills.items()
        }

    def generate_report(
        self,
        fills: list[FillAnalysis],
        *,
        account_id: Optional[str] = None,
        account_name: Optional[str] = None,
        lookback_days: int = 30,
    ) -> FillQualityReport:
        """Generate a complete fill quality report."""
        overall_scorecard = self._build_scorecard(fills)
        zone_scorecards = self.build_zone_scorecard(fills)
        order_type_breakdown = self.build_order_type_scorecard(fills)
        slippage_distribution = self._build_slippage_distribution(fills)

        return FillQualityReport(
            generated_at=datetime.now(UTC),
            account_id=account_id,
            account_name=account_name,
            lookback_days=lookback_days,
            total_fills=len(fills),
            overall_scorecard=overall_scorecard,
            zone_scorecards=zone_scorecards,
            order_type_breakdown=order_type_breakdown,
            slippage_distribution=slippage_distribution,
            correlation_with_volatility=None,  # Would need market data to compute
        )

    def _build_scorecard(self, fills: list[FillAnalysis]) -> FillScorecard:
        """Build a scorecard from a list of fills."""
        if not fills:
            return FillScorecard(
                fill_count=0,
                total_contracts=0,
                avg_slippage_ticks=0.0,
                median_slippage_ticks=0.0,
                max_slippage_ticks=0.0,
                p95_slippage_ticks=0.0,
                total_slippage_dollars=0.0,
                protective_fill_count=0,
                protective_avg_slippage_ticks=0.0,
                limit_fill_count=0,
                market_fill_count=0,
            )

        slippages = [abs(f.slippage_ticks) for f in fills]
        sorted_slippages = sorted(slippages)
        p95_idx = int(len(sorted_slippages) * 0.95)
        p95 = sorted_slippages[min(p95_idx, len(sorted_slippages) - 1)]

        protective_fills = [f for f in fills if f.is_protective]
        limit_fills = [f for f in fills if f.order_type and "limit" in f.order_type.lower()]
        market_fills = [f for f in fills if f.order_type and "market" in f.order_type.lower()]

        return FillScorecard(
            fill_count=len(fills),
            total_contracts=sum(f.quantity for f in fills),
            avg_slippage_ticks=round(mean(slippages), 4) if slippages else 0.0,
            median_slippage_ticks=round(median(slippages), 4) if slippages else 0.0,
            max_slippage_ticks=round(max(slippages), 4) if slippages else 0.0,
            p95_slippage_ticks=round(p95, 4),
            total_slippage_dollars=round(sum(abs(f.slippage_dollars) for f in fills), 2),
            protective_fill_count=len(protective_fills),
            protective_avg_slippage_ticks=(
                round(mean([abs(f.slippage_ticks) for f in protective_fills]), 4)
                if protective_fills
                else 0.0
            ),
            limit_fill_count=len(limit_fills),
            market_fill_count=len(market_fills),
        )

    def _build_slippage_distribution(self, fills: list[FillAnalysis]) -> dict[str, int]:
        """Build a histogram of slippage buckets."""
        distribution: dict[str, int] = {
            "0_ticks": 0,
            "0.25_ticks": 0,
            "0.5_ticks": 0,
            "0.75_ticks": 0,
            "1_tick": 0,
            "1.25_ticks": 0,
            "1.5_ticks": 0,
            "2+_ticks": 0,
        }

        for fill in fills:
            abs_slip = abs(fill.slippage_ticks)
            if abs_slip == 0:
                distribution["0_ticks"] += 1
            elif abs_slip <= 0.25:
                distribution["0.25_ticks"] += 1
            elif abs_slip <= 0.5:
                distribution["0.5_ticks"] += 1
            elif abs_slip <= 0.75:
                distribution["0.75_ticks"] += 1
            elif abs_slip <= 1.0:
                distribution["1_tick"] += 1
            elif abs_slip <= 1.25:
                distribution["1.25_ticks"] += 1
            elif abs_slip <= 1.5:
                distribution["1.5_ticks"] += 1
            else:
                distribution["2+_ticks"] += 1

        return distribution

    def _compute_slippage_ticks(
        self, filled_price: float, expected_price: float, side: str
    ) -> float:
        """Compute slippage in ticks (positive = unfavorable)."""
        if expected_price == 0 or filled_price == 0:
            return 0.0

        tick_size = 0.25  # ES tick size
        price_diff = filled_price - expected_price
        ticks = price_diff / tick_size

        # For buys, positive slippage means paid more (bad)
        # For sells, positive slippage means received less (bad)
        if side.lower() in {"sell", "short", "ask", "1"}:
            ticks = -ticks

        return round(ticks, 4)

    def _normalize_side(self, side: Any) -> str:
        """Normalize side to 'buy' or 'sell'."""
        if side is None:
            return "unknown"
        side_str = str(side).strip().lower()
        if side_str in {"0", "buy", "long", "bid"}:
            return "buy"
        if side_str in {"1", "sell", "short", "ask"}:
            return "sell"
        return side_str or "unknown"

    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse a timestamp value."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            import pandas as pd

            ts = pd.Timestamp(value)
            if ts.tzinfo is None:
                ts = ts.tz_localize(UTC)
            return ts.to_pydatetime()
        except Exception:
            return None


def build_fill_quality_report(
    *,
    account_id: Optional[str] = None,
    days_back: int = 30,
    source: str = "both",
) -> dict[str, Any]:
    """Build a fill quality report for CLI consumption."""
    analyzer = FillQualityAnalyzer()
    fills: list[FillAnalysis] = []

    if source in {"both", "observability"}:
        fills.extend(analyzer.analyze_fills_from_observability(days_back=days_back))

    if source in {"both", "topstep"}:
        fills.extend(analyzer.analyze_fills_from_topstep(account_id=account_id, days_back=days_back))

    report = analyzer.generate_report(
        fills,
        account_id=account_id,
        lookback_days=days_back,
    )

    return {
        "generated_at": report.generated_at.isoformat(),
        "account_id": report.account_id,
        "account_name": report.account_name,
        "lookback_days": report.lookback_days,
        "total_fills": report.total_fills,
        "overall_scorecard": {
            "fill_count": report.overall_scorecard.fill_count,
            "total_contracts": report.overall_scorecard.total_contracts,
            "avg_slippage_ticks": report.overall_scorecard.avg_slippage_ticks,
            "median_slippage_ticks": report.overall_scorecard.median_slippage_ticks,
            "max_slippage_ticks": report.overall_scorecard.max_slippage_ticks,
            "p95_slippage_ticks": report.overall_scorecard.p95_slippage_ticks,
            "total_slippage_dollars": report.overall_scorecard.total_slippage_dollars,
            "protective_fill_count": report.overall_scorecard.protective_fill_count,
            "protective_avg_slippage_ticks": report.overall_scorecard.protective_avg_slippage_ticks,
            "limit_fill_count": report.overall_scorecard.limit_fill_count,
            "market_fill_count": report.overall_scorecard.market_fill_count,
        },
        "zone_scorecards": {
            zone: {
                "fill_count": card.fill_count,
                "avg_slippage_ticks": card.avg_slippage_ticks,
                "max_slippage_ticks": card.max_slippage_ticks,
                "total_slippage_dollars": card.total_slippage_dollars,
            }
            for zone, card in report.zone_scorecards.items()
        },
        "order_type_breakdown": {
            order_type: {
                "fill_count": card.fill_count,
                "avg_slippage_ticks": card.avg_slippage_ticks,
                "total_slippage_dollars": card.total_slippage_dollars,
            }
            for order_type, card in report.order_type_breakdown.items()
        },
        "slippage_distribution": report.slippage_distribution,
        "fills": [
            {
                "order_id": f.order_id,
                "trade_id": f.trade_id,
                "symbol": f.symbol,
                "side": f.side,
                "quantity": f.quantity,
                "expected_price": f.expected_price,
                "filled_price": f.filled_price,
                "slippage_ticks": f.slippage_ticks,
                "slippage_dollars": f.slippage_dollars,
                "zone": f.zone,
                "order_type": f.order_type,
                "is_protective": f.is_protective,
                "timestamp": f.timestamp.isoformat() if f.timestamp else None,
            }
            for f in fills[:100]  # Limit output
        ],
    }
