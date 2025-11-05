from doctr_process.logging_setup import setup_logging, shutdown_logging
from doctr_process.ocr.config_utils import load_config


def test_env_override(monkeypatch, tmp_path):
    # Write a dummy config
    config_path = tmp_path / "config.yaml"
    config_path.write_text("foo: bar\nbaz: qux\n")
    monkeypatch.setenv("FOO", "env_foo")
    cfg = load_config(str(config_path))
    assert cfg["foo"] == "env_foo"
    assert cfg["baz"] == "qux"


def test_logging_creates_runid_file(tmp_path):
    log_dir = tmp_path / "logs"
    run_id = setup_logging(log_dir=str(log_dir))
    log_file = log_dir / f"run_{run_id}.json"
    import logging

    logging.info("test log entry")
    assert log_file.exists()
    contents = log_file.read_text()
    assert "run_id" in contents
    shutdown_logging()
