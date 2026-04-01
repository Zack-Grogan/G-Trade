"""Status icon helpers for the G-Trade GUI."""

from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush

from src.gui.util.styles import PROFIT_GREEN, LOSS_RED, WARNING_YELLOW, TEXT_SECONDARY


# ---------------------------------------------------------------------------
# Status dot enum
# ---------------------------------------------------------------------------

class StatusDot(Enum):
    GREEN = PROFIT_GREEN
    YELLOW = WARNING_YELLOW
    RED = LOSS_RED
    GRAY = TEXT_SECONDARY


# ---------------------------------------------------------------------------
# Pixmap factory
# ---------------------------------------------------------------------------

def create_status_dot(color: str, size: int = 12) -> QPixmap:
    """Create a colored circle pixmap of the given size."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor(color)))
    painter.setPen(Qt.NoPen)
    margin = 1
    painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)
    painter.end()

    return pixmap


# ---------------------------------------------------------------------------
# Status-to-color mappers
# ---------------------------------------------------------------------------

_RISK_COLOR_MAP = {
    "normal": PROFIT_GREEN,
    "reduced": WARNING_YELLOW,
    "circuit_breaker": LOSS_RED,
}

_ENGINE_COLOR_MAP = {
    "running": PROFIT_GREEN,
    "healthy": PROFIT_GREEN,
    "degraded": WARNING_YELLOW,
    "stopped": TEXT_SECONDARY,
    "error": LOSS_RED,
}


def status_color_for_risk(risk_state: str) -> str:
    """Map risk state string to a hex color."""
    return _RISK_COLOR_MAP.get(risk_state.lower(), TEXT_SECONDARY)


def status_color_for_engine(status: str) -> str:
    """Map engine status string to a hex color."""
    return _ENGINE_COLOR_MAP.get(status.lower(), TEXT_SECONDARY)
