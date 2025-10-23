from PyQt6.QtCore import QObject, pyqtSignal

class WorkerSignals(QObject):
    """الإشارات التي يرسلها العامل إلى الواجهة"""
    result = pyqtSignal(object)    # نتيجة العمل (أي نوع بيانات)
    error = pyqtSignal(str)        # نص الخطأ عند الفشل
    finished = pyqtSignal()        # عند الانتهاء
    progress = pyqtSignal(int)     # نسبة التقدم (0-100) إن وُجدت

class BackgroundWorker(QObject):
    """
    BackgroundWorker يَنفّذ callable ثقيل خارج خيط الواجهة.
    الاستخدام:
      worker = BackgroundWorker(func, *args, **kwargs)
      worker.moveToThread(thread)
      thread.started.connect(worker.run)
    """
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        """يشغّل الوظيفة الممرّرة ويلتقط النتيجة/الأخطاء"""
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