"""
Tests for the observability module.
"""

import pytest
import json
import csv
from pathlib import Path
from unittest.mock import patch
from src.doctr_process.observability import (
    ObservabilityManager, 
    ExceptionRecord, 
    MetricRecord,
    initialize_observability,
    record_exception,
    record_metric,
    finalize_observability
)


def test_observability_manager_creation(tmp_path):
    """Test that ObservabilityManager creates proper directory structure."""
    run_id = "20231201-143000"
    output_dir = tmp_path / "outputs"
    
    manager = ObservabilityManager(run_id, str(output_dir))
    
    assert manager.run_id == run_id
    assert manager.run_dir.exists()
    assert manager.run_dir.name == f"run_{run_id}"
    assert manager.run_dir.parent == output_dir


def test_exception_recording(tmp_path):
    """Test recording and exporting exceptions."""
    run_id = "20231201-143000"
    manager = ObservabilityManager(run_id, str(tmp_path))
    
    # Create a test exception
    try:
        raise ValueError("Test exception")
    except Exception as e:
        exc_type, exc_value, exc_traceback = type(e), e, e.__traceback__
        manager.record_exception(exc_type, exc_value, exc_traceback, "test_context")
    
    assert len(manager.exceptions) == 1
    
    exc_record = manager.exceptions[0]
    assert exc_record.exception_type == "ValueError"
    assert exc_record.exception_message == "Test exception"
    assert exc_record.context == "test_context"
    assert exc_record.run_id == run_id
    
    # Export to CSV
    csv_path = manager.export_exceptions_csv()
    assert Path(csv_path).exists()
    
    # Verify CSV contents
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 1
    assert rows[0]['exception_type'] == "ValueError"
    assert rows[0]['exception_message'] == "Test exception"
    assert rows[0]['context'] == "test_context"


def test_metric_recording(tmp_path):
    """Test recording and exporting metrics."""
    run_id = "20231201-143000"
    manager = ObservabilityManager(run_id, str(tmp_path))
    
    # Record some metrics
    manager.record_metric("processing_time", 5.2, "timing", "seconds")
    manager.record_metric("pages_processed", 10, "counter", "pages")
    manager.record_metric("memory_usage", 85.5, "gauge", "MB")
    
    assert len(manager.metrics) == 3
    
    # Export to JSON
    json_path = manager.export_metrics_json()
    assert Path(json_path).exists()
    
    # Verify JSON contents
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data['run_id'] == run_id
    assert len(data['metrics']) == 3
    assert data['summary']['total_metrics'] == 3
    
    # Check metric types
    metric_names = [m['metric_name'] for m in data['metrics']]
    assert 'processing_time' in metric_names
    assert 'pages_processed' in metric_names
    assert 'memory_usage' in metric_names


def test_run_summary_creation(tmp_path):
    """Test creation of run summary."""
    run_id = "20231201-143000"
    manager = ObservabilityManager(run_id, str(tmp_path))
    
    # Add some data
    manager.record_metric("test_metric", 1.0, "gauge")
    try:
        raise RuntimeError("Test error")
    except Exception as e:
        exc_type, exc_value, exc_traceback = type(e), e, e.__traceback__
        manager.record_exception(exc_type, exc_value, exc_traceback)
    
    # Create summary
    summary_path = manager.create_run_summary()
    assert Path(summary_path).exists()
    
    # Verify summary contents
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    assert summary['run_id'] == run_id
    assert summary['total_exceptions'] == 1
    assert summary['total_metrics'] == 1
    assert 'RuntimeError' in summary['exception_types']
    assert 'test_metric' in summary['metric_names']


def test_finalize_run(tmp_path):
    """Test finalizing a run with all outputs."""
    run_id = "20231201-143000"
    manager = ObservabilityManager(run_id, str(tmp_path))
    
    # Add data
    manager.record_metric("test_metric", 42.0, "gauge")
    try:
        raise ValueError("Test exception")
    except Exception as e:
        exc_type, exc_value, exc_traceback = type(e), e, e.__traceback__
        manager.record_exception(exc_type, exc_value, exc_traceback)
    
    # Finalize
    files_created = manager.finalize_run()
    
    # Check that all expected files were created
    assert "exceptions_csv" in files_created
    assert "metrics_json" in files_created
    assert "run_summary" in files_created
    
    # Verify files exist
    for file_path in files_created.values():
        assert Path(file_path).exists()


def test_global_observability_functions(tmp_path):
    """Test global observability functions."""
    run_id = "20231201-143000"
    
    # Initialize
    manager = initialize_observability(run_id, str(tmp_path))
    assert manager is not None
    assert manager.run_id == run_id
    
    # Record data using global functions
    record_metric("global_metric", 100.0, "counter")
    
    try:
        raise TypeError("Global exception")
    except Exception as e:
        record_exception(type(e), e, e.__traceback__, "global_test")
    
    # Finalize using global function
    files_created = finalize_observability()
    
    assert "metrics_json" in files_created
    assert "exceptions_csv" in files_created
    assert "run_summary" in files_created


def test_json_logging_output(tmp_path):
    """Test that JSON logging produces valid JSON output."""
    from src.doctr_process.logging_setup import setup_logging, shutdown_logging
    import logging
    
    # Setup logging with JSON output
    log_dir = tmp_path / "logs"
    run_id = setup_logging(app_name="testapp", log_dir=str(log_dir), level="DEBUG")
    
    # Log some messages
    logger = logging.getLogger("test_logger")
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")
    
    # Add custom fields
    logger.info("Custom message", extra={"custom_field": "custom_value"})
    
    shutdown_logging()
    
    # Check that JSON log file was created
    json_log_file = log_dir / "testapp.json"
    assert json_log_file.exists()
    
    # Verify JSON format
    with open(json_log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    assert len(lines) >= 4  # At least 4 log messages
    
    # Each line should be valid JSON
    for line in lines:
        if line.strip():  # Skip empty lines
            data = json.loads(line.strip())
            assert "timestamp" in data
            assert "level" in data
            assert "message" in data
            assert "run_id" in data
            assert data["run_id"] == run_id


def test_observability_with_logging_integration(tmp_path):
    """Test observability integration with logging system."""
    from src.doctr_process.logging_setup import setup_logging, shutdown_logging
    from src.doctr_process.observability import initialize_observability
    
    # Setup logging
    log_dir = tmp_path / "logs"
    run_id = setup_logging(app_name="testapp", log_dir=str(log_dir), level="DEBUG")
    
    # Manually initialize observability with the test tmp_path
    initialize_observability(run_id, str(tmp_path / "outputs"))
    
    # Use global observability functions
    record_metric("integration_test_metric", 123.45, "gauge", "units")
    
    try:
        raise RuntimeError("Integration test exception")
    except Exception as e:
        record_exception(type(e), e, e.__traceback__, "integration_test")
    
    # Shutdown should finalize observability
    shutdown_logging()
    
    # Check that observability files were created
    run_dir = tmp_path / "outputs" / f"run_{run_id}"
    assert run_dir.exists()
    
    metrics_file = run_dir / "metrics.json"
    exceptions_file = run_dir / "exceptions.csv"
    summary_file = run_dir / "run_summary.json"
    
    assert metrics_file.exists()
    assert exceptions_file.exists()
    assert summary_file.exists()