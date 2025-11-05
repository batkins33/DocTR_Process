"""Integration tests for Invoice CSV exporter with database (Issue #17)."""
import tempfile
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.truck_tickets.database import create_all_tables, seed_reference_data
from src.truck_tickets.database.ticket_repository import TicketRepository
from src.truck_tickets.exporters.invoice_csv_exporter import InvoiceMatchingExporter


class TestInvoiceIntegration:
    """Integration tests for invoice exporter with database."""

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

    def test_export_from_database_tickets(self, session, repository):
        """Test exporting invoice CSV from database tickets."""
        # Create test tickets
        ticket_data = [
            {
                "ticket_number": "WM-40000001",
                "ticket_date": date(2024, 10, 17),
                "job_name": "24-105",
                "vendor_name": "WASTE_MANAGEMENT_LEWISVILLE",
                "material_name": "CLASS_2_CONTAMINATED",
                "source_name": "PODIUM",
                "destination_name": "WASTE_MANAGEMENT_LEWISVILLE",
                "ticket_type_name": "EXPORT",
                "quantity": 15.5,
                "quantity_unit": "TONS",
                "truck_number": "1234",
                "manifest_number": "WM-MAN-2024-001234",
                "file_id": "batch1.pdf",
                "file_page": 1,
                "extraction_confidence": 0.95
            },
            {
                "ticket_number": "WM-40000002",
                "ticket_date": date(2024, 10, 17),
                "job_name": "24-105",
                "vendor_name": "WASTE_MANAGEMENT_LEWISVILLE",
                "material_name": "NON_CONTAMINATED",
                "source_name": "SPG",
                "destination_name": "LDI_YARD",
                "ticket_type_name": "EXPORT",
                "quantity": 18.0,
                "quantity_unit": "TONS",
                "truck_number": "1235",
                "file_id": "batch1.pdf",
                "file_page": 2,
                "extraction_confidence": 0.92
            },
            {
                "ticket_number": "LDI-70000001",
                "ticket_date": date(2024, 10, 18),
                "job_name": "24-105",
                "vendor_name": "LDI_YARD",
                "material_name": "NON_CONTAMINATED",
                "source_name": "SPG",
                "destination_name": "LDI_YARD",
                "ticket_type_name": "EXPORT",
                "quantity": 20.0,
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
                "vendor": ticket.vendor.vendor_name if ticket.vendor else "UNKNOWN",
                "ticket_date": ticket.ticket_date.strftime("%Y-%m-%d"),
                "material": ticket.material.material_name if ticket.material else "UNKNOWN",
                "quantity": float(ticket.quantity) if ticket.quantity else None,
                "quantity_unit": ticket.quantity_unit,
                "truck_number": ticket.truck_number or "",
                "file_id": ticket.file_id,
                "file_page": ticket.file_page
            })

        # Export to CSV
        exporter = InvoiceMatchingExporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_match.csv"
            exporter.export(ticket_dicts, output_path)

            # Verify file was created
            assert output_path.exists()

            # Read and verify content
            with open(output_path, "r") as f:
                lines = f.readlines()

            # Should have header + 3 data rows
            assert len(lines) == 4

            # Check header
            header = lines[0].strip()
            assert "ticket_number" in header
            assert "truck_number" in header

            # Check all tickets are present
            content = "".join(lines)
            assert "LDI-70000001" in content
            assert "WM-40000001" in content
            assert "WM-40000002" in content

            # Verify truck numbers are included
            content = "".join(lines)
            assert "1234" in content
            assert "1235" in content
            assert "2056" in content

    def test_export_with_vendor_grouping(self, session, repository):
        """Test export_by_vendor creates separate files."""
        # Use simple dict data to test the export_by_vendor functionality
        ticket_dicts = [
            {
                "ticket_number": "WM-50000001",
                "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
                "ticket_date": "2024-10-17",
                "material": "CLASS_2_CONTAMINATED",
                "quantity": 15.5,
                "quantity_unit": "TONS",
                "truck_number": "1234",
                "file_id": "test.pdf",
                "file_page": 1
            },
            {
                "ticket_number": "LDI-80000001",
                "vendor": "LDI_YARD",
                "ticket_date": "2024-10-17",
                "material": "NON_CONTAMINATED",
                "quantity": 20.0,
                "quantity_unit": "TONS",
                "truck_number": "2056",
                "file_id": "test.pdf",
                "file_page": 2
            },
        ]

        # Export by vendor
        exporter = InvoiceMatchingExporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            exporter.export_by_vendor(ticket_dicts, tmpdir)

            # Should create 2 files
            files = list(Path(tmpdir).glob("invoice_match_*.csv"))
            assert len(files) == 2

            # Verify file names
            file_names = [f.name for f in files]
            assert "invoice_match_LDI_YARD.csv" in file_names
            assert "invoice_match_WASTE_MANAGEMENT_LEWISVILLE.csv" in file_names

    def test_summary_report_from_database(self, session, repository):
        """Test summary report generation."""
        # Use simple dict data to test summary functionality
        ticket_dicts = [
            {
                "ticket_number": "WM-60000001",
                "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
                "ticket_date": "2024-10-17",
                "material": "CLASS_2_CONTAMINATED",
                "quantity": 15.5,
                "quantity_unit": "TONS",
                "truck_number": "",
                "file_id": "test.pdf",
                "file_page": 1
            },
            {
                "ticket_number": "WM-60000002",
                "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
                "ticket_date": "2024-10-17",
                "material": "CLASS_2_CONTAMINATED",
                "quantity": 20.0,
                "quantity_unit": "TONS",
                "truck_number": "",
                "file_id": "test.pdf",
                "file_page": 2
            },
        ]

        # Generate summary
        exporter = InvoiceMatchingExporter()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "summary.csv"
            exporter.generate_summary_report(ticket_dicts, output_path)

            assert output_path.exists()

            # Read and verify
            with open(output_path, "r") as f:
                lines = f.readlines()

            # Should have header + 1 vendor
            assert len(lines) == 2

            # Check totals
            data_line = lines[1]
            assert "WASTE_MANAGEMENT_LEWISVILLE" in data_line
            assert "2" in data_line  # 2 tickets
            assert "35.5" in data_line  # 15.5 + 20.0 = 35.5
