"""Compatibility wrapper for the local Flask operator console."""

from .flask_console import (
    DebugServer,
    TradingState,
    get_server,
    get_state,
    record_error,
    set_state,
    create_app,
)

__all__ = [
    "DebugServer",
    "TradingState",
    "create_app",
    "get_server",
    "get_state",
    "record_error",
    "set_state",
]
