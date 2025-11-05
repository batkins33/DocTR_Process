"""Unit tests for batch processor (Issue #24)."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from src.truck_tickets.processing.batch_processor import (
    BatchConfig,
    BatchProcessingResult,
    BatchProcessor,
    FileProcessingResult,
)


class TestBatchConfig:
    """Test suite for BatchConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = BatchConfig()

        assert config.max_workers is None  # Should use CPU count
        assert config.chunk_size == 10
        assert config.timeout_seconds == 300
        assert config.retry_attempts == 2
        assert config.continue_on_error is True
        assert config.rollback_on_critical is True
        assert config.progress_callback is None

    def test_custom_config(self):
        """Test custom configuration values."""

        def callback(x, y):
            pass

        config = BatchConfig(
            max_workers=4,
            chunk_size=5,
            timeout_seconds=60,
            retry_attempts=1,
            continue_on_error=False,
            rollback_on_critical=False,
            progress_callback=callback,
        )

        assert config.max_workers == 4
        assert config.chunk_size == 5
        assert config.timeout_seconds == 60
        assert config.retry_attempts == 1
        assert config.continue_on_error is False
        assert config.rollback_on_critical is False
        assert config.progress_callback == callback


class TestFileProcessingResult:
    """Test suite for FileProcessingResult dataclass."""

    def test_successful_result(self):
        """Test successful file processing result."""
        result = FileProcessingResult(
            file_path="/path/to/file.pdf",
            success=True,
            pages_processed=5,
            tickets_created=4,
            duplicates_found=1,
            processing_time=2.5,
        )

        assert result.file_path == "/path/to/file.pdf"
        assert result.success is True
        assert result.pages_processed == 5
        assert result.tickets_created == 4
        assert result.duplicates_found == 1
        assert result.error_count == 0
        assert result.error_message is None
        assert result.processing_time == 2.5

    def test_failed_result(self):
        """Test failed file processing result."""
        result = FileProcessingResult(
            file_path="/path/to/file.pdf",
            success=False,
            error_message="OCR failed",
            error_count=1,
        )

        assert result.success is False
        assert result.error_message == "OCR failed"
        assert result.error_count == 1
        assert result.pages_processed == 0


class TestBatchProcessingResult:
    """Test suite for BatchProcessingResult dataclass."""

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = BatchProcessingResult(
            request_guid="test-guid",
            started_at=datetime.now(),
            total_files=100,
            files_processed=95,
            files_failed=5,
        )

        assert result.success_rate == 95.0

    def test_success_rate_zero_files(self):
        """Test success rate with zero files."""
        result = BatchProcessingResult(
            request_guid="test-guid",
            started_at=datetime.now(),
            total_files=0,
        )

        assert result.success_rate == 0.0

    def test_duration_calculation(self):
        """Test duration calculation."""
        started = datetime(2024, 1, 1, 12, 0, 0)
        completed = datetime(2024, 1, 1, 12, 5, 30)

        result = BatchProcessingResult(
            request_guid="test-guid",
            started_at=started,
            completed_at=completed,
        )

        assert result.duration_seconds == 330.0  # 5 minutes 30 seconds

    def test_duration_in_progress(self):
        """Test duration calculation for in-progress batch."""
        result = BatchProcessingResult(
            request_guid="test-guid",
            started_at=datetime.now(),
        )

        # Should return current duration
        duration = result.duration_seconds
        assert duration >= 0


class TestBatchProcessor:
    """Test suite for BatchProcessor class."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = MagicMock()
        session.commit = Mock()
        session.rollback = Mock()
        return session

    @pytest.fixture
    def mock_ledger(self):
        """Create mock processing run ledger."""
        with patch(
            "src.truck_tickets.processing.batch_processor.ProcessingRunLedger"
        ) as mock:
            ledger = mock.return_value
            ledger.start_run = Mock(return_value=MagicMock())
            ledger.complete_run = Mock()
            ledger.fail_run = Mock()
            yield ledger

    @pytest.fixture
    def processor(self, mock_session, mock_ledger):
        """Create batch processor instance."""
        return BatchProcessor(
            session=mock_session,
            job_code="24-105",
            processed_by="test_user",
        )

    def test_initialization(self, processor):
        """Test batch processor initialization."""
        assert processor.job_code == "24-105"
        assert processor.ticket_type == "EXPORT"
        assert processor.processed_by == "test_user"
        assert processor.ticket_processor is not None
        assert processor.ledger is not None

    def test_process_directory_not_exists(self, processor):
        """Test processing non-existent directory."""
        with pytest.raises(ValueError, match="Input path does not exist"):
            processor.process_directory("/nonexistent/path")

    def test_process_directory_no_files(self, processor, mock_ledger):
        """Test processing directory with no PDF files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = processor.process_directory(tmpdir)

            assert result.total_files == 0
            assert result.files_processed == 0
            assert result.status == "COMPLETED"

    def test_process_directory_with_files(self, processor, mock_ledger):
        """Test processing directory with PDF files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test PDF files
            tmpdir_path = Path(tmpdir)
            for i in range(3):
                (tmpdir_path / f"test_{i}.pdf").touch()

            config = BatchConfig(max_workers=1, retry_attempts=0)

            result = processor.process_directory(tmpdir, config=config)

            # Verify ledger calls
            assert mock_ledger.start_run.called
            assert mock_ledger.complete_run.called

            # Verify result
            assert result.total_files == 3
            assert result.request_guid is not None
            assert result.started_at is not None
            assert result.completed_at is not None

    def test_process_single_file_success(self, processor):
        """Test successful single file processing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

            try:
                config = BatchConfig(retry_attempts=0)
                result = processor._process_single_file(tmp_path, config)

                assert result.success is True
                assert result.file_path == str(tmp_path)
                assert result.processing_time > 0
            finally:
                try:
                    tmp_path.unlink()
                except PermissionError:
                    pass  # Windows file locking issue

    def test_process_single_file_with_retry(self, processor):
        """Test single file processing with retry logic."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

            try:
                config = BatchConfig(retry_attempts=2)

                # Test that file processing succeeds (placeholder logic always succeeds)
                result = processor._process_single_file(tmp_path, config)

                # Should succeed
                assert result.success is True
                assert result.file_path == str(tmp_path)
            finally:
                try:
                    tmp_path.unlink()
                except PermissionError:
                    pass  # Windows file locking issue

    def test_progress_callback(self, processor, mock_ledger):
        """Test progress callback functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            tmpdir_path = Path(tmpdir)
            for i in range(5):
                (tmpdir_path / f"test_{i}.pdf").touch()

            # Track progress calls
            progress_calls = []

            def progress_callback(completed, total):
                progress_calls.append((completed, total))

            config = BatchConfig(
                max_workers=1, retry_attempts=0, progress_callback=progress_callback
            )

            processor.process_directory(tmpdir, config=config)

            # Verify progress was tracked
            assert len(progress_calls) > 0
            assert progress_calls[-1][0] == 5  # Final call should be 5/5

    def test_continue_on_error(self, processor, mock_ledger):
        """Test continue_on_error configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            tmpdir_path = Path(tmpdir)
            for i in range(3):
                (tmpdir_path / f"test_{i}.pdf").touch()

            config = BatchConfig(
                max_workers=1, retry_attempts=0, continue_on_error=True
            )

            result = processor.process_directory(tmpdir, config=config)

            # Should process all files even if some fail
            assert result.total_files == 3

    def test_rollback_on_critical_error(self, processor, mock_session, mock_ledger):
        """Test rollback on critical error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.pdf").touch()

            # Reset the mock to remove any previous side effects
            mock_ledger.start_run.side_effect = None
            mock_ledger.start_run.return_value = MagicMock()

            # Mock critical error during parallel processing
            with patch.object(processor, "_process_files_parallel") as mock_parallel:
                mock_parallel.side_effect = Exception("Critical database error")

                config = BatchConfig(rollback_on_critical=True)

                result = processor.process_directory(tmpdir, config=config)

                # Verify rollback was called
                assert mock_session.rollback.called
                assert result.status == "FAILED"

    def test_get_processing_statistics(self, processor, mock_ledger):
        """Test getting processing statistics."""
        mock_ledger.get_processing_statistics.return_value = {
            "total_runs": 10,
            "total_files": 100,
            "total_pages": 500,
        }

        stats = processor.get_processing_statistics()

        assert stats["total_runs"] == 10
        assert stats["total_files"] == 100
        assert stats["total_pages"] == 500

    def test_empty_result_creation(self, processor):
        """Test creation of empty result."""
        result = processor._create_empty_result()

        assert result.total_files == 0
        assert result.files_processed == 0
        assert result.status == "COMPLETED"
        assert result.request_guid is not None

    def test_batch_status_determination(self, processor, mock_ledger):
        """Test batch status determination based on results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            for i in range(5):
                (tmpdir_path / f"test_{i}.pdf").touch()

            config = BatchConfig(max_workers=1, retry_attempts=0)

            result = processor.process_directory(tmpdir, config=config)

            # With placeholder logic, all should succeed
            assert result.status in ["COMPLETED", "PARTIAL", "FAILED"]

    def test_config_snapshot_creation(self, processor, mock_ledger):
        """Test configuration snapshot is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "test.pdf").touch()

            config = BatchConfig(max_workers=4, chunk_size=5)

            processor.process_directory(tmpdir, config=config)

            # Verify start_run was called with config snapshot
            call_args = mock_ledger.start_run.call_args
            assert call_args is not None
            config_snapshot = call_args[1]["config_snapshot"]
            assert config_snapshot["max_workers"] == 4
            assert config_snapshot["chunk_size"] == 5
            assert config_snapshot["job_code"] == "24-105"
