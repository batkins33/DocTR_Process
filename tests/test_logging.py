import logging
import time

from doctr_process.logging_setup import setup_logging, shutdown_logging


def test_logging_writes_files(tmp_path):
    logdir = tmp_path / "logs"
    setup_logging(app_name="testapp", log_dir=str(logdir), level="DEBUG")
    logging.getLogger(__name__).warning("hello error")
    time.sleep(0.05)
    shutdown_logging()
    assert (logdir / "testapp.log").exists()
    assert (logdir / "testapp.error.log").exists()
