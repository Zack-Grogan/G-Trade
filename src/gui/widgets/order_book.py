"""Open / recent orders table widget.

Displays active and recent order lifecycle rows from the observability store
in a color-coded QTableView with 2-second auto-refresh.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QTimer, Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from src.gui.util.formatters import fmt_time
from src.gui.util.styles import (
    STATUS_CANCELLED,
    STATUS_FILLED,
    STATUS_PARTIAL,
    STATUS_PENDING,
    STATUS_REJECTED,
    STATUS_WORKING,
    TEXT_MUTED,
    TEXT_PRIMARY,
    qcolor,
    status_color,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Table model
# ---------------------------------------------------------------------------

_COLUMNS = [
    "Order ID",
    "Account",
    "Time",
    "Side",
    "Role",
    "Status",
    "Price",
    "Qty",
    "Filled",
    "Last Update",
]

# Keys expected in the dicts returned by store.query_order_lifecycle().
_KEY_MAP: dict[str, str] = {
    "Order ID": "order_id",
    "Account": "tenant_id",
    "Time": "observed_at",
    "Side": "side",
    "Role": "role",
    "Status": "status",
    "Price": "limit_price",
    "Qty": "quantity",
    "Filled": "filled_quantity",
    "Last Update": "observed_at",
}


def _cell_text(row: dict[str, Any], column: str) -> str:
    """Extract a display string for a given column from an order-lifecycle row."""
    key = _KEY_MAP.get(column, "")
    raw = row.get(key)
    if raw is None:
        return "--"

    if column == "Time":
        return _format_timestamp(raw)
    if column == "Last Update":
        return _format_timestamp(raw)
    if column == "Price":
        try:
            return f"{float(raw):,.2f}"
        except (TypeError, ValueError):
            return str(raw)
    if column in ("Qty", "Filled"):
        try:
            val = int(raw)
            return str(val) if val else "--"
        except (TypeError, ValueError):
            return str(raw)
    if column == "Order ID":
        text = str(raw)
        return text[-12:] if len(text) > 12 else text
    if column == "Account":
        return str(raw) if raw else "--"
    return str(raw) if raw else "--"


def _format_timestamp(value: Any) -> str:
    """Convert an ISO-ish timestamp string or datetime to HH:MM:SS."""
    if isinstance(value, datetime):
        return fmt_time(value)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
            return fmt_time(dt)
        except (ValueError, TypeError):
            return value[:19] if len(value) >= 19 else value
    return str(value)


class OrderTableModel(QAbstractTableModel):
    """Read-only table model backed by a list of order-lifecycle dicts."""

    COLUMNS = _COLUMNS

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []

    # -- public API --------------------------------------------------------

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        """Replace all data and refresh the view."""
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def row_data(self, row_idx: int) -> dict[str, Any] | None:
        if 0 <= row_idx < len(self._rows):
            return self._rows[row_idx]
        return None

    # -- QAbstractTableModel overrides -------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(self.COLUMNS)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: C901
        if not index.isValid():
            return None

        row_idx = index.row()
        col_idx = index.column()
        if row_idx < 0 or row_idx >= len(self._rows):
            return None

        row = self._rows[row_idx]
        col_name = self.COLUMNS[col_idx]

        if role == Qt.ItemDataRole.DisplayRole:
            return _cell_text(row, col_name)

        if role == Qt.ItemDataRole.ForegroundRole:
            if col_name == "Status":
                hex_color = status_color(str(row.get("status", "")))
                return qcolor(hex_color)
            if col_name == "Side":
                side = str(row.get("side", "")).upper()
                if side == "BUY":
                    return qcolor(STATUS_FILLED)
                if side == "SELL":
                    return qcolor(STATUS_REJECTED)
            return qcolor(TEXT_PRIMARY)

        if role == Qt.ItemDataRole.FontRole:
            if col_name == "Status":
                font = QFont()
                font.setBold(True)
                return font

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col_name in ("Price", "Qty", "Filled"):
                return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        return None


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class OrderBookWidget(QWidget):
    """Panel showing open and recent orders with auto-refresh."""

    REFRESH_INTERVAL_MS = 2000
    DEFAULT_ROW_LIMIT = 100

    def __init__(self, store: Any = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = store
        self._row_limit = self.DEFAULT_ROW_LIMIT

        self._build_ui()
        self._setup_timer()

    # -- UI construction ---------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Title
        title = QLabel("Open / Recent Orders")
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 1)
        title.setFont(title_font)
        layout.addWidget(title)

        # Status indicator
        self._status_label = QLabel("Waiting for data...")
        self._status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._status_label)

        # Table
        self._model = OrderTableModel(self)
        self._table = QTableView(self)
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.setSortingEnabled(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(True)

        # Column sizing
        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Sensible initial widths
        _initial_widths = [100, 90, 80, 50, 60, 90, 80, 40, 50, 80]
        for i, w in enumerate(_initial_widths):
            if i < len(_COLUMNS):
                header.resizeSection(i, w)

        layout.addWidget(self._table, stretch=1)

    def _setup_timer(self) -> None:
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(self.REFRESH_INTERVAL_MS)
        self._refresh_timer.timeout.connect(self.refresh)

    # -- Public API --------------------------------------------------------

    def set_store(self, store: Any) -> None:
        """Attach or replace the observability store and trigger an immediate refresh."""
        self._store = store
        self.refresh()

    def refresh(self) -> None:
        """Fetch latest orders and update the table model."""
        if self._store is None:
            return
        try:
            rows = self._store.query_order_lifecycle(limit=self._row_limit)
            self._model.set_rows(rows)
            count = len(rows)
            self._status_label.setText(f"{count} order{'s' if count != 1 else ''} loaded")
        except Exception:
            logger.exception("OrderBookWidget.refresh failed")
            self._status_label.setText("Error loading orders")

    # -- Visibility-driven timer management --------------------------------

    def showEvent(self, event) -> None:  # noqa: N802
        """Start auto-refresh when the widget becomes visible."""
        super().showEvent(event)
        self.refresh()
        self._refresh_timer.start()

    def hideEvent(self, event) -> None:  # noqa: N802
        """Stop auto-refresh when the widget is hidden."""
        super().hideEvent(event)
        self._refresh_timer.stop()
