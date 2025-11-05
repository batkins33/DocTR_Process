"""Duplicate ticket detection with 120-day rolling window.

This module implements the critical duplicate detection logic required by spec v1.1.
Prevents double-entry of tickets by checking for existing records with matching
(ticket_number, vendor_id) within a 120-day window.

Compliance Note:
    Duplicate detection is critical for invoice matching accuracy and preventing
    double-billing. All potential duplicates must be routed to review queue.

Business Rules:
    - Primary key: (ticket_number, vendor_id)
    - Rolling window: 120 days before ticket_date
    - Action on duplicate: Mark as duplicate, set review_required=True
    - Store reference: duplicate_of = original_ticket_id
"""

from datetime import date, timedelta

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..models.sql_processing import ReviewQueue
from ..models.sql_truck_ticket import TruckTicket


class DuplicateDetectionResult:
    """Result of duplicate detection check.

    Attributes:
        is_duplicate: Whether a duplicate was found
        original_ticket_id: ID of the original ticket if duplicate found
        original_ticket_date: Date of the original ticket
        original_file_id: File path of the original ticket
        days_apart: Number of days between original and new ticket
        confidence: Confidence score of duplicate match (0.0-1.0)
    """

    def __init__(
        self,
        is_duplicate: bool,
        original_ticket_id: int | None = None,
        original_ticket_date: date | None = None,
        original_file_id: str | None = None,
        days_apart: int | None = None,
        confidence: float = 1.0,
    ):
        self.is_duplicate = is_duplicate
        self.original_ticket_id = original_ticket_id
        self.original_ticket_date = original_ticket_date
        self.original_file_id = original_file_id
        self.days_apart = days_apart
        self.confidence = confidence

    def __repr__(self) -> str:
        if self.is_duplicate:
            return (
                f"<DuplicateDetectionResult(is_duplicate=True, "
                f"original_id={self.original_ticket_id}, "
                f"days_apart={self.days_apart})>"
            )
        return "<DuplicateDetectionResult(is_duplicate=False)>"


class DuplicateDetector:
    """Detects duplicate tickets using 120-day rolling window.

    This class implements the duplicate detection strategy defined in spec v1.1:
    - Check for existing ticket with same (ticket_number, vendor_id)
    - Within rolling 120-day window before current ticket date
    - If found: Mark as duplicate and route to review queue

    Example:
        ```python
        detector = DuplicateDetector(session)
        result = detector.check_duplicate(
            ticket_number="WM-12345678",
            vendor_id=1,
            ticket_date=date(2024, 10, 17)
        )

        if result.is_duplicate:
            print(f"Duplicate found! Original: {result.original_ticket_id}")
            print(f"Days apart: {result.days_apart}")
        ```

    Attributes:
        session: SQLAlchemy database session
        window_days: Number of days for rolling window (default: 120)
    """

    def __init__(self, session: Session, window_days: int = 120):
        """Initialize duplicate detector.

        Args:
            session: SQLAlchemy database session
            window_days: Number of days for rolling window (default: 120)
        """
        self.session = session
        self.window_days = window_days

    def check_duplicate(
        self, ticket_number: str, vendor_id: int | None, ticket_date: date
    ) -> DuplicateDetectionResult:
        """Check if ticket is a duplicate within rolling window.

        Queries database for existing ticket with matching (ticket_number, vendor_id)
        within the rolling window period. The window extends from (ticket_date - window_days)
        to ticket_date.

        Args:
            ticket_number: Ticket number to check (e.g., "WM-12345678")
            vendor_id: Vendor ID (can be None if vendor unknown)
            ticket_date: Date of the ticket being checked

        Returns:
            DuplicateDetectionResult with is_duplicate=True if match found

        Example:
            ```python
            result = detector.check_duplicate(
                ticket_number="WM-12345678",
                vendor_id=1,
                ticket_date=date(2024, 10, 17)
            )
            ```
        """
        # Calculate window boundaries
        window_start = ticket_date - timedelta(days=self.window_days)
        window_end = ticket_date

        # Build query for duplicate check
        query = select(TruckTicket).where(
            and_(
                TruckTicket.ticket_number == ticket_number,
                TruckTicket.ticket_date >= window_start,
                TruckTicket.ticket_date <= window_end,
                TruckTicket.duplicate_of.is_(None),  # Only check against originals
            )
        )

        # Add vendor filter if vendor is known
        if vendor_id is not None:
            query = query.where(TruckTicket.vendor_id == vendor_id)

        # Order by date to get the earliest occurrence
        query = query.order_by(TruckTicket.ticket_date.asc())

        # Execute query
        existing_ticket = self.session.execute(query).scalars().first()

        if existing_ticket:
            # Calculate days between tickets
            days_apart = (ticket_date - existing_ticket.ticket_date).days

            return DuplicateDetectionResult(
                is_duplicate=True,
                original_ticket_id=existing_ticket.ticket_id,
                original_ticket_date=existing_ticket.ticket_date,
                original_file_id=existing_ticket.file_id,
                days_apart=days_apart,
                confidence=1.0 if vendor_id is not None else 0.85,
            )

        return DuplicateDetectionResult(is_duplicate=False)

    def mark_as_duplicate(
        self,
        ticket_id: int,
        original_ticket_id: int,
        reason: str = "Duplicate ticket detected within 120-day window",
    ) -> None:
        """Mark a ticket as duplicate and set review flag.

        Updates the ticket record to:
        - Set duplicate_of = original_ticket_id
        - Set review_required = True
        - Set review_reason = reason

        Args:
            ticket_id: ID of the duplicate ticket to mark
            original_ticket_id: ID of the original ticket
            reason: Reason for marking as duplicate

        Example:
            ```python
            detector.mark_as_duplicate(
                ticket_id=456,
                original_ticket_id=123,
                reason="Duplicate ticket - same number and vendor"
            )
            ```
        """
        ticket = self.session.get(TruckTicket, ticket_id)
        if ticket:
            ticket.duplicate_of = original_ticket_id
            ticket.review_required = True
            ticket.review_reason = reason
            self.session.commit()

    def create_review_queue_entry(
        self,
        ticket_id: int,
        original_ticket_id: int,
        detected_fields: dict | None = None,
        suggested_fixes: dict | None = None,
    ) -> ReviewQueue:
        """Create review queue entry for duplicate ticket.

        Routes the duplicate ticket to the review queue with WARNING severity.
        Includes details about both the original and duplicate tickets for
        manual review.

        Args:
            ticket_id: ID of the duplicate ticket
            original_ticket_id: ID of the original ticket
            detected_fields: Dictionary of detected field values (optional)
            suggested_fixes: Dictionary of suggested corrections (optional)

        Returns:
            Created ReviewQueue entry

        Example:
            ```python
            review_entry = detector.create_review_queue_entry(
                ticket_id=456,
                original_ticket_id=123,
                detected_fields={
                    "ticket_number": "WM-12345678",
                    "ticket_date": "2024-10-17",
                    "vendor": "Waste Management"
                },
                suggested_fixes={
                    "action": "Verify if re-scan or legitimate duplicate load"
                }
            )
            ```
        """
        import json

        # Get both tickets for context
        duplicate_ticket = self.session.get(TruckTicket, ticket_id)
        original_ticket = self.session.get(TruckTicket, original_ticket_id)

        if not duplicate_ticket or not original_ticket:
            raise ValueError("Ticket IDs not found in database")

        # Build detected fields JSON
        if detected_fields is None:
            detected_fields = {
                "ticket_number": duplicate_ticket.ticket_number,
                "ticket_date": str(duplicate_ticket.ticket_date),
                "vendor_id": duplicate_ticket.vendor_id,
                "quantity": (
                    float(duplicate_ticket.quantity)
                    if duplicate_ticket.quantity
                    else None
                ),
                "file_id": duplicate_ticket.file_id,
            }

        # Build suggested fixes JSON
        if suggested_fixes is None:
            days_apart = (
                duplicate_ticket.ticket_date - original_ticket.ticket_date
            ).days
            suggested_fixes = {
                "original_ticket_id": original_ticket_id,
                "original_date": str(original_ticket.ticket_date),
                "original_file": original_ticket.file_id,
                "days_apart": days_apart,
                "action": "Verify if re-scan or legitimate duplicate load",
                "note": f"Same ticket number found {days_apart} days earlier",
            }

        # Create review queue entry
        review_entry = ReviewQueue(
            ticket_id=ticket_id,
            page_id=f"{duplicate_ticket.file_id}#page{duplicate_ticket.file_page or 1}",
            reason="DUPLICATE_TICKET",
            severity="WARNING",
            file_path=duplicate_ticket.file_id,
            page_num=duplicate_ticket.file_page,
            detected_fields=json.dumps(detected_fields),
            suggested_fixes=json.dumps(suggested_fixes),
            resolved=False,
        )

        self.session.add(review_entry)
        self.session.commit()

        return review_entry

    def check_and_handle_duplicate(
        self,
        ticket_number: str,
        vendor_id: int | None,
        ticket_date: date,
        ticket_id: int | None = None,
    ) -> DuplicateDetectionResult:
        """Check for duplicate and automatically handle if found.

        This is a convenience method that combines check_duplicate(),
        mark_as_duplicate(), and create_review_queue_entry() into a single call.

        If a duplicate is found:
        1. Marks the ticket as duplicate
        2. Creates review queue entry
        3. Returns detection result

        Args:
            ticket_number: Ticket number to check
            vendor_id: Vendor ID (can be None)
            ticket_date: Date of the ticket
            ticket_id: ID of the ticket being checked (required if duplicate found)

        Returns:
            DuplicateDetectionResult

        Example:
            ```python
            result = detector.check_and_handle_duplicate(
                ticket_number="WM-12345678",
                vendor_id=1,
                ticket_date=date(2024, 10, 17),
                ticket_id=456
            )

            if result.is_duplicate:
                print(f"Duplicate handled! Routed to review queue.")
            ```
        """
        result = self.check_duplicate(ticket_number, vendor_id, ticket_date)

        if result.is_duplicate and ticket_id is not None:
            # Mark as duplicate
            self.mark_as_duplicate(
                ticket_id=ticket_id,
                original_ticket_id=result.original_ticket_id,
                reason=f"Duplicate ticket detected ({result.days_apart} days after original)",
            )

            # Create review queue entry
            self.create_review_queue_entry(
                ticket_id=ticket_id, original_ticket_id=result.original_ticket_id
            )

        return result

    def get_duplicate_statistics(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> dict:
        """Get statistics about duplicate detection.

        Returns counts and metrics about duplicates found in the system.
        Useful for monitoring and reporting.

        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dictionary with duplicate statistics

        Example:
            ```python
            stats = detector.get_duplicate_statistics(
                start_date=date(2024, 10, 1),
                end_date=date(2024, 10, 31)
            )
            print(f"Duplicates found: {stats['total_duplicates']}")
            print(f"Duplicate rate: {stats['duplicate_rate']:.2%}")
            ```
        """
        from sqlalchemy import func

        # Build base query
        query = select(func.count(TruckTicket.ticket_id))

        if start_date:
            query = query.where(TruckTicket.ticket_date >= start_date)
        if end_date:
            query = query.where(TruckTicket.ticket_date <= end_date)

        # Get total tickets
        total_tickets = self.session.execute(query).scalar() or 0

        # Get duplicate count
        duplicate_query = query.where(TruckTicket.duplicate_of.isnot(None))
        total_duplicates = self.session.execute(duplicate_query).scalar() or 0

        # Calculate rate
        duplicate_rate = total_duplicates / total_tickets if total_tickets > 0 else 0.0

        return {
            "total_tickets": total_tickets,
            "total_duplicates": total_duplicates,
            "unique_tickets": total_tickets - total_duplicates,
            "duplicate_rate": duplicate_rate,
            "window_days": self.window_days,
            "start_date": start_date,
            "end_date": end_date,
        }
