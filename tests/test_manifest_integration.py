"""Integration tests for Manifest Log exporter with database (Issue #18)."""
import tempfile
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.truck_tickets.database import create_all_tables, seed_reference_data
from src.truck_tickets.database.ticket_repository import TicketRepository
from src.truck_tickets.exporters.manifest_log_exporter import ManifestLogExporter


class TestManifestIntegration:
    """Integration tests for manifest log exporter with database."""

    @pytest.fixture
    def session(self):
        """Create in-memory database with seeded data."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        create_all_tables(engine)
        session_factory = sessionmaker(bind=engine)
        sess = session_factory()
        seed_reference_data(sess, job_code="24-105", job_name="PHMS New Pediatric Campus")
        try:
            yield sess
        finally:
            sess.close()
            engine.dispose()

    @pytest.fixture
    def repository(self, session):
        """Create repository instance."""
        return TicketRepository(session)

    def test_export_from_database_contaminated_only(self, session, repository):
        """Test exporting manifest log from database with contaminated tickets."""
        # Create test tickets (contaminated and non-contaminated)
        ticket_data = [
            # Contaminated ticket with manifest
            {
                "ticket_number": "WM-80000001",
                "ticket_date": date(2024, 10, 17),
                "job_name": "24-105",
                "vendor_name": "WASTE_MANAGEMENT_LEWISVILLE",
                "material_name": "CLASS_2_CONTAMINATED",
                "source_name": "PODIUM",
                "destination_name": "WASTE_MANAGEMENT_LEWISVILLE",
                "ticket_type_name": "EXPORT",
                "quantity": 18.5,
                "quantity_unit": "TONS",
                "truck_number": "1234",
                "manifest_number": "WM-MAN-2024-001234",
                "file_id": "batch1.pdf",
                "file_page": 1,
                "extraction_confidence": 0.95
            },
            # Another contaminated ticket
            {
                "ticket_number": "WM-80000002",
                "ticket_date": date(2024, 10, 17),
                "job_name": "24-105",
                "vendor_name": "WASTE_MANAGEMENT_LEWISVILLE",
                "material_name": "CLASS_2_CONTAMINATED",
                "source_name": "PIER_EX",
                "destination_name": "WASTE_MANAGEMENT_LEWISVILLE",
                "ticket_type_name": "EXPORT",
                "quantity": 20.0,
                "quantity_unit": "TONS",
                "truck_number": "1235",
                "manifest_number": "WM-MAN-2024-001235",
                "file_id": "batch1.pdf",
                "file_page": 2,
                "extraction_confidence": 0.93
            },
            # Non-contaminated ticket (should be filtered out)
            {
                "ticket_number": "LDI-90000001",
                "ticket_date": date(2024, 10, 17),
                "job_name": "24-105",
                "vendor_name": "LDI_YARD",
                "material_name": "NON_CONTAMINATED",
                "source_name": "SPG",
                "destination_name": "LDI_YARD",
                "ticket_type_name": "EXPORT",
                "quantity": 15.0,
                "quantity_unit": "TONS",
                "truck_number": "2056",
                "file_id": "batch2.pdf",
                "file_page": 1,
                "extraction_confidence": 0.88
            },
        ]

        # Insert tickets
        for data in ticket_data:
            repository.create(**data)

        # Query tickets back from database
        from src.truck_tickets.models.sql_truck_ticket import TruckTicket
        db_tickets = session.query(TruckTicket).all()

        # Convert to dict format for exporter
        ticket_dicts = []
        for ticket in db_tickets:
            ticket_dicts.append({
                "ticket_number": ticket.ticket_number,
                "manifest_number": ticket.manifest_number or "",
                "ticket_date": ticket.ticket_date.strftime("%Y-%m-%d"),
                "source": ticket.source.source_name if ticket.source else "UNKNOWN",
                "destination": ticket.destination.destination_name if ticket.destination else "UNKNOWN",
                "material": ticket.material.material_name if ticket.material else "UNKNOWN",
                "quantity": float(ticket.quantity) if ticket.quantity else None,
                "quantity_unit": ticket.quantity_unit,
                "truck_number": ticket.truck_number or "",
                "file_id": ticket.file_id,
                "file_page": ticket.file_page
            })

        # Export to CSV
        exporter = ManifestLogExporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"
            exporter.export(ticket_dicts, output_path)

            # Verify file was created
            assert output_path.exists()

            # Read and verify content
            content = output_path.read_text()
            lines = content.split("\n")

            # Should have header + 2 contaminated tickets (not the NON_CONTAMINATED one)
            assert len([l for l in lines if l.strip()]) == 3  # header + 2 data rows

            # Check header includes truck_number
            assert "truck_number" in lines[0]

            # Verify contaminated tickets are included
            assert "WM-80000001" in content
            assert "WM-80000002" in content
            assert "WM-MAN-2024-001234" in content
            assert "WM-MAN-2024-001235" in content

            # Verify non-contaminated ticket is excluded
            assert "LDI-90000001" not in content

            # Verify truck numbers are included
            assert "1234" in content
            assert "1235" in content

    def test_export_with_spoils_material(self, session, repository):
        """Test that SPOILS material is included in manifest log."""
        # Create SPOILS ticket
        repository.create(
            ticket_number="WM-90000001",
            ticket_date=date(2024, 10, 17),
            job_name="24-105",
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            material_name="SPOILS",
            source_name="BECK_SPOILS",
            destination_name="WASTE_MANAGEMENT_LEWISVILLE",
            ticket_type_name="EXPORT",
            quantity=12.0,
            quantity_unit="TONS",
            truck_number="5000",
            manifest_number="WM-MAN-2024-999999",
            file_id="test.pdf",
            file_page=1,
            extraction_confidence=0.90
        )

        # Query and convert
        from src.truck_tickets.models.sql_truck_ticket import TruckTicket
        db_tickets = session.query(TruckTicket).all()

        ticket_dicts = []
        for ticket in db_tickets:
            ticket_dicts.append({
                "ticket_number": ticket.ticket_number,
                "manifest_number": ticket.manifest_number or "",
                "ticket_date": ticket.ticket_date.strftime("%Y-%m-%d"),
                "source": ticket.source.source_name if ticket.source else "UNKNOWN",
                "destination": ticket.destination.destination_name if ticket.destination else "UNKNOWN",
                "material": ticket.material.material_name if ticket.material else "UNKNOWN",
                "quantity": float(ticket.quantity) if ticket.quantity else None,
                "quantity_unit": ticket.quantity_unit,
                "truck_number": ticket.truck_number or "",
                "file_id": ticket.file_id,
                "file_page": ticket.file_page
            })

        # Export
        exporter = ManifestLogExporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"
            exporter.export(ticket_dicts, output_path)

            content = output_path.read_text()

            # Verify SPOILS is included
            assert "SPOILS" in content
            assert "WM-MAN-2024-999999" in content
            assert "WM-90000001" in content

    def test_monthly_summary_from_database(self, session, repository):
        """Test monthly summary generation from database tickets."""
        # Create multiple contaminated tickets
        for i in range(3):
            repository.create(
                ticket_number=f"WM-95000{i:03d}",
                ticket_date=date(2024, 10, 17 + i),
                job_name="24-105",
                vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
                material_name="CLASS_2_CONTAMINATED",
                source_name="PODIUM",
                destination_name="WASTE_MANAGEMENT_LEWISVILLE",
                ticket_type_name="EXPORT",
                quantity=15.0 + i,
                quantity_unit="TONS",
                manifest_number=f"WM-MAN-2024-88888{i}",
                file_id="test.pdf",
                file_page=i + 1,
                extraction_confidence=0.90
            )

        # Query and convert
        from src.truck_tickets.models.sql_truck_ticket import TruckTicket
        db_tickets = session.query(TruckTicket).all()

        ticket_dicts = []
        for ticket in db_tickets:
            ticket_dicts.append({
                "ticket_number": ticket.ticket_number,
                "manifest_number": ticket.manifest_number or "",
                "ticket_date": ticket.ticket_date.strftime("%Y-%m-%d"),
                "source": ticket.source.source_name if ticket.source else "UNKNOWN",
                "destination": ticket.destination.destination_name if ticket.destination else "UNKNOWN",
                "material": ticket.material.material_name if ticket.material else "UNKNOWN",
                "quantity": float(ticket.quantity) if ticket.quantity else None,
                "quantity_unit": ticket.quantity_unit,
                "truck_number": ticket.truck_number or "",
                "file_id": ticket.file_id,
                "file_page": ticket.file_page
            })

        # Generate summary
        exporter = ManifestLogExporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "monthly_summary.csv"
            exporter.generate_monthly_summary(ticket_dicts, output_path)

            assert output_path.exists()

            content = output_path.read_text()
            lines = content.split("\n")

            # Should have header + at least 1 month
            assert len([l for l in lines if l.strip()]) >= 2

            # Check for 2024-10 month
            assert "2024-10" in content

            # Check totals (3 loads, ~48 tons total)
            assert "3" in content  # load count
