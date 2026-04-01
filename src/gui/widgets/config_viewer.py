"""Read-only configuration tree viewer widget.

Recursively renders the Config dataclass hierarchy in a QTreeWidget
with key-parameter highlighting.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import fields as dataclass_fields, is_dataclass
from pathlib import Path
from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.gui.util.styles import ACCENT_BLUE, TEXT_MUTED, TEXT_PRIMARY

logger = logging.getLogger(__name__)

# Parameters that are highlighted in bold as they are operationally critical.
KEY_PARAMS: frozenset[str] = frozenset({
    "min_entry_score",
    "min_score_gap",
    "max_daily_loss",
    "max_position_loss",
    "max_consecutive_losses",
    "max_trades_per_hour",
    "max_daily_trades",
    "max_trades_per_zone",
    "default_contracts",
    "max_contracts",
    "stop_loss_atr",
    "full_size_score",
    "evaluation_drawdown_mirror_enabled",
    "evaluation_trailing_drawdown_dollars",
    "evaluation_starting_equity",
    "prac_only",
    "launch_gate_enabled",
    "enable_circuit_breakers",
})


def _type_label(value: Any) -> str:
    """Return a short type label for display."""
    if value is None:
        return "None"
    t = type(value).__name__
    if is_dataclass(value):
        return type(value).__name__
    return t


def _value_text(value: Any, max_len: int = 200) -> str:
    """Produce a display-friendly string for a config value."""
    if is_dataclass(value):
        return ""
    text = str(value)
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def _config_hash(config: Any) -> str:
    """Compute a short hash of the config for display."""
    try:
        import yaml

        if is_dataclass(config):
            from dataclasses import asdict

            data = asdict(config)
        else:
            data = config
        raw = yaml.dump(data, default_flow_style=True, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:12]
    except Exception:
        return "n/a"


class ConfigViewerWidget(QWidget):
    """Read-only tree display of the full Config dataclass hierarchy."""

    def __init__(self, config: Any = None, config_path: str | None = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._config = config
        self._config_path = config_path

        self._build_ui()

        if config is not None:
            self.load_config(config, config_path)

    # -- UI construction ---------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Title
        title = QLabel("Configuration")
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(title_font.pointSize() + 1)
        title.setFont(title_font)
        layout.addWidget(title)

        # Header info bar
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.setSpacing(16)

        self._path_label = QLabel("Path: --")
        self._path_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        header_layout.addWidget(self._path_label)

        self._hash_label = QLabel("Hash: --")
        self._hash_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        header_layout.addWidget(self._hash_label)

        header_layout.addStretch()
        layout.addWidget(header_frame)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setColumnCount(3)
        self._tree.setHeaderLabels(["Parameter", "Value", "Type"])
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)

        header = self._tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.resizeSection(1, 250)

        layout.addWidget(self._tree, stretch=1)

    # -- Public API --------------------------------------------------------

    def load_config(self, config: Any, config_path: str | None = None) -> None:
        """Populate the tree from a Config dataclass instance."""
        self._config = config
        self._config_path = config_path
        self._tree.clear()

        # Update header
        path_text = config_path if config_path else "in-memory"
        self._path_label.setText(f"Path: {path_text}")
        self._hash_label.setText(f"Hash: {_config_hash(config)}")

        # Recursively populate
        self._populate_tree(self._tree.invisibleRootItem(), config)

        # Expand top-level items by default
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item is not None:
                item.setExpanded(True)

    def _populate_tree(self, parent_item: QTreeWidgetItem, obj: Any, prefix: str = "") -> None:
        """Recursively add config fields as tree items."""
        if not is_dataclass(obj):
            return

        for f in dataclass_fields(obj):
            value = getattr(obj, f.name)
            type_text = _type_label(value)
            value_text = _value_text(value)

            item = QTreeWidgetItem(parent_item, [f.name, value_text, type_text])

            # Highlight key parameters
            is_key = f.name in KEY_PARAMS
            if is_key:
                bold_font = item.font(0)
                bold_font.setBold(True)
                item.setFont(0, bold_font)
                item.setFont(1, bold_font)
                item.setForeground(0, QTreeWidgetItem().foreground(0))  # default color

            # Recurse into nested dataclasses
            if is_dataclass(value):
                self._populate_tree(item, value, prefix=f"{prefix}{f.name}.")
                item.setExpanded(False)
            elif isinstance(value, dict):
                self._populate_dict(item, value, prefix=f"{prefix}{f.name}.")
            elif isinstance(value, list):
                self._populate_list(item, value, prefix=f"{prefix}{f.name}.")

    def _populate_dict(self, parent_item: QTreeWidgetItem, d: dict, prefix: str = "") -> None:
        """Add dict entries as child items."""
        for k, v in d.items():
            key_str = str(k)
            if isinstance(v, dict):
                child = QTreeWidgetItem(parent_item, [key_str, "", "dict"])
                self._populate_dict(child, v, prefix=f"{prefix}{key_str}.")
            elif is_dataclass(v):
                child = QTreeWidgetItem(parent_item, [key_str, "", _type_label(v)])
                self._populate_tree(child, v, prefix=f"{prefix}{key_str}.")
            else:
                QTreeWidgetItem(parent_item, [key_str, str(v)[:200], _type_label(v)])

    def _populate_list(self, parent_item: QTreeWidgetItem, lst: list, prefix: str = "") -> None:
        """Add list entries as indexed child items."""
        for i, v in enumerate(lst):
            idx_str = f"[{i}]"
            if is_dataclass(v):
                child = QTreeWidgetItem(parent_item, [idx_str, "", _type_label(v)])
                self._populate_tree(child, v, prefix=f"{prefix}{idx_str}.")
            elif isinstance(v, dict):
                child = QTreeWidgetItem(parent_item, [idx_str, "", "dict"])
                self._populate_dict(child, v, prefix=f"{prefix}{idx_str}.")
            else:
                QTreeWidgetItem(parent_item, [idx_str, str(v)[:200], _type_label(v)])
