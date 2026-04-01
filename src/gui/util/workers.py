"""Background thread helpers for the G-Trade GUI."""

from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Slot


class WorkerSignals(QObject):
    """Signals emitted by a Worker runnable."""
    finished = Signal()
    error = Signal(str)
    result = Signal(object)


class Worker(QRunnable):
    """Generic background worker for DB queries and API calls."""

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()


def run_in_background(fn, *args, on_result=None, on_error=None, **kwargs):
    """Convenience: run *fn* in the global thread pool, connect callbacks.

    Returns the Worker instance so callers can hold a reference if needed.
    """
    worker = Worker(fn, *args, **kwargs)
    if on_result:
        worker.signals.result.connect(on_result)
    if on_error:
        worker.signals.error.connect(on_error)
    QThreadPool.globalInstance().start(worker)
    return worker
