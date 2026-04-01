"""Topstep evaluation / combine rule tracker widget.

Displays progress bars for profit target, trailing drawdown, daily loss,
position limits, and trading-day counters with a rule-checklist section.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from src.gui.util.formatters import fmt_dollar, fmt_ratio
from src.gui.util.styles import (
    ACCENT_BLUE,
    PROGRESS_CAUTION,
    PROGRESS_DANGER,
    PROGRESS_SAFE,
    RULE_FAIL,
    RULE_PASS,
    TEXT_MUTED,
    TEXT_PRIMARY,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PROGRESS_RESOLUTION = 1000  # QProgressBar integer range for sub-percent precision


def _pct(current: float, target: float) -> float:
    """Return a 0-100 percentage; guards against division by zero."""
    if target == 0:
        return 100.0
    return max(0.0, min(100.0, abs(current / target) * 100.0))


def _progress_bar_style(color: str) -> str:
    return f"QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}"


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class EvaluationTrackerWidget(QWidget):
    """Topstep combine / evaluation rule tracker with progress bars and checklist."""

    def __init__(
        self,
        config: Any = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._bars: dict[str, tuple[QProgressBar, QLabel]] = {}
        self._rules: dict[str, QLabel] = {}

        self._build_ui()

        if config is not None:
            self._apply_config_defaults(config)

    # -- UI construction ---------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Title
        title = QLabel("Topstep Evaluation Tracker")
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 2)
        title.setFont(title_font)
        layout.addWidget(title)

        # Progress bars group
        progress_group = QGroupBox("Progress")
        progress_layout = QGridLayout(progress_group)
        progress_layout.setSpacing(8)
        progress_layout.setContentsMargins(8, 16, 8, 8)

        self._add_progress_row(progress_layout, 0, "profit_target", "Profit Target")
        self._add_progress_row(progress_layout, 1, "trailing_drawdown", "Trailing Drawdown Floor")
        self._add_progress_row(progress_layout, 2, "daily_loss", "Daily Loss Limit")
        self._add_progress_row(progress_layout, 3, "max_position", "Max Position")
        self._add_progress_row(progress_layout, 4, "trading_days", "Trading Days")

        layout.addWidget(progress_group)

        # Rule checklist group
        rules_group = QGroupBox("Rule Checklist")
        rules_layout = QVBoxLayout(rules_group)
        rules_layout.setSpacing(4)
        rules_layout.setContentsMargins(8, 16, 8, 8)

        self._add_rule_row(rules_layout, "no_daily_loss_breach", "Daily loss limit not breached")
        self._add_rule_row(rules_layout, "no_drawdown_breach", "Trailing drawdown not breached")
        self._add_rule_row(rules_layout, "min_trading_days", "Minimum trading days met")
        self._add_rule_row(rules_layout, "profit_target_met", "Profit target reached")
        self._add_rule_row(rules_layout, "position_limit_ok", "Position size within limits")
        self._add_rule_row(rules_layout, "no_prohibited_products", "No prohibited products traded")

        layout.addWidget(rules_group)

        # Status line
        self._status_label = QLabel("No state data yet")
        self._status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self._status_label)

        layout.addStretch()

    def _add_progress_row(
        self,
        grid: QGridLayout,
        row: int,
        key: str,
        label_text: str,
    ) -> None:
        """Create a label + progress bar + value label row in the grid."""
        label = QLabel(label_text)
        label.setMinimumWidth(150)
        grid.addWidget(label, row, 0)

        bar = QProgressBar()
        bar.setRange(0, _PROGRESS_RESOLUTION)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setMinimumHeight(20)
        grid.addWidget(bar, row, 1)

        value_label = QLabel("-- / --")
        value_label.setMinimumWidth(160)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        grid.addWidget(value_label, row, 2)

        self._bars[key] = (bar, value_label)

    def _add_rule_row(self, parent_layout: QVBoxLayout, key: str, description: str) -> None:
        """Create a rule checklist line with status icon."""
        row = QHBoxLayout()
        row.setSpacing(8)

        icon_label = QLabel("--")
        icon_label.setFixedWidth(24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = icon_label.font()
        icon_font.setPointSize(icon_font.pointSize() + 2)
        icon_font.setBold(True)
        icon_label.setFont(icon_font)
        row.addWidget(icon_label)

        desc_label = QLabel(description)
        row.addWidget(desc_label, stretch=1)

        parent_layout.addLayout(row)
        self._rules[key] = icon_label

    # -- Config defaults ---------------------------------------------------

    def _apply_config_defaults(self, config: Any) -> None:
        """Set target values from the config before any live state arrives."""
        risk = getattr(config, "risk", None)
        account = getattr(config, "account", None)

        if risk is not None:
            daily_max = getattr(risk, "max_daily_loss", 600)
            self._update_bar("daily_loss", 0.0, daily_max, is_loss_limit=True)

            if getattr(risk, "evaluation_drawdown_mirror_enabled", False):
                equity = getattr(risk, "evaluation_starting_equity", 50000)
                dd = getattr(risk, "evaluation_trailing_drawdown_dollars", 2000)
                floor = equity - dd
                self._update_bar("trailing_drawdown", equity, floor, is_loss_limit=False)

        if account is not None:
            max_contracts = getattr(account, "max_contracts", 5)
            self._update_bar("max_position", 0, max_contracts, is_loss_limit=False)

    # -- Public API --------------------------------------------------------

    def set_config(self, config: Any) -> None:
        """Update stored config and re-apply defaults."""
        self._config = config
        self._apply_config_defaults(config)

    def update_state(self, state_dict: dict[str, Any]) -> None:
        """Update all bars and rules from a TradingState.to_dict() or equivalent.

        Expected keys (all optional -- missing keys are simply skipped):
            daily_pnl, equity, account_balance, position, max_contracts,
            max_daily_loss, trailing_drawdown_floor, profit_target,
            trading_days, min_trading_days, evaluation_hwm
        """
        config = self._config
        risk = getattr(config, "risk", None) if config else None
        account = getattr(config, "account", None) if config else None

        # --- Profit target ---
        profit_target = state_dict.get("profit_target", 3000.0)
        realized_pnl = state_dict.get("daily_pnl", 0.0)
        # If there's a cumulative session P&L, prefer it
        cumulative_pnl = state_dict.get("cumulative_pnl", realized_pnl)
        self._update_bar("profit_target", cumulative_pnl, profit_target, is_loss_limit=False)
        self._set_rule("profit_target_met", cumulative_pnl >= profit_target)

        # --- Trailing drawdown ---
        equity = state_dict.get("equity") or state_dict.get("account_balance", 0.0)
        if risk and getattr(risk, "evaluation_drawdown_mirror_enabled", False):
            starting = getattr(risk, "evaluation_starting_equity", 50000)
            dd_dollars = getattr(risk, "evaluation_trailing_drawdown_dollars", 2000)
            hwm = state_dict.get("evaluation_hwm", starting)
            floor = hwm - dd_dollars
            self._update_bar("trailing_drawdown", equity, floor, is_loss_limit=False)
            self._set_rule("no_drawdown_breach", equity > floor)
        else:
            dd_floor = state_dict.get("trailing_drawdown_floor")
            if dd_floor is not None:
                self._update_bar("trailing_drawdown", equity, dd_floor, is_loss_limit=False)
                self._set_rule("no_drawdown_breach", equity > dd_floor)
            else:
                self._set_rule("no_drawdown_breach", True)

        # --- Daily loss ---
        daily_pnl = state_dict.get("daily_pnl", 0.0)
        max_daily = state_dict.get("max_daily_loss")
        if max_daily is None and risk:
            max_daily = getattr(risk, "max_daily_loss", 600)
        if max_daily:
            self._update_bar("daily_loss", daily_pnl, max_daily, is_loss_limit=True)
            self._set_rule("no_daily_loss_breach", daily_pnl > -max_daily)

        # --- Max position ---
        position = abs(state_dict.get("position", 0))
        max_contracts = state_dict.get("max_contracts")
        if max_contracts is None and account:
            max_contracts = getattr(account, "max_contracts", 5)
        if max_contracts:
            self._update_bar("max_position", position, max_contracts, is_loss_limit=False)
            self._set_rule("position_limit_ok", position <= max_contracts)

        # --- Trading days ---
        trading_days = state_dict.get("trading_days", 0)
        min_days = state_dict.get("min_trading_days", 10)
        self._update_bar("trading_days", trading_days, min_days, is_loss_limit=False)
        self._set_rule("min_trading_days", trading_days >= min_days)

        # --- Prohibited products (always pass in normal operation) ---
        self._set_rule("no_prohibited_products", state_dict.get("no_prohibited_products", True))

        self._status_label.setText("State updated")

    # -- Internal ----------------------------------------------------------

    def _update_bar(
        self,
        key: str,
        current: float,
        target: float,
        *,
        is_loss_limit: bool = False,
    ) -> None:
        """Update a named progress bar with current/target values."""
        if key not in self._bars:
            return

        bar, value_label = self._bars[key]

        if is_loss_limit:
            # For loss limits: current is a negative P&L, target is the max loss (positive).
            # Progress fills as losses approach the limit.
            used = abs(min(current, 0))
            pct = _pct(used, target)
            bar.setValue(int(pct / 100.0 * _PROGRESS_RESOLUTION))
            value_label.setText(f"{fmt_dollar(current)} / -{fmt_dollar(target, signed=False)}")

            if pct >= 80:
                color = PROGRESS_DANGER
            elif pct >= 50:
                color = PROGRESS_CAUTION
            else:
                color = PROGRESS_SAFE
        else:
            # For targets: progress fills toward the goal.
            if key == "trailing_drawdown":
                # Show equity vs floor -- "safe" means equity is well above floor.
                if target > 0:
                    # Distance from floor as fraction of a meaningful range
                    margin = current - target
                    # Use a fixed reference range: show margin as % of total range
                    range_ref = max(target * 0.1, 500)  # 10% of floor or $500
                    safe_pct = max(0.0, min(100.0, margin / range_ref * 100.0))
                    bar.setValue(int(safe_pct / 100.0 * _PROGRESS_RESOLUTION))
                    value_label.setText(
                        f"{fmt_dollar(current, signed=False)} / {fmt_dollar(target, signed=False)} floor"
                    )
                    if safe_pct <= 20:
                        color = PROGRESS_DANGER
                    elif safe_pct <= 50:
                        color = PROGRESS_CAUTION
                    else:
                        color = PROGRESS_SAFE
                else:
                    bar.setValue(0)
                    value_label.setText("--")
                    color = PROGRESS_SAFE
            elif key in ("max_position", "trading_days"):
                pct = _pct(current, target)
                bar.setValue(int(pct / 100.0 * _PROGRESS_RESOLUTION))
                value_label.setText(f"{int(current)} / {int(target)}")
                if key == "trading_days":
                    color = PROGRESS_SAFE if pct >= 100 else ACCENT_BLUE
                else:
                    color = PROGRESS_SAFE if pct < 80 else PROGRESS_CAUTION
            else:
                # Profit target
                pct = _pct(current, target) if target > 0 else 0
                bar.setValue(int(pct / 100.0 * _PROGRESS_RESOLUTION))
                value_label.setText(
                    f"{fmt_dollar(current, signed=False)} / {fmt_dollar(target, signed=False)}"
                )
                if pct >= 100:
                    color = PROGRESS_SAFE
                elif pct >= 60:
                    color = ACCENT_BLUE
                else:
                    color = PROGRESS_CAUTION

        bar.setStyleSheet(_progress_bar_style(color))

    def _set_rule(self, key: str, passed: bool) -> None:
        """Set a rule checklist item to pass or fail."""
        if key not in self._rules:
            return
        icon_label = self._rules[key]
        if passed:
            icon_label.setText("P")
            icon_label.setStyleSheet(f"color: {RULE_PASS}; font-weight: bold;")
        else:
            icon_label.setText("X")
            icon_label.setStyleSheet(f"color: {RULE_FAIL}; font-weight: bold;")
