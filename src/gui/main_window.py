"""Main application window for G-Trade."""

import logging
from datetime import datetime
from typing import Any, Optional

from PySide6.QtCore import Qt, QSettings, QTimer, Slot
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QLabel,
    QStatusBar,
    QMenuBar,
    QMenu,
    QComboBox,
    QSystemTrayIcon,
    QSplitter,
    QMessageBox,
)

from src.gui.util.styles import (
    PROFIT_GREEN,
    LOSS_RED,
    TEXT_SECONDARY,
    ACCENT_BLUE,
    BG_MEDIUM,
    BG_LIGHT,
)
from src.gui.util.formatters import format_pnl, format_price
from src.gui.util.icons import create_status_dot, status_color_for_engine, status_color_for_risk

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Page definitions
# ---------------------------------------------------------------------------

_PAGES = [
    ("Dashboard", "src.gui.widgets.dashboard", "DashboardWidget"),
    ("Chart", "src.gui.widgets.candle_chart", "CandleChartWidget"),
    ("Trades", "src.gui.widgets.trade_history", "TradeHistoryWidget"),
    ("Analysis", "src.gui.widgets.analysis_panel", "AnalysisPanelWidget"),
    ("Orders", "src.gui.widgets.order_book", "OrderBookWidget"),
    ("Logs", "src.gui.widgets.log_viewer", "LogViewerWidget"),
    ("Config", "src.gui.widgets.config_viewer", "ConfigViewerWidget"),
    ("Evaluation", "src.gui.widgets.evaluation_tracker", "EvaluationTrackerWidget"),
]


def _placeholder(name: str) -> QWidget:
    """Return a placeholder widget when a page module cannot be loaded."""
    w = QWidget()
    layout = QVBoxLayout(w)
    lbl = QLabel(f"{name}\n\n(Widget not yet implemented)")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 18px;")
    layout.addWidget(lbl)
    return w


# ---------------------------------------------------------------------------
# MainWindow
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    """Top-level window with sidebar navigation and status bar."""

    SETTINGS_GROUP = "MainWindow"

    def __init__(
        self,
        config,
        account_mgr,
        engine_bridge,
        store,
        allow_live: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.config = config
        self.account_mgr = account_mgr
        self.engine_bridge = engine_bridge
        self.store = store
        self.allow_live = allow_live

        self.setWindowTitle("G-Trade")
        self.setMinimumSize(1200, 750)

        self._settings = QSettings("G-Trade", "G-Trade")

        # -- Build UI --
        self._build_menubar()
        self._build_central()
        self._build_statusbar()
        self._build_tray_icon()
        self._register_shortcuts()

        # -- Signals from data bridges --
        self._connect_signals()

        # -- Restore previous state --
        self._restore_state()

        # -- Load trade history on startup --
        self._initial_trade_load()

    # ------------------------------------------------------------------ #
    # Menu bar
    # ------------------------------------------------------------------ #

    def _build_menubar(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("&File")
        export_act = QAction("&Export...", self)
        export_act.setShortcut(QKeySequence("Ctrl+E"))
        export_act.triggered.connect(self._on_export)
        file_menu.addAction(export_act)
        file_menu.addSeparator()
        quit_act = QAction("&Quit", self)
        quit_act.setShortcut(QKeySequence("Ctrl+Q"))
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        # View
        view_menu = menubar.addMenu("&View")
        refresh_act = QAction("&Refresh", self)
        refresh_act.setShortcut(QKeySequence("Ctrl+R"))
        refresh_act.triggered.connect(self._on_refresh)
        view_menu.addAction(refresh_act)
        force_refresh_act = QAction("Force Refresh &All", self)
        force_refresh_act.setShortcut(QKeySequence("F5"))
        force_refresh_act.triggered.connect(self._on_force_refresh)
        view_menu.addAction(force_refresh_act)

        # Engine
        engine_menu = menubar.addMenu("&Engine")
        start_act = QAction("&Start", self)
        start_act.triggered.connect(self._on_engine_start)
        engine_menu.addAction(start_act)
        stop_act = QAction("S&top", self)
        stop_act.triggered.connect(self._on_engine_stop)
        engine_menu.addAction(stop_act)
        restart_act = QAction("&Restart", self)
        restart_act.triggered.connect(self._on_engine_restart)
        engine_menu.addAction(restart_act)

        if not self.allow_live:
            start_act.setEnabled(False)
            stop_act.setEnabled(False)
            restart_act.setEnabled(False)

        # Help
        help_menu = menubar.addMenu("&Help")
        about_act = QAction("&About", self)
        about_act.triggered.connect(self._on_about)
        help_menu.addAction(about_act)

    # ------------------------------------------------------------------ #
    # Central widget: sidebar + stacked pages
    # ------------------------------------------------------------------ #

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -- Sidebar --
        sidebar = QWidget()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(f"background-color: {BG_MEDIUM};")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 4, 0, 4)
        sidebar_layout.setSpacing(0)

        # Account switcher at top of sidebar
        self._account_combo = QComboBox()
        self._account_combo.setToolTip("Switch account")
        self._account_combo.currentIndexChanged.connect(self._on_account_changed)
        sidebar_layout.addWidget(self._account_combo)

        # Nav list
        self._nav_list = QListWidget()
        self._nav_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {BG_MEDIUM};
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px 16px;
                border-left: 3px solid transparent;
            }}
            QListWidget::item:selected {{
                background-color: {BG_LIGHT};
                border-left: 3px solid {ACCENT_BLUE};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {BG_LIGHT};
            }}
        """)
        for label, _, _ in _PAGES:
            item = QListWidgetItem(label)
            self._nav_list.addItem(item)
        self._nav_list.currentRowChanged.connect(self._on_page_changed)
        sidebar_layout.addWidget(self._nav_list)

        # -- Stacked pages --
        self._stack = QStackedWidget()
        self._page_widgets: list[QWidget] = []

        for label, module_path, class_name in _PAGES:
            widget = self._load_page_widget(label, module_path, class_name)
            self._page_widgets.append(widget)
            self._stack.addWidget(widget)

        # Splitter for sidebar + content
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar)
        splitter.addWidget(self._stack)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setHandleWidth(1)

        main_layout.addWidget(splitter)

        # Populate account combo
        self._refresh_account_list()

    def _load_page_widget(self, label: str, module_path: str, class_name: str) -> QWidget:
        """Lazy-import a page widget; return placeholder on failure."""
        try:
            import importlib
            import inspect

            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)

            # Build kwargs based on what the constructor actually accepts.
            sig = inspect.signature(cls.__init__)
            params = set(sig.parameters.keys()) - {"self"}
            kwargs: dict = {}
            if "config" in params:
                kwargs["config"] = self.config
            if "account_mgr" in params:
                kwargs["account_mgr"] = self.account_mgr
            if "engine_bridge" in params:
                kwargs["engine_bridge"] = self.engine_bridge
            if "store" in params:
                kwargs["store"] = self.store
            if "parent" in params:
                kwargs["parent"] = None

            return cls(**kwargs)
        except Exception as exc:
            log.warning("Could not load page %s: %s", label, exc, exc_info=True)
            return _placeholder(label)

    # ------------------------------------------------------------------ #
    # Status bar
    # ------------------------------------------------------------------ #

    def _build_statusbar(self):
        sb = self.statusBar()

        self._sb_account = QLabel("Account: --")
        self._sb_engine = QLabel("Engine: --")
        self._sb_position = QLabel("Pos: flat")
        self._sb_pnl = QLabel("P&L: $0.00")
        self._sb_risk = QLabel("Risk: --")
        self._sb_zone = QLabel("Zone: --")
        self._sb_price = QLabel("Price: --")
        self._sb_feed = QLabel("Feed: --")

        for w in (
            self._sb_account,
            self._sb_engine,
            self._sb_position,
            self._sb_pnl,
            self._sb_risk,
            self._sb_zone,
            self._sb_price,
            self._sb_feed,
        ):
            w.setStyleSheet("padding: 0 8px;")
            sb.addPermanentWidget(w)

    # ------------------------------------------------------------------ #
    # System tray
    # ------------------------------------------------------------------ #

    def _build_tray_icon(self):
        self._tray: Optional[QSystemTrayIcon] = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray = QSystemTrayIcon(self)
            self._tray.setToolTip("G-Trade")
            # Use a small green dot as default icon
            icon_pix = create_status_dot(PROFIT_GREEN, 32)
            self._tray.setIcon(QIcon(icon_pix))
            self._tray.activated.connect(self._on_tray_activated)
            self._tray.show()

    # ------------------------------------------------------------------ #
    # Keyboard shortcuts
    # ------------------------------------------------------------------ #

    def _register_shortcuts(self):
        for idx in range(min(len(_PAGES), 8)):
            act = QAction(self)
            act.setShortcut(QKeySequence(f"Ctrl+{idx + 1}"))
            page_idx = idx
            act.triggered.connect(lambda checked=False, i=page_idx: self._switch_page(i))
            self.addAction(act)

    # ------------------------------------------------------------------ #
    # Signal wiring
    # ------------------------------------------------------------------ #

    def _connect_signals(self):
        """Connect data bridge signals to status bar and widget updates."""
        eb = self.engine_bridge

        # Engine status signal -> status bar + tray
        if hasattr(eb, "engine_status_changed"):
            eb.engine_status_changed.connect(self._update_engine_status)

        # State updates -> status bar + dashboard widget
        if hasattr(eb, "state_updated"):
            eb.state_updated.connect(self._on_state_updated)

        # Health updates (for feed freshness, etc.)
        if hasattr(eb, "health_updated"):
            eb.health_updated.connect(self._on_health_updated)

        # Trade completed -> tray notification
        if hasattr(eb, "trade_completed"):
            eb.trade_completed.connect(self._on_trade_completed)

        # Account signals
        if hasattr(self.account_mgr, "account_changed"):
            self.account_mgr.account_changed.connect(self._update_account_label)
        if hasattr(self.account_mgr, "accounts_loaded"):
            self.account_mgr.accounts_loaded.connect(lambda _: self._refresh_account_list())

    # ------------------------------------------------------------------ #
    # Slots -- navigation
    # ------------------------------------------------------------------ #

    @Slot(int)
    def _on_page_changed(self, index: int):
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)

    def _switch_page(self, index: int):
        self._nav_list.setCurrentRow(index)

    @Slot(int)
    def _on_account_changed(self, index: int):
        account_id = self._account_combo.currentData()
        if account_id is not None and hasattr(self.account_mgr, "switch_account"):
            self.account_mgr.switch_account(account_id)

    # ------------------------------------------------------------------ #
    # Slots -- state & health updates from engine bridge
    # ------------------------------------------------------------------ #

    @Slot(dict)
    def _on_state_updated(self, state_dict: dict):
        """Handle TradingState.to_dict() from the engine bridge.

        Updates the status bar AND forwards to the dashboard widget.
        """
        # Status bar updates
        status = state_dict.get("status") or state_dict.get("process_status", {}).get("status")
        if status:
            self._update_engine_status(status)

        # Position
        pos = state_dict.get("position")
        if isinstance(pos, dict):
            qty = pos.get("quantity", 0)
            side = pos.get("side", "flat")
            text = f"Pos: {qty} {side}" if qty else "Pos: flat"
        elif pos is not None:
            text = f"Pos: {pos}"
        else:
            text = "Pos: flat"
        self._sb_position.setText(text)

        # P&L from risk section
        risk = state_dict.get("risk", {})
        daily_pnl = risk.get("daily_pnl")
        if daily_pnl is not None:
            self._update_pnl(float(daily_pnl))

        # Risk state
        risk_state = risk.get("risk_state") or risk.get("state")
        if risk_state:
            self._update_risk(str(risk_state))

        # Last price
        last_price = state_dict.get("last_price")
        if last_price is not None:
            self._update_price(float(last_price))

        # Zone
        zone_info = state_dict.get("zone", {})
        if isinstance(zone_info, dict):
            zone_name = zone_info.get("current_zone") or zone_info.get("name")
            if zone_name:
                self._sb_zone.setText(f"Zone: {zone_name}")
        elif zone_info:
            self._sb_zone.setText(f"Zone: {zone_info}")

        # Forward full state to dashboard widget
        dashboard = self._page_widgets[0] if self._page_widgets else None
        if dashboard and hasattr(dashboard, "update_state"):
            try:
                dashboard.update_state(state_dict)
            except Exception:
                pass

    @Slot(dict)
    def _on_health_updated(self, health_dict: dict):
        """Handle to_health_dict() updates - feed freshness, etc."""
        # Feed freshness is not directly in health dict but we can check
        # market_stream_connected
        connected = health_dict.get("market_stream_connected")
        if connected is not None:
            if connected:
                self._sb_feed.setText("Feed: OK")
                self._sb_feed.setStyleSheet(f"color: {PROFIT_GREEN}; padding: 0 8px;")
            else:
                self._sb_feed.setText("Feed: DOWN")
                self._sb_feed.setStyleSheet(f"color: {LOSS_RED}; padding: 0 8px;")

    @Slot(dict)
    def _on_trade_completed(self, trade_info: dict):
        """Notify via system tray on trade completion."""
        if self._tray:
            pnl = trade_info.get("daily_pnl", 0)
            trades = trade_info.get("trades_today", 0)
            self._tray.showMessage(
                "G-Trade: Trade Completed",
                f"Trades today: {trades} | Daily P&L: {format_pnl(pnl)}",
                QSystemTrayIcon.Information,
                3000,
            )

    # ------------------------------------------------------------------ #
    # Slots -- status bar updates
    # ------------------------------------------------------------------ #

    @Slot(str)
    def _update_engine_status(self, status: str):
        color = status_color_for_engine(status)
        self._sb_engine.setText(f"Engine: {status}")
        self._sb_engine.setStyleSheet(f"color: {color}; padding: 0 8px;")
        if self._tray:
            self._tray.setIcon(QIcon(create_status_dot(color, 32)))

    @Slot(float)
    def _update_pnl(self, value: float):
        text = f"P&L: {format_pnl(value)}"
        color = PROFIT_GREEN if value >= 0 else LOSS_RED
        self._sb_pnl.setText(text)
        self._sb_pnl.setStyleSheet(f"color: {color}; padding: 0 8px;")

    @Slot(str)
    def _update_risk(self, state: str):
        color = status_color_for_risk(state)
        self._sb_risk.setText(f"Risk: {state}")
        self._sb_risk.setStyleSheet(f"color: {color}; padding: 0 8px;")
        if self._tray and state == "circuit_breaker":
            self._tray.showMessage("G-Trade Risk Alert", f"Risk state: {state}", QSystemTrayIcon.Warning, 5000)

    @Slot(float)
    def _update_price(self, price: float):
        self._sb_price.setText(f"Price: {format_price(price)}")

    @Slot(str)
    def _update_account_label(self, account_id: str):
        # Find account name from the loaded accounts
        for acct in self.account_mgr.accounts:
            if str(acct.account_id) == str(account_id):
                self._sb_account.setText(f"Account: {acct.name}")
                return
        self._sb_account.setText(f"Account: {account_id}")

    # ------------------------------------------------------------------ #
    # Trade history initial load
    # ------------------------------------------------------------------ #

    def _initial_trade_load(self):
        """Load trade history data into the Trades widget on startup."""
        trades_widget = self._page_widgets[2] if len(self._page_widgets) > 2 else None
        if trades_widget and hasattr(trades_widget, "load_trades"):
            try:
                trades_widget.load_trades(self.store)
            except Exception as exc:
                log.warning("Initial trade load failed: %s", exc)

    # ------------------------------------------------------------------ #
    # Menu action handlers
    # ------------------------------------------------------------------ #

    @Slot()
    def _on_export(self):
        log.info("Export triggered")

    @Slot()
    def _on_refresh(self):
        """Refresh the active page."""
        current = self._stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()

    @Slot()
    def _on_force_refresh(self):
        """Force refresh all pages."""
        for widget in self._page_widgets:
            if hasattr(widget, "refresh"):
                try:
                    widget.refresh()
                except Exception as exc:
                    log.warning("Refresh failed for %s: %s", type(widget).__name__, exc)

    @Slot()
    def _on_engine_start(self):
        if hasattr(self.engine_bridge, "start_engine"):
            self.engine_bridge.start_engine()

    @Slot()
    def _on_engine_stop(self):
        if hasattr(self.engine_bridge, "stop_engine"):
            self.engine_bridge.stop_engine()

    @Slot()
    def _on_engine_restart(self):
        if hasattr(self.engine_bridge, "stop_engine"):
            self.engine_bridge.stop_engine("restart requested")
            # Re-start after a short delay to let shutdown complete
            QTimer.singleShot(2000, self._on_engine_start)

    @Slot()
    def _on_about(self):
        QMessageBox.about(
            self,
            "About G-Trade",
            "G-Trade Desktop\n\nAutomated ES futures trading system.\n\nBuilt with PySide6.",
        )

    @Slot(QSystemTrayIcon.ActivationReason)
    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isMinimized():
                self.showNormal()
            self.raise_()
            self.activateWindow()

    # ------------------------------------------------------------------ #
    # Account list
    # ------------------------------------------------------------------ #

    def _refresh_account_list(self):
        self._account_combo.blockSignals(True)
        self._account_combo.clear()
        accounts = self.account_mgr.accounts
        if accounts:
            for acct in accounts:
                label = f"{acct.name} ({acct.account_id})"
                self._account_combo.addItem(label, str(acct.account_id))
        else:
            self._account_combo.addItem("(no accounts)")
        self._account_combo.blockSignals(False)

    # ------------------------------------------------------------------ #
    # State persistence
    # ------------------------------------------------------------------ #

    def _save_state(self):
        self._settings.beginGroup(self.SETTINGS_GROUP)
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("windowState", self.saveState())
        self._settings.setValue("activePage", self._nav_list.currentRow())
        self._settings.setValue("lastAccount", self._account_combo.currentIndex())
        self._settings.endGroup()

    def _restore_state(self):
        self._settings.beginGroup(self.SETTINGS_GROUP)
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self._settings.value("windowState")
        if state:
            self.restoreState(state)
        page = self._settings.value("activePage", 0, type=int)
        self._nav_list.setCurrentRow(page)
        acct_idx = self._settings.value("lastAccount", 0, type=int)
        if 0 <= acct_idx < self._account_combo.count():
            self._account_combo.setCurrentIndex(acct_idx)
        self._settings.endGroup()

    # ------------------------------------------------------------------ #
    # Close event
    # ------------------------------------------------------------------ #

    def closeEvent(self, event):
        # Stop engine if running
        if hasattr(self.engine_bridge, "is_running") and self.engine_bridge.is_running:
            if hasattr(self.engine_bridge, "stop_engine"):
                try:
                    self.engine_bridge.stop_engine("GUI closing")
                except Exception as exc:
                    log.warning("Engine stop on close failed: %s", exc)

        self._save_state()

        if self._tray:
            self._tray.hide()

        event.accept()
