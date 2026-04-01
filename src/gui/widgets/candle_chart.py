"""Candlestick chart widget with volume sub-plot, trade markers, and crosshair.

Uses pyqtgraph for high-performance rendering of OHLCV data with
overlaid trade entry/exit markers.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen, QPicture
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.gui.util.styles import (
    BG_CARD,
    BG_PRIMARY,
    BG_SECONDARY,
    CHART_BG,
    CHART_GRID,
    LOSS_RED,
    NEUTRAL_GRAY,
    PROFIT_GREEN,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour constants for candles
# ---------------------------------------------------------------------------

_GREEN = QColor("#26a69a")
_RED = QColor("#ef5350")
_GREEN_FILL = QColor("#26a69a")
_RED_FILL = QColor("#ef5350")
_VOLUME_GREEN = QColor(38, 166, 154, 80)
_VOLUME_RED = QColor(239, 83, 80, 80)
_CROSSHAIR_PEN = pg.mkPen(color=(255, 255, 255, 60), style=Qt.DashLine, width=1)

# Trade marker colours
_MARKER_LONG_ENTRY = QColor(PROFIT_GREEN)
_MARKER_SHORT_ENTRY = QColor(LOSS_RED)
_MARKER_EXIT = QColor("#ffffff")


# ---------------------------------------------------------------------------
# Custom candlestick item
# ---------------------------------------------------------------------------


class CandlestickItem(pg.GraphicsObject):
    """Custom pyqtgraph graphics item for OHLCV candlesticks.

    *data* is a numpy structured array or regular array with columns:
        [time_epoch, open, high, low, close]
    where time_epoch is a POSIX timestamp (float).
    """

    def __init__(self, data: Optional[np.ndarray] = None) -> None:
        super().__init__()
        self._data = data
        self._picture = QPicture()
        if data is not None and len(data) > 0:
            self._generate_picture()

    def set_data(self, data: np.ndarray) -> None:
        self._data = data
        self._picture = QPicture()
        self._generate_picture()
        self.prepareGeometryChange()
        self.informViewBoundsChanged()
        self.update()

    def _generate_picture(self) -> None:
        if self._data is None or len(self._data) == 0:
            return

        self._picture = QPicture()
        painter = QPainter(self._picture)
        painter.setRenderHint(QPainter.Antialiasing, False)

        data = self._data
        n = len(data)

        # Determine candle width from median time delta
        if n >= 2:
            diffs = np.diff(data[:, 0])
            diffs = diffs[diffs > 0]
            width = float(np.median(diffs)) * 0.6 if len(diffs) > 0 else 60.0 * 0.6
        else:
            width = 60.0 * 0.6

        half_w = width / 2.0

        for i in range(n):
            t = float(data[i, 0])
            o = float(data[i, 1])
            h = float(data[i, 2])
            l_ = float(data[i, 3])
            c = float(data[i, 4])

            is_bullish = c >= o

            if is_bullish:
                pen = QPen(_GREEN, 1)
                brush = QBrush(_GREEN_FILL)
            else:
                pen = QPen(_RED, 1)
                brush = QBrush(_RED_FILL)

            painter.setPen(pen)
            painter.setBrush(brush)

            # Wick (high-low line)
            painter.drawLine(
                pg.Point(t, l_),
                pg.Point(t, h),
            )

            # Body (open-close rectangle)
            body_top = max(o, c)
            body_bottom = min(o, c)
            body_height = body_top - body_bottom
            if body_height < 0.01:
                # Doji - draw a thin line
                painter.drawLine(
                    pg.Point(t - half_w, o),
                    pg.Point(t + half_w, o),
                )
            else:
                painter.drawRect(
                    pg.QtCore.QRectF(
                        t - half_w,
                        body_bottom,
                        width,
                        body_height,
                    )
                )

        painter.end()

    def paint(self, p: QPainter, *args: Any) -> None:
        p.drawPicture(0, 0, self._picture)

    def boundingRect(self) -> pg.QtCore.QRectF:
        if self._data is None or len(self._data) == 0:
            return pg.QtCore.QRectF(0, 0, 1, 1)
        t_min = float(self._data[:, 0].min())
        t_max = float(self._data[:, 0].max())
        price_min = float(self._data[:, 3].min())  # low
        price_max = float(self._data[:, 2].max())  # high
        margin = (price_max - price_min) * 0.05 or 1.0
        return pg.QtCore.QRectF(
            t_min, price_min - margin, t_max - t_min, price_max - price_min + 2 * margin
        )


# ---------------------------------------------------------------------------
# Volume bars item
# ---------------------------------------------------------------------------


class VolumeBarItem(pg.GraphicsObject):
    """Volume bars rendered below the candle chart.

    *data* has columns: [time_epoch, open, high, low, close, volume]
    """

    def __init__(self, data: Optional[np.ndarray] = None) -> None:
        super().__init__()
        self._data = data
        self._picture = QPicture()
        if data is not None and len(data) > 0:
            self._generate_picture()

    def set_data(self, data: np.ndarray) -> None:
        self._data = data
        self._picture = QPicture()
        self._generate_picture()
        self.prepareGeometryChange()
        self.informViewBoundsChanged()
        self.update()

    def _generate_picture(self) -> None:
        if self._data is None or len(self._data) == 0:
            return

        self._picture = QPicture()
        painter = QPainter(self._picture)
        painter.setRenderHint(QPainter.Antialiasing, False)

        data = self._data
        n = len(data)

        if n >= 2:
            diffs = np.diff(data[:, 0])
            diffs = diffs[diffs > 0]
            width = float(np.median(diffs)) * 0.6 if len(diffs) > 0 else 60.0 * 0.6
        else:
            width = 60.0 * 0.6

        half_w = width / 2.0

        for i in range(n):
            t = float(data[i, 0])
            o = float(data[i, 1])
            c = float(data[i, 4])
            vol = float(data[i, 5]) if data.shape[1] > 5 else 0.0
            if vol <= 0:
                continue

            is_bullish = c >= o
            color = _VOLUME_GREEN if is_bullish else _VOLUME_RED
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color))
            painter.drawRect(
                pg.QtCore.QRectF(t - half_w, 0, width, vol)
            )

        painter.end()

    def paint(self, p: QPainter, *args: Any) -> None:
        p.drawPicture(0, 0, self._picture)

    def boundingRect(self) -> pg.QtCore.QRectF:
        if self._data is None or len(self._data) == 0:
            return pg.QtCore.QRectF(0, 0, 1, 1)
        t_min = float(self._data[:, 0].min())
        t_max = float(self._data[:, 0].max())
        vol_max = float(self._data[:, 5].max()) if self._data.shape[1] > 5 else 1.0
        return pg.QtCore.QRectF(t_min, 0, t_max - t_min, vol_max)


# ---------------------------------------------------------------------------
# Epoch axis item for human-readable time labels
# ---------------------------------------------------------------------------


class _EpochAxisItem(pg.AxisItem):
    """X-axis that converts POSIX epoch floats to datetime strings."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._fmt = "%m/%d %H:%M"

    def set_format(self, fmt: str) -> None:
        self._fmt = fmt

    def tickStrings(self, values: list[float], scale: float, spacing: float) -> list[str]:  # noqa: N802
        result: list[str] = []
        for v in values:
            try:
                dt = datetime.fromtimestamp(v, tz=UTC)
                result.append(dt.strftime(self._fmt))
            except (OSError, ValueError, OverflowError):
                result.append("")
        return result


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------


class CandleChartWidget(QWidget):
    """Candlestick chart with volume sub-plot, trade markers, and crosshair.

    Signals:
        timeframe_changed(str): emitted when user clicks a timeframe button
    """

    timeframe_changed = Signal(str)

    # Available timeframes
    TIMEFRAMES = ["1m", "5m", "15m", "1h"]

    def __init__(self, store=None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = store
        self._current_tf = "5m"
        self._candle_data: Optional[np.ndarray] = None  # Nx5 or Nx6
        self._trade_markers: list[pg.ScatterPlotItem] = []
        self._trade_labels: list[pg.TextItem] = []

        self._build_ui()
        self._setup_crosshair()

        # Wire signals to refresh
        self.timeframe_changed.connect(lambda _tf: self.refresh())

    # ── public API ──────────────────────────────────────────────────────────

    def set_candle_data(self, bars: list[dict[str, Any]]) -> None:
        """Set OHLCV data from a list of bar dicts.

        Each dict should have: time (datetime or str), open, high, low, close, volume.
        This matches the output of TopstepClient.retrieve_bars().
        """
        if not bars:
            return

        rows: list[list[float]] = []
        for bar in bars:
            t = bar.get("time")
            if isinstance(t, datetime):
                epoch = t.timestamp()
            elif isinstance(t, (int, float)):
                epoch = float(t)
            else:
                try:
                    text = str(t).strip()
                    if text.endswith("Z"):
                        text = text[:-1] + "+00:00"
                    epoch = datetime.fromisoformat(text).timestamp()
                except Exception:
                    continue

            o = float(bar.get("open", 0))
            h = float(bar.get("high", 0))
            l_ = float(bar.get("low", 0))
            c = float(bar.get("close", 0))
            v = float(bar.get("volume", 0))
            rows.append([epoch, o, h, l_, c, v])

        if not rows:
            return

        data = np.array(rows, dtype=np.float64)
        # Sort by time
        data = data[data[:, 0].argsort()]
        self._candle_data = data

        self._candle_item.set_data(data[:, :5])
        self._volume_item.set_data(data)

        # Auto-range
        self._candle_plot.autoRange()
        self._volume_plot.autoRange()

        # Update axis format based on timeframe
        self._update_axis_format()

    def set_candle_data_numpy(self, data: np.ndarray) -> None:
        """Set data from a numpy array directly.

        Columns: [epoch, open, high, low, close] or [epoch, open, high, low, close, volume].
        """
        if data is None or len(data) == 0:
            return

        self._candle_data = data
        self._candle_item.set_data(data[:, :5])

        if data.shape[1] >= 6:
            self._volume_item.set_data(data)

        self._candle_plot.autoRange()
        self._volume_plot.autoRange()
        self._update_axis_format()

    def add_trade_markers(self, trades: list[dict[str, Any]]) -> None:
        """Overlay trade entry/exit arrows on the candle chart.

        Each trade dict should have: entry_time, exit_time, direction, entry_price,
        exit_price, pnl.
        """
        # Clear previous markers
        self.clear_trade_markers()

        entry_x: list[float] = []
        entry_y: list[float] = []
        entry_brushes: list[QBrush] = []
        entry_symbols: list[str] = []

        exit_x: list[float] = []
        exit_y: list[float] = []

        for trade in trades:
            # Entry marker
            entry_t = self._to_epoch(trade.get("entry_time"))
            entry_p = trade.get("entry_price")
            if entry_t is not None and entry_p is not None:
                direction = str(trade.get("direction", "")).upper()
                entry_x.append(entry_t)
                entry_y.append(float(entry_p))
                if direction == "LONG":
                    entry_brushes.append(pg.mkBrush(_MARKER_LONG_ENTRY))
                    entry_symbols.append("t1")  # up triangle
                else:
                    entry_brushes.append(pg.mkBrush(_MARKER_SHORT_ENTRY))
                    entry_symbols.append("t")  # down triangle

            # Exit marker
            exit_t = self._to_epoch(trade.get("exit_time"))
            exit_p = trade.get("exit_price")
            if exit_t is not None and exit_p is not None:
                exit_x.append(exit_t)
                exit_y.append(float(exit_p))

                # P&L label at exit
                pnl = trade.get("pnl")
                if pnl is not None:
                    pnl_val = float(pnl)
                    color = PROFIT_GREEN if pnl_val >= 0 else LOSS_RED
                    sign = "+" if pnl_val >= 0 else ""
                    label = pg.TextItem(
                        text=f"{sign}${pnl_val:,.0f}",
                        color=color,
                        anchor=(0.5, 1.2),
                    )
                    label.setFont(QFont("sans-serif", 8, QFont.Bold))
                    label.setPos(exit_t, float(exit_p))
                    self._candle_plot.addItem(label)
                    self._trade_labels.append(label)

        # Entry scatter
        if entry_x:
            # pyqtgraph scatter needs uniform symbol; group by symbol type
            for sym, sym_label in [("t1", "LONG"), ("t", "SHORT")]:
                xs = [
                    entry_x[i]
                    for i in range(len(entry_x))
                    if entry_symbols[i] == sym
                ]
                ys = [
                    entry_y[i]
                    for i in range(len(entry_y))
                    if entry_symbols[i] == sym
                ]
                if xs:
                    brush = (
                        pg.mkBrush(_MARKER_LONG_ENTRY)
                        if sym == "t1"
                        else pg.mkBrush(_MARKER_SHORT_ENTRY)
                    )
                    scatter = pg.ScatterPlotItem(
                        x=xs,
                        y=ys,
                        symbol=sym,
                        size=14,
                        pen=pg.mkPen(None),
                        brush=brush,
                    )
                    self._candle_plot.addItem(scatter)
                    self._trade_markers.append(scatter)

        # Exit scatter (white circles)
        if exit_x:
            scatter = pg.ScatterPlotItem(
                x=exit_x,
                y=exit_y,
                symbol="o",
                size=10,
                pen=pg.mkPen("w", width=1.5),
                brush=pg.mkBrush(255, 255, 255, 80),
            )
            self._candle_plot.addItem(scatter)
            self._trade_markers.append(scatter)

    def clear_trade_markers(self) -> None:
        """Remove all trade overlay markers."""
        for item in self._trade_markers:
            self._candle_plot.removeItem(item)
        self._trade_markers.clear()
        for item in self._trade_labels:
            self._candle_plot.removeItem(item)
        self._trade_labels.clear()

    # ── data loading ─────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Load candle data from the observability store."""
        if self._store is None:
            return
        try:
            from src.gui.data.chart_data import ChartDataProvider

            tf_map = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}
            minutes = tf_map.get(self._current_tf, 5)

            end_time = datetime.now(UTC)
            # Fetch enough history for ~200 candles
            hours = max(4, minutes * 200 / 60)
            start_time = end_time - timedelta(hours=hours)

            provider = ChartDataProvider(self._store)
            # load_candles is signal-based; connect once, call, then disconnect
            df_holder: list = []

            def _on_ready(df):
                df_holder.append(df)

            provider.candles_ready.connect(_on_ready)
            provider.load_candles(
                symbol="F.US.EP",
                start_time=start_time,
                end_time=end_time,
                timeframe_minutes=minutes,
            )

            if df_holder and df_holder[0] is not None and not df_holder[0].empty:
                df = df_holder[0]
                bars: list[dict[str, Any]] = []
                for idx, row in df.iterrows():
                    bars.append({
                        "time": idx,
                        "open": row["open"],
                        "high": row["high"],
                        "low": row["low"],
                        "close": row["close"],
                        "volume": row.get("volume", 0),
                    })
                self.set_candle_data(bars)
        except Exception:
            import traceback
            traceback.print_exc()

    def showEvent(self, event) -> None:  # noqa: N802
        """Load data when the widget becomes visible."""
        super().showEvent(event)
        self.refresh()

    # ── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Toolbar
        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        # Graphics layout widget containing candle plot and volume plot
        self._graphics_layout = pg.GraphicsLayoutWidget()
        self._graphics_layout.setBackground(CHART_BG)

        # Candle plot
        self._candle_axis = _EpochAxisItem(orientation="bottom")
        self._candle_plot = self._graphics_layout.addPlot(
            row=0,
            col=0,
            axisItems={"bottom": self._candle_axis},
        )
        self._candle_plot.showGrid(x=True, y=True, alpha=0.15)
        self._candle_plot.setLabel("left", "Price")
        self._candle_plot.getAxis("left").setStyle(tickFont=QFont("sans-serif", 9))
        self._candle_plot.getAxis("left").setPen(pg.mkPen(CHART_GRID))
        self._candle_axis.setPen(pg.mkPen(CHART_GRID))

        self._candle_item = CandlestickItem()
        self._candle_plot.addItem(self._candle_item)

        # Volume plot (linked X axis)
        self._volume_axis = _EpochAxisItem(orientation="bottom")
        self._volume_plot = self._graphics_layout.addPlot(
            row=1,
            col=0,
            axisItems={"bottom": self._volume_axis},
        )
        self._volume_plot.showGrid(x=True, y=True, alpha=0.1)
        self._volume_plot.setLabel("left", "Volume")
        self._volume_plot.setMaximumHeight(120)
        self._volume_plot.getAxis("left").setStyle(tickFont=QFont("sans-serif", 8))
        self._volume_plot.getAxis("left").setPen(pg.mkPen(CHART_GRID))
        self._volume_axis.setPen(pg.mkPen(CHART_GRID))

        # Link X axes
        self._volume_plot.setXLink(self._candle_plot)

        self._volume_item = VolumeBarItem()
        self._volume_plot.addItem(self._volume_item)

        # OHLCV tooltip label
        self._tooltip_label = QLabel("", self)
        self._tooltip_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; padding: 2px 6px; "
            f"background-color: {BG_SECONDARY}; border-radius: 3px;"
        )
        self._tooltip_label.setFixedHeight(20)

        layout.addWidget(self._tooltip_label)
        layout.addWidget(self._graphics_layout, stretch=1)

    def _build_toolbar(self) -> QFrame:
        frame = QFrame(self)
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SECONDARY};
                border: 1px solid #2a3a5e;
                border-radius: 6px;
                padding: 2px;
            }}
            """
        )
        h = QHBoxLayout(frame)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(4)

        # Timeframe buttons
        self._tf_buttons: dict[str, QPushButton] = {}
        for tf in self.TIMEFRAMES:
            btn = QPushButton(tf, self)
            btn.setCheckable(True)
            btn.setChecked(tf == self._current_tf)
            btn.setFixedWidth(44)
            btn.setStyleSheet(self._tf_button_style())
            btn.clicked.connect(lambda checked, _tf=tf: self._on_timeframe(_tf))
            h.addWidget(btn)
            self._tf_buttons[tf] = btn

        h.addStretch()

        # Symbol label (informational)
        self._symbol_label = QLabel("ES", self)
        self._symbol_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold;"
        )
        h.addWidget(self._symbol_label)

        h.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh", self)
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4a90d9; color: #fff; border: none;
                border-radius: 4px; padding: 5px 12px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background-color: #5da0e9; }
            """
        )
        refresh_btn.clicked.connect(self.refresh)
        h.addWidget(refresh_btn)

        return frame

    @staticmethod
    def _tf_button_style() -> str:
        return """
            QPushButton {
                background-color: #1a1a2e; color: #94a3b8; border: 1px solid #3a4a6e;
                border-radius: 4px; padding: 4px 6px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { border-color: #4a90d9; color: #e2e8f0; }
            QPushButton:checked {
                background-color: #4a90d9; color: #ffffff; border-color: #4a90d9;
            }
        """

    # ── crosshair ───────────────────────────────────────────────────────────

    def _setup_crosshair(self) -> None:
        self._vline = pg.InfiniteLine(angle=90, movable=False, pen=_CROSSHAIR_PEN)
        self._hline = pg.InfiniteLine(angle=0, movable=False, pen=_CROSSHAIR_PEN)
        self._candle_plot.addItem(self._vline, ignoreBounds=True)
        self._candle_plot.addItem(self._hline, ignoreBounds=True)

        self._candle_plot.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def _on_mouse_moved(self, pos: pg.QtCore.QPointF) -> None:
        if not self._candle_plot.sceneBoundingRect().contains(pos):
            return

        mouse_point = self._candle_plot.getViewBox().mapSceneToView(pos)
        x = mouse_point.x()
        y = mouse_point.y()

        self._vline.setPos(x)
        self._hline.setPos(y)

        # Find nearest candle for tooltip
        if self._candle_data is not None and len(self._candle_data) > 0:
            idx = int(np.searchsorted(self._candle_data[:, 0], x))
            idx = max(0, min(idx, len(self._candle_data) - 1))
            bar = self._candle_data[idx]
            try:
                dt = datetime.fromtimestamp(bar[0], tz=UTC)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except (OSError, ValueError):
                time_str = "?"
            o, h, l_, c = bar[1], bar[2], bar[3], bar[4]
            vol = int(bar[5]) if len(bar) > 5 else 0
            self._tooltip_label.setText(
                f"  {time_str}   O: {o:,.2f}  H: {h:,.2f}  L: {l_:,.2f}  C: {c:,.2f}  V: {vol:,}"
            )

    # ── slot handlers ───────────────────────────────────────────────────────

    def _on_timeframe(self, tf: str) -> None:
        self._current_tf = tf
        for name, btn in self._tf_buttons.items():
            btn.setChecked(name == tf)
        self.timeframe_changed.emit(tf)

    # ── helpers ─────────────────────────────────────────────────────────────

    def _update_axis_format(self) -> None:
        if self._current_tf in ("1m", "5m"):
            fmt = "%H:%M"
        elif self._current_tf == "15m":
            fmt = "%m/%d %H:%M"
        else:
            fmt = "%m/%d %H:00"
        self._candle_axis.set_format(fmt)
        self._volume_axis.set_format(fmt)

    @staticmethod
    def _to_epoch(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, datetime):
            return value.timestamp()
        try:
            text = str(value).strip()
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            return datetime.fromisoformat(text).timestamp()
        except (ValueError, TypeError):
            return None

    def set_symbol_label(self, symbol: str) -> None:
        self._symbol_label.setText(symbol)
