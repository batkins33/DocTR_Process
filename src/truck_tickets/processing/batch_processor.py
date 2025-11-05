"""Batch processing with error recovery and thread pool management.

Issue #24: Batch Processing with Error Recovery
Implements multi-threaded PDF processing with graceful error handling,
progress tracking, and rollback capabilities.
"""

import logging
import os
import time
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..database.processing_run_ledger import ProcessingRunLedger
from .ticket_processor import ProcessingResult, TicketProcessor


@dataclass
class BatchConfig:
    """Configuration for batch processing operations."""

    max_workers: int | None = None  # None = CPU count
    chunk_size: int = 10  # Files per batch
    timeout_seconds: int = 300  # 5 minutes per file
    retry_attempts: int = 2
    continue_on_error: bool = True
    rollback_on_critical: bool = True
    progress_callback: Callable[[int, int], None] | None = None


@dataclass
class FileProcessingResult:
    """Result of processing a single file."""

    file_path: str
    success: bool
    pages_processed: int = 0
    tickets_created: int = 0
    tickets_updated: int = 0
    duplicates_found: int = 0
    review_queue_count: int = 0
    error_count: int = 0
    error_message: str | None = None
    processing_time: float = 0.0
    page_results: list[ProcessingResult] = field(default_factory=list)


@dataclass
class BatchProcessingResult:
    """Result of batch processing operation."""

    request_guid: str
    started_at: datetime
    completed_at: datetime | None = None
    total_files: int = 0
    files_processed: int = 0
    files_failed: int = 0
    total_pages: int = 0
    tickets_created: int = 0
    tickets_updated: int = 0
    duplicates_found: int = 0
    review_queue_count: int = 0
    error_count: int = 0
    file_results: list[FileProcessingResult] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    status: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, FAILED, PARTIAL

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_files == 0:
            return 0.0
        return (self.files_processed / self.total_files) * 100

    @property
    def duration_seconds(self) -> float:
        """Calculate total processing duration."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (datetime.now() - self.started_at).total_seconds()


class BatchProcessor:
    """Manages batch processing of PDF files with error recovery.

    Features:
    - Multi-threaded processing with configurable thread pool
    - Graceful error handling and recovery
    - Progress tracking and reporting
    - Automatic retry on transient failures
    - Rollback on critical errors
    - Integration with ProcessingRunLedger for audit trail

    Example:
        ```python
        processor = BatchProcessor(session, job_code="24-105")

        # Configure batch processing
        config = BatchConfig(
            max_workers=6,
            continue_on_error=True,
            progress_callback=lambda done, total: print(f"{done}/{total}")
        )

        # Process directory
        result = processor.process_directory(
            input_path="/path/to/pdfs",
            config=config
        )

        print(f"Processed {result.files_processed}/{result.total_files} files")
        print(f"Success rate: {result.success_rate:.1f}%")
        ```
    """

    def __init__(
        self,
        session: Session,
        job_code: str = "24-105",
        ticket_type: str = "EXPORT",
        processed_by: str | None = None,
    ):
        """Initialize batch processor.

        Args:
            session: SQLAlchemy database session
            job_code: Job code for tickets
            ticket_type: Ticket type (EXPORT or IMPORT)
            processed_by: User/process identifier for audit trail
        """
        self.session = session
        self.job_code = job_code
        self.ticket_type = ticket_type
        self.processed_by = processed_by or f"BatchProcessor-{os.getpid()}"
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.ticket_processor = TicketProcessor(session, job_code, ticket_type)
        self.ledger = ProcessingRunLedger(session)

    def process_directory(
        self,
        input_path: str | Path,
        config: BatchConfig | None = None,
        file_pattern: str = "*.pdf",
    ) -> BatchProcessingResult:
        """Process all PDF files in a directory.

        Args:
            input_path: Path to directory containing PDFs
            config: Batch processing configuration
            file_pattern: Glob pattern for files (default: *.pdf)

        Returns:
            BatchProcessingResult with comprehensive statistics

        Raises:
            ValueError: If input path doesn't exist
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise ValueError(f"Input path does not exist: {input_path}")

        config = config or BatchConfig()

        # Find all PDF files
        pdf_files = list(input_path.rglob(file_pattern))
        if not pdf_files:
            self.logger.warning(
                f"No files matching '{file_pattern}' found in {input_path}"
            )
            return self._create_empty_result()

        self.logger.info(f"Found {len(pdf_files)} files to process")

        # Start processing run in ledger
        request_guid = str(uuid.uuid4())
        config_snapshot = {
            "input_path": str(input_path),
            "file_pattern": file_pattern,
            "max_workers": config.max_workers or os.cpu_count(),
            "chunk_size": config.chunk_size,
            "job_code": self.job_code,
            "ticket_type": self.ticket_type,
        }

        self.ledger.start_run(
            processed_by=self.processed_by,
            config_snapshot=config_snapshot,
            request_guid=request_guid,
        )

        # Initialize result
        result = BatchProcessingResult(
            request_guid=request_guid,
            started_at=datetime.now(),
            total_files=len(pdf_files),
        )

        try:
            # Process files in parallel
            result = self._process_files_parallel(pdf_files, config, result)

            # Determine final status
            if result.files_failed == 0:
                result.status = "COMPLETED"
            elif result.files_processed > 0:
                result.status = "PARTIAL"
            else:
                result.status = "FAILED"

            # Complete processing run in ledger
            self.ledger.complete_run(
                request_guid=request_guid,
                status=result.status,
                final_stats={
                    "files_count": result.files_processed,
                    "pages_count": result.total_pages,
                    "tickets_created": result.tickets_created,
                    "tickets_updated": result.tickets_updated,
                    "duplicates_found": result.duplicates_found,
                    "review_queue_count": result.review_queue_count,
                    "error_count": result.error_count,
                },
            )

        except Exception as e:
            self.logger.error(f"Critical error in batch processing: {e}", exc_info=True)
            result.status = "FAILED"
            result.errors.append(
                {
                    "type": "CRITICAL_ERROR",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Mark run as failed
            self.ledger.fail_run(request_guid, error_message=str(e))

            # Rollback if configured
            if config.rollback_on_critical:
                self.logger.warning(
                    "Rolling back database changes due to critical error"
                )
                self.session.rollback()
            else:
                self.session.commit()

        finally:
            result.completed_at = datetime.now()

        return result

    def _process_files_parallel(
        self,
        pdf_files: list[Path],
        config: BatchConfig,
        result: BatchProcessingResult,
    ) -> BatchProcessingResult:
        """Process files in parallel using thread pool.

        Args:
            pdf_files: List of PDF file paths
            config: Batch configuration
            result: Result object to update

        Returns:
            Updated BatchProcessingResult
        """
        max_workers = config.max_workers or os.cpu_count()
        self.logger.info(f"Starting parallel processing with {max_workers} workers")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all files for processing
            future_to_file = {
                executor.submit(self._process_single_file, pdf_file, config): pdf_file
                for pdf_file in pdf_files
            }

            # Process completed files
            completed = 0
            for future in as_completed(future_to_file):
                pdf_file = future_to_file[future]
                completed += 1

                try:
                    file_result = future.result(timeout=config.timeout_seconds)
                    result.file_results.append(file_result)

                    # Update statistics
                    if file_result.success:
                        result.files_processed += 1
                        result.total_pages += file_result.pages_processed
                        result.tickets_created += file_result.tickets_created
                        result.tickets_updated += file_result.tickets_updated
                        result.duplicates_found += file_result.duplicates_found
                        result.review_queue_count += file_result.review_queue_count
                        result.error_count += file_result.error_count
                    else:
                        result.files_failed += 1
                        result.error_count += 1
                        result.errors.append(
                            {
                                "file": str(pdf_file),
                                "error": file_result.error_message,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )

                    # Report progress
                    if config.progress_callback:
                        config.progress_callback(completed, len(pdf_files))

                    # Log progress
                    if completed % 10 == 0 or completed == len(pdf_files):
                        self.logger.info(
                            f"Progress: {completed}/{len(pdf_files)} files "
                            f"({result.files_processed} successful, {result.files_failed} failed)"
                        )

                except TimeoutError:
                    self.logger.error(f"Timeout processing {pdf_file}")
                    result.files_failed += 1
                    result.errors.append(
                        {
                            "file": str(pdf_file),
                            "error": "Processing timeout",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                except Exception as e:
                    self.logger.error(
                        f"Error processing {pdf_file}: {e}", exc_info=True
                    )
                    result.files_failed += 1
                    result.errors.append(
                        {
                            "file": str(pdf_file),
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    if not config.continue_on_error:
                        self.logger.error("Stopping batch processing due to error")
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

        return result

    def _process_single_file(
        self, pdf_file: Path, config: BatchConfig
    ) -> FileProcessingResult:
        """Process a single PDF file with retry logic.

        Args:
            pdf_file: Path to PDF file
            config: Batch configuration

        Returns:
            FileProcessingResult
        """
        start_time = time.time()
        file_result = FileProcessingResult(file_path=str(pdf_file), success=False)

        for attempt in range(config.retry_attempts + 1):
            try:
                self.logger.debug(f"Processing {pdf_file.name} (attempt {attempt + 1})")

                # Process PDF with TicketProcessor
                page_results = self.ticket_processor.process_pdf(str(pdf_file))

                # Aggregate results
                file_result.success = True
                file_result.pages_processed = len(page_results)
                file_result.page_results = page_results

                # Count outcomes
                for page_result in page_results:
                    if page_result.success:
                        if page_result.ticket_id:
                            file_result.tickets_created += 1
                        if page_result.duplicate_of:
                            file_result.duplicates_found += 1
                    else:
                        file_result.error_count += 1
                        if page_result.review_queue_id:
                            file_result.review_queue_count += 1

                file_result.processing_time = time.time() - start_time

                self.logger.info(
                    f"✓ Successfully processed {pdf_file.name}: "
                    f"{file_result.pages_processed} pages, "
                    f"{file_result.tickets_created} tickets"
                )
                break

            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1}/{config.retry_attempts + 1} failed for {pdf_file.name}: {e}"
                )

                if attempt == config.retry_attempts:
                    # Final attempt failed
                    file_result.success = False
                    file_result.error_message = str(e)
                    file_result.error_count = 1
                    file_result.processing_time = time.time() - start_time
                    self.logger.error(
                        f"✗ Failed to process {pdf_file.name} after {config.retry_attempts + 1} attempts"
                    )
                else:
                    # Wait before retry
                    time.sleep(1 * (attempt + 1))  # Exponential backoff

        return file_result

    def _create_empty_result(self) -> BatchProcessingResult:
        """Create an empty result for when no files are found."""
        return BatchProcessingResult(
            request_guid=str(uuid.uuid4()),
            started_at=datetime.now(),
            completed_at=datetime.now(),
            status="COMPLETED",
        )

    def get_processing_statistics(self) -> dict[str, Any]:
        """Get overall processing statistics from ledger.

        Returns:
            Dictionary with processing statistics
        """
        return self.ledger.get_processing_statistics()
