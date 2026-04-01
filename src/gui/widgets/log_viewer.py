"""Runtime log viewer widget.

Displays color-coded log entries from the observability store with level
filtering, text search, auto-scroll, and paginated loading.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.gui.util.styles import LOG_LEVEL_COLORS, TEXT_MUTED, TEXT_PRIMARY, qcolor

logger = logging.getLogger(__name__)


def _format_log_line(entry: dict[str, Any]) -> str:
    """Build a single log line from a runtime-log dict.

    Format: [TIMESTAMP] [LEVEL] logger_name: message
    """
    ts = entry.get("logged_at", "")
    if isinstance(ts, datetime):
        ts = ts.strftime("%H:%M:%S.%f")[:12]
    elif isinstance(ts, str):
        # Trim to time portion
        try:
            dt = datetime.fromisoformat(ts)
            ts = dt.strftime("%H:%M:%S.%f")[:12]
        except (ValueError, TypeError):
            ts = ts[:19]

    level = str(entry.get("level", "INFO")).upper()
    logger_name = entry.get("logger_name", "")
    message = entry.get("message", "")
    exc = entry.get("exception_text", "")

    line = f"[{ts}] [{level:7s}] {logger_name}: {message}"
    if exc:
        line += f"\n    {exc}"
    return line


class LogViewerWidget(QWidget):
    """Panel showing runtime logs with filtering, search, and auto-scroll."""

    REFRESH_INTERVAL_MS = 5000
    DEFAULT_PAGE_SIZE = 200

    LEVEL_COLORS = LOG_LEVEL_COLORS

    def __init__(self, store: Any = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._store = store
        self._filters: dict[str, bool] = {
            "DEBUG": False,
            "INFO": True,
            "WARNING": True,
            "ERROR": True,
        }
        self._search_text = ""
        self._pin_to_bottom = True
        self._page_size = self.DEFAULT_PAGE_SIZE
        self._all_logs: list[dict[str, Any]] = []
        self._last_id: int | None = None

        self._build_ui()
        self._setup_timer()

    # -- UI construction ---------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Title
        title = QLabel("Runtime Logs")
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 1)
        title.setFont(title_font)
        layout.addWidget(title)

        # Filter row
        filter_row = QHBoxLayout()
        filter_row.setSpacing(12)

        for level in ("DEBUG", "INFO", "WARNING", "ERROR"):
            cb = QCheckBox(level)
            cb.setChecked(self._filters[level])
            color = self.LEVEL_COLORS.get(level, TEXT_PRIMARY)
            cb.setStyleSheet(f"QCheckBox {{ color: {color}; }}")
            cb.toggled.connect(self._make_filter_toggle(level))
            filter_row.addWidget(cb)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Search bar
        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        search_label = QLabel("Search:")
        search_row.addWidget(search_label)
        self._search_field = QLineEdit()
        self._search_field.setPlaceholderText("Filter log text...")
        self._search_field.setClearButtonEnabled(True)
        self._search_field.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self._search_field, stretch=1)
        layout.addLayout(search_row)

        # Log text area
        self._text_area = QPlainTextEdit()
        self._text_area.setReadOnly(True)
        self._text_area.setMaximumBlockCount(5000)
        mono_font = QFont("Menlo", 11)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        self._text_area.setFont(mono_font)
        layout.addWidget(self._text_area, stretch=1)

        # Bottom controls
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(8)

        self._status_label = QLabel("Waiting for data...")
        self._status_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        bottom_row.addWidget(self._status_label)

        bottom_row.addStretch()

        self._pin_checkbox = QCheckBox("Pin to bottom")
        self._pin_checkbox.setChecked(self._pin_to_bottom)
        self._pin_checkbox.toggled.connect(self._on_pin_toggled)
        bottom_row.addWidget(self._pin_checkbox)

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self._on_clear)
        bottom_row.addWidget(clear_btn)

        layout.addLayout(bottom_row)

    def _setup_timer(self) -> None:
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(self.REFRESH_INTERVAL_MS)
        self._refresh_timer.timeout.connect(self.refresh)

    # -- Callbacks ---------------------------------------------------------

    def _make_filter_toggle(self, level: str):
        """Return a slot that toggles the given level filter."""
        def _toggle(checked: bool) -> None:
            self._filters[level] = checked
            self._rerender()
        return _toggle

    def _on_search_changed(self, text: str) -> None:
        self._search_text = text.strip().lower()
        self._rerender()

    def _on_pin_toggled(self, checked: bool) -> None:
        self._pin_to_bottom = checked
        if checked:
            self._scroll_to_bottom()

    def _on_clear(self) -> None:
        self._all_logs.clear()
        self._last_id = None
        self._text_area.clear()
        self._status_label.setText("Cleared")

    # -- Public API --------------------------------------------------------

    def set_store(self, store: Any) -> None:
        """Attach or replace the observability store."""
        self._store = store
        self._all_logs.clear()
        self._last_id = None
        self.refresh()

    def refresh(self) -> None:
        """Fetch new log entries from the store and append them."""
        if self._store is None:
            return
        try:
            kwargs: dict[str, Any] = {"limit": self._page_size, "ascending": True}
            if self._last_id is not None:
                kwargs["after_id"] = self._last_id
            rows = self._store.query_runtime_logs(**kwargs)
            if rows:
                self._all_logs.extend(rows)
                # Track highest id for incremental loading
                for r in rows:
                    rid = r.get("id")
                    if rid is not None:
                        if self._last_id is None or int(rid) > self._last_id:
                            self._last_id = int(rid)
                self._rerender()
            total = len(self._all_logs)
            self._status_label.setText(f"{total} log entries")
        except Exception:
            logger.exception("LogViewerWidget.refresh failed")
            self._status_label.setText("Error loading logs")

    # -- Rendering ---------------------------------------------------------

    def _rerender(self) -> None:
        """Re-apply filters and repaint the text area."""
        self._text_area.clear()

        filtered = self._filter_logs(self._all_logs)
        cursor = self._text_area.textCursor()
        cursor.beginEditBlock()
        for entry in filtered:
            self._append_log_entry(cursor, entry)
        cursor.endEditBlock()

        if self._pin_to_bottom:
            self._scroll_to_bottom()

    def _filter_logs(self, logs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply level and search filters."""
        result: list[dict[str, Any]] = []
        for entry in logs:
            level = str(entry.get("level", "INFO")).upper()
            if not self._filters.get(level, True):
                continue
            if self._search_text:
                text = _format_log_line(entry).lower()
                if self._search_text not in text:
                    continue
            result.append(entry)
        return result

    def _append_log_entry(self, cursor: QTextCursor, entry: dict[str, Any]) -> None:
        """Append a single color-coded log line at the given cursor."""
        level = str(entry.get("level", "INFO")).upper()
        color = self.LEVEL_COLORS.get(level, TEXT_PRIMARY)
        line = _format_log_line(entry)

        fmt = QTextCharFormat()
        fmt.setForeground(qcolor(color))
        if level == "ERROR":
            fmt.setFontWeight(QFont.Weight.Bold)

        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(line + "\n", fmt)

    def _scroll_to_bottom(self) -> None:
        sb = self._text_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    # -- Visibility-driven timer management --------------------------------

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self.refresh()
        self._refresh_timer.start()

    def hideEvent(self, event) -> None:  # noqa: N802
        super().hideEvent(event)
        self._refresh_timer.stop()
