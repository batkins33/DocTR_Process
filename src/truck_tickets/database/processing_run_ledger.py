"""Processing run ledger for tracking batch processing operations.

Issue #21: Processing Run Ledger
Implements audit trail for processing runs with statistics and configuration tracking.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from ..models.sql_processing import ProcessingRun


class ProcessingRunLedger:
    """Manages processing run tracking and audit trail."""

    def __init__(self, session: Session):
        """Initialize processing run ledger.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.logger = logging.getLogger(__name__)

    def start_run(
        self,
        processed_by: str,
        config_snapshot: dict[str, Any] | None = None,
        request_guid: str | None = None,
    ) -> ProcessingRun:
        """Start a new processing run.

        Args:
            processed_by: User or process identifier
            config_snapshot: Configuration used for this run
            request_guid: Optional custom GUID (auto-generated if not provided)

        Returns:
            ProcessingRun instance
        """
        if request_guid is None:
            request_guid = str(uuid.uuid4())

        # Serialize config snapshot
        config_json = None
        if config_snapshot:
            config_json = json.dumps(config_snapshot, default=str, indent=2)

        processing_run = ProcessingRun(
            request_guid=request_guid,
            started_at=datetime.now(),
            processed_by=processed_by,
            status="IN_PROGRESS",
            config_snapshot=config_json,
            files_count=0,
            pages_count=0,
            tickets_created=0,
            tickets_updated=0,
            duplicates_found=0,
            review_queue_count=0,
            error_count=0,
        )

        self.session.add(processing_run)
        self.session.commit()

        self.logger.info(f"Started processing run {request_guid} by {processed_by}")

        return processing_run

    def update_run_progress(
        self,
        request_guid: str,
        files_count: int | None = None,
        pages_count: int | None = None,
        tickets_created: int | None = None,
        tickets_updated: int | None = None,
        duplicates_found: int | None = None,
        review_queue_count: int | None = None,
        error_count: int | None = None,
    ) -> ProcessingRun:
        """Update processing run statistics.

        Args:
            request_guid: Processing run identifier
            files_count: Number of files processed
            pages_count: Number of pages processed
            tickets_created: Number of new tickets created
            tickets_updated: Number of existing tickets updated
            duplicates_found: Number of duplicate tickets found
            review_queue_count: Number of items sent to review queue
            error_count: Number of errors encountered

        Returns:
            Updated ProcessingRun instance

        Raises:
            ValueError: If processing run not found
        """
        processing_run = self.get_run_by_guid(request_guid)

        if files_count is not None:
            processing_run.files_count = files_count
        if pages_count is not None:
            processing_run.pages_count = pages_count
        if tickets_created is not None:
            processing_run.tickets_created = tickets_created
        if tickets_updated is not None:
            processing_run.tickets_updated = tickets_updated
        if duplicates_found is not None:
            processing_run.duplicates_found = duplicates_found
        if review_queue_count is not None:
            processing_run.review_queue_count = review_queue_count
        if error_count is not None:
            processing_run.error_count = error_count

        self.session.commit()

        self.logger.debug(f"Updated run {request_guid} progress")

        return processing_run

    def complete_run(
        self,
        request_guid: str,
        status: str = "COMPLETED",
        final_stats: dict[str, int] | None = None,
    ) -> ProcessingRun:
        """Complete a processing run.

        Args:
            request_guid: Processing run identifier
            status: Final status (COMPLETED, FAILED)
            final_stats: Final statistics to update

        Returns:
            Completed ProcessingRun instance

        Raises:
            ValueError: If processing run not found
        """
        processing_run = self.get_run_by_guid(request_guid)

        processing_run.completed_at = datetime.now()
        processing_run.status = status

        # Update final statistics if provided
        if final_stats:
            for key, value in final_stats.items():
                if hasattr(processing_run, key):
                    setattr(processing_run, key, value)

        self.session.commit()

        duration = processing_run.duration_seconds or 0
        self.logger.info(
            f"Completed processing run {request_guid} "
            f"with status {status} in {duration}s"
        )

        # Log summary statistics
        self._log_run_summary(processing_run)

        return processing_run

    def fail_run(
        self,
        request_guid: str,
        error_message: str | None = None,
    ) -> ProcessingRun:
        """Mark a processing run as failed.

        Args:
            request_guid: Processing run identifier
            error_message: Optional error description

        Returns:
            Failed ProcessingRun instance
        """
        processing_run = self.complete_run(request_guid, status="FAILED")

        if error_message:
            self.logger.error(f"Processing run {request_guid} failed: {error_message}")

        return processing_run

    def get_run_by_guid(self, request_guid: str) -> ProcessingRun:
        """Get processing run by GUID.

        Args:
            request_guid: Processing run identifier

        Returns:
            ProcessingRun instance

        Raises:
            ValueError: If processing run not found
        """
        processing_run = (
            self.session.query(ProcessingRun)
            .filter_by(request_guid=request_guid)
            .first()
        )

        if not processing_run:
            raise ValueError(f"Processing run not found: {request_guid}")

        return processing_run

    def get_recent_runs(self, limit: int = 10) -> list[ProcessingRun]:
        """Get recent processing runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of ProcessingRun instances
        """
        return (
            self.session.query(ProcessingRun)
            .order_by(ProcessingRun.started_at.desc())
            .limit(limit)
            .all()
        )

    def get_runs_by_user(self, processed_by: str) -> list[ProcessingRun]:
        """Get processing runs by user.

        Args:
            processed_by: User identifier

        Returns:
            List of ProcessingRun instances
        """
        return (
            self.session.query(ProcessingRun)
            .filter_by(processed_by=processed_by)
            .order_by(ProcessingRun.started_at.desc())
            .all()
        )

    def get_failed_runs(self) -> list[ProcessingRun]:
        """Get all failed processing runs.

        Returns:
            List of failed ProcessingRun instances
        """
        return (
            self.session.query(ProcessingRun)
            .filter_by(status="FAILED")
            .order_by(ProcessingRun.started_at.desc())
            .all()
        )

    def get_in_progress_runs(self) -> list[ProcessingRun]:
        """Get all in-progress processing runs.

        Returns:
            List of in-progress ProcessingRun instances
        """
        return (
            self.session.query(ProcessingRun)
            .filter_by(status="IN_PROGRESS")
            .order_by(ProcessingRun.started_at.desc())
            .all()
        )

    def cleanup_old_runs(self, days_to_keep: int = 90) -> int:
        """Clean up old processing runs.

        Args:
            days_to_keep: Number of days to keep runs

        Returns:
            Number of runs deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        deleted_count = (
            self.session.query(ProcessingRun)
            .filter(ProcessingRun.started_at < cutoff_date)
            .delete()
        )

        self.session.commit()

        if deleted_count > 0:
            self.logger.info(
                f"Cleaned up {deleted_count} processing runs older than {days_to_keep} days"
            )

        return deleted_count

    def get_processing_statistics(self) -> dict[str, Any]:
        """Get overall processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        from sqlalchemy import func

        # Get aggregate statistics
        stats = (
            self.session.query(
                func.count(ProcessingRun.run_id).label("total_runs"),
                func.sum(ProcessingRun.files_count).label("total_files"),
                func.sum(ProcessingRun.pages_count).label("total_pages"),
                func.sum(ProcessingRun.tickets_created).label("total_tickets_created"),
                func.sum(ProcessingRun.tickets_updated).label("total_tickets_updated"),
                func.sum(ProcessingRun.duplicates_found).label("total_duplicates"),
                func.sum(ProcessingRun.review_queue_count).label("total_review_items"),
                func.sum(ProcessingRun.error_count).label("total_errors"),
                func.avg(ProcessingRun.pages_count).label("avg_pages_per_run"),
            )
            .filter(ProcessingRun.status == "COMPLETED")
            .first()
        )

        # Count by status
        status_counts = (
            self.session.query(
                ProcessingRun.status,
                func.count(ProcessingRun.run_id).label("count"),
            )
            .group_by(ProcessingRun.status)
            .all()
        )

        return {
            "total_runs": stats.total_runs or 0,
            "total_files": stats.total_files or 0,
            "total_pages": stats.total_pages or 0,
            "total_tickets_created": stats.total_tickets_created or 0,
            "total_tickets_updated": stats.total_tickets_updated or 0,
            "total_duplicates": stats.total_duplicates or 0,
            "total_review_items": stats.total_review_items or 0,
            "total_errors": stats.total_errors or 0,
            "avg_pages_per_run": float(stats.avg_pages_per_run or 0),
            "status_counts": dict(status_counts),
        }

    def _log_run_summary(self, processing_run: ProcessingRun):
        """Log summary of processing run results."""
        self.logger.info("=" * 60)
        self.logger.info("PROCESSING RUN SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Run ID: {processing_run.request_guid}")
        self.logger.info(f"Status: {processing_run.status}")
        self.logger.info(f"Duration: {processing_run.duration_seconds}s")
        self.logger.info(f"Files Processed: {processing_run.files_count or 0}")
        self.logger.info(f"Pages Processed: {processing_run.pages_count or 0}")
        self.logger.info(f"Tickets Created: {processing_run.tickets_created or 0}")
        self.logger.info(f"Tickets Updated: {processing_run.tickets_updated or 0}")
        self.logger.info(f"Duplicates Found: {processing_run.duplicates_found or 0}")
        self.logger.info(
            f"Review Queue Items: {processing_run.review_queue_count or 0}"
        )
        self.logger.info(f"Errors: {processing_run.error_count or 0}")

        if processing_run.success_rate is not None:
            self.logger.info(f"Success Rate: {processing_run.success_rate:.1%}")

        self.logger.info("=" * 60)
