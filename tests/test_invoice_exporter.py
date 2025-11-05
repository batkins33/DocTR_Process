"""Unit tests for Invoice Matching CSV exporter (Issue #17)."""
import tempfile
from pathlib import Path

import pytest

from src.truck_tickets.exporters.invoice_csv_exporter import InvoiceMatchingExporter


class TestInvoiceMatchingExporter:
    """Test suite for invoice matching CSV exporter."""

    @pytest.fixture
    def sample_tickets(self):
        """Create sample ticket data for testing."""
        return [
            {
                "ticket_number": "WM-40000003",
                "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
                "ticket_date": "2024-10-18",
                "material": "CLASS_2_CONTAMINATED",
                "quantity": 14.5,
                "quantity_unit": "TONS",
                "truck_number": "1234",
                "file_id": "batch1.pdf",
                "file_page": 3
            },
            {
                "ticket_number": "WM-40000001",
                "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
                "ticket_date": "2024-10-17",
                "material": "CLASS_2_CONTAMINATED",
                "quantity": 15.5,
                "quantity_unit": "TONS",
                "truck_number": "1235",
                "file_id": "batch1.pdf",
                "file_page": 1
            },
            {
                "ticket_number": "LDI-70000001",
                "vendor": "LDI_YARD",
                "ticket_date": "2024-10-17",
                "material": "NON_CONTAMINATED",
                "quantity": 18.0,
                "quantity_unit": "TONS",
                "truck_number": "2056",
                "file_id": "batch2.pdf",
                "file_page": 1
            },
            {
                "ticket_number": "WM-40000002",
                "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
                "ticket_date": "2024-10-17",
                "material": "SPOILS",
                "quantity": 12.0,
                "quantity_unit": "TONS",
                "truck_number": "",  # Missing truck number
                "file_id": "batch1.pdf",
                "file_page": 2
            },
        ]

    @pytest.fixture
    def exporter(self):
        """Create exporter instance."""
        return InvoiceMatchingExporter()

    def test_exporter_initialization(self, exporter):
        """Test exporter initializes correctly."""
        assert exporter.logger is not None

    def test_export_creates_file(self, exporter, sample_tickets):
        """Test that export creates a CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_match.csv"

            exporter.export(sample_tickets, output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_export_pipe_delimited(self, exporter, sample_tickets):
        """Test that CSV uses pipe delimiter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_match.csv"

            exporter.export(sample_tickets, output_path)

            # Read file and check for pipe delimiters
            content = output_path.read_text()
            assert "|" in content
            assert "," not in content.split("\n")[0]  # Header should use pipes, not commas

    def test_export_correct_headers(self, exporter, sample_tickets):
        """Test that CSV has correct headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_match.csv"

            exporter.export(sample_tickets, output_path)

            # Read first line (header)
            with open(output_path, "r") as f:
                header = f.readline().strip()

            expected_header = "ticket_number|vendor|date|material|quantity|units|truck_number|file_ref"
            assert header == expected_header

    def test_export_sorting_by_vendor_date_ticket(self, exporter, sample_tickets):
        """Test that tickets are sorted by vendor, then date, then ticket number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_match.csv"

            exporter.export(sample_tickets, output_path)

            # Read all lines
            with open(output_path, "r") as f:
                lines = f.readlines()

            # Skip header, check data rows
            data_lines = [line.strip() for line in lines[1:]]

            # Expected order:
            # 1. LDI_YARD (comes before WASTE_MANAGEMENT alphabetically)
            # 2. WASTE_MANAGEMENT 2024-10-17 WM-40000001
            # 3. WASTE_MANAGEMENT 2024-10-17 WM-40000002
            # 4. WASTE_MANAGEMENT 2024-10-18 WM-40000003

            assert "LDI-70000001" in data_lines[0]
            assert "WM-40000001" in data_lines[1]
            assert "WM-40000002" in data_lines[2]
            assert "WM-40000003" in data_lines[3]

    def test_export_includes_truck_number(self, exporter, sample_tickets):
        """Test that truck_number column is included (v1.1 field)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_match.csv"

            exporter.export(sample_tickets, output_path)

            content = output_path.read_text()

            # Check header includes truck_number
            assert "truck_number" in content.split("\n")[0]

            # Check data includes truck numbers
            assert "1234" in content
            assert "1235" in content
            assert "2056" in content

    def test_format_quantity(self, exporter):
        """Test quantity formatting."""
        assert exporter._format_quantity(15.5) == "15.5"
        assert exporter._format_quantity(15.0) == "15.0"
        assert exporter._format_quantity(15) == "15.0"
        assert exporter._format_quantity("15.5") == "15.5"
        assert exporter._format_quantity(None) == ""
        assert exporter._format_quantity("") == ""
        assert exporter._format_quantity("invalid") == "invalid"

    def test_format_file_ref(self, exporter):
        """Test file reference formatting."""
        # With file_id and file_page
        ticket1 = {"file_id": "batch1.pdf", "file_page": 1}
        assert exporter._format_file_ref(ticket1) == "batch1.pdf-p1"

        # With only file_id
        ticket2 = {"file_id": "batch1.pdf"}
        assert exporter._format_file_ref(ticket2) == "batch1.pdf"

        # With file_ref fallback
        ticket3 = {"file_ref": "custom-ref.pdf-p5"}
        assert exporter._format_file_ref(ticket3) == "custom-ref.pdf-p5"

        # Empty
        ticket4 = {}
        assert exporter._format_file_ref(ticket4) == ""

    def test_export_with_missing_fields(self, exporter):
        """Test export handles missing optional fields gracefully."""
        tickets = [
            {
                "ticket_number": "TEST-001",
                "vendor": "TEST_VENDOR",
                "ticket_date": "2024-10-17",
                "material": "TEST_MATERIAL",
                # Missing: quantity, quantity_unit, truck_number, file_id, file_page
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_match.csv"

            # Should not raise exception
            exporter.export(tickets, output_path)

            assert output_path.exists()

            # Read and verify
            with open(output_path, "r") as f:
                lines = f.readlines()

            # Should have header + 1 data row
            assert len(lines) == 2

            # Data row should have empty fields for missing values
            data_row = lines[1].strip()
            assert "TEST-001" in data_row
            assert "TEST_VENDOR" in data_row

    def test_export_empty_tickets_list(self, exporter):
        """Test export handles empty ticket list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_match.csv"

            exporter.export([], output_path)

            assert output_path.exists()

            # Should have header only
            with open(output_path, "r") as f:
                lines = f.readlines()

            assert len(lines) == 1  # Header only
            assert "ticket_number" in lines[0]

    def test_export_by_vendor(self, exporter, sample_tickets):
        """Test export_by_vendor creates separate files per vendor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            exporter.export_by_vendor(sample_tickets, output_dir)

            # Should create 2 files (LDI_YARD and WASTE_MANAGEMENT_LEWISVILLE)
            files = list(output_dir.glob("invoice_match_*.csv"))
            assert len(files) == 2

            # Check file names
            file_names = [f.name for f in files]
            assert "invoice_match_LDI_YARD.csv" in file_names
            assert "invoice_match_WASTE_MANAGEMENT_LEWISVILLE.csv" in file_names

    def test_generate_summary_report(self, exporter, sample_tickets):
        """Test summary report generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_summary.csv"

            exporter.generate_summary_report(sample_tickets, output_path)

            assert output_path.exists()

            # Read and verify
            with open(output_path, "r") as f:
                lines = f.readlines()

            # Should have header + 2 vendors
            assert len(lines) == 3

            # Check header
            assert "vendor" in lines[0]
            assert "ticket_count" in lines[0]
            assert "total_quantity" in lines[0]

            # Check data (sorted by vendor name)
            content = "".join(lines)
            assert "LDI_YARD" in content
            assert "WASTE_MANAGEMENT_LEWISVILLE" in content

    def test_export_with_pathlib_path(self, exporter, sample_tickets):
        """Test export accepts Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "invoice_match.csv"

            # Should accept Path object
            exporter.export(sample_tickets, output_path)

            assert output_path.exists()

    def test_export_with_string_path(self, exporter, sample_tickets):
        """Test export accepts string paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "invoice_match.csv")

            # Should accept string path
            exporter.export(sample_tickets, output_path)

            assert Path(output_path).exists()
