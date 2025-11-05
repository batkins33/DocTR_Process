"""Unit tests for processing run ledger (Issue #21)."""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from src.truck_tickets.database.processing_run_ledger import ProcessingRunLedger
from src.truck_tickets.models.sql_processing import ProcessingRun


class TestProcessingRunLedger:
    """Test suite for processing run ledger."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        session.query.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )
        session.query.return_value.order_by.return_value.all.return_value = []
        session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = (
            []
        )
        session.query.return_value.filter.return_value.delete.return_value = 0
        return session

    @pytest.fixture
    def ledger(self, mock_session):
        """Create processing run ledger instance."""
        return ProcessingRunLedger(mock_session)

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration."""
        return {
            "vendor_templates": ["WM_LEWISVILLE", "LDI_YARD"],
            "threads": 4,
            "dry_run": False,
            "input_path": "/path/to/pdfs",
            "job_code": "24-105",
        }

    def test_start_run_basic(self, ledger, mock_session, sample_config):
        """Test starting a basic processing run."""
        processed_by = "test_user"

        ledger.start_run(processed_by, sample_config)

        # Verify ProcessingRun was created
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        # Check the created run
        added_run = mock_session.add.call_args[0][0]
        assert isinstance(added_run, ProcessingRun)
        assert added_run.processed_by == processed_by
        assert added_run.status == "IN_PROGRESS"
        assert added_run.started_at is not None
        assert added_run.request_guid is not None

        # Check config snapshot
        assert added_run.config_snapshot is not None
        config_data = json.loads(added_run.config_snapshot)
        assert config_data["job_code"] == "24-105"
        assert config_data["threads"] == 4

    def test_start_run_with_custom_guid(self, ledger, mock_session):
        """Test starting run with custom GUID."""
        custom_guid = "custom-test-guid-123"
        processed_by = "test_user"

        ledger.start_run(processed_by, request_guid=custom_guid)

        added_run = mock_session.add.call_args[0][0]
        assert added_run.request_guid == custom_guid

    def test_start_run_without_config(self, ledger, mock_session):
        """Test starting run without config snapshot."""
        processed_by = "test_user"

        ledger.start_run(processed_by)

        added_run = mock_session.add.call_args[0][0]
        assert added_run.config_snapshot is None

    def test_update_run_progress(self, ledger, mock_session):
        """Test updating run progress."""
        # Setup mock to return a ProcessingRun
        mock_run = ProcessingRun(
            request_guid="test-guid",
            started_at=datetime.now(),
            processed_by="test_user",
            status="IN_PROGRESS",
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_run
        )

        # Update progress
        updated_run = ledger.update_run_progress(
            "test-guid",
            files_count=10,
            pages_count=25,
            tickets_created=20,
            tickets_updated=3,
            duplicates_found=2,
            review_queue_count=1,
            error_count=0,
        )

        # Verify updates
        assert updated_run.files_count == 10
        assert updated_run.pages_count == 25
        assert updated_run.tickets_created == 20
        assert updated_run.tickets_updated == 3
        assert updated_run.duplicates_found == 2
        assert updated_run.review_queue_count == 1
        assert updated_run.error_count == 0

        mock_session.commit.assert_called_once()

    def test_update_run_progress_partial(self, ledger, mock_session):
        """Test updating only some progress fields."""
        mock_run = ProcessingRun(
            request_guid="test-guid",
            started_at=datetime.now(),
            processed_by="test_user",
            status="IN_PROGRESS",
            files_count=5,
            pages_count=10,
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_run
        )

        # Update only some fields
        updated_run = ledger.update_run_progress(
            "test-guid",
            pages_count=15,
            tickets_created=12,
        )

        # Verify only specified fields were updated
        assert updated_run.files_count == 5  # Unchanged
        assert updated_run.pages_count == 15  # Updated
        assert updated_run.tickets_created == 12  # Updated

    def test_complete_run_success(self, ledger, mock_session):
        """Test completing a run successfully."""
        mock_run = ProcessingRun(
            request_guid="test-guid",
            started_at=datetime.now(),
            processed_by="test_user",
            status="IN_PROGRESS",
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_run
        )

        final_stats = {
            "files_count": 10,
            "pages_count": 25,
            "tickets_created": 22,
        }

        completed_run = ledger.complete_run("test-guid", "COMPLETED", final_stats)

        assert completed_run.status == "COMPLETED"
        assert completed_run.completed_at is not None
        assert completed_run.files_count == 10
        assert completed_run.pages_count == 25
        assert completed_run.tickets_created == 22

        mock_session.commit.assert_called_once()

    def test_complete_run_default_status(self, ledger, mock_session):
        """Test completing run with default COMPLETED status."""
        mock_run = ProcessingRun(
            request_guid="test-guid",
            started_at=datetime.now(),
            processed_by="test_user",
            status="IN_PROGRESS",
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_run
        )

        completed_run = ledger.complete_run("test-guid")

        assert completed_run.status == "COMPLETED"

    def test_fail_run(self, ledger, mock_session):
        """Test marking a run as failed."""
        mock_run = ProcessingRun(
            request_guid="test-guid",
            started_at=datetime.now(),
            processed_by="test_user",
            status="IN_PROGRESS",
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_run
        )

        failed_run = ledger.fail_run("test-guid", "Database connection error")

        assert failed_run.status == "FAILED"
        assert failed_run.completed_at is not None

    def test_get_run_by_guid_found(self, ledger, mock_session):
        """Test getting run by GUID when it exists."""
        mock_run = ProcessingRun(
            request_guid="test-guid",
            started_at=datetime.now(),
            processed_by="test_user",
            status="COMPLETED",
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_run
        )

        run = ledger.get_run_by_guid("test-guid")

        assert run == mock_run
        mock_session.query.assert_called_with(ProcessingRun)

    def test_get_run_by_guid_not_found(self, ledger, mock_session):
        """Test getting run by GUID when it doesn't exist."""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError, match="Processing run not found: test-guid"):
            ledger.get_run_by_guid("test-guid")

    def test_get_recent_runs(self, ledger, mock_session):
        """Test getting recent processing runs."""
        mock_runs = [
            ProcessingRun(
                request_guid="run1", started_at=datetime.now(), processed_by="user1"
            ),
            ProcessingRun(
                request_guid="run2", started_at=datetime.now(), processed_by="user2"
            ),
        ]
        mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_runs
        )

        runs = ledger.get_recent_runs(limit=5)

        assert runs == mock_runs
        mock_session.query.assert_called_with(ProcessingRun)

    def test_get_runs_by_user(self, ledger, mock_session):
        """Test getting runs by specific user."""
        mock_runs = [
            ProcessingRun(
                request_guid="run1", started_at=datetime.now(), processed_by="test_user"
            ),
        ]
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = (
            mock_runs
        )

        runs = ledger.get_runs_by_user("test_user")

        assert runs == mock_runs

    def test_get_failed_runs(self, ledger, mock_session):
        """Test getting failed processing runs."""
        mock_runs = [
            ProcessingRun(
                request_guid="run1",
                started_at=datetime.now(),
                processed_by="user1",
                status="FAILED",
            ),
        ]
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = (
            mock_runs
        )

        runs = ledger.get_failed_runs()

        assert runs == mock_runs

    def test_get_in_progress_runs(self, ledger, mock_session):
        """Test getting in-progress processing runs."""
        mock_runs = [
            ProcessingRun(
                request_guid="run1",
                started_at=datetime.now(),
                processed_by="user1",
                status="IN_PROGRESS",
            ),
        ]
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = (
            mock_runs
        )

        runs = ledger.get_in_progress_runs()

        assert runs == mock_runs

    def test_cleanup_old_runs(self, ledger, mock_session):
        """Test cleaning up old processing runs."""
        mock_session.query.return_value.filter.return_value.delete.return_value = 5

        deleted_count = ledger.cleanup_old_runs(days_to_keep=30)

        assert deleted_count == 5
        mock_session.commit.assert_called_once()

    def test_cleanup_old_runs_none_deleted(self, ledger, mock_session):
        """Test cleanup when no old runs exist."""
        mock_session.query.return_value.filter.return_value.delete.return_value = 0

        deleted_count = ledger.cleanup_old_runs(days_to_keep=30)

        assert deleted_count == 0

    def test_get_processing_statistics(self, ledger, mock_session):
        """Test getting processing statistics."""
        # Mock aggregate query result
        mock_stats = MagicMock()
        mock_stats.total_runs = 10
        mock_stats.total_files = 100
        mock_stats.total_pages = 250
        mock_stats.total_tickets_created = 200
        mock_stats.total_tickets_updated = 30
        mock_stats.total_duplicates = 5
        mock_stats.total_review_items = 15
        mock_stats.total_errors = 2
        mock_stats.avg_pages_per_run = 25.0

        # Mock status counts
        mock_status_counts = [
            ("COMPLETED", 8),
            ("FAILED", 1),
            ("IN_PROGRESS", 1),
        ]

        # Setup mock returns
        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_stats
        )
        mock_session.query.return_value.group_by.return_value.all.return_value = (
            mock_status_counts
        )

        stats = ledger.get_processing_statistics()

        assert stats["total_runs"] == 10
        assert stats["total_files"] == 100
        assert stats["total_pages"] == 250
        assert stats["total_tickets_created"] == 200
        assert stats["total_tickets_updated"] == 30
        assert stats["total_duplicates"] == 5
        assert stats["total_review_items"] == 15
        assert stats["total_errors"] == 2
        assert stats["avg_pages_per_run"] == 25.0
        assert stats["status_counts"]["COMPLETED"] == 8
        assert stats["status_counts"]["FAILED"] == 1
        assert stats["status_counts"]["IN_PROGRESS"] == 1

    def test_get_processing_statistics_empty(self, ledger, mock_session):
        """Test getting statistics when no runs exist."""
        # Mock empty result
        mock_stats = MagicMock()
        mock_stats.total_runs = None
        mock_stats.total_files = None
        mock_stats.total_pages = None
        mock_stats.total_tickets_created = None
        mock_stats.total_tickets_updated = None
        mock_stats.total_duplicates = None
        mock_stats.total_review_items = None
        mock_stats.total_errors = None
        mock_stats.avg_pages_per_run = None

        mock_session.query.return_value.filter.return_value.first.return_value = (
            mock_stats
        )
        mock_session.query.return_value.group_by.return_value.all.return_value = []

        stats = ledger.get_processing_statistics()

        # Should handle None values gracefully
        assert stats["total_runs"] == 0
        assert stats["total_files"] == 0
        assert stats["avg_pages_per_run"] == 0.0
        assert stats["status_counts"] == {}

    def test_log_run_summary(self, ledger, mock_session, caplog):
        """Test logging of run summary."""
        import logging

        caplog.set_level(logging.INFO)

        mock_run = ProcessingRun(
            request_guid="test-guid",
            started_at=datetime.now() - timedelta(seconds=120),
            completed_at=datetime.now(),
            processed_by="test_user",
            status="COMPLETED",
            files_count=10,
            pages_count=25,
            tickets_created=20,
            tickets_updated=3,
            duplicates_found=2,
            review_queue_count=1,
            error_count=0,
        )

        ledger._log_run_summary(mock_run)

        # Check that summary was logged
        assert "PROCESSING RUN SUMMARY" in caplog.text
        assert "test-guid" in caplog.text
        assert "COMPLETED" in caplog.text
        assert "Files Processed: 10" in caplog.text
        assert "Pages Processed: 25" in caplog.text

    def test_integration_full_lifecycle(self, ledger, mock_session, sample_config):
        """Test full processing run lifecycle."""
        # Mock run for queries
        mock_run = ProcessingRun(
            request_guid="test-guid",
            started_at=datetime.now(),
            processed_by="test_user",
            status="IN_PROGRESS",
        )
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            mock_run
        )

        # 1. Start run
        ledger.start_run("test_user", sample_config)
        request_guid = mock_session.add.call_args[0][0].request_guid

        # 2. Update progress multiple times
        ledger.update_run_progress(request_guid, files_count=5, pages_count=12)
        ledger.update_run_progress(request_guid, tickets_created=10, tickets_updated=2)

        # 3. Complete run
        final_stats = {
            "files_count": 10,
            "pages_count": 25,
            "tickets_created": 22,
            "tickets_updated": 2,
            "duplicates_found": 1,
            "review_queue_count": 0,
            "error_count": 0,
        }
        ledger.complete_run(request_guid, "COMPLETED", final_stats)

        # Verify all operations called commit
        assert mock_session.commit.call_count >= 3
