"""Tests for file hash utilities and file tracking.

Tests cover:
1. SHA-256 hash calculation
2. Hash verification
3. File tracking and duplicate detection
4. Integration with TicketProcessor
"""

import pytest
from src.truck_tickets.database import FileTracker
from src.truck_tickets.utils import calculate_file_hash, get_file_info, verify_file_hash


class TestFileHashUtilities:
    """Test file hash utility functions."""

    def test_calculate_file_hash(self, tmp_path):
        """Test SHA-256 hash calculation."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        # Calculate hash
        hash_value = calculate_file_hash(test_file)

        # Verify hash format
        assert len(hash_value) == 64  # SHA-256 is 64 hex characters
        assert all(c in "0123456789abcdef" for c in hash_value.lower())

        # Verify hash is consistent
        hash_value2 = calculate_file_hash(test_file)
        assert hash_value == hash_value2

    def test_calculate_hash_different_files(self, tmp_path):
        """Test that different files produce different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("Content 1")
        file2.write_text("Content 2")

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 != hash2

    def test_calculate_hash_same_content(self, tmp_path):
        """Test that files with same content produce same hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        content = "Same content"
        file1.write_text(content)
        file2.write_text(content)

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        assert hash1 == hash2

    def test_calculate_hash_large_file(self, tmp_path):
        """Test hash calculation for large file (tests chunked reading)."""
        large_file = tmp_path / "large.bin"

        # Create 1MB file
        with open(large_file, "wb") as f:
            f.write(b"x" * (1024 * 1024))

        # Should handle large file without loading into memory
        hash_value = calculate_file_hash(large_file)

        assert len(hash_value) == 64

    def test_calculate_hash_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_file_hash("nonexistent.txt")

    def test_verify_file_hash_match(self, tmp_path):
        """Test hash verification with matching hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        expected_hash = calculate_file_hash(test_file)

        assert verify_file_hash(test_file, expected_hash) is True

    def test_verify_file_hash_mismatch(self, tmp_path):
        """Test hash verification with non-matching hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        wrong_hash = "0" * 64

        assert verify_file_hash(test_file, wrong_hash) is False

    def test_get_file_info(self, tmp_path):
        """Test getting file information."""
        test_file = tmp_path / "test.txt"
        content = "Test content"
        test_file.write_text(content)

        info = get_file_info(test_file)

        assert "path" in info
        assert "name" in info
        assert "size" in info
        assert "hash" in info
        assert "modified" in info

        assert info["name"] == "test.txt"
        assert info["size"] == len(content)
        assert len(info["hash"]) == 64


class TestFileTracker:
    """Test file tracking and duplicate detection."""

    def test_check_duplicate_file_new(self, session, tmp_path):
        """Test duplicate check for new file."""
        tracker = FileTracker(session)

        test_file = tmp_path / "new.pdf"
        test_file.write_text("New file content")

        result = tracker.check_duplicate_file(test_file)

        assert result.is_duplicate is False
        assert len(result.file_hash) == 64

    def test_check_duplicate_file_existing(self, session, sample_ticket, tmp_path):
        """Test duplicate check for existing file."""
        tracker = FileTracker(session)

        # Create file with known hash
        test_file = tmp_path / "existing.pdf"
        test_file.write_text("Existing content")
        file_hash = calculate_file_hash(test_file)

        # Update sample ticket with this hash
        sample_ticket.file_hash = file_hash
        sample_ticket.file_id = str(test_file)
        session.commit()

        # Check for duplicate
        result = tracker.check_duplicate_file(test_file)

        assert result.is_duplicate is True
        assert result.file_hash == file_hash
        assert result.original_file_path == str(test_file)
        assert result.ticket_count == 1
        assert sample_ticket.ticket_id in result.ticket_ids

    def test_get_file_processing_record(self, session, sample_ticket):
        """Test getting file processing record."""
        tracker = FileTracker(session)

        # Set hash on sample ticket
        file_hash = "a" * 64
        sample_ticket.file_hash = file_hash
        session.commit()

        # Get processing record
        record = tracker.get_file_processing_record(file_hash)

        assert record is not None
        assert record.file_hash == file_hash
        assert record.ticket_count == 1
        assert sample_ticket.ticket_id in record.ticket_ids

    def test_get_file_processing_record_not_found(self, session):
        """Test getting record for non-existent hash."""
        tracker = FileTracker(session)

        record = tracker.get_file_processing_record("nonexistent_hash")

        assert record is None

    def test_get_all_processed_files(self, session, sample_ticket):
        """Test getting all processed files."""
        tracker = FileTracker(session)

        # Set hash on sample ticket
        sample_ticket.file_hash = "a" * 64
        session.commit()

        # Get all files
        files = tracker.get_all_processed_files()

        assert len(files) >= 1
        assert any(f.file_hash == "a" * 64 for f in files)

    def test_get_processing_statistics(self, session, sample_ticket):
        """Test getting processing statistics."""
        tracker = FileTracker(session)

        # Set hash on sample ticket
        sample_ticket.file_hash = "b" * 64
        session.commit()

        # Get statistics
        stats = tracker.get_processing_statistics()

        assert "total_files" in stats
        assert "total_tickets" in stats
        assert "avg_tickets_per_file" in stats
        assert "files_with_duplicates" in stats

        assert stats["total_files"] >= 1
        assert stats["total_tickets"] >= 1


class TestTicketProcessorIntegration:
    """Test integration with TicketProcessor."""

    def test_process_pdf_with_duplicate_check(self, session, tmp_path):
        """Test PDF processing with duplicate file detection."""

        # This would require a real PDF file and full setup
        # Placeholder for integration test
        pytest.skip("Requires full PDF processing setup")

    def test_duplicate_file_prevented(self, session):
        """Test that duplicate file processing is prevented."""
        # Placeholder for integration test
        pytest.skip("Requires full PDF processing setup")


# Fixtures


@pytest.fixture
def sample_ticket(session):
    """Create a sample ticket for testing."""
    from datetime import date

    from src.truck_tickets.models.sql_truck_ticket import TruckTicket

    ticket = TruckTicket(
        ticket_number="TEST-001",
        ticket_date=date(2024, 11, 7),
        job_id=1,
        material_id=1,
        ticket_type_id=1,
        file_id="/path/to/test.pdf",
        file_page=1,
    )

    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    return ticket
