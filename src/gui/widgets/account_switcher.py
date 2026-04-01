"""Account selection widget for the G-Trade sidebar.

Provides a QComboBox to switch between Topstep accounts and a mini detail
card showing balance, equity, available margin, open P&L, and realized P&L.
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.gui.util.formatters import format_pnl, pnl_color
from src.gui.util.styles import (
    ACCENT_BLUE,
    BG_LIGHT,
    BG_MEDIUM,
    BORDER_COLOR,
    INFO_BLUE,
    LOSS_RED,
    PROFIT_GREEN,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LIVE_BORDER = PROFIT_GREEN
_PRACTICE_BORDER = INFO_BLUE


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class AccountSwitcherWidget(QWidget):
    """Persistent sidebar widget for selecting the active trading account.

    Signals
    -------
    account_selected(str)
        Emitted with the ``account_id`` whenever the user picks a different
        account from the combo box.
    refresh_requested()
        Emitted when the user clicks the refresh button.
    """

    account_selected = Signal(str)
    refresh_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("AccountSwitcherWidget")

        # account_id -> display metadata (stashed for lookup on index change)
        self._account_ids: list[str] = []
        self._is_practice: dict[str, bool] = {}

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # -- header row: combo + refresh button ----------------------------
        header = QHBoxLayout()
        header.setSpacing(4)

        self._combo = QComboBox()
        self._combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._combo.setMinimumHeight(30)
        self._combo.currentIndexChanged.connect(self._on_index_changed)
        header.addWidget(self._combo)

        self._refresh_btn = QPushButton("\u21bb")  # Unicode refresh arrow
        self._refresh_btn.setFixedSize(30, 30)
        self._refresh_btn.setToolTip("Refresh accounts")
        self._refresh_btn.clicked.connect(self.refresh_requested.emit)
        header.addWidget(self._refresh_btn)

        root.addLayout(header)

        # -- detail card ---------------------------------------------------
        self._detail_card = QFrame()
        self._detail_card.setObjectName("account_detail_card")
        self._apply_card_border(is_practice=True)

        grid = QGridLayout(self._detail_card)
        grid.setContentsMargins(10, 8, 10, 8)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(4)

        # Row labels and value widgets
        self._balance_lbl = self._add_row(grid, 0, "Balance")
        self._equity_lbl = self._add_row(grid, 1, "Equity")
        self._available_lbl = self._add_row(grid, 2, "Available")
        self._open_pnl_lbl = self._add_row(grid, 3, "Open P&L")
        self._realized_pnl_lbl = self._add_row(grid, 4, "Realized P&L")

        root.addWidget(self._detail_card)

    def _add_row(self, grid: QGridLayout, row: int, label: str) -> QLabel:
        """Add a label + value pair to *grid* and return the value QLabel."""
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: transparent;")
        grid.addWidget(lbl, row, 0, Qt.AlignmentFlag.AlignLeft)

        val = QLabel("--")
        val.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold; background: transparent;"
        )
        val.setAlignment(Qt.AlignmentFlag.AlignRight)
        grid.addWidget(val, row, 1, Qt.AlignmentFlag.AlignRight)

        return val

    def _apply_card_border(self, is_practice: bool = True) -> None:
        border_color = _PRACTICE_BORDER if is_practice else _LIVE_BORDER
        self._detail_card.setStyleSheet(
            f"QFrame#account_detail_card {{ "
            f"background-color: {BG_MEDIUM}; "
            f"border: 2px solid {border_color}; "
            f"border-radius: 6px; }}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_accounts(self, accounts: list[Any]) -> None:
        """Populate the combo box with a list of accounts.

        Each item can be:
        - A dict with keys ``account_id``, ``name``, ``is_practice``
        - An ``Account`` dataclass instance (from ``topstep_client``)
        """
        self._combo.blockSignals(True)
        self._combo.clear()
        self._account_ids.clear()
        self._is_practice.clear()

        for acct in accounts:
            if isinstance(acct, dict):
                aid = str(acct.get("account_id", acct.get("id", "")))
                name = str(acct.get("name", ""))
                is_prac = bool(acct.get("is_practice", False))
            else:
                # Assume dataclass-like object (Account)
                aid = str(getattr(acct, "account_id", ""))
                name = str(getattr(acct, "name", ""))
                is_prac = bool(getattr(acct, "is_practice", False))

            tag = "PRAC" if is_prac else "LIVE"
            short_id = aid[-8:] if len(aid) > 8 else aid
            display = f"{name} ({short_id}) [{tag}]"

            self._account_ids.append(aid)
            self._is_practice[aid] = is_prac
            self._combo.addItem(display, userData=aid)

        self._combo.blockSignals(False)

        # Trigger initial selection signal if any accounts present
        if self._account_ids:
            self._on_index_changed(self._combo.currentIndex())

    def update_account_info(self, account_dict: dict[str, Any]) -> None:
        """Update the detail card with fresh account data.

        Expected keys: ``balance``, ``equity``, ``available``,
        ``open_pnl``, ``realized_pnl``, ``is_practice``.
        """

        def _dollar(key: str) -> str:
            v = account_dict.get(key)
            if v is None:
                return "--"
            return f"${v:,.2f}"

        self._balance_lbl.setText(_dollar("balance"))
        self._equity_lbl.setText(_dollar("equity"))
        self._available_lbl.setText(_dollar("available"))

        # Open P&L with color
        open_pnl = account_dict.get("open_pnl")
        if open_pnl is not None:
            self._open_pnl_lbl.setText(format_pnl(open_pnl))
            self._open_pnl_lbl.setStyleSheet(
                f"color: {pnl_color(open_pnl)}; font-size: 12px; "
                f"font-weight: bold; background: transparent;"
            )
        else:
            self._open_pnl_lbl.setText("--")

        # Realized P&L with color
        realized_pnl = account_dict.get("realized_pnl")
        if realized_pnl is not None:
            self._realized_pnl_lbl.setText(format_pnl(realized_pnl))
            self._realized_pnl_lbl.setStyleSheet(
                f"color: {pnl_color(realized_pnl)}; font-size: 12px; "
                f"font-weight: bold; background: transparent;"
            )
        else:
            self._realized_pnl_lbl.setText("--")

        # Border color
        is_prac = account_dict.get("is_practice", True)
        self._apply_card_border(is_practice=bool(is_prac))

    def current_account_id(self) -> Optional[str]:
        """Return the currently selected account_id, or None."""
        idx = self._combo.currentIndex()
        if 0 <= idx < len(self._account_ids):
            return self._account_ids[idx]
        return None

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_index_changed(self, index: int) -> None:
        if 0 <= index < len(self._account_ids):
            aid = self._account_ids[index]
            is_prac = self._is_practice.get(aid, True)
            self._apply_card_border(is_practice=is_prac)
            self.account_selected.emit(aid)
