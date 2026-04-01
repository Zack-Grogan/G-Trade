"""Real-time trading dashboard widget -- 3-column grid of live trading state.

Receives ``TradingState.to_dict()`` payloads via ``update_state()`` and
refreshes every metric in-place.
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.gui.util.formatters import (
    format_currency,
    format_pnl,
    format_score,
    pnl_color,
)
from src.gui.util.styles import (
    ACCENT_BLUE,
    BG_DARK,
    BG_LIGHT,
    BG_MEDIUM,
    BORDER_COLOR,
    GRAY,
    GRAY_LIGHT,
    LOSS_RED,
    PROFIT_GREEN,
    PROGRESS_CAUTION,
    PROGRESS_DANGER,
    PROGRESS_SAFE,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_YELLOW,
)

# ---------------------------------------------------------------------------
# Inline QSS helpers (scoped to dashboard only)
# ---------------------------------------------------------------------------

_CARD_QSS = (
    f"QFrame {{ background-color: {BG_MEDIUM}; border: 1px solid {BORDER_COLOR}; "
    f"border-radius: 6px; padding: 8px; }}"
)

_LABEL_QSS = f"color: {TEXT_MUTED}; font-size: 10px; background: transparent;"
_VALUE_QSS = f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: bold; background: transparent;"


def _badge_qss(bg: str, fg: str = TEXT_PRIMARY) -> str:
    return (
        f"background-color: {bg}; color: {fg}; "
        f"border-radius: 4px; padding: 4px 10px; font-weight: bold;"
    )


def _dot_qss(color: str, size: int = 10) -> str:
    r = size // 2
    return (
        f"background-color: {color}; border-radius: {r}px; "
        f"min-width: {size}px; max-width: {size}px; "
        f"min-height: {size}px; max-height: {size}px;"
    )


def _progress_qss(chunk_color: str) -> str:
    return (
        f"QProgressBar {{ background-color: {BG_LIGHT}; border: 1px solid {BORDER_COLOR}; "
        f"border-radius: 4px; height: 14px; text-align: center; "
        f"color: {TEXT_PRIMARY}; font-size: 10px; }}"
        f"QProgressBar::chunk {{ background-color: {chunk_color}; border-radius: 3px; }}"
    )


# ---------------------------------------------------------------------------
# Status -> color maps
# ---------------------------------------------------------------------------

_ENGINE_COLORS: dict[str, str] = {
    "healthy": PROFIT_GREEN,
    "running": PROFIT_GREEN,
    "replay": WARNING_YELLOW,
    "degraded": WARNING_YELLOW,
    "stopped": GRAY,
    "error": LOSS_RED,
}

_RISK_COLORS: dict[str, str] = {
    "normal": PROFIT_GREEN,
    "reduced": WARNING_YELLOW,
    "circuit_breaker": LOSS_RED,
}


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class DashboardWidget(QWidget):
    """Three-column real-time trading dashboard.

    Call ``update_state(state_dict)`` with the output of
    ``TradingState.to_dict()`` to refresh every field.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("DashboardWidget")

        self._max_daily_trades = 10
        self._max_trades_per_hour = 6
        self._max_consecutive_losses = 3

        root = QHBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        root.addLayout(self._build_column_1(), stretch=1)
        root.addLayout(self._build_column_2(), stretch=1)
        root.addLayout(self._build_column_3(), stretch=1)

    # -- card factory ------------------------------------------------------

    def _create_metric_card(
        self,
        label: str,
        value: str = "--",
        parent: Optional[QWidget] = None,
    ) -> QFrame:
        """Small styled card: top label + bold value below."""
        card = QFrame(parent or self)
        card.setStyleSheet(_CARD_QSS)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(8, 6, 8, 6)
        vbox.setSpacing(2)

        lbl = QLabel(label)
        lbl.setStyleSheet(_LABEL_QSS)
        vbox.addWidget(lbl)

        val = QLabel(value)
        val.setObjectName("value")
        val.setStyleSheet(_VALUE_QSS)
        vbox.addWidget(val)

        return card

    @staticmethod
    def _value_label(card: QFrame) -> QLabel:
        return card.findChild(QLabel, "value")  # type: ignore[return-value]

    @staticmethod
    def _heading(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; font-weight: bold; "
            f"padding: 2px 0; background: transparent;"
        )
        return lbl

    # -- column 1: position & pnl ------------------------------------------

    def _build_column_1(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)
        col.addWidget(self._heading("POSITION & P&L"))

        # Position badge
        self._position_badge = QLabel("FLAT")
        self._position_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._position_badge.setStyleSheet(_badge_qss(GRAY))
        self._position_badge.setMinimumHeight(38)
        font = self._position_badge.font()
        font.setPointSize(16)
        font.setBold(True)
        self._position_badge.setFont(font)
        col.addWidget(self._position_badge)

        # Position P&L (large)
        self._position_pnl_card = self._create_metric_card("Position P&L", "$0.00")
        pnl_val = self._value_label(self._position_pnl_card)
        pnl_val.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 22px; font-weight: bold; background: transparent;"
        )
        col.addWidget(self._position_pnl_card)

        # Daily P&L with progress bar
        daily_frame = QFrame()
        daily_frame.setStyleSheet(_CARD_QSS)
        dvbox = QVBoxLayout(daily_frame)
        dvbox.setContentsMargins(8, 6, 8, 6)
        dvbox.setSpacing(4)

        dl = QLabel("Daily P&L")
        dl.setStyleSheet(_LABEL_QSS)
        dvbox.addWidget(dl)

        self._daily_pnl_value = QLabel("$0.00")
        self._daily_pnl_value.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 16px; font-weight: bold; background: transparent;"
        )
        dvbox.addWidget(self._daily_pnl_value)

        self._daily_pnl_bar = QProgressBar()
        self._daily_pnl_bar.setRange(0, 100)
        self._daily_pnl_bar.setValue(0)
        self._daily_pnl_bar.setTextVisible(True)
        self._daily_pnl_bar.setFormat("0% of max loss")
        self._daily_pnl_bar.setStyleSheet(_progress_qss(PROGRESS_SAFE))
        dvbox.addWidget(self._daily_pnl_bar)

        col.addWidget(daily_frame)

        # Equity curve placeholder
        self._equity_curve_frame = QFrame()
        self._equity_curve_frame.setObjectName("equity_curve_placeholder")
        self._equity_curve_frame.setStyleSheet(
            f"background-color: {BG_DARK}; border-radius: 6px; "
            f"border: 1px solid {BORDER_COLOR};"
        )
        self._equity_curve_frame.setMinimumHeight(120)
        self._equity_curve_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        ph_lbl = QLabel("Intraday Equity Curve")
        ph_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; background: transparent;")
        ph_lay = QVBoxLayout(self._equity_curve_frame)
        ph_lay.addWidget(ph_lbl)
        col.addWidget(self._equity_curve_frame)

        col.addStretch()
        return col

    # -- column 2: engine & alpha ------------------------------------------

    def _build_column_2(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)
        col.addWidget(self._heading("ENGINE & ALPHA"))

        # Engine status row
        status_row = QHBoxLayout()
        self._engine_dot = QLabel()
        self._engine_dot.setFixedSize(12, 12)
        self._engine_dot.setStyleSheet(_dot_qss(GRAY, 12))
        status_row.addWidget(self._engine_dot)
        self._engine_status_label = QLabel("STOPPED")
        self._engine_status_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 13px; font-weight: bold; background: transparent;"
        )
        status_row.addWidget(self._engine_status_label)
        status_row.addStretch()
        col.addLayout(status_row)

        # Zone
        self._zone_card = self._create_metric_card("Zone", "-- (inactive)")
        col.addWidget(self._zone_card)

        # Long / Short score gauges
        self._long_score_card, self._long_score_bar = self._build_score_gauge("Long Score")
        col.addWidget(self._long_score_card)
        self._short_score_card, self._short_score_bar = self._build_score_gauge("Short Score")
        col.addWidget(self._short_score_card)

        # Flat bias
        self._flat_bias_card = self._create_metric_card("Flat Bias", "0.0")
        col.addWidget(self._flat_bias_card)

        # Active vetoes
        self._vetoes_card = self._create_metric_card("Active Vetoes", "none")
        col.addWidget(self._vetoes_card)

        # Last signal
        self._last_signal_card = self._create_metric_card("Last Signal", "--")
        col.addWidget(self._last_signal_card)

        # Strategy
        self._strategy_card = self._create_metric_card("Strategy", "--")
        col.addWidget(self._strategy_card)

        col.addStretch()
        return col

    def _build_score_gauge(self, label: str) -> tuple[QFrame, QProgressBar]:
        card = QFrame()
        card.setStyleSheet(_CARD_QSS)
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(8, 6, 8, 6)
        vbox.setSpacing(2)

        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet(_LABEL_QSS)
        row.addWidget(lbl)
        val_lbl = QLabel("0.0")
        val_lbl.setObjectName("value")
        val_lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 12px; font-weight: bold; background: transparent;"
        )
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(val_lbl)
        vbox.addLayout(row)

        bar = QProgressBar()
        bar.setRange(0, 100)  # 0.0-10.0 mapped to 0-100
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(10)
        bar.setStyleSheet(_progress_qss(PROGRESS_SAFE))
        vbox.addWidget(bar)

        return card, bar

    # -- column 3: risk & account ------------------------------------------

    def _build_column_3(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(6)
        col.addWidget(self._heading("RISK & ACCOUNT"))

        # Risk state badge
        self._risk_badge = QLabel("NORMAL")
        self._risk_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._risk_badge.setStyleSheet(_badge_qss(PROFIT_GREEN))
        self._risk_badge.setMinimumHeight(28)
        col.addWidget(self._risk_badge)

        # Trade counters
        self._trades_today_card = self._create_metric_card("Trades Today", "0 / 10")
        col.addWidget(self._trades_today_card)

        self._trades_hour_card = self._create_metric_card("Trades / Hour", "0 / 6")
        col.addWidget(self._trades_hour_card)

        self._consec_losses_card = self._create_metric_card("Consec. Losses", "0 / 3")
        col.addWidget(self._consec_losses_card)

        # Account section
        col.addWidget(self._heading("ACCOUNT"))

        self._balance_card = self._create_metric_card("Balance", "--")
        col.addWidget(self._balance_card)

        self._equity_card = self._create_metric_card("Equity", "--")
        col.addWidget(self._equity_card)

        self._available_card = self._create_metric_card("Available", "--")
        col.addWidget(self._available_card)

        self._margin_card = self._create_metric_card("Margin Used", "--")
        col.addWidget(self._margin_card)

        # Feed freshness + broker connection
        conn_row = QHBoxLayout()
        self._feed_fresh_card = self._create_metric_card("Feed Age", "--")
        conn_row.addWidget(self._feed_fresh_card)

        broker_col = QVBoxLayout()
        broker_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._broker_dot = QLabel()
        self._broker_dot.setFixedSize(12, 12)
        self._broker_dot.setStyleSheet(_dot_qss(GRAY, 12))
        broker_col.addWidget(self._broker_dot, alignment=Qt.AlignmentFlag.AlignCenter)
        bl = QLabel("Broker")
        bl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; background: transparent;")
        broker_col.addWidget(bl, alignment=Qt.AlignmentFlag.AlignCenter)
        conn_row.addLayout(broker_col)

        col.addLayout(conn_row)
        col.addStretch()
        return col

    # ======================================================================
    # Public API
    # ======================================================================

    @property
    def equity_curve_frame(self) -> QFrame:
        """The placeholder QFrame where a pyqtgraph chart can be embedded."""
        return self._equity_curve_frame

    def set_risk_limits(
        self,
        max_daily_trades: int = 10,
        max_trades_per_hour: int = 6,
        max_consecutive_losses: int = 3,
    ) -> None:
        """Set the denominator values shown in ratio displays.

        Call once at startup with values from ``RiskConfig``.
        """
        self._max_daily_trades = max_daily_trades
        self._max_trades_per_hour = max_trades_per_hour
        self._max_consecutive_losses = max_consecutive_losses

    def update_state(self, state: dict[str, Any]) -> None:
        """Refresh every field from a ``TradingState.to_dict()`` payload."""
        self._update_position(state)
        self._update_engine(state)
        self._update_risk(state)
        self._update_account(state)
        self._update_heartbeat(state)

    # ======================================================================
    # Private updaters
    # ======================================================================

    def _update_position(self, state: dict[str, Any]) -> None:
        pos = state.get("position", {})
        contracts: int = pos.get("contracts", 0)
        pos_pnl: float = pos.get("pnl", 0.0)

        # Position badge
        if contracts > 0:
            badge_text = f"LONG {contracts}"
            badge_bg = PROFIT_GREEN
        elif contracts < 0:
            badge_text = f"SHORT {abs(contracts)}"
            badge_bg = LOSS_RED
        else:
            badge_text = "FLAT"
            badge_bg = GRAY
        self._position_badge.setText(badge_text)
        self._position_badge.setStyleSheet(_badge_qss(badge_bg))

        # Position P&L
        val = self._value_label(self._position_pnl_card)
        val.setText(format_pnl(pos_pnl))
        val.setStyleSheet(
            f"color: {pnl_color(pos_pnl)}; font-size: 22px; font-weight: bold; background: transparent;"
        )

        # Daily P&L
        acct = state.get("account", {})
        daily: float = acct.get("daily_pnl", 0.0)
        self._daily_pnl_value.setText(format_pnl(daily))
        self._daily_pnl_value.setStyleSheet(
            f"color: {pnl_color(daily)}; font-size: 16px; font-weight: bold; background: transparent;"
        )

        # Progress bar toward max loss
        risk = state.get("risk", {})
        max_loss: float = risk.get("max_daily_loss", 600)
        pct = min(int(abs(daily) / max_loss * 100), 100) if max_loss > 0 else 0
        self._daily_pnl_bar.setValue(pct)
        self._daily_pnl_bar.setFormat(f"{pct}% of ${max_loss:,.0f} limit")

        if pct >= 80:
            chunk = PROGRESS_DANGER
        elif pct >= 50:
            chunk = PROGRESS_CAUTION
        else:
            chunk = PROGRESS_SAFE
        self._daily_pnl_bar.setStyleSheet(_progress_qss(chunk))

    def _update_engine(self, state: dict[str, Any]) -> None:
        status = str(state.get("status", "stopped")).lower()
        color = _ENGINE_COLORS.get(status, GRAY)
        self._engine_dot.setStyleSheet(_dot_qss(color, 12))
        self._engine_status_label.setText(status.upper())
        self._engine_status_label.setStyleSheet(
            f"color: {color}; font-size: 13px; font-weight: bold; background: transparent;"
        )

        # Zone
        zone = state.get("zone", {})
        zone_name = zone.get("name") or "--"
        zone_state = zone.get("state", "inactive")
        self._value_label(self._zone_card).setText(f"{zone_name} ({zone_state})")

        # Alpha
        alpha = state.get("alpha", {})
        long_s: float = alpha.get("long_score", 0.0) or 0.0
        short_s: float = alpha.get("short_score", 0.0) or 0.0
        flat_b: float = alpha.get("flat_bias", 0.0) or 0.0

        self._value_label(self._long_score_card).setText(format_score(long_s))
        self._long_score_bar.setValue(min(int(long_s * 10), 100))

        self._value_label(self._short_score_card).setText(format_score(short_s))
        self._short_score_bar.setValue(min(int(short_s * 10), 100))

        self._value_label(self._flat_bias_card).setText(format_score(flat_b))

        # Vetoes
        vetoes = alpha.get("active_vetoes", [])
        self._value_label(self._vetoes_card).setText(
            ", ".join(str(v) for v in vetoes) if vetoes else "none"
        )

        # Last signal
        sig = state.get("last_signal")
        if sig and isinstance(sig, dict):
            sig_dir = sig.get("direction", "?")
            sig_score = sig.get("score", "?")
            self._value_label(self._last_signal_card).setText(f"{sig_dir} @ {sig_score}")
        else:
            self._value_label(self._last_signal_card).setText("--")

        # Strategy
        strat = state.get("strategy") or "--"
        self._value_label(self._strategy_card).setText(str(strat))

    def _update_risk(self, state: dict[str, Any]) -> None:
        risk = state.get("risk", {})
        risk_st = str(risk.get("state", "normal")).lower()
        r_color = _RISK_COLORS.get(risk_st, PROFIT_GREEN)
        self._risk_badge.setText(risk_st.replace("_", " ").upper())
        self._risk_badge.setStyleSheet(_badge_qss(r_color))

        trades_today: int = risk.get("trades_today", 0)
        trades_hour: int = risk.get("trades_this_hour", 0)
        consec: int = risk.get("consecutive_losses", 0)

        self._value_label(self._trades_today_card).setText(
            f"{trades_today} / {self._max_daily_trades}"
        )
        self._value_label(self._trades_hour_card).setText(
            f"{trades_hour} / {self._max_trades_per_hour}"
        )
        self._value_label(self._consec_losses_card).setText(
            f"{consec} / {self._max_consecutive_losses}"
        )

    def _update_account(self, state: dict[str, Any]) -> None:
        acct = state.get("account", {})

        def _dollar(key: str) -> str:
            v = acct.get(key)
            if v is None:
                return "--"
            return f"${v:,.2f}"

        self._value_label(self._balance_card).setText(_dollar("balance"))
        self._value_label(self._equity_card).setText(_dollar("equity"))
        self._value_label(self._available_card).setText(_dollar("available"))
        self._value_label(self._margin_card).setText(_dollar("margin_used"))

    def _update_heartbeat(self, state: dict[str, Any]) -> None:
        hb = state.get("heartbeat", {})

        # Feed freshness
        feed_stale: bool = hb.get("feed_stale", False)
        age = hb.get("last_tick_age_seconds")
        if age is not None:
            s = int(age)
            if s < 60:
                age_text = f"{s}s"
            else:
                age_text = f"{s // 60}m{s % 60:02d}s"
        else:
            age_text = "--"
        if feed_stale:
            age_text += " (STALE)"
        self._value_label(self._feed_fresh_card).setText(age_text)

        # Broker connection dot
        connected: bool = hb.get("market_stream_connected", False)
        self._broker_dot.setStyleSheet(_dot_qss(PROFIT_GREEN if connected else LOSS_RED, 12))
