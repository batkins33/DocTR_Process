"""File tracking service for duplicate file detection.

This module provides services to track which files have been processed
and detect duplicate file processing based on SHA-256 hash.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.sql_truck_ticket import TruckTicket
from ..utils.file_hash import calculate_file_hash

logger = logging.getLogger(__name__)


@dataclass
class FileProcessingRecord:
    """Record of a previously processed file."""

    file_hash: str
    file_path: str
    first_processed: datetime
    last_processed: datetime
    ticket_count: int
    ticket_ids: list[int]


@dataclass
class DuplicateFileResult:
    """Result of duplicate file detection."""

    is_duplicate: bool
    file_hash: str
    original_file_path: str | None = None
    original_processing_date: datetime | None = None
    ticket_count: int = 0
    ticket_ids: list[int] | None = None

    @property
    def message(self) -> str:
        """Get human-readable message about duplicate status."""
        if not self.is_duplicate:
            return "File has not been processed before"

        return (
            f"Duplicate file detected! "
            f"Original: {self.original_file_path} "
            f"(processed {self.original_processing_date}, "
            f"{self.ticket_count} tickets created)"
        )


class FileTracker:
    """Service for tracking processed files and detecting duplicates.

    This service uses SHA-256 file hashes to:
    1. Detect when the same file is processed multiple times
    2. Track which files have been processed
    3. Prevent duplicate data entry from reprocessed files

    Example:
        ```python
        tracker = FileTracker(session)

        # Check if file has been processed
        result = tracker.check_duplicate_file("invoice.pdf")

        if result.is_duplicate:
            print(f"File already processed: {result.message}")
            print(f"Original tickets: {result.ticket_ids}")
        else:
            # Process the file
            process_pdf("invoice.pdf")
        ```
    """

    def __init__(self, session: Session):
        """Initialize file tracker.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session

    def check_duplicate_file(
        self,
        file_path: str | Path,
        file_hash: str | None = None,
    ) -> DuplicateFileResult:
        """Check if a file has been processed before.

        Args:
            file_path: Path to file to check
            file_hash: Optional pre-calculated hash (calculates if None)

        Returns:
            DuplicateFileResult indicating if file is a duplicate

        Example:
            ```python
            result = tracker.check_duplicate_file("invoice.pdf")

            if result.is_duplicate:
                print(f"Already processed: {result.ticket_count} tickets")
            ```
        """
        # Calculate hash if not provided
        if file_hash is None:
            try:
                file_hash = calculate_file_hash(file_path)
            except Exception as e:
                logger.error(f"Error calculating hash for {file_path}: {e}")
                return DuplicateFileResult(
                    is_duplicate=False,
                    file_hash="",
                )

        # Query for existing tickets with this hash
        query = select(TruckTicket).where(TruckTicket.file_hash == file_hash)
        existing_tickets = list(self.session.execute(query).scalars().all())

        if not existing_tickets:
            return DuplicateFileResult(
                is_duplicate=False,
                file_hash=file_hash,
            )

        # File has been processed before
        ticket_ids = [t.ticket_id for t in existing_tickets]
        first_ticket = min(existing_tickets, key=lambda t: t.created_at)

        return DuplicateFileResult(
            is_duplicate=True,
            file_hash=file_hash,
            original_file_path=first_ticket.file_id,
            original_processing_date=first_ticket.created_at,
            ticket_count=len(existing_tickets),
            ticket_ids=ticket_ids,
        )

    def get_file_processing_record(
        self,
        file_hash: str,
    ) -> FileProcessingRecord | None:
        """Get processing record for a file by hash.

        Args:
            file_hash: SHA-256 hash of file

        Returns:
            FileProcessingRecord if file has been processed, None otherwise

        Example:
            ```python
            record = tracker.get_file_processing_record(hash_value)

            if record:
                print(f"File processed {record.ticket_count} times")
                print(f"First: {record.first_processed}")
                print(f"Last: {record.last_processed}")
            ```
        """
        query = select(TruckTicket).where(TruckTicket.file_hash == file_hash)
        tickets = list(self.session.execute(query).scalars().all())

        if not tickets:
            return None

        ticket_ids = [t.ticket_id for t in tickets]
        created_dates = [t.created_at for t in tickets]

        return FileProcessingRecord(
            file_hash=file_hash,
            file_path=tickets[0].file_id or "",
            first_processed=min(created_dates),
            last_processed=max(created_dates),
            ticket_count=len(tickets),
            ticket_ids=ticket_ids,
        )

    def get_all_processed_files(self) -> list[FileProcessingRecord]:
        """Get records of all processed files.

        Returns:
            List of FileProcessingRecord for all unique files processed

        Example:
            ```python
            files = tracker.get_all_processed_files()

            for file in files:
                print(f"{file.file_path}: {file.ticket_count} tickets")
            ```
        """
        # Get all unique file hashes
        query = (
            select(TruckTicket.file_hash)
            .where(TruckTicket.file_hash.isnot(None))
            .distinct()
        )

        file_hashes = [row[0] for row in self.session.execute(query).all()]

        # Get processing record for each hash
        records = []
        for file_hash in file_hashes:
            record = self.get_file_processing_record(file_hash)
            if record:
                records.append(record)

        return records

    def get_processing_statistics(self) -> dict:
        """Get statistics about file processing.

        Returns:
            Dictionary with processing statistics:
            - total_files: Number of unique files processed
            - total_tickets: Total tickets created
            - avg_tickets_per_file: Average tickets per file
            - files_with_duplicates: Number of files processed multiple times

        Example:
            ```python
            stats = tracker.get_processing_statistics()

            print(f"Files processed: {stats['total_files']}")
            print(f"Total tickets: {stats['total_tickets']}")
            print(f"Avg per file: {stats['avg_tickets_per_file']:.1f}")
            ```
        """
        # Count unique files
        unique_files_query = select(
            func.count(func.distinct(TruckTicket.file_hash))
        ).where(TruckTicket.file_hash.isnot(None))
        total_files = self.session.execute(unique_files_query).scalar() or 0

        # Count total tickets with file hash
        total_tickets_query = select(func.count(TruckTicket.ticket_id)).where(
            TruckTicket.file_hash.isnot(None)
        )
        total_tickets = self.session.execute(total_tickets_query).scalar() or 0

        # Calculate average
        avg_tickets_per_file = total_tickets / total_files if total_files > 0 else 0

        # Find files processed multiple times
        # (This is a simplified check - could be enhanced)
        records = self.get_all_processed_files()
        files_with_duplicates = sum(1 for r in records if r.ticket_count > 1)

        return {
            "total_files": total_files,
            "total_tickets": total_tickets,
            "avg_tickets_per_file": avg_tickets_per_file,
            "files_with_duplicates": files_with_duplicates,
        }
