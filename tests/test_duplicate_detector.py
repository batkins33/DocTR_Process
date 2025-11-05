"""Comprehensive tests for duplicate detection logic.

Tests the 120-day rolling window duplicate detection as specified in v1.1.
Critical for compliance and invoice matching accuracy.
"""

from datetime import date, timedelta
from unittest.mock import Mock

import pytest
from src.truck_tickets.database.duplicate_detector import (
    DuplicateDetectionResult,
    DuplicateDetector,
)
from src.truck_tickets.models.sql_processing import ReviewQueue
from src.truck_tickets.models.sql_truck_ticket import TruckTicket


class TestDuplicateDetectionResult:
    """Test DuplicateDetectionResult data class."""

    def test_not_duplicate(self):
        """Test result for non-duplicate ticket."""
        result = DuplicateDetectionResult(is_duplicate=False)

        assert not result.is_duplicate
        assert result.original_ticket_id is None
        assert result.original_ticket_date is None
        assert result.days_apart is None
        assert result.confidence == 1.0

    def test_duplicate_found(self):
        """Test result when duplicate is found."""
        result = DuplicateDetectionResult(
            is_duplicate=True,
            original_ticket_id=123,
            original_ticket_date=date(2024, 10, 1),
            original_file_id="batch1/file1.pdf",
            days_apart=15,
            confidence=1.0,
        )

        assert result.is_duplicate
        assert result.original_ticket_id == 123
        assert result.original_ticket_date == date(2024, 10, 1)
        assert result.original_file_id == "batch1/file1.pdf"
        assert result.days_apart == 15
        assert result.confidence == 1.0

    def test_repr_not_duplicate(self):
        """Test string representation for non-duplicate."""
        result = DuplicateDetectionResult(is_duplicate=False)
        repr_str = repr(result)

        assert "is_duplicate=False" in repr_str

    def test_repr_duplicate(self):
        """Test string representation for duplicate."""
        result = DuplicateDetectionResult(
            is_duplicate=True, original_ticket_id=123, days_apart=15
        )
        repr_str = repr(result)

        assert "is_duplicate=True" in repr_str
        assert "original_id=123" in repr_str
        assert "days_apart=15" in repr_str


class TestDuplicateDetector:
    """Test DuplicateDetector class."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock()
        session.execute = Mock()
        session.get = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session

    @pytest.fixture
    def detector(self, mock_session):
        """Create DuplicateDetector instance with mock session."""
        return DuplicateDetector(mock_session, window_days=120)

    def test_init_default_window(self, mock_session):
        """Test initialization with default 120-day window."""
        detector = DuplicateDetector(mock_session)

        assert detector.session == mock_session
        assert detector.window_days == 120

    def test_init_custom_window(self, mock_session):
        """Test initialization with custom window."""
        detector = DuplicateDetector(mock_session, window_days=90)

        assert detector.window_days == 90

    def test_check_duplicate_not_found(self, detector, mock_session):
        """Test check_duplicate when no duplicate exists."""
        # Mock query result - no existing ticket
        mock_result = Mock()
        mock_result.scalars().first.return_value = None
        mock_session.execute.return_value = mock_result

        result = detector.check_duplicate(
            ticket_number="WM-12345678", vendor_id=1, ticket_date=date(2024, 10, 17)
        )

        assert not result.is_duplicate
        assert result.original_ticket_id is None
        assert mock_session.execute.called

    def test_check_duplicate_found_same_vendor(self, detector, mock_session):
        """Test check_duplicate when duplicate found with same vendor."""
        # Create mock existing ticket
        existing_ticket = Mock(spec=TruckTicket)
        existing_ticket.ticket_id = 123
        existing_ticket.ticket_date = date(2024, 10, 1)
        existing_ticket.file_id = "batch1/file1.pdf"

        # Mock query result
        mock_result = Mock()
        mock_result.scalars().first.return_value = existing_ticket
        mock_session.execute.return_value = mock_result

        result = detector.check_duplicate(
            ticket_number="WM-12345678", vendor_id=1, ticket_date=date(2024, 10, 17)
        )

        assert result.is_duplicate
        assert result.original_ticket_id == 123
        assert result.original_ticket_date == date(2024, 10, 1)
        assert result.original_file_id == "batch1/file1.pdf"
        assert result.days_apart == 16  # Oct 17 - Oct 1
        assert result.confidence == 1.0  # High confidence with vendor match

    def test_check_duplicate_found_no_vendor(self, detector, mock_session):
        """Test check_duplicate when duplicate found without vendor."""
        # Create mock existing ticket
        existing_ticket = Mock(spec=TruckTicket)
        existing_ticket.ticket_id = 123
        existing_ticket.ticket_date = date(2024, 10, 1)
        existing_ticket.file_id = "batch1/file1.pdf"

        # Mock query result
        mock_result = Mock()
        mock_result.scalars().first.return_value = existing_ticket
        mock_session.execute.return_value = mock_result

        result = detector.check_duplicate(
            ticket_number="WM-12345678",
            vendor_id=None,  # Vendor unknown
            ticket_date=date(2024, 10, 17),
        )

        assert result.is_duplicate
        assert result.confidence == 0.85  # Lower confidence without vendor

    def test_check_duplicate_window_boundaries(self, detector, mock_session):
        """Test that window boundaries are calculated correctly."""
        # Mock no duplicate found
        mock_result = Mock()
        mock_result.scalars().first.return_value = None
        mock_session.execute.return_value = mock_result

        ticket_date = date(2024, 10, 17)
        detector.check_duplicate(
            ticket_number="WM-12345678", vendor_id=1, ticket_date=ticket_date
        )

        # Verify window calculation
        expected_start = ticket_date - timedelta(days=120)
        assert expected_start == date(2024, 6, 19)  # 120 days before Oct 17

    def test_mark_as_duplicate(self, detector, mock_session):
        """Test marking a ticket as duplicate."""
        # Create mock ticket
        mock_ticket = Mock(spec=TruckTicket)
        mock_ticket.ticket_id = 456
        mock_session.get.return_value = mock_ticket

        detector.mark_as_duplicate(
            ticket_id=456, original_ticket_id=123, reason="Test duplicate"
        )

        assert mock_ticket.duplicate_of == 123
        assert mock_ticket.review_required is True
        assert mock_ticket.review_reason == "Test duplicate"
        assert mock_session.commit.called

    def test_mark_as_duplicate_ticket_not_found(self, detector, mock_session):
        """Test marking duplicate when ticket doesn't exist."""
        mock_session.get.return_value = None

        # Should not raise error, just do nothing
        detector.mark_as_duplicate(ticket_id=999, original_ticket_id=123)

        assert not mock_session.commit.called

    def test_create_review_queue_entry(self, detector, mock_session):
        """Test creating review queue entry for duplicate."""
        # Create mock tickets
        duplicate_ticket = Mock(spec=TruckTicket)
        duplicate_ticket.ticket_id = 456
        duplicate_ticket.ticket_number = "WM-12345678"
        duplicate_ticket.ticket_date = date(2024, 10, 17)
        duplicate_ticket.vendor_id = 1
        duplicate_ticket.quantity = 25.5
        duplicate_ticket.file_id = "batch2/file2.pdf"
        duplicate_ticket.file_page = 1

        original_ticket = Mock(spec=TruckTicket)
        original_ticket.ticket_id = 123
        original_ticket.ticket_date = date(2024, 10, 1)
        original_ticket.file_id = "batch1/file1.pdf"

        mock_session.get.side_effect = [duplicate_ticket, original_ticket]

        review_entry = detector.create_review_queue_entry(
            ticket_id=456, original_ticket_id=123
        )

        assert isinstance(review_entry, ReviewQueue)
        assert review_entry.ticket_id == 456
        assert review_entry.reason == "DUPLICATE_TICKET"
        assert review_entry.severity == "WARNING"
        assert review_entry.resolved is False
        assert mock_session.add.called
        assert mock_session.commit.called

    def test_create_review_queue_entry_invalid_ids(self, detector, mock_session):
        """Test creating review entry with invalid ticket IDs."""
        mock_session.get.return_value = None

        with pytest.raises(ValueError, match="Ticket IDs not found"):
            detector.create_review_queue_entry(ticket_id=999, original_ticket_id=888)

    def test_check_and_handle_duplicate_not_found(self, detector, mock_session):
        """Test check_and_handle when no duplicate exists."""
        # Mock no duplicate
        mock_result = Mock()
        mock_result.scalars().first.return_value = None
        mock_session.execute.return_value = mock_result

        result = detector.check_and_handle_duplicate(
            ticket_number="WM-12345678",
            vendor_id=1,
            ticket_date=date(2024, 10, 17),
            ticket_id=456,
        )

        assert not result.is_duplicate
        assert not mock_session.get.called  # Should not try to mark/create review

    def test_check_and_handle_duplicate_found(self, detector, mock_session):
        """Test check_and_handle when duplicate is found."""
        # Mock existing ticket
        existing_ticket = Mock(spec=TruckTicket)
        existing_ticket.ticket_id = 123
        existing_ticket.ticket_date = date(2024, 10, 1)
        existing_ticket.file_id = "batch1/file1.pdf"

        # Mock query result
        mock_result = Mock()
        mock_result.scalars().first.return_value = existing_ticket

        # Mock tickets for mark and review queue
        duplicate_ticket = Mock(spec=TruckTicket)
        duplicate_ticket.ticket_id = 456
        duplicate_ticket.ticket_number = "WM-12345678"
        duplicate_ticket.ticket_date = date(2024, 10, 17)
        duplicate_ticket.vendor_id = 1
        duplicate_ticket.quantity = 25.5
        duplicate_ticket.file_id = "batch2/file2.pdf"
        duplicate_ticket.file_page = 1

        mock_session.execute.return_value = mock_result
        mock_session.get.side_effect = [
            duplicate_ticket,
            duplicate_ticket,
            existing_ticket,
        ]

        result = detector.check_and_handle_duplicate(
            ticket_number="WM-12345678",
            vendor_id=1,
            ticket_date=date(2024, 10, 17),
            ticket_id=456,
        )

        assert result.is_duplicate
        assert result.original_ticket_id == 123
        assert mock_session.commit.called  # Should mark and create review

    def test_get_duplicate_statistics(self, detector, mock_session):
        """Test getting duplicate statistics."""
        # Mock total tickets count
        mock_total_result = Mock()
        mock_total_result.scalar.return_value = 100

        # Mock duplicates count
        mock_dup_result = Mock()
        mock_dup_result.scalar.return_value = 5

        mock_session.execute.side_effect = [mock_total_result, mock_dup_result]

        stats = detector.get_duplicate_statistics(
            start_date=date(2024, 10, 1), end_date=date(2024, 10, 31)
        )

        assert stats["total_tickets"] == 100
        assert stats["total_duplicates"] == 5
        assert stats["unique_tickets"] == 95
        assert stats["duplicate_rate"] == 0.05
        assert stats["window_days"] == 120

    def test_get_duplicate_statistics_no_tickets(self, detector, mock_session):
        """Test statistics when no tickets exist."""
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        stats = detector.get_duplicate_statistics()

        assert stats["total_tickets"] == 0
        assert stats["total_duplicates"] == 0
        assert stats["duplicate_rate"] == 0.0


class TestDuplicateDetectionEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def detector(self, mock_session):
        """Create detector instance."""
        return DuplicateDetector(mock_session)

    def test_exact_window_boundary(self, detector, mock_session):
        """Test duplicate detection at exact 120-day boundary."""
        existing_ticket = Mock(spec=TruckTicket)
        existing_ticket.ticket_id = 123
        existing_ticket.ticket_date = date(2024, 6, 19)  # Exactly 120 days before
        existing_ticket.file_id = "batch1/file1.pdf"

        mock_result = Mock()
        mock_result.scalars().first.return_value = existing_ticket
        mock_session.execute.return_value = mock_result

        result = detector.check_duplicate(
            ticket_number="WM-12345678",
            vendor_id=1,
            ticket_date=date(2024, 10, 17),  # 120 days after
        )

        assert result.is_duplicate
        assert result.days_apart == 120

    def test_outside_window(self, detector, mock_session):
        """Test that tickets outside window are not detected."""
        # Mock no result (outside window)
        mock_result = Mock()
        mock_result.scalars().first.return_value = None
        mock_session.execute.return_value = mock_result

        result = detector.check_duplicate(
            ticket_number="WM-12345678", vendor_id=1, ticket_date=date(2024, 10, 17)
        )

        assert not result.is_duplicate

    def test_same_day_duplicate(self, detector, mock_session):
        """Test duplicate on same day (0 days apart)."""
        existing_ticket = Mock(spec=TruckTicket)
        existing_ticket.ticket_id = 123
        existing_ticket.ticket_date = date(2024, 10, 17)
        existing_ticket.file_id = "batch1/file1.pdf"

        mock_result = Mock()
        mock_result.scalars().first.return_value = existing_ticket
        mock_session.execute.return_value = mock_result

        result = detector.check_duplicate(
            ticket_number="WM-12345678", vendor_id=1, ticket_date=date(2024, 10, 17)
        )

        assert result.is_duplicate
        assert result.days_apart == 0

    def test_different_ticket_number_same_vendor(self, detector, mock_session):
        """Test that different ticket numbers are not duplicates."""
        mock_result = Mock()
        mock_result.scalars().first.return_value = None
        mock_session.execute.return_value = mock_result

        result = detector.check_duplicate(
            ticket_number="WM-99999999",  # Different number
            vendor_id=1,
            ticket_date=date(2024, 10, 17),
        )

        assert not result.is_duplicate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
