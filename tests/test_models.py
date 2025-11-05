"""Test SQLAlchemy models for basic functionality."""

from datetime import date, datetime

import pytest
from src.truck_tickets.models import (
    DestinationModel,
    JobModel,
    MaterialModel,
    ProcessingRun,
    ReviewQueue,
    SourceModel,
    TicketTypeModel,
    TruckTicketModel,
    VendorModel,
)


class TestSQLAlchemyModels:
    """Test basic SQLAlchemy model functionality."""

    def test_model_creation(self):
        """Test that all models can be instantiated."""

        # Test reference models
        JobModel(
            job_code="24-105", job_name="Test Project", start_date=date(2024, 1, 1)
        )

        MaterialModel(
            material_name="CLASS_2_CONTAMINATED",
            material_class="CONTAMINATED",
            requires_manifest=True,
        )

        SourceModel(
            source_name="PODIUM", source_type="EXCAVATION", description="Test source"
        )

        DestinationModel(
            destination_name="WASTE_MANAGEMENT_LEWISVILLE",
            facility_type="DISPOSAL",
            requires_manifest=True,
        )

        VendorModel(
            vendor_name="Waste Management", vendor_code="WM", vendor_type="DISPOSAL"
        )

        TicketTypeModel(type_name="EXPORT")

        # Test main ticket model
        ticket = TruckTicketModel(
            ticket_number="WM-12345678",
            ticket_date=date(2024, 10, 17),
            quantity=25.5,
            quantity_unit="TONS",
            truck_number="123",
            job_id=1,
            material_id=1,
            source_id=1,
            destination_id=1,
            vendor_id=1,
            ticket_type_id=1,
            manifest_number="WM-MAN-2024-001234",
            file_id="test.pdf",
            file_page=1,
            confidence_score=0.95,
        )

        # Verify basic attributes
        assert ticket.ticket_number == "WM-12345678"
        assert ticket.truck_number == "123"  # v1.1 field
        assert not ticket.is_export  # Default ticket_type_id = 1 (IMPORT)
        assert not ticket.is_duplicate
        assert not ticket.needs_review  # High confidence

    def test_review_queue_model(self):
        """Test ReviewQueue model creation and properties."""

        review = ReviewQueue(
            reason="MISSING_MANIFEST",
            severity="CRITICAL",
            file_path="test.pdf",
            page_num=1,
        )

        assert review.is_critical
        assert not review.is_warning
        assert not review.is_info
        assert not review.resolved

    def test_processing_run_model(self):
        """Test ProcessingRun model creation and properties."""

        run = ProcessingRun(
            request_guid="test-guid-123",
            started_at=datetime.now(),
            status="IN_PROGRESS",
            files_count=10,
            pages_count=50,
        )

        assert run.is_in_progress
        assert not run.is_completed
        assert not run.is_failed
        assert run.success_rate is None  # No tickets processed yet

    def test_model_relationships(self):
        """Test that model relationships are properly defined."""

        # Check that TruckTicket has relationships defined
        assert hasattr(TruckTicketModel, "job")
        assert hasattr(TruckTicketModel, "material")
        assert hasattr(TruckTicketModel, "vendor")
        assert hasattr(TruckTicketModel, "review_entries")

        # Check that reference models have back relationships
        assert hasattr(JobModel, "truck_tickets")
        assert hasattr(MaterialModel, "truck_tickets")
        assert hasattr(VendorModel, "truck_tickets")

    def test_model_repr(self):
        """Test that models have meaningful string representations."""

        ticket = TruckTicketModel(
            ticket_number="WM-12345678",
            ticket_date=date(2024, 10, 17),
            job_id=1,
            material_id=1,
            ticket_type_id=1,
        )

        repr_str = repr(ticket)
        assert "TruckTicket" in repr_str
        assert "WM-12345678" in repr_str

        review = ReviewQueue(reason="MISSING_MANIFEST", severity="CRITICAL")

        review_repr = repr(review)
        assert "ReviewQueue" in review_repr
        assert "MISSING_MANIFEST" in review_repr


if __name__ == "__main__":
    pytest.main([__file__])
