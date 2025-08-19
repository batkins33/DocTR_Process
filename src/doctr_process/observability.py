"""
Observability module for exception tracking, metrics collection, and unified run folders.
"""

import csv
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import traceback


@dataclass
class ExceptionRecord:
    """Structure for tracking exceptions."""
    timestamp: str
    run_id: str
    exception_type: str
    exception_message: str
    traceback: str
    filename: str
    line_number: int
    function_name: str
    severity: str = "ERROR"
    context: str = ""


@dataclass
class MetricRecord:
    """Structure for tracking performance and operational metrics."""
    timestamp: str
    run_id: str
    metric_name: str
    metric_value: float
    metric_type: str  # "counter", "gauge", "timing", "rate"
    unit: str = ""
    tags: Dict[str, str] = None


class ObservabilityManager:
    """Manages observability data collection and output."""
    
    def __init__(self, run_id: str, output_dir: str = "outputs"):
        self.run_id = run_id
        self.output_dir = Path(output_dir)
        self.run_dir = self.output_dir / f"run_{run_id}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        
        self.exceptions: List[ExceptionRecord] = []
        self.metrics: List[MetricRecord] = []
        
        # Validate paths to prevent traversal
        if not str(self.run_dir.resolve()).startswith(str(self.output_dir.resolve())):
            raise ValueError(f"Invalid run directory path: {self.run_dir}")
        
        self.logger = logging.getLogger(__name__)
    
    def record_exception(
        self, 
        exc_type: type, 
        exc_value: Exception, 
        exc_traceback, 
        context: str = "",
        severity: str = "ERROR"
    ):
        """Record an exception for later analysis."""
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Get the frame where the exception occurred
        frame = exc_traceback.tb_frame if exc_traceback else None
        filename = frame.f_code.co_filename if frame else ""
        line_number = exc_traceback.tb_lineno if exc_traceback else 0
        function_name = frame.f_code.co_name if frame else ""
        
        record = ExceptionRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            run_id=self.run_id,
            exception_type=exc_type.__name__,
            exception_message=str(exc_value),
            traceback=tb_str,
            filename=os.path.basename(filename),
            line_number=line_number,
            function_name=function_name,
            severity=severity,
            context=context
        )
        
        self.exceptions.append(record)
        self.logger.error(
            "Exception recorded: %s in %s:%d (%s)", 
            record.exception_type, 
            record.filename, 
            record.line_number,
            context,
            extra={"exception_record": True}
        )
    
    def record_metric(
        self, 
        name: str, 
        value: float, 
        metric_type: str = "gauge", 
        unit: str = "",
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a metric for later analysis."""
        record = MetricRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            run_id=self.run_id,
            metric_name=name,
            metric_value=value,
            metric_type=metric_type,
            unit=unit,
            tags=tags or {}
        )
        
        self.metrics.append(record)
        self.logger.debug(
            "Metric recorded: %s=%s %s", 
            name, 
            value, 
            unit,
            extra={"metric_record": True}
        )
    
    def export_exceptions_csv(self) -> str:
        """Export exceptions to CSV file."""
        if not self.exceptions:
            return ""
            
        csv_path = self.run_dir / "exceptions.csv"
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'timestamp', 'run_id', 'exception_type', 'exception_message',
                'filename', 'line_number', 'function_name', 'severity', 'context'
            ])
            
            # Write exception records
            for exc in self.exceptions:
                writer.writerow([
                    exc.timestamp, exc.run_id, exc.exception_type, 
                    exc.exception_message, exc.filename, exc.line_number,
                    exc.function_name, exc.severity, exc.context
                ])
        
        self.logger.info("Exceptions exported to %s", csv_path)
        return str(csv_path)
    
    def export_metrics_json(self) -> str:
        """Export metrics to JSON file."""
        json_path = self.run_dir / "metrics.json"
        
        metrics_data = {
            "run_id": self.run_id,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": [asdict(metric) for metric in self.metrics],
            "summary": self._calculate_metrics_summary()
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2)
        
        self.logger.info("Metrics exported to %s", json_path)
        return str(json_path)
    
    def _calculate_metrics_summary(self) -> Dict[str, Any]:
        """Calculate summary statistics for metrics."""
        summary = {
            "total_metrics": len(self.metrics),
            "metric_types": {},
            "run_duration": None
        }
        
        # Count metrics by type
        for metric in self.metrics:
            metric_type = metric.metric_type
            if metric_type not in summary["metric_types"]:
                summary["metric_types"][metric_type] = 0
            summary["metric_types"][metric_type] += 1
        
        # Calculate run duration if we have start/end timestamps
        timestamps = [metric.timestamp for metric in self.metrics]
        if timestamps:
            start_time = min(timestamps)
            end_time = max(timestamps)
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration = (end_dt - start_dt).total_seconds()
                summary["run_duration"] = duration
            except ValueError:
                pass  # Ignore if timestamps can't be parsed
        
        return summary
    
    def create_run_summary(self) -> str:
        """Create a run summary with key information."""
        summary_path = self.run_dir / "run_summary.json"
        
        summary_data = {
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_directory": str(self.run_dir),
            "total_exceptions": len(self.exceptions),
            "total_metrics": len(self.metrics),
            "exception_types": list(set(exc.exception_type for exc in self.exceptions)),
            "metric_names": list(set(metric.metric_name for metric in self.metrics)),
            "files_created": list(self.run_dir.glob("*"))
        }
        
        # Convert Path objects to strings for JSON serialization
        summary_data["files_created"] = [str(f.name) for f in summary_data["files_created"]]
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2)
        
        self.logger.info("Run summary created at %s", summary_path)
        return str(summary_path)
    
    def finalize_run(self) -> Dict[str, str]:
        """Finalize the run by exporting all observability data."""
        files_created = {}
        
        # Export exceptions if any
        if self.exceptions:
            files_created["exceptions_csv"] = self.export_exceptions_csv()
        
        # Export metrics
        files_created["metrics_json"] = self.export_metrics_json()
        
        # Create run summary
        files_created["run_summary"] = self.create_run_summary()
        
        self.logger.info(
            "Run %s finalized. Created %d files in %s", 
            self.run_id, 
            len(files_created), 
            self.run_dir
        )
        
        return files_created


# Global observability manager instance
_observability_manager: Optional[ObservabilityManager] = None


def get_observability_manager() -> Optional[ObservabilityManager]:
    """Get the current observability manager instance."""
    return _observability_manager


def initialize_observability(run_id: str, output_dir: str = "outputs") -> ObservabilityManager:
    """Initialize the global observability manager."""
    global _observability_manager
    _observability_manager = ObservabilityManager(run_id, output_dir)
    return _observability_manager


def record_exception(exc_type: type, exc_value: Exception, exc_traceback, context: str = ""):
    """Record an exception using the global observability manager."""
    if _observability_manager:
        _observability_manager.record_exception(exc_type, exc_value, exc_traceback, context)


def record_metric(name: str, value: float, metric_type: str = "gauge", unit: str = "", tags: Dict[str, str] = None):
    """Record a metric using the global observability manager."""
    if _observability_manager:
        _observability_manager.record_metric(name, value, metric_type, unit, tags)


def finalize_observability() -> Dict[str, str]:
    """Finalize observability data collection and export."""
    if _observability_manager:
        return _observability_manager.finalize_run()
    return {}