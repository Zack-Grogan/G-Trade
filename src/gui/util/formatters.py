"""Display formatting helpers for the G-Trade GUI."""

from datetime import datetime
from typing import Union

from src.gui.util.styles import PROFIT_GREEN, LOSS_RED, TEXT_SECONDARY


# ---------------------------------------------------------------------------
# Currency / P&L
# ---------------------------------------------------------------------------

def format_currency(value: float, signed: bool = True) -> str:
    """Format as '$1,234.56' with optional sign prefix."""
    if not signed:
        return f"${abs(value):,.2f}"
    if value >= 0:
        return f"+${value:,.2f}"
    return f"-${abs(value):,.2f}"


def format_pnl(value: float) -> str:
    """Format P&L as '+$125.00' or '-$75.00'."""
    if value >= 0:
        return f"+${value:,.2f}"
    return f"-${abs(value):,.2f}"


def format_percent(value: float) -> str:
    """Format as '65.2%'."""
    return f"{value:.1f}%"


# ---------------------------------------------------------------------------
# Time / Date
# ---------------------------------------------------------------------------

def format_time(dt: datetime) -> str:
    """Format as '10:30:45 AM'."""
    return dt.strftime("%I:%M:%S %p").lstrip("0")


def format_date(dt: datetime) -> str:
    """Format as '2026-03-23'."""
    return dt.strftime("%Y-%m-%d")


def format_datetime(dt: datetime) -> str:
    """Format as '2026-03-23 10:30:45'."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_duration(minutes: float) -> str:
    """Format duration: '1h 30m', '45m', '2h'."""
    if minutes < 0:
        minutes = abs(minutes)
    total_minutes = int(round(minutes))
    if total_minutes == 0:
        return "0m"
    hours = total_minutes // 60
    mins = total_minutes % 60
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


# ---------------------------------------------------------------------------
# Trading
# ---------------------------------------------------------------------------

def format_contracts(qty: int) -> str:
    """Format as '1 ct' or '3 cts'."""
    if abs(qty) == 1:
        return f"{qty} ct"
    return f"{qty} cts"


def format_price(value: float) -> str:
    """Format price as '5892.25'."""
    return f"{value:.2f}"


def format_score(value: float) -> str:
    """Format score with one decimal: '7.5'."""
    return f"{value:.1f}"


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def pnl_color(value: float) -> str:
    """Return hex color string: green for positive, red for negative, gray for zero."""
    if value > 0:
        return PROFIT_GREEN
    if value < 0:
        return LOSS_RED
    return TEXT_SECONDARY


# ---------------------------------------------------------------------------
# Short aliases used by some widgets
# ---------------------------------------------------------------------------

fmt_dollar = format_currency
fmt_pnl = format_pnl
fmt_percent = format_percent
fmt_time = format_time


def fmt_ratio(current: Union[int, float], maximum: Union[int, float]) -> str:
    """Format a ratio like '3 / 10'."""
    return f"{current} / {maximum}"
