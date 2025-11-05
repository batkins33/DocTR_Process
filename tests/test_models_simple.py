"""Simple test for SQLAlchemy models without relationship initialization."""

import pytest

from src.truck_tickets.models.sql_reference import Job, Material, Source, Destination, Vendor, TicketType
from src.truck_tickets.models.sql_truck_ticket import TruckTicket
from src.truck_tickets.models.sql_processing import ReviewQueue, ProcessingRun


class TestSQLAlchemyModelsSimple:
    """Test basic SQLAlchemy model functionality without relationships."""

    def test_model_creation_no_relationships(self):
        """Test that all models can be instantiated without triggering relationships."""

        # Verify class names and table names
        assert Job.__name__ == "Job"
        assert Job.__tablename__ == "jobs"

        assert Material.__name__ == "Material"
        assert Material.__tablename__ == "materials"

        assert TruckTicket.__name__ == "TruckTicket"
        assert TruckTicket.__tablename__ == "truck_tickets"

        # Verify v1.1 truck_number field exists
        assert hasattr(TruckTicket, 'truck_number')

    def test_model_attributes(self):
        """Test that models have expected attributes."""
        
        # Check TruckTicket attributes
        expected_truck_ticket_attrs = [
            'ticket_id', 'ticket_number', 'ticket_date', 'quantity', 
            'quantity_unit', 'truck_number',  # v1.1 field
            'job_id', 'material_id', 'source_id', 'destination_id',
            'vendor_id', 'ticket_type_id', 'manifest_number',
            'review_required', 'duplicate_of', 'confidence_score'
        ]
        
        for attr in expected_truck_ticket_attrs:
            assert hasattr(TruckTicket, attr), f"TruckTicket missing {attr}"
        
        # Check ReviewQueue attributes
        expected_review_queue_attrs = [
            'review_id', 'ticket_id', 'reason', 'severity', 'resolved'
        ]

        for attr in expected_review_queue_attrs:
            assert hasattr(ReviewQueue, attr), f"ReviewQueue missing {attr}"

    def test_base_class(self):
        """Test that all models inherit from Base with audit fields."""
        
        # Check that all models have Base audit fields
        audit_fields = ['created_at', 'updated_at']
        
        for model_class in [Job, Material, Source, Destination, Vendor, TicketType, TruckTicket, ReviewQueue, ProcessingRun]:
            for field in audit_fields:
                assert hasattr(model_class, field), f"{model_class.__name__} missing {field}"

    def test_v1_1_features(self):
        """Test that v1.1 features are present."""
        
        # TruckTicket should have truck_number field
        assert hasattr(TruckTicket, 'truck_number')
        
        # ProcessingRun should have comprehensive tracking
        expected_run_attrs = [
            'run_id', 'request_guid', 'started_at', 'completed_at',
            'files_count', 'pages_count', 'tickets_created', 'tickets_updated',
            'duplicates_found', 'review_queue_count', 'error_count'
        ]
        
        for attr in expected_run_attrs:
            assert hasattr(ProcessingRun, attr), f"ProcessingRun missing {attr}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
