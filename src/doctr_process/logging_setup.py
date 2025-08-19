import atexit
import json
import logging
import logging.config
import os
import queue
import sys
import threading
import time
from logging.handlers import QueueHandler, QueueListener, TimedRotatingFileHandler, RotatingFileHandler

_log_q = queue.Queue()
_listener = None
_initialized = False
_run_id: str | None = None


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
        except Exception as e:
            # If widget is gone (e.g., app shutting down), log the error
            logging.getLogger(__name__).error("Error updating GUI log widget: %s", str(e).replace('\n', ' ').replace('\r', ' '), exc_info=True)

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
        super().__init__();
        self.run_id = run_id

    def filter(self, record):
        record.run_id = self.run_id
        return True


def shutdown_logging():
    global _listener, _initialized, _run_id
    if _listener:
        try:
            _listener.stop()  # flushes all handlers
        finally:
            _listener = None
    _initialized = False
    _run_id = None


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


def setup_logging(app_name: str = "doctr_app", log_dir: str = "logs", level: str = "INFO"):
    global _initialized, _listener, _run_id
    if _initialized:
        return _run_id
    _initialized = True

    # Validate log_dir to prevent path traversal
    if '..' in log_dir or os.path.isabs(log_dir):
        raise ValueError(f"Invalid log directory path: {log_dir}")

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
    _run_id = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    rc = RunContext(_run_id)
    for h in sinks:
        h.addFilter(rc)

    # Tame noisy third-party loggers
    for noisy in ("PIL", "urllib3", "fitz", "botocore", "PaddleOCR", "pdfminer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    install_global_exception_logging()
    atexit.register(shutdown_logging)
    run_file = os.path.join(log_dir, f"run_{_run_id}.json")
    # Validate run_file path to prevent traversal attacks
    if not os.path.abspath(run_file).startswith(os.path.abspath(log_dir)):
        raise ValueError(f"Invalid run file path: {run_file}")
    with open(run_file, "w", encoding="utf-8") as f:
        json.dump({"run_id": _run_id}, f)
    logging.getLogger(__name__).info("Logging initialized (level=%s, dir=%s)", level, str(log_dir).replace('\n', ' ').replace('\r', ' '))
    return _run_id


def set_gui_log_widget(scrolled_text_widget):
    _gui_handler.set_gui_widget(scrolled_text_widget)
