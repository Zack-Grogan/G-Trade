"""Application entry point for the G-Trade desktop GUI."""

import logging
import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

log = logging.getLogger(__name__)


def launch_gui(config, allow_live: bool = False):
    """Launch the G-Trade desktop GUI.

    Parameters
    ----------
    config : src.config.Config
        Loaded application configuration.
    allow_live : bool
        If True, enable live trading engine controls (otherwise paper-only).
    """
    app = QApplication(sys.argv)
    app.setApplicationName("G-Trade")
    app.setOrganizationName("G-Trade")

    # Apply the dark trading theme
    from src.gui.util.styles import load_dark_stylesheet
    app.setStyleSheet(load_dark_stylesheet())

    # Observability store (tape / metrics)
    from src.observability.store import get_observability_store
    store = get_observability_store()
    store.start()

    # Data layer bridges
    from src.gui.data.account_manager import AccountManager
    from src.gui.data.engine_bridge import EngineBridge

    account_mgr = AccountManager(config)

    # Try to authenticate and load accounts
    client = None
    try:
        from src.market.topstep_client import TopstepClient
        client = TopstepClient()
        log.info("Authenticating with TopstepX API...")
        if client.authenticate():
            log.info("Authentication successful")
            account_mgr.set_client(client)
            account_mgr.load_accounts()
        else:
            log.warning("Authentication failed - account switcher will be empty")
    except Exception as exc:
        log.warning("Failed to connect to TopstepX API: %s", exc)

    engine_bridge = EngineBridge(config)

    # Main window
    from src.gui.main_window import MainWindow

    window = MainWindow(
        config,
        account_mgr,
        engine_bridge,
        store,
        allow_live=allow_live,
    )
    window.show()

    sys.exit(app.exec())


def main():
    """Direct entry point for the ``es-trade-gui`` console script."""
    from src.config import get_config

    config = get_config()
    launch_gui(config)


if __name__ == "__main__":
    main()
