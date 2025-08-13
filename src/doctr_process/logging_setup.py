import logging, logging.config, sys, queue, threading, os, atexit, time
from logging.handlers import QueueHandler, QueueListener, TimedRotatingFileHandler, RotatingFileHandler


_log_q = queue.Queue()
_listener = None
_initialized = False


class TkTextHandler(logging.Handler):
    """Optional GUI sink; call set_gui_widget(widget) to activate."""
    def __init__(self):
        super().__init__()
        self._widget = None

    def set_gui_widget(self, widget):
        self._widget = widget

    def emit(self, record):
        if not self._widget:
            return
        msg = self.format(record)
        try:
            self._widget.after(0, self._append, msg)
        except Exception:
            # If widget is gone (e.g., app shutting down), ignore
            pass

    def _append(self, msg):
        try:
            self._widget.configure(state="normal")
            self._widget.insert("end", msg + "\n")
            self._widget.see("end")
        finally:
            self._widget.configure(state="disabled")
class UTCFormatter(logging.Formatter):
    converter = time.gmtime

class RunContext(logging.Filter):
    def __init__(self, run_id: str): 
        super().__init__(); self.run_id = run_id
    def filter(self, record):
        record.run_id = self.run_id
        return True
def shutdown_logging():
    global _listener
    if _listener:
        try:
            _listener.stop()  # flushes all handlers
        finally:
            _listener = None

_gui_handler = TkTextHandler()

def install_global_exception_logging():
    def _hook(exc_type, exc, tb):
        logging.getLogger(__name__).exception("Uncaught exception", exc_info=(exc_type, exc, tb))
    sys.excepthook = _hook

    if hasattr(threading, "excepthook"):
        def _thread_hook(args):
            logging.getLogger(args.thread.name or __name__).exception(
                "Uncaught thread exception",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
            )
        threading.excepthook = _thread_hook


def setup_logging(app_name: str="doctr_app", log_dir: str="logs", level: str="INFO"):
    global _initialized, _listener
    if _initialized:
        return
    _initialized = True

    os.makedirs(log_dir, exist_ok=True)

    base_fmt = "%(asctime)s %(run_id)s %(levelname)s %(name)s %(filename)s:%(lineno)d - %(message)s"
    console_fmt = "[%(levelname)s] %(name)s: %(message)s"
    level_num = getattr(logging, level.upper(), logging.INFO)

    # Handlers (final sinks)
    file_info = TimedRotatingFileHandler(
        os.path.join(log_dir, f"{app_name}.log"),
        when="midnight", backupCount=14, encoding="utf-8"
    )
    file_info.setLevel(level_num)
    file_info.setFormatter(UTCFormatter(base_fmt))

    file_err = RotatingFileHandler(
        os.path.join(log_dir, f"{app_name}.error.log"),
        maxBytes=5_000_000, backupCount=10, encoding="utf-8"
    )
    file_err.setLevel(logging.WARNING)
    file_err.setFormatter(UTCFormatter(base_fmt))

    console = None
    try:
        if sys.stderr and sys.stderr.isatty():  # avoid console under pythonw / no TTY
            console = logging.StreamHandler(stream=sys.stderr)
            console.setLevel(level_num)
            console.setFormatter(logging.Formatter(console_fmt))
    except Exception:
        console = None  # be safe on odd environments

    gui = _gui_handler
    gui.setLevel(level_num)
    gui.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))

    # Root logger routes through the queue
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()
    root.addHandler(QueueHandler(_log_q))

    # Listener consumes from queue and writes to sinks
    sinks = [file_info, file_err, gui] + ([console] if console else [])
    _listener = QueueListener(_log_q, *sinks, respect_handler_level=True)
    _listener.start()

    # Add a run context to all sinks
    run_id = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    rc = RunContext(run_id)
    for h in sinks:
        h.addFilter(rc)

    # Tame noisy third-party loggers
    for noisy in ("PIL", "urllib3", "fitz", "botocore", "PaddleOCR", "pdfminer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    install_global_exception_logging()
    atexit.register(shutdown_logging)
    logging.getLogger(__name__).info("Logging initialized (level=%s, dir=%s)", level, log_dir)

def set_gui_log_widget(scrolled_text_widget):
    _gui_handler.set_gui_widget(scrolled_text_widget)
