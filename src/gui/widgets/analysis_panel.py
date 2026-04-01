"""Trade analysis report panel.

Renders a TradeAnalysisReport as styled summary cards, zone/regime tables,
threshold sensitivity chart, hold-time distribution, hourly heatmap,
and warnings.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Optional

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.analysis.trade_analyzer import (
    TradeAnalysisReport,
    TradeStats,
    ZoneTradeStats,
    build_trade_analysis_report,
    render_trade_analysis_summary,
)
from src.gui.util.formatters import fmt_dollar, fmt_percent, fmt_pnl
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
    pnl_color,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

_CARD_STYLE = (
    f"background-color: {BG_CARD}; border-radius: 6px; "
    f"padding: 12px; border: 1px solid #2a3a5e;"
)

_TABLE_STYLE = f"""
    QTableWidget {{
        background-color: {BG_SECONDARY};
        color: {TEXT_PRIMARY};
        gridline-color: #2a3a5e;
        border: 1px solid #2a3a5e;
        border-radius: 6px;
        font-size: 11px;
        selection-background-color: #3a4a6e;
    }}
    QTableWidget::item {{
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

_WARNING_STYLE = (
    "background-color: #3e2e10; color: #ffd600; "
    "border: 1px solid #f9a825; border-radius: 6px; "
    "padding: 8px 16px; font-size: 11px;"
)


# ---------------------------------------------------------------------------
# Metric card helper
# ---------------------------------------------------------------------------


def _make_card(title: str, value: str, color: str = TEXT_PRIMARY) -> QFrame:
    """Create a small stat card (QFrame) with a title and a prominent value."""
    card = QFrame()
    card.setStyleSheet(_CARD_STYLE)
    card.setMinimumWidth(140)
    card.setMinimumHeight(72)

    v = QVBoxLayout(card)
    v.setContentsMargins(10, 8, 10, 8)
    v.setSpacing(2)

    title_label = QLabel(title)
    title_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: bold;")
    title_label.setAlignment(Qt.AlignLeft)
    v.addWidget(title_label)

    value_label = QLabel(value)
    value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
    value_label.setAlignment(Qt.AlignLeft)
    v.addWidget(value_label)

    v.addStretch()
    return card


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------


class AnalysisPanelWidget(QWidget):
    """Trade analysis report panel."""

    report_generated = Signal(object)  # emits TradeAnalysisReport

    def __init__(
        self,
        store: Any = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._store = store
        self._report: Optional[TradeAnalysisReport] = None

        self._build_ui()
        self._connect_signals()

    # ── public API ──────────────────────────────────────────────────────────

    def set_store(self, store: Any) -> None:
        self._store = store

    def load_run_ids(self) -> None:
        """Populate the run-ID dropdown from store.query_run_manifests()."""
        if self._store is None:
            return
        try:
            manifests = self._store.query_run_manifests(limit=50)
        except Exception:
            logger.exception("Failed to query run manifests")
            manifests = []

        self._run_combo.blockSignals(True)
        self._run_combo.clear()
        for m in manifests:
            run_id = m.get("run_id", "")
            label = run_id
            data_mode = m.get("data_mode", "")
            symbol = m.get("symbol", "")
            if data_mode:
                label += f" [{data_mode}]"
            if symbol:
                label += f" {symbol}"
            self._run_combo.addItem(label, userData=run_id)
        self._run_combo.blockSignals(False)

    def generate_report(self) -> None:
        """Build the analysis report for the currently selected run_id."""
        if self._store is None:
            return

        run_id = self._run_combo.currentData()
        if not run_id:
            return

        try:
            report = build_trade_analysis_report(
                run_id=run_id,
                store=self._store,
            )
        except Exception:
            logger.exception("Failed to generate report for run_id=%s", run_id)
            return

        self._report = report
        self._render_report(report)
        self.report_generated.emit(report)

    def set_report(self, report: TradeAnalysisReport) -> None:
        """Directly set and render a report (useful for testing)."""
        self._report = report
        self._render_report(report)

    def export_markdown(self) -> None:
        """Export the current report as a markdown file."""
        if self._report is None:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analysis Report",
            f"trade_analysis_{self._report.run_id}.md",
            "Markdown Files (*.md);;All Files (*)",
        )
        if not path:
            return

        md = render_trade_analysis_summary(self._report)
        try:
            with open(path, "w") as f:
                f.write(md)
        except Exception:
            logger.exception("Failed to export markdown to %s", path)

    # ── UI construction ─────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # Top bar
        top = self._build_top_bar()
        root.addWidget(top)

        # Scroll area
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet(
            f"""
            QScrollArea {{ background-color: transparent; border: none; }}
            QScrollBar:vertical {{
                background-color: {BG_SECONDARY}; width: 10px; border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: #666; min-height: 30px; border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            """
        )

        self._content = QWidget()
        self._content.setObjectName("scrollContent")
        self._content.setStyleSheet("QWidget#scrollContent { background: transparent; }")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)

        # Placeholder
        self._placeholder = QLabel("Select a run and click Generate Report")
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 14px; padding: 40px;"
        )
        self._content_layout.addWidget(self._placeholder)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll, stretch=1)

    def _build_top_bar(self) -> QFrame:
        frame = QFrame(self)
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SECONDARY};
                border: 1px solid #2a3a5e;
                border-radius: 6px;
                padding: 4px;
            }}
            QComboBox {{
                background-color: #1a1a2e; color: {TEXT_PRIMARY};
                border: 1px solid #3a4a6e; border-radius: 4px;
                padding: 4px 8px; min-height: 24px; font-size: 11px;
            }}
            QComboBox:hover {{ border-color: #4a90d9; }}
            QComboBox::drop-down {{ border: none; }}
            QLabel {{ color: {TEXT_SECONDARY}; font-size: 11px; }}
            """
        )
        h = QHBoxLayout(frame)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(8)

        h.addWidget(QLabel("Run ID:"))
        self._run_combo = QComboBox(self)
        self._run_combo.setMinimumWidth(280)
        self._run_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        h.addWidget(self._run_combo)

        self._generate_btn = QPushButton("Generate Report", self)
        self._generate_btn.setStyleSheet(
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
        h.addWidget(self._generate_btn)

        self._export_btn = QPushButton("Export Markdown", self)
        self._export_btn.setEnabled(False)
        self._export_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #2a3a5e; color: {TEXT_PRIMARY}; border: none;
                border-radius: 4px; padding: 6px 14px; font-size: 11px;
            }}
            QPushButton:hover {{ background-color: #3a4a6e; }}
            QPushButton:disabled {{ color: #4a5568; background-color: #1e1e2e; }}
            """
        )
        h.addWidget(self._export_btn)

        h.addStretch()
        return frame

    def _connect_signals(self) -> None:
        self._generate_btn.clicked.connect(self.generate_report)
        self._export_btn.clicked.connect(self.export_markdown)

    # ── rendering ───────────────────────────────────────────────────────────

    def _render_report(self, report: TradeAnalysisReport) -> None:
        """Clear the scroll content and render the full report."""
        self._clear_content()
        self._export_btn.setEnabled(True)

        lay = self._content_layout

        # Section header
        lay.addWidget(self._section_label(
            f"Analysis: {report.run_id}  |  {report.symbol}  |  "
            f"{report.generated_at.strftime('%Y-%m-%d %H:%M')}"
        ))

        # 1. Summary cards
        lay.addWidget(self._render_summary_cards(report.overall_stats))

        # 2. Zone breakdown table
        if report.zone_stats:
            lay.addWidget(self._section_label("Zone Breakdown"))
            lay.addWidget(self._render_zone_table(report.zone_stats))

        # 3. Threshold sensitivity bar chart
        if report.threshold_sensitivity:
            lay.addWidget(self._section_label("Threshold Sensitivity"))
            lay.addWidget(self._render_threshold_chart(report.threshold_sensitivity))

        # 4. Hold time distribution
        if report.hold_time_distribution:
            lay.addWidget(self._section_label("Hold Time Distribution"))
            lay.addWidget(self._render_hold_time_chart(report.hold_time_distribution))

        # 5. Hourly breakdown heatmap
        if report.hourly_breakdown:
            lay.addWidget(self._section_label("Hourly Breakdown"))
            lay.addWidget(self._render_hourly_table(report.hourly_breakdown))

        # 6. Regime breakdown
        if report.regime_stats:
            lay.addWidget(self._section_label("Regime Breakdown"))
            lay.addWidget(self._render_regime_table(report.regime_stats))

        # 7. Warnings
        if report.warnings:
            lay.addWidget(self._section_label("Warnings"))
            for w in report.warnings:
                lbl = QLabel(f"  {w}")
                lbl.setWordWrap(True)
                lbl.setStyleSheet(_WARNING_STYLE)
                lay.addWidget(lbl)

        lay.addStretch()

    def _clear_content(self) -> None:
        """Remove all widgets from the scroll content."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: bold; "
            f"padding: 6px 0 2px 0;"
        )
        return lbl

    # ── 1. Summary cards ────────────────────────────────────────────────────

    def _render_summary_cards(self, stats: TradeStats) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none;")
        grid = QGridLayout(frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        cards = [
            ("Total Trades", str(stats.trade_count), TEXT_PRIMARY),
            ("Win Rate", f"{stats.win_rate:.1%}", pnl_color(stats.win_rate - 0.5)),
            ("Total P&L", fmt_pnl(stats.total_pnl), pnl_color(stats.total_pnl)),
            ("Profit Factor", f"{stats.profit_factor:.2f}", pnl_color(stats.profit_factor - 1.0)),
            ("Avg Win", fmt_dollar(stats.avg_win, signed=False), PROFIT_GREEN),
            ("Avg Loss", fmt_dollar(stats.avg_loss, signed=False), LOSS_RED),
            ("Avg Hold", f"{stats.avg_hold_minutes:.0f} min", TEXT_PRIMARY),
            ("Max Win", fmt_dollar(stats.max_win, signed=False), PROFIT_GREEN),
            ("Max Loss", fmt_dollar(stats.max_loss, signed=False), LOSS_RED),
            ("Max Consec Wins", str(stats.max_consecutive_wins), PROFIT_GREEN),
            ("Max Consec Losses", str(stats.max_consecutive_losses), LOSS_RED),
        ]

        if stats.max_drawdown is not None:
            cards.append(("Max Drawdown", fmt_dollar(stats.max_drawdown), LOSS_RED))

        cols = 4
        for i, (title, value, color) in enumerate(cards):
            card = _make_card(title, value, color)
            grid.addWidget(card, i // cols, i % cols)

        return frame

    # ── 2. Zone table ───────────────────────────────────────────────────────

    def _render_zone_table(self, zone_stats: list[ZoneTradeStats]) -> QTableWidget:
        headers = [
            "Zone", "Trades", "Win Rate", "P&L", "Avg Hold (min)",
            "Trades/Hr", "Avg Score", "Top Strategy",
        ]
        table = QTableWidget(len(zone_stats), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setStyleSheet(_TABLE_STYLE)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        table.setMaximumHeight(min(40 + 30 * len(zone_stats), 300))

        for row, zs in enumerate(zone_stats):
            items = [
                (zs.zone, None),
                (str(zs.stats.trade_count), None),
                (f"{zs.stats.win_rate:.1%}", pnl_color(zs.stats.win_rate - 0.5)),
                (fmt_pnl(zs.stats.total_pnl), pnl_color(zs.stats.total_pnl)),
                (f"{zs.stats.avg_hold_minutes:.0f}", None),
                (f"{zs.trades_per_hour:.2f}", None),
                (f"{zs.avg_entry_score:.1f}", None),
                (zs.most_common_strategy, None),
            ]
            for col, (text, color) in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignRight | Qt.AlignVCenter
                    if col >= 1
                    else Qt.AlignLeft | Qt.AlignVCenter
                )
                if color:
                    item.setForeground(QColor(color))
                table.setItem(row, col, item)

        table.resizeColumnsToContents()
        return table

    # ── 3. Threshold sensitivity chart ──────────────────────────────────────

    def _render_threshold_chart(self, sensitivity: list) -> QWidget:
        """Bar chart: threshold on X, passing-trade P&L on Y, with win-rate labels."""
        widget = pg.PlotWidget()
        widget.setBackground(CHART_BG)
        widget.showGrid(x=False, y=True, alpha=0.15)
        widget.setLabel("left", "P&L ($)")
        widget.setLabel("bottom", "Threshold")
        widget.setFixedHeight(220)
        widget.getAxis("left").setPen(pg.mkPen(CHART_GRID))
        widget.getAxis("bottom").setPen(pg.mkPen(CHART_GRID))

        thresholds = [s.threshold for s in sensitivity]
        pnls = [s.pnl_of_passing_trades for s in sensitivity]
        win_rates = [s.win_rate_of_passing_trades for s in sensitivity]

        colors = [QColor(PROFIT_GREEN) if p >= 0 else QColor(LOSS_RED) for p in pnls]
        brushes = [pg.mkBrush(c) for c in colors]

        bar_width = 0.2 if len(thresholds) > 1 else 0.5
        bar = pg.BarGraphItem(
            x=thresholds,
            height=pnls,
            width=bar_width,
            brushes=brushes,
            pens=[pg.mkPen(c, width=1) for c in colors],
        )
        widget.addItem(bar)

        # Win rate labels above bars
        for i, (th, pnl, wr) in enumerate(zip(thresholds, pnls, win_rates)):
            text = pg.TextItem(
                text=f"{wr:.0%}",
                color=TEXT_SECONDARY,
                anchor=(0.5, 1.0 if pnl >= 0 else 0.0),
            )
            text.setFont(QFont("sans-serif", 8))
            text.setPos(th, pnl)
            widget.addItem(text)

        return widget

    # ── 4. Hold time distribution ───────────────────────────────────────────

    def _render_hold_time_chart(self, distribution: dict[str, int]) -> QWidget:
        """Horizontal bar chart of hold-time buckets."""
        widget = pg.PlotWidget()
        widget.setBackground(CHART_BG)
        widget.showGrid(x=True, y=False, alpha=0.15)
        widget.setLabel("bottom", "Trade Count")
        widget.setFixedHeight(200)
        widget.getAxis("left").setPen(pg.mkPen(CHART_GRID))
        widget.getAxis("bottom").setPen(pg.mkPen(CHART_GRID))

        buckets = list(distribution.keys())
        counts = list(distribution.values())
        n = len(buckets)

        if n == 0:
            return widget

        y_positions = list(range(n))

        # Horizontal bars
        bar = pg.BarGraphItem(
            x0=0,
            y=y_positions,
            height=0.6,
            width=counts,
            brush=pg.mkBrush("#4a90d9"),
            pen=pg.mkPen("#5da0e9", width=1),
        )
        widget.addItem(bar)

        # Bucket labels on the left axis
        y_axis = widget.getAxis("left")
        ticks = [(i, buckets[i]) for i in range(n)]
        y_axis.setTicks([ticks])
        y_axis.setStyle(tickFont=QFont("sans-serif", 9))

        # Count labels at the end of each bar
        for i, count in enumerate(counts):
            if count > 0:
                text = pg.TextItem(
                    text=str(count),
                    color=TEXT_PRIMARY,
                    anchor=(0.0, 0.5),
                )
                text.setFont(QFont("sans-serif", 9, QFont.Bold))
                text.setPos(count, i)
                widget.addItem(text)

        widget.invertY(True)
        return widget

    # ── 5. Hourly breakdown ─────────────────────────────────────────────────

    def _render_hourly_table(self, hourly: dict[int, dict[str, Any]]) -> QTableWidget:
        """Table showing trade stats by hour of day."""
        sorted_hours = sorted(hourly.keys())
        headers = ["Hour", "Trades", "Wins", "Win Rate", "P&L"]
        table = QTableWidget(len(sorted_hours), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setStyleSheet(_TABLE_STYLE)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        table.setMaximumHeight(min(40 + 30 * len(sorted_hours), 400))

        for row, hour in enumerate(sorted_hours):
            data = hourly[hour]
            trades = data.get("trades", 0)
            wins = data.get("wins", 0)
            wr = data.get("win_rate", 0.0)
            pnl = data.get("pnl", 0.0)

            # Color-code the row based on P&L intensity
            items = [
                (f"{hour:02d}:00", None),
                (str(trades), None),
                (str(wins), None),
                (f"{wr:.0%}", pnl_color(wr - 0.5)),
                (fmt_pnl(pnl), pnl_color(pnl)),
            ]
            for col, (text, color) in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignRight | Qt.AlignVCenter
                    if col >= 1
                    else Qt.AlignLeft | Qt.AlignVCenter
                )
                if color:
                    item.setForeground(QColor(color))
                # Background intensity based on trade count for heatmap effect
                if trades > 0 and col == 0:
                    max_trades = max(
                        (hourly[h].get("trades", 0) for h in sorted_hours), default=1
                    )
                    intensity = min(trades / max(max_trades, 1), 1.0)
                    bg = QColor(74, 144, 217, int(intensity * 80))
                    item.setBackground(bg)
                table.setItem(row, col, item)

        table.resizeColumnsToContents()
        return table

    # ── 6. Regime table ─────────────────────────────────────────────────────

    def _render_regime_table(self, regime_stats: dict[str, TradeStats]) -> QTableWidget:
        headers = [
            "Regime", "Trades", "Win Rate", "P&L", "Profit Factor",
            "Avg Win", "Avg Loss", "Avg Hold (min)",
        ]
        regimes = sorted(regime_stats.keys())
        table = QTableWidget(len(regimes), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setStyleSheet(_TABLE_STYLE)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.horizontalHeader().setStretchLastSection(True)
        table.setMaximumHeight(min(40 + 30 * len(regimes), 300))

        for row, regime in enumerate(regimes):
            stats = regime_stats[regime]
            items = [
                (regime, None),
                (str(stats.trade_count), None),
                (f"{stats.win_rate:.1%}", pnl_color(stats.win_rate - 0.5)),
                (fmt_pnl(stats.total_pnl), pnl_color(stats.total_pnl)),
                (f"{stats.profit_factor:.2f}", pnl_color(stats.profit_factor - 1.0)),
                (fmt_dollar(stats.avg_win, signed=False), PROFIT_GREEN),
                (fmt_dollar(stats.avg_loss, signed=False), LOSS_RED),
                (f"{stats.avg_hold_minutes:.0f}", None),
            ]
            for col, (text, color) in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignRight | Qt.AlignVCenter
                    if col >= 1
                    else Qt.AlignLeft | Qt.AlignVCenter
                )
                if color:
                    item.setForeground(QColor(color))
                table.setItem(row, col, item)

        table.resizeColumnsToContents()
        return table
