"""Intraday equity curve widget using pyqtgraph.

Displays daily P&L over time with break-even and max-loss reference lines.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.gui.util.styles import (
    BG_DARK,
    BORDER_COLOR,
    LOSS_RED,
    PROFIT_GREEN,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class DailyPnlChart(QWidget):
    """Pyqtgraph-based intraday P&L chart.

    Parameters
    ----------
    max_daily_loss:
        The max daily loss limit in dollars (positive number).  Drawn as a
        red dashed line at ``-max_daily_loss``.
    parent:
        Optional parent widget.
    """

    def __init__(
        self,
        max_daily_loss: float = 600.0,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._max_daily_loss = abs(max_daily_loss)
        self._timestamps: list[float] = []
        self._pnl_values: list[float] = []

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Configure pyqtgraph global defaults for dark theme
        pg.setConfigOptions(antialias=True, background=BG_DARK, foreground=TEXT_PRIMARY)

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setTitle("Daily P&L", color=TEXT_PRIMARY, size="11pt")
        self._plot_widget.showGrid(x=True, y=True, alpha=0.15)
        layout.addWidget(self._plot_widget)

        plot_item = self._plot_widget.getPlotItem()
        if plot_item is not None:
            plot_item.setLabel("left", "P&L ($)", color=TEXT_SECONDARY)
            plot_item.setLabel("bottom", "Time", color=TEXT_SECONDARY)

            # Use a custom time axis
            axis = plot_item.getAxis("bottom")
            axis.setStyle(tickTextOffset=6)
            axis.enableAutoSIPrefix(False)

        # Break-even line at y=0 (white dashed)
        self._zero_line = pg.InfiniteLine(
            pos=0,
            angle=0,
            pen=pg.mkPen(color=TEXT_PRIMARY, width=1, style=pg.QtCore.Qt.PenStyle.DashLine),
            label="Break-even",
            labelOpts={
                "color": TEXT_PRIMARY,
                "position": 0.05,
                "anchors": [(0, 1), (0, 1)],
            },
        )
        self._plot_widget.addItem(self._zero_line)

        # Max daily loss line (red dashed)
        self._loss_line = pg.InfiniteLine(
            pos=-self._max_daily_loss,
            angle=0,
            pen=pg.mkPen(color=LOSS_RED, width=1.5, style=pg.QtCore.Qt.PenStyle.DashLine),
            label=f"Max Loss (-${self._max_daily_loss:,.0f})",
            labelOpts={
                "color": LOSS_RED,
                "position": 0.05,
                "anchors": [(0, 1), (0, 1)],
            },
        )
        self._plot_widget.addItem(self._loss_line)

        # Equity curve line
        self._curve = self._plot_widget.plot(
            pen=pg.mkPen(color=PROFIT_GREEN, width=2),
            name="P&L",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_max_daily_loss(self, value: float) -> None:
        """Update the max daily loss reference line."""
        self._max_daily_loss = abs(value)
        self._loss_line.setValue(-self._max_daily_loss)
        self._loss_line.label.setFormat(f"Max Loss (-${self._max_daily_loss:,.0f})")

    def update_snapshots(self, snapshots: list[dict]) -> None:
        """Replace the entire curve with snapshot data.

        Each dict should have ``"timestamp"`` (ISO string or epoch float)
        and ``"daily_pnl"`` (float).
        """
        self._timestamps.clear()
        self._pnl_values.clear()

        for snap in snapshots:
            ts = snap.get("timestamp")
            pnl = snap.get("daily_pnl", 0.0)
            epoch = self._to_epoch(ts)
            if epoch is not None:
                self._timestamps.append(epoch)
                self._pnl_values.append(float(pnl))

        self._refresh_curve()

    def add_point(self, timestamp: float | datetime | str, pnl: float) -> None:
        """Append a single data point for real-time updates.

        Parameters
        ----------
        timestamp:
            Unix epoch seconds, datetime, or ISO-format string.
        pnl:
            Current daily P&L value in dollars.
        """
        epoch = self._to_epoch(timestamp)
        if epoch is None:
            return
        self._timestamps.append(epoch)
        self._pnl_values.append(float(pnl))
        self._refresh_curve()

    def clear(self) -> None:
        """Clear all data points."""
        self._timestamps.clear()
        self._pnl_values.clear()
        self._refresh_curve()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _refresh_curve(self) -> None:
        if not self._timestamps:
            self._curve.setData([], [])
            return

        self._curve.setData(self._timestamps, self._pnl_values)

        # Auto-range Y axis with some padding
        if self._pnl_values:
            y_min = min(min(self._pnl_values), -self._max_daily_loss) * 1.1
            y_max = max(max(self._pnl_values), 50) * 1.1
            self._plot_widget.setYRange(y_min, y_max, padding=0.05)

    @staticmethod
    def _to_epoch(ts: float | datetime | str | None) -> float | None:
        """Coerce various timestamp types to epoch seconds."""
        if ts is None:
            return None
        if isinstance(ts, (int, float)):
            return float(ts)
        if isinstance(ts, datetime):
            return ts.timestamp()
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts).timestamp()
            except (ValueError, TypeError):
                return None
        return None
