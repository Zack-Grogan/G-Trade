"""Trade history table widget with filtering, pagination, and click-to-expand detail.

Displays completed trades from the observability store in a sortable,
filterable QTableView backed by a custom QAbstractTableModel.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any, Optional

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
    Signal,
)
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.gui.util.formatters import fmt_dollar, fmt_pnl
from src.gui.util.styles import (
    BG_CARD,
    BG_PRIMARY,
    BG_SECONDARY,
    LOSS_RED,
    NEUTRAL_GRAY,
    PROFIT_GREEN,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    pnl_color,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PAGE_SIZE = 100

_COLUMNS = [
    "Entry Time",
    "Exit Time",
    "Direction",
    "Contracts",
    "Entry Price",
    "Exit Price",
    "P&L",
    "Zone",
    "Strategy",
    "Regime",
    "Hold Time",
]

_COL_ENTRY_TIME = 0
_COL_EXIT_TIME = 1
_COL_DIRECTION = 2
_COL_CONTRACTS = 3
_COL_ENTRY_PRICE = 4
_COL_EXIT_PRICE = 5
_COL_PNL = 6
_COL_ZONE = 7
_COL_STRATEGY = 8
_COL_REGIME = 9
_COL_HOLD_TIME = 10

_TIME_FMT = "%Y-%m-%d %H:%M"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError:
        return None


def _hold_label(entry: Optional[datetime], exit_: Optional[datetime]) -> str:
    if entry is None or exit_ is None:
        return "--"
    delta = exit_ - entry
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        return "--"
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _hold_minutes(entry: Optional[datetime], exit_: Optional[datetime]) -> float:
    if entry is None or exit_ is None:
        return 0.0
    return max(0.0, (exit_ - entry).total_seconds() / 60.0)


# ---------------------------------------------------------------------------
# Table model
# ---------------------------------------------------------------------------


class TradeTableModel(QAbstractTableModel):
    """Model backing the trade history table."""

    COLUMNS = _COLUMNS

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._trades: list[dict[str, Any]] = []

    # -- public API ----------------------------------------------------------

    def set_trades(self, trades: list[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._trades = list(trades)
        self.endResetModel()

    def trade_at(self, row: int) -> Optional[dict[str, Any]]:
        if 0 <= row < len(self._trades):
            return self._trades[row]
        return None

    def all_trades(self) -> list[dict[str, Any]]:
        return list(self._trades)

    # -- QAbstractTableModel overrides ---------------------------------------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(self._trades)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return len(_COLUMNS)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(_COLUMNS):
                return _COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # noqa: C901
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._trades):
            return None

        trade = self._trades[row]
        entry_dt = _parse_dt(trade.get("entry_time"))
        exit_dt = _parse_dt(trade.get("exit_time"))

        if role == Qt.DisplayRole:
            return self._display_value(trade, col, entry_dt, exit_dt)

        if role == Qt.ForegroundRole:
            return self._foreground(trade, col)

        if role == Qt.FontRole:
            if col in (_COL_DIRECTION, _COL_PNL):
                font = QFont()
                font.setBold(True)
                return font

        if role == Qt.TextAlignmentRole:
            if col in (_COL_CONTRACTS, _COL_ENTRY_PRICE, _COL_EXIT_PRICE, _COL_PNL):
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        # UserRole stores the raw sort key
        if role == Qt.UserRole:
            return self._sort_key(trade, col, entry_dt, exit_dt)

        return None

    # -- internals -----------------------------------------------------------

    def _display_value(
        self,
        trade: dict[str, Any],
        col: int,
        entry_dt: Optional[datetime],
        exit_dt: Optional[datetime],
    ) -> str:
        if col == _COL_ENTRY_TIME:
            return entry_dt.strftime(_TIME_FMT) if entry_dt else "--"
        if col == _COL_EXIT_TIME:
            return exit_dt.strftime(_TIME_FMT) if exit_dt else "--"
        if col == _COL_DIRECTION:
            d = str(trade.get("direction", "")).upper()
            return d if d in ("LONG", "SHORT") else d or "--"
        if col == _COL_CONTRACTS:
            return str(trade.get("contracts", "--"))
        if col == _COL_ENTRY_PRICE:
            price = trade.get("entry_price")
            return f"{float(price):,.2f}" if price is not None else "--"
        if col == _COL_EXIT_PRICE:
            price = trade.get("exit_price")
            return f"{float(price):,.2f}" if price is not None else "--"
        if col == _COL_PNL:
            pnl = trade.get("pnl")
            return fmt_pnl(float(pnl)) if pnl is not None else "--"
        if col == _COL_ZONE:
            return str(trade.get("zone") or "--")
        if col == _COL_STRATEGY:
            return str(trade.get("strategy") or "--")
        if col == _COL_REGIME:
            return str(trade.get("regime") or "--")
        if col == _COL_HOLD_TIME:
            return _hold_label(entry_dt, exit_dt)
        return ""

    def _foreground(self, trade: dict[str, Any], col: int) -> Optional[QBrush]:
        if col == _COL_PNL:
            pnl = trade.get("pnl")
            if pnl is not None:
                return QBrush(QColor(pnl_color(float(pnl))))
        if col == _COL_DIRECTION:
            d = str(trade.get("direction", "")).upper()
            if d == "LONG":
                return QBrush(QColor(PROFIT_GREEN))
            if d == "SHORT":
                return QBrush(QColor(LOSS_RED))
        return QBrush(QColor(TEXT_PRIMARY))

    def _sort_key(
        self,
        trade: dict[str, Any],
        col: int,
        entry_dt: Optional[datetime],
        exit_dt: Optional[datetime],
    ) -> Any:
        if col == _COL_ENTRY_TIME:
            return entry_dt.timestamp() if entry_dt else 0.0
        if col == _COL_EXIT_TIME:
            return exit_dt.timestamp() if exit_dt else 0.0
        if col == _COL_PNL:
            pnl = trade.get("pnl")
            return float(pnl) if pnl is not None else 0.0
        if col == _COL_CONTRACTS:
            return int(trade.get("contracts", 0))
        if col == _COL_ENTRY_PRICE:
            return float(trade.get("entry_price", 0))
        if col == _COL_EXIT_PRICE:
            return float(trade.get("exit_price", 0))
        if col == _COL_HOLD_TIME:
            return _hold_minutes(entry_dt, exit_dt)
        return self._display_value(trade, col, entry_dt, exit_dt)


# ---------------------------------------------------------------------------
# Sortable proxy
# ---------------------------------------------------------------------------


class _SortProxy(QSortFilterProxyModel):
    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # noqa: N802
        lv = self.sourceModel().data(left, Qt.UserRole)
        rv = self.sourceModel().data(right, Qt.UserRole)
        if isinstance(lv, (int, float)) and isinstance(rv, (int, float)):
            return lv < rv
        return str(lv) < str(rv)


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------


class TradeHistoryWidget(QWidget):
    """Full trade-history panel: filter bar, table, detail pane, pagination."""

    trade_selected = Signal(dict)  # emitted when a row is clicked

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._all_trades: list[dict[str, Any]] = []
        self._filtered_trades: list[dict[str, Any]] = []
        self._page = 0

        self._build_ui()
        self._connect_signals()

    # ── public API ──────────────────────────────────────────────────────────

    def load_trades(
        self,
        store: Any,
        run_id: Optional[str] = None,
        symbol: str = "ES",
    ) -> None:
        """Query completed trades from the observability store and populate."""
        try:
            trades = store.query_completed_trades(
                run_id=run_id,
                limit=10000,
                ascending=True,
            )
        except Exception:
            logger.exception("Failed to load trades from store")
            trades = []
        self.set_trades(trades)

    def set_trades(self, trades: list[dict[str, Any]]) -> None:
        """Directly set trade data (useful for testing or external sources)."""
        self._all_trades = list(trades)
        self._populate_filter_options()
        self._page = 0
        self.apply_filters()

    def apply_filters(self) -> None:
        """Apply the current filter bar settings and refresh the table."""
        filtered = list(self._all_trades)

        # Date range
        start_date = self._date_from.date().toPython()
        end_date = self._date_to.date().toPython()
        start_dt = datetime(start_date.year, start_date.month, start_date.day, tzinfo=UTC)
        end_dt = datetime(
            end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=UTC
        )
        filtered = [
            t
            for t in filtered
            if self._trade_in_range(t, start_dt, end_dt)
        ]

        # Zone
        zone = self._zone_combo.currentText()
        if zone and zone != "All":
            filtered = [t for t in filtered if (t.get("zone") or "Unknown") == zone]

        # Direction
        direction = self._dir_combo.currentText()
        if direction == "Long":
            filtered = [
                t for t in filtered if str(t.get("direction", "")).upper() == "LONG"
            ]
        elif direction == "Short":
            filtered = [
                t for t in filtered if str(t.get("direction", "")).upper() == "SHORT"
            ]

        # P&L
        pnl_filter = self._pnl_combo.currentText()
        if pnl_filter == "Winners":
            filtered = [t for t in filtered if float(t.get("pnl", 0)) > 0]
        elif pnl_filter == "Losers":
            filtered = [t for t in filtered if float(t.get("pnl", 0)) < 0]

        # Search
        search = self._search_edit.text().strip().lower()
        if search:
            filtered = [t for t in filtered if self._trade_matches_search(t, search)]

        self._filtered_trades = filtered
        self._page = 0
        self._refresh_table()

    # ── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Filter bar
        self._filter_frame = self._build_filter_bar()
        layout.addWidget(self._filter_frame)

        # Splitter: table on top, detail below
        splitter = QSplitter(Qt.Vertical, self)
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background: {BG_SECONDARY}; height: 3px; }}"
        )

        # Table
        self._model = TradeTableModel(self)
        self._proxy = _SortProxy(self)
        self._proxy.setSourceModel(self._model)

        self._table = QTableView(self)
        self._table.setModel(self._proxy)
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setStyleSheet(
            f"""
            QTableView {{
                background-color: {BG_SECONDARY};
                alternate-background-color: {BG_CARD};
                color: {TEXT_PRIMARY};
                gridline-color: transparent;
                border: 1px solid #2a3a5e;
                border-radius: 6px;
                font-size: 11px;
                selection-background-color: #3a4a6e;
                selection-color: {TEXT_PRIMARY};
            }}
            QTableView::item {{
                padding: 4px 8px;
            }}
            QHeaderView::section {{
                background-color: #1a1a2e;
                color: {TEXT_PRIMARY};
                padding: 6px 8px;
                border: none;
                border-bottom: 2px solid #4a90d9;
                font-weight: bold;
                font-size: 11px;
            }}
            """
        )

        header = self._table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(_COL_ENTRY_TIME, QHeaderView.Interactive)
        header.setSectionResizeMode(_COL_EXIT_TIME, QHeaderView.Interactive)
        header.resizeSection(_COL_ENTRY_TIME, 140)
        header.resizeSection(_COL_EXIT_TIME, 140)

        splitter.addWidget(self._table)

        # Detail pane
        self._detail_frame = self._build_detail_pane()
        self._detail_frame.setVisible(False)
        splitter.addWidget(self._detail_frame)
        splitter.setSizes([600, 200])

        layout.addWidget(splitter, stretch=1)

        # Pagination bar
        self._pagination_bar = self._build_pagination_bar()
        layout.addWidget(self._pagination_bar)

    def _build_filter_bar(self) -> QFrame:
        frame = QFrame(self)
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SECONDARY};
                border: 1px solid #2a3a5e;
                border-radius: 6px;
                padding: 4px;
            }}
            QComboBox, QDateEdit, QLineEdit {{
                background-color: #1a1a2e;
                color: {TEXT_PRIMARY};
                border: 1px solid #3a4a6e;
                border-radius: 4px;
                padding: 4px 8px;
                min-height: 24px;
                font-size: 11px;
            }}
            QComboBox:hover, QDateEdit:hover, QLineEdit:hover {{
                border-color: #4a90d9;
            }}
            QComboBox::drop-down {{ border: none; }}
            QLabel {{ color: {TEXT_SECONDARY}; font-size: 11px; }}
            """
        )
        h = QHBoxLayout(frame)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(8)

        # Date range
        h.addWidget(QLabel("From:"))
        self._date_from = QDateEdit(self)
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(datetime.now(UTC).date() - timedelta(days=30))
        h.addWidget(self._date_from)

        h.addWidget(QLabel("To:"))
        self._date_to = QDateEdit(self)
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(datetime.now(UTC).date())
        h.addWidget(self._date_to)

        # Zone
        h.addWidget(QLabel("Zone:"))
        self._zone_combo = QComboBox(self)
        self._zone_combo.addItem("All")
        self._zone_combo.setMinimumWidth(100)
        h.addWidget(self._zone_combo)

        # Direction
        h.addWidget(QLabel("Direction:"))
        self._dir_combo = QComboBox(self)
        self._dir_combo.addItems(["All", "Long", "Short"])
        h.addWidget(self._dir_combo)

        # P&L
        h.addWidget(QLabel("P&L:"))
        self._pnl_combo = QComboBox(self)
        self._pnl_combo.addItems(["All", "Winners", "Losers"])
        h.addWidget(self._pnl_combo)

        # Search
        h.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit(self)
        self._search_edit.setPlaceholderText("zone, strategy, regime...")
        self._search_edit.setMinimumWidth(140)
        h.addWidget(self._search_edit)

        # Apply button
        btn = QPushButton("Apply", self)
        btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4a90d9; color: #fff; border: none;
                border-radius: 4px; padding: 6px 14px; font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #5da0e9; }
            QPushButton:pressed { background-color: #3a7ec9; }
            """
        )
        btn.clicked.connect(self.apply_filters)
        h.addWidget(btn)

        h.addStretch()

        # Count label
        self._count_label = QLabel("0 trades", self)
        self._count_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        h.addWidget(self._count_label)

        return frame

    def _build_detail_pane(self) -> QFrame:
        frame = QFrame(self)
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid #2a3a5e;
                border-radius: 6px;
            }}
            """
        )
        v = QVBoxLayout(frame)
        v.setContentsMargins(12, 8, 12, 8)
        v.setSpacing(4)

        # Header row
        hdr = QHBoxLayout()
        self._detail_title = QLabel("Trade Detail", self)
        self._detail_title.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: bold;"
        )
        hdr.addWidget(self._detail_title)
        hdr.addStretch()

        close_btn = QPushButton("Close", self)
        close_btn.setFixedHeight(24)
        close_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent; color: {TEXT_MUTED};
                border: 1px solid #3a4a6e; border-radius: 4px;
                padding: 2px 10px; font-size: 10px;
            }}
            QPushButton:hover {{ color: {TEXT_PRIMARY}; border-color: #5a6a8e; }}
            """
        )
        close_btn.clicked.connect(lambda: self._detail_frame.setVisible(False))
        hdr.addWidget(close_btn)
        v.addLayout(hdr)

        # Scores summary
        self._detail_scores = QLabel("", self)
        self._detail_scores.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        self._detail_scores.setWordWrap(True)
        v.addWidget(self._detail_scores)

        # Full JSON
        self._detail_text = QTextEdit(self)
        self._detail_text.setReadOnly(True)
        self._detail_text.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {BG_SECONDARY};
                color: {TEXT_PRIMARY};
                border: 1px solid #2a3a5e;
                border-radius: 4px;
                font-family: 'Menlo', 'Consolas', monospace;
                font-size: 10px;
                padding: 6px;
            }}
            """
        )
        v.addWidget(self._detail_text, stretch=1)

        return frame

    def _build_pagination_bar(self) -> QFrame:
        frame = QFrame(self)
        frame.setStyleSheet(f"background: transparent;")
        h = QHBoxLayout(frame)
        h.setContentsMargins(0, 2, 0, 2)
        h.setSpacing(8)

        self._page_label = QLabel("Page 1", self)
        self._page_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        h.addWidget(self._page_label)

        h.addStretch()

        self._prev_btn = QPushButton("Previous", self)
        self._prev_btn.setEnabled(False)
        self._prev_btn.setStyleSheet(self._page_button_style())
        h.addWidget(self._prev_btn)

        self._next_btn = QPushButton("Load More", self)
        self._next_btn.setStyleSheet(self._page_button_style())
        h.addWidget(self._next_btn)

        return frame

    @staticmethod
    def _page_button_style() -> str:
        return """
            QPushButton {
                background-color: #2a3a5e; color: #e2e8f0; border: none;
                border-radius: 4px; padding: 5px 12px; font-size: 11px;
            }
            QPushButton:hover { background-color: #3a4a6e; }
            QPushButton:disabled { color: #4a5568; background-color: #1e1e2e; }
        """

    # ── signals ─────────────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._table.clicked.connect(self._on_row_clicked)
        self._next_btn.clicked.connect(self._next_page)
        self._prev_btn.clicked.connect(self._prev_page)
        self._search_edit.returnPressed.connect(self.apply_filters)

    # ── slot handlers ───────────────────────────────────────────────────────

    def _on_row_clicked(self, index: QModelIndex) -> None:
        source_index = self._proxy.mapToSource(index)
        trade = self._model.trade_at(source_index.row())
        if trade is None:
            return
        self._show_detail(trade)
        self.trade_selected.emit(trade)

    def _show_detail(self, trade: dict[str, Any]) -> None:
        direction = str(trade.get("direction", "")).upper()
        pnl = trade.get("pnl")
        pnl_str = fmt_pnl(float(pnl)) if pnl is not None else "--"
        self._detail_title.setText(
            f"Trade Detail  |  {direction}  |  P&L: {pnl_str}"
        )

        # Scores
        payload = trade.get("payload", {})
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        score_parts: list[str] = []
        for key in (
            "entry_score",
            "long_score",
            "short_score",
            "exit_score",
            "entry_reason",
            "exit_reason",
        ):
            val = payload.get(key) or trade.get(key)
            if val is not None:
                label = key.replace("_", " ").title()
                score_parts.append(f"{label}: {val}")
        self._detail_scores.setText("  |  ".join(score_parts) if score_parts else "")

        # Full JSON
        try:
            pretty = json.dumps(trade, indent=2, default=str)
        except Exception:
            pretty = str(trade)
        self._detail_text.setPlainText(pretty)
        self._detail_frame.setVisible(True)

    def _next_page(self) -> None:
        max_page = max(0, (len(self._filtered_trades) - 1) // PAGE_SIZE)
        if self._page < max_page:
            self._page += 1
            self._refresh_table()

    def _prev_page(self) -> None:
        if self._page > 0:
            self._page -= 1
            self._refresh_table()

    # ── internal ────────────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        start = self._page * PAGE_SIZE
        end = start + PAGE_SIZE
        page_trades = self._filtered_trades[start:end]
        self._model.set_trades(page_trades)

        total = len(self._filtered_trades)
        showing_end = min(end, total)
        self._count_label.setText(
            f"{total} trades (showing {start + 1}-{showing_end})" if total else "0 trades"
        )

        max_page = max(0, (total - 1) // PAGE_SIZE) if total else 0
        self._page_label.setText(f"Page {self._page + 1} / {max_page + 1}")
        self._prev_btn.setEnabled(self._page > 0)
        self._next_btn.setEnabled(self._page < max_page)

    def _populate_filter_options(self) -> None:
        zones: set[str] = set()
        for t in self._all_trades:
            z = t.get("zone")
            if z:
                zones.add(z)

        current = self._zone_combo.currentText()
        self._zone_combo.blockSignals(True)
        self._zone_combo.clear()
        self._zone_combo.addItem("All")
        for z in sorted(zones):
            self._zone_combo.addItem(z)
        idx = self._zone_combo.findText(current)
        if idx >= 0:
            self._zone_combo.setCurrentIndex(idx)
        self._zone_combo.blockSignals(False)

        # Set date range to cover data
        if self._all_trades:
            entry_times = [
                _parse_dt(t.get("entry_time")) for t in self._all_trades
            ]
            entry_times = [dt for dt in entry_times if dt is not None]
            if entry_times:
                self._date_from.setDate(min(entry_times).date())
                self._date_to.setDate(max(entry_times).date())

    @staticmethod
    def _trade_in_range(
        trade: dict[str, Any], start: datetime, end: datetime
    ) -> bool:
        entry_dt = _parse_dt(trade.get("entry_time"))
        if entry_dt is None:
            return True  # include trades with no timestamp
        return start <= entry_dt <= end

    @staticmethod
    def _trade_matches_search(trade: dict[str, Any], search: str) -> bool:
        searchable = " ".join(
            str(trade.get(k) or "")
            for k in ("zone", "strategy", "regime", "direction", "trade_id")
        ).lower()
        payload = trade.get("payload", {})
        if isinstance(payload, dict):
            searchable += " " + json.dumps(payload).lower()
        return search in searchable
