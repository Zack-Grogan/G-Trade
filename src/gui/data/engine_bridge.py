"""Bridge between the TradingEngine and the PySide6 event loop.

The engine runs in a dedicated :class:`QThread` while a 1-second
:class:`QTimer` polls :func:`src.runtime.state.get_state` and emits
Qt signals that GUI widgets can connect to.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from PySide6.QtCore import QObject, QThread, QTimer, Signal

from src.config import Config, get_config, set_config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# EngineThread -- runs the full start-up sequence in a background QThread
# ---------------------------------------------------------------------------


class EngineThread(QThread):
    """Runs TradingEngine in a background thread.

    The thread mirrors the initialisation sequence of ``src.cli.commands.start``
    so that every singleton (observability store, broker client, executor,
    scheduler, risk manager, trading engine) is created with
    ``force_recreate=True`` and then wired together before calling
    ``engine.start()``.

    ``engine.start()`` authenticates, selects the account, opens the market
    stream, and spawns the engine's internal ``_run`` reconciliation loop as
    a daemon thread.  After ``start()`` returns, the engine is live.
    This thread then blocks on a ``threading.Event`` until a stop is
    requested, at which point it calls ``engine.stop()`` and exits.
    """

    state_updated = Signal(dict)
    health_updated = Signal(dict)
    trade_completed = Signal(dict)
    engine_error = Signal(str)
    engine_stopped = Signal()

    def __init__(self, config: Config) -> None:
        super().__init__()
        self._config = config
        self._engine = None  # type: ignore[assignment]
        self._observability = None  # type: ignore[assignment]
        self._stop_requested = False

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------

    def run(self) -> None:  # noqa: C901 -- sequential start-up is inherently long
        """Main engine thread.  Mirrors cli ``start()`` initialisation."""
        import threading

        from src.engine import get_risk_manager, get_scheduler, get_trading_engine
        from src.execution import get_executor
        from src.market import get_client
        from src.observability import get_observability_store
        from src.runtime import get_state, set_state

        try:
            # Ensure the global config is the one the GUI loaded.
            set_config(self._config)

            # 1. Observability store -----------------------------------------
            observability = get_observability_store(force_recreate=True)
            observability.start()
            self._observability = observability

            # 2. Broker client -----------------------------------------------
            get_client(force_recreate=True)

            # 3. Executor ----------------------------------------------------
            get_executor(force_recreate=True)

            # 4. Zone scheduler ----------------------------------------------
            get_scheduler(force_recreate=True)

            # 5. Risk manager ------------------------------------------------
            get_risk_manager(force_recreate=True)

            # 6. Trading engine ----------------------------------------------
            engine = get_trading_engine(force_recreate=True)
            self._engine = engine

            # 7. Set global runtime state ------------------------------------
            set_state(
                running=True,
                status="running",
                start_time=time.time(),
                tenant_id=getattr(self._config, "tenant_id", None),
                data_mode="live",
                replay_summary=None,
            )

            # 8. Start the engine (authenticates, opens stream, spawns _run) -
            engine.start()

            # 9. Block until stop is requested --------------------------------
            #    engine.start() is non-blocking (it spawns a daemon thread
            #    internally).  We keep *this* QThread alive by polling so
            #    that Qt considers the thread running.
            while not self._stop_requested:
                # Check engine health and liveness
                if not engine._running:
                    # Engine stopped on its own (e.g. stream failure).
                    break
                self.msleep(500)

        except Exception as exc:
            logger.exception("EngineThread: start-up failed")
            self.engine_error.emit(str(exc))
            try:
                set_state(running=False, status="error")
            except Exception:
                pass
        finally:
            # Ensure a clean shutdown if the engine was started.
            try:
                if self._engine is not None and self._engine._running:
                    self._engine.stop()
            except Exception:
                logger.exception("EngineThread: error during engine.stop()")
            try:
                set_state(running=False, status="stopped")
            except Exception:
                pass
            try:
                if self._observability is not None:
                    self._observability.force_flush()
                    self._observability.stop()
            except Exception:
                pass
            self.engine_stopped.emit()

    # ------------------------------------------------------------------
    # Shutdown request
    # ------------------------------------------------------------------

    def request_stop(self, reason: str = "GUI shutdown") -> None:
        """Request a graceful engine shutdown from any thread."""
        logger.info("EngineThread: stop requested -- %s", reason)
        self._stop_requested = True
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                logger.exception("EngineThread: error requesting engine stop")


# ---------------------------------------------------------------------------
# EngineBridge -- manages EngineThread lifecycle + state polling for the GUI
# ---------------------------------------------------------------------------


class EngineBridge(QObject):
    """High-level facade for GUI panels.

    *  ``start_engine()`` / ``stop_engine()`` control the
       :class:`EngineThread`.
    *  A 1-second :class:`QTimer` reads the in-process
       :class:`~src.runtime.state.TradingState` and re-emits it as Qt
       signals so that widgets can update without touching engine internals.
    """

    state_updated = Signal(dict)
    health_updated = Signal(dict)
    trade_completed = Signal(dict)
    engine_status_changed = Signal(str)  # "running" | "stopped" | "error"

    def __init__(self, config: Optional[Config] = None) -> None:
        super().__init__()
        self._config: Config = config or get_config()
        self._thread: Optional[EngineThread] = None
        self._poll_timer = QTimer()
        self._poll_timer.setInterval(1000)
        self._poll_timer.timeout.connect(self._poll_state)
        self._status: str = "stopped"
        self._last_trades_today: int = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def status(self) -> str:
        """Current engine status string."""
        return self._status

    @property
    def is_running(self) -> bool:
        return self._status == "running"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start_engine(self) -> None:
        """Create an :class:`EngineThread`, wire signals, and start it."""
        if self._thread is not None and self._thread.isRunning():
            logger.warning("EngineBridge.start_engine called while engine is already running")
            return

        self._thread = EngineThread(self._config)

        # Forward thread signals
        self._thread.state_updated.connect(self.state_updated)
        self._thread.health_updated.connect(self.health_updated)
        self._thread.trade_completed.connect(self.trade_completed)
        self._thread.engine_error.connect(self._on_engine_error)
        self._thread.engine_stopped.connect(self._on_engine_stopped)

        self._thread.start()
        self._poll_timer.start()
        self._set_status("running")

    def stop_engine(self, reason: str = "GUI shutdown") -> None:
        """Request a graceful engine shutdown."""
        if self._thread is not None and self._thread.isRunning():
            self._thread.request_stop(reason)
            # Do not stop poll timer here -- _on_engine_stopped handles it.

    def wait_for_stop(self, timeout_ms: int = 10000) -> bool:
        """Block the calling thread until the engine thread exits.

        Returns ``True`` if the thread finished within *timeout_ms*,
        ``False`` on timeout.
        """
        if self._thread is None:
            return True
        return self._thread.wait(timeout_ms)

    # ------------------------------------------------------------------
    # State polling
    # ------------------------------------------------------------------

    def _poll_state(self) -> None:
        """Read TradingState from the in-process singleton and emit."""
        try:
            from src.runtime.state import get_state

            state = get_state()
            state_dict = state.to_dict()
            self.state_updated.emit(state_dict)

            health_dict = state.to_health_dict()
            self.health_updated.emit(health_dict)

            # Detect new completed trades by comparing trades_today counter.
            trades_today = state.trades_today
            if trades_today > self._last_trades_today:
                self._last_trades_today = trades_today
                # Emit a lightweight notification; panels that need the full
                # trade record should query the ObservabilityStore.
                self.trade_completed.emit({
                    "trades_today": trades_today,
                    "daily_pnl": state.daily_pnl,
                    "position": state.position,
                })

        except Exception:
            # Swallow -- polling must never crash the GUI main thread.
            pass

    # ------------------------------------------------------------------
    # Internal signal handlers
    # ------------------------------------------------------------------

    def _on_engine_error(self, msg: str) -> None:
        logger.error("EngineBridge received engine error: %s", msg)
        self._set_status("error")

    def _on_engine_stopped(self) -> None:
        self._poll_timer.stop()
        self._set_status("stopped")
        logger.info("EngineBridge: engine stopped")

    def _set_status(self, status: str) -> None:
        if self._status != status:
            self._status = status
            self.engine_status_changed.emit(status)
