"""Dark theme QSS stylesheet for G-Trade trading application."""

from __future__ import annotations

from PySide6.QtGui import QColor

# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------

PROFIT_GREEN = "#00c853"
LOSS_RED = "#ff1744"
INFO_BLUE = "#2979ff"
WARNING_YELLOW = "#ffd600"

BG_DARK = "#0f0f1a"
BG_MEDIUM = "#1a1a2e"
BG_LIGHT = "#25253d"

TEXT_PRIMARY = "#e0e0e0"
TEXT_SECONDARY = "#8888aa"
TEXT_MUTED = "#606080"

ACCENT_BLUE = "#3f51b5"
BORDER_COLOR = "#2e2e4a"

ORANGE = "#ff9800"
GRAY = "#808080"
GRAY_LIGHT = "#b0b0b0"

# ---- Order / status palette ----
STATUS_FILLED = PROFIT_GREEN
STATUS_WORKING = WARNING_YELLOW
STATUS_REJECTED = LOSS_RED
STATUS_CANCELLED = "#ef5350"
STATUS_PENDING = GRAY_LIGHT
STATUS_PARTIAL = ORANGE

# ---- Log level palette ----
LOG_LEVEL_COLORS: dict[str, str] = {
    "DEBUG": GRAY,
    "INFO": TEXT_PRIMARY,
    "WARNING": WARNING_YELLOW,
    "ERROR": LOSS_RED,
}

# ---- Progress bar palette ----
PROGRESS_SAFE = PROFIT_GREEN
PROGRESS_CAUTION = WARNING_YELLOW
PROGRESS_DANGER = LOSS_RED

# ---- Evaluation rule states ----
RULE_PASS = PROFIT_GREEN
RULE_FAIL = LOSS_RED

# ---- Aliases used by chart/analysis widgets ----
BG_PRIMARY = BG_DARK
BG_SECONDARY = BG_MEDIUM
BG_CARD = BG_LIGHT
CHART_BG = BG_DARK
CHART_GRID = BORDER_COLOR
NEUTRAL_GRAY = GRAY


def pnl_color(value: float) -> str:
    """Return hex color for P&L values: green positive, red negative, gray zero."""
    if value > 0:
        return PROFIT_GREEN
    if value < 0:
        return LOSS_RED
    return TEXT_SECONDARY


def qcolor(hex_color: str) -> QColor:
    """Convert a hex color string to a QColor."""
    return QColor(hex_color)


def status_color(status: str) -> str:
    """Return the hex color for a given order status string."""
    key = (status or "").lower().replace(" ", "_")
    mapping = {
        "filled": STATUS_FILLED,
        "working": STATUS_WORKING,
        "new": STATUS_WORKING,
        "accepted": STATUS_WORKING,
        "pending_new": STATUS_PENDING,
        "pending": STATUS_PENDING,
        "partially_filled": STATUS_PARTIAL,
        "rejected": STATUS_REJECTED,
        "cancelled": STATUS_CANCELLED,
        "canceled": STATUS_CANCELLED,
        "expired": STATUS_CANCELLED,
    }
    return mapping.get(key, TEXT_SECONDARY)


def load_dark_stylesheet() -> str:
    """Return the full QSS dark-theme stylesheet string."""
    return _QSS


# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------

_QSS = f"""
/* ====================================================================
   G-Trade Dark Theme
   ==================================================================== */

/* -- Base ------------------------------------------------------------ */

QMainWindow {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
}}

QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}}

QLabel {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    padding: 1px;
}}

/* -- Buttons --------------------------------------------------------- */

QPushButton {{
    background-color: {BG_LIGHT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 6px 16px;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {ACCENT_BLUE};
    border-color: {ACCENT_BLUE};
}}

QPushButton:pressed {{
    background-color: #303070;
}}

QPushButton:disabled {{
    background-color: {BG_MEDIUM};
    color: {TEXT_SECONDARY};
    border-color: {BORDER_COLOR};
}}

/* -- ComboBox -------------------------------------------------------- */

QComboBox {{
    background-color: {BG_LIGHT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 24px;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 6px solid {TEXT_SECONDARY};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_MEDIUM};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: {ACCENT_BLUE};
    selection-color: {TEXT_PRIMARY};
}}

/* -- Tables ---------------------------------------------------------- */

QTableView, QTableWidget {{
    background-color: {BG_DARK};
    alternate-background-color: {BG_MEDIUM};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    gridline-color: {BORDER_COLOR};
    selection-background-color: {ACCENT_BLUE};
    selection-color: {TEXT_PRIMARY};
}}

QTableView::item, QTableWidget::item {{
    padding: 4px 8px;
}}

QHeaderView {{
    background-color: {BG_MEDIUM};
}}

QHeaderView::section {{
    background-color: {BG_MEDIUM};
    color: {TEXT_PRIMARY};
    border: none;
    border-right: 1px solid {BORDER_COLOR};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 6px 8px;
    font-weight: bold;
}}

QHeaderView::section:hover {{
    background-color: {BG_LIGHT};
}}

/* -- Trees & Lists --------------------------------------------------- */

QTreeWidget, QListWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    outline: none;
}}

QTreeWidget::item, QListWidget::item {{
    padding: 4px 8px;
    border: none;
}}

QTreeWidget::item:selected, QListWidget::item:selected {{
    background-color: {ACCENT_BLUE};
    color: {TEXT_PRIMARY};
}}

QTreeWidget::item:hover, QListWidget::item:hover {{
    background-color: {BG_LIGHT};
}}

/* -- Scroll Area ----------------------------------------------------- */

QScrollArea {{
    background-color: {BG_DARK};
    border: none;
}}

/* -- Frames & Groups ------------------------------------------------- */

QFrame {{
    background-color: {BG_DARK};
    border: none;
}}

QGroupBox {{
    background-color: {BG_MEDIUM};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: {ACCENT_BLUE};
}}

/* -- Tabs ------------------------------------------------------------ */

QTabWidget::pane {{
    background-color: {BG_DARK};
    border: 1px solid {BORDER_COLOR};
    border-top: none;
}}

QTabBar::tab {{
    background-color: {BG_MEDIUM};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {ACCENT_BLUE};
}}

QTabBar::tab:hover:!selected {{
    background-color: {BG_LIGHT};
    color: {TEXT_PRIMARY};
}}

/* -- Line Edit & Date Edit ------------------------------------------- */

QLineEdit, QDateEdit {{
    background-color: {BG_LIGHT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 24px;
    selection-background-color: {ACCENT_BLUE};
}}

QLineEdit:focus, QDateEdit:focus {{
    border-color: {ACCENT_BLUE};
}}

QDateEdit::drop-down {{
    border: none;
    width: 20px;
}}

/* -- Checkbox -------------------------------------------------------- */

QCheckBox {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER_COLOR};
    border-radius: 3px;
    background-color: {BG_LIGHT};
}}

QCheckBox::indicator:checked {{
    background-color: {ACCENT_BLUE};
    border-color: {ACCENT_BLUE};
}}

QCheckBox::indicator:hover {{
    border-color: {ACCENT_BLUE};
}}

/* -- Status Bar ------------------------------------------------------ */

QStatusBar {{
    background-color: {BG_MEDIUM};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BORDER_COLOR};
    min-height: 24px;
}}

QStatusBar::item {{
    border: none;
}}

/* -- Menu Bar & Menu ------------------------------------------------- */

QMenuBar {{
    background-color: {BG_MEDIUM};
    color: {TEXT_PRIMARY};
    border-bottom: 1px solid {BORDER_COLOR};
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 6px 12px;
}}

QMenuBar::item:selected {{
    background-color: {ACCENT_BLUE};
}}

QMenu {{
    background-color: {BG_MEDIUM};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
}}

QMenu::item:selected {{
    background-color: {ACCENT_BLUE};
}}

QMenu::separator {{
    height: 1px;
    background-color: {BORDER_COLOR};
    margin: 4px 8px;
}}

/* -- Toolbar --------------------------------------------------------- */

QToolBar {{
    background-color: {BG_MEDIUM};
    border: none;
    spacing: 4px;
    padding: 2px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {BORDER_COLOR};
    margin: 4px 2px;
}}

/* -- Progress Bar ---------------------------------------------------- */

QProgressBar {{
    background-color: {BG_LIGHT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    text-align: center;
    color: {TEXT_PRIMARY};
    min-height: 18px;
}}

QProgressBar::chunk {{
    background-color: {ACCENT_BLUE};
    border-radius: 3px;
}}

/* -- Splitter -------------------------------------------------------- */

QSplitter::handle {{
    background-color: {BORDER_COLOR};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

QSplitter::handle:hover {{
    background-color: {ACCENT_BLUE};
}}

/* -- Scrollbars ------------------------------------------------------ */

QScrollBar:vertical {{
    background-color: {BG_DARK};
    width: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {BG_LIGHT};
    min-height: 30px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {TEXT_SECONDARY};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {BG_DARK};
    height: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {BG_LIGHT};
    min-width: 30px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {TEXT_SECONDARY};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* -- Tooltips -------------------------------------------------------- */

QToolTip {{
    background-color: {BG_LIGHT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    padding: 4px 8px;
    border-radius: 4px;
}}
"""
