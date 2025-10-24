from PyQt6.QtCore import QObject, pyqtSignal

class WorkerSignals(QObject):
    """Signals emitted by the background worker."""
    result = pyqtSignal(object)    # Result of the task (any data type)
    error = pyqtSignal(str)        # Error message when execution fails
    finished = pyqtSignal()        # Emitted when work is complete
    progress = pyqtSignal(int)     # Optional progress value (0-100)

class BackgroundWorker(QObject):
    """Execute a heavy callable away from the UI thread."""
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        """Run the provided callable and capture results or errors."""
        try:
            result = self.func(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            try:
                err_text = str(e)
            except:
                err_text = "Unknown error in worker"
            self.signals.error.emit(err_text)
        finally:
            self.signals.finished.emit()