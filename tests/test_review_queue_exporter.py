"""Unit tests for review queue exporter (Issue #20)."""

import json
import tempfile
from pathlib import Path

import pytest
from src.truck_tickets.exporters.review_queue_exporter import ReviewQueueExporter


class TestReviewQueueExporter:
    """Test suite for review queue exporter."""

    @pytest.fixture
    def exporter(self):
        """Create review queue exporter instance."""
        return ReviewQueueExporter()

    @pytest.fixture
    def sample_review_items(self):
        """Create sample review queue items."""
        return [
            {
                "page_id": "file1.pdf-p3",
                "reason": "MISSING_MANIFEST",
                "severity": "CRITICAL",
                "file_path": "/path/file1.pdf",
                "page_num": 3,
                "detected_fields": {"ticket": "12345", "material": "CLASS_2"},
                "suggested_fixes": {"action": "manual_entry"},
                "created_at": "2024-10-17 14:32:01",
            },
            {
                "page_id": "file2.pdf-p1",
                "reason": "EXTRACTION_FAILED",
                "severity": "WARNING",
                "file_path": "/path/file2.pdf",
                "page_num": 1,
                "detected_fields": {"vendor": "UNKNOWN"},
                "suggested_fixes": {"action": "review_ocr"},
                "created_at": "2024-10-17 14:30:15",
            },
            {
                "page_id": "file3.pdf-p2",
                "reason": "LOW_CONFIDENCE",
                "severity": "INFO",
                "file_path": "/path/file3.pdf",
                "page_num": 2,
                "detected_fields": {"ticket": "67890", "confidence": 0.7},
                "suggested_fixes": {"action": "verify_ticket"},
                "created_at": "2024-10-17 14:35:22",
            },
        ]

    def test_export_basic(self, exporter, sample_review_items):
        """Test basic CSV export functionality."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            exporter.export(sample_review_items, output_path)

            # Verify file was created
            assert Path(output_path).exists()

            # Read and verify content
            with open(output_path, encoding="utf-8") as f:
                content = f.read()

            # Check header
            assert (
                "page_id,reason,severity,file_path,page_num,detected_fields,suggested_fixes,created_at"
                in content
            )

            # Check data rows
            assert "file1.pdf-p3" in content
            assert "MISSING_MANIFEST" in content
            assert "CRITICAL" in content

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_sorting_by_severity(self, exporter, sample_review_items):
        """Test that export sorts by severity (CRITICAL first)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            exporter.export(sample_review_items, output_path)

            with open(output_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Skip header, check first data row is CRITICAL
            assert "CRITICAL" in lines[1]
            assert "WARNING" in lines[2]
            assert "INFO" in lines[3]

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_json_fields(self, exporter, sample_review_items):
        """Test that JSON fields are properly serialized."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            exporter.export(sample_review_items, output_path)

            with open(output_path, encoding="utf-8") as f:
                content = f.read()

            # Check JSON serialization (with CSV double-quote escaping)
            assert '""ticket"": ""12345""' in content
            assert '""material"": ""CLASS_2""' in content
            assert '""action"": ""manual_entry""' in content

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_empty_list(self, exporter):
        """Test export with empty review items list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            exporter.export([], output_path)

            # Verify file was created with header only
            with open(output_path, encoding="utf-8") as f:
                lines = f.readlines()

            assert len(lines) == 1  # Header only
            assert "page_id,reason,severity" in lines[0]

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_by_reason(self, exporter, sample_review_items):
        """Test export grouped by reason."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            exporter.export_by_reason(sample_review_items, output_dir)

            # Check that reason-specific files were created
            missing_manifest_file = output_dir / "review_queue_MISSING_MANIFEST.csv"
            extraction_failed_file = output_dir / "review_queue_EXTRACTION_FAILED.csv"
            low_confidence_file = output_dir / "review_queue_LOW_CONFIDENCE.csv"

            assert missing_manifest_file.exists()
            assert extraction_failed_file.exists()
            assert low_confidence_file.exists()

            # Verify content of one file
            with open(missing_manifest_file, encoding="utf-8") as f:
                content = f.read()
            assert "MISSING_MANIFEST" in content
            assert "CRITICAL" in content

    def test_generate_summary_report(self, exporter, sample_review_items):
        """Test summary report generation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            exporter.generate_summary_report(sample_review_items, output_path)

            # Verify file was created
            assert Path(output_path).exists()

            with open(output_path, encoding="utf-8") as f:
                content = f.read()

            # Check header
            assert "reason,severity,item_count,affected_files" in content

            # Check summary data
            assert "MISSING_MANIFEST,CRITICAL,1,1" in content
            assert "EXTRACTION_FAILED,WARNING,1,1" in content
            assert "LOW_CONFIDENCE,INFO,1,1" in content

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_critical_only(self, exporter, sample_review_items):
        """Test export of only critical items."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            exporter.export_critical_only(sample_review_items, output_path)

            with open(output_path, encoding="utf-8") as f:
                content = f.read()

            # Should only contain CRITICAL items
            assert "CRITICAL" in content
            assert "WARNING" not in content
            assert "INFO" not in content
            assert "MISSING_MANIFEST" in content

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_critical_only_empty(self, exporter):
        """Test export critical only when no critical items exist."""
        non_critical_items = [
            {
                "page_id": "file1.pdf-p1",
                "reason": "LOW_CONFIDENCE",
                "severity": "INFO",
                "file_path": "/path/file1.pdf",
                "page_num": 1,
                "detected_fields": {},
                "suggested_fixes": {},
                "created_at": "2024-10-17 14:30:00",
            }
        ]

        # Use a non-existent path to test that no file is created
        output_path = Path(tempfile.gettempdir()) / "test_critical_empty.csv"

        # Ensure file doesn't exist before test
        output_path.unlink(missing_ok=True)

        # Should not create file when no critical items
        exporter.export_critical_only(non_critical_items, output_path)
        assert not output_path.exists()

    def test_check_missing_manifests(self, exporter, sample_review_items):
        """Test missing manifest detection."""
        missing_manifests = exporter.check_missing_manifests(sample_review_items)

        assert len(missing_manifests) == 1
        assert missing_manifests[0]["reason"] == "MISSING_MANIFEST"
        assert missing_manifests[0]["severity"] == "CRITICAL"

    def test_check_missing_manifests_none(self, exporter):
        """Test missing manifest detection when none exist."""
        items_without_missing_manifests = [
            {
                "page_id": "file1.pdf-p1",
                "reason": "LOW_CONFIDENCE",
                "severity": "INFO",
                "file_path": "/path/file1.pdf",
                "page_num": 1,
                "detected_fields": {},
                "suggested_fixes": {},
                "created_at": "2024-10-17 14:30:00",
            }
        ]

        missing_manifests = exporter.check_missing_manifests(
            items_without_missing_manifests
        )
        assert len(missing_manifests) == 0

    def test_export_for_gui(self, exporter, sample_review_items):
        """Test JSON export for GUI application."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            exporter.export_for_gui(sample_review_items, output_path)

            # Verify file was created
            assert Path(output_path).exists()

            # Load and verify JSON content
            with open(output_path, encoding="utf-8") as f:
                data = json.load(f)

            assert len(data) == 3
            # Should be sorted by severity (CRITICAL first)
            assert data[0]["severity"] == "CRITICAL"
            assert data[1]["severity"] == "WARNING"
            assert data[2]["severity"] == "INFO"

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_export_with_missing_fields(self, exporter):
        """Test export with items missing optional fields."""
        minimal_items = [
            {
                "reason": "UNKNOWN_ERROR",
                "severity": "WARNING",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            exporter.export(minimal_items, output_path)

            with open(output_path, encoding="utf-8") as f:
                content = f.read()

            # Should handle missing fields gracefully
            assert "UNKNOWN_ERROR" in content
            assert "WARNING" in content

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_severity_summary_logging(self, exporter, sample_review_items, caplog):
        """Test severity summary logging."""
        import logging

        caplog.set_level(logging.INFO)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            exporter.export(sample_review_items, output_path)

            # Check log messages
            assert "1 critical, 1 warnings, 1 info" in caplog.text
            assert "1 CRITICAL items require immediate attention" in caplog.text

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_pathlib_path_support(self, exporter, sample_review_items):
        """Test that Path objects are supported for output paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "review_queue.csv"

            exporter.export(sample_review_items, output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0
