"""Unit tests for Manifest Log CSV exporter (Issue #18)."""
import tempfile
from pathlib import Path

import pytest

from src.truck_tickets.exporters.manifest_log_exporter import ManifestLogExporter


class TestManifestLogExporter:
    """Test suite for manifest log exporter (regulatory compliance)."""

    @pytest.fixture
    def sample_tickets(self):
        """Create sample ticket data for testing."""
        return [
            # Contaminated tickets with manifests
            {
                "ticket_number": "WM-40000001",
                "manifest_number": "WM-MAN-2024-001234",
                "ticket_date": "2024-10-17",
                "source": "PODIUM",
                "destination": "WASTE_MANAGEMENT_LEWISVILLE",
                "material": "CLASS_2_CONTAMINATED",
                "quantity": 18.5,
                "quantity_unit": "TONS",
                "truck_number": "1234",
                "file_id": "batch1.pdf",
                "file_page": 1
            },
            {
                "ticket_number": "WM-40000002",
                "manifest_number": "WM-MAN-2024-001235",
                "ticket_date": "2024-10-17",
                "source": "PIER_EX",
                "destination": "WASTE_MANAGEMENT_LEWISVILLE",
                "material": "CLASS_2_CONTAMINATED",
                "quantity": 20.0,
                "quantity_unit": "TONS",
                "truck_number": "1235",
                "file_id": "batch1.pdf",
                "file_page": 2
            },
            # Spoils ticket (also requires manifest)
            {
                "ticket_number": "WM-40000003",
                "manifest_number": "WM-MAN-2024-555555",
                "ticket_date": "2024-10-18",
                "source": "BECK_SPOILS",
                "destination": "WASTE_MANAGEMENT_LEWISVILLE",
                "material": "SPOILS",
                "quantity": 14.0,
                "quantity_unit": "TONS",
                "truck_number": "2056",
                "file_id": "batch2.pdf",
                "file_page": 1
            },
            # Non-contaminated ticket (should be filtered out)
            {
                "ticket_number": "LDI-70000001",
                "ticket_date": "2024-10-17",
                "source": "SPG",
                "destination": "LDI_YARD",
                "material": "NON_CONTAMINATED",
                "quantity": 15.0,
                "quantity_unit": "TONS",
                "truck_number": "3000",
                "file_id": "batch3.pdf",
                "file_page": 1
            },
        ]

    @pytest.fixture
    def exporter(self):
        """Create exporter instance."""
        return ManifestLogExporter()

    def test_exporter_initialization(self, exporter):
        """Test exporter initializes correctly."""
        assert exporter.logger is not None

    def test_export_creates_file(self, exporter, sample_tickets):
        """Test that export creates a CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            exporter.export(sample_tickets, output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_export_correct_headers(self, exporter, sample_tickets):
        """Test that CSV has correct headers including truck_number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            exporter.export(sample_tickets, output_path)

            # Read first line (header)
            with open(output_path, "r") as f:
                header = f.readline().strip()

            expected_header = "ticket_number,manifest_number,date,source,waste_facility,material,quantity,units,truck_number,file_ref"
            assert header == expected_header

    def test_export_filters_contaminated_only(self, exporter, sample_tickets):
        """Test that only contaminated material is exported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            exporter.export(sample_tickets, output_path)

            # Read all lines
            with open(output_path, "r") as f:
                lines = f.readlines()

            # Should have header + 3 contaminated tickets (not the NON_CONTAMINATED one)
            assert len(lines) == 4

            content = "".join(lines)
            assert "WM-40000001" in content  # Contaminated
            assert "WM-40000002" in content  # Contaminated
            assert "WM-40000003" in content  # Spoils
            assert "LDI-70000001" not in content  # Non-contaminated (filtered out)

    def test_export_sorting_by_date_manifest(self, exporter, sample_tickets):
        """Test that tickets are sorted by date, then manifest number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            exporter.export(sample_tickets, output_path)

            # Read data lines
            with open(output_path, "r") as f:
                lines = f.readlines()

            data_lines = [line.strip() for line in lines[1:]]

            # Expected order:
            # 1. 2024-10-17 WM-MAN-2024-001234
            # 2. 2024-10-17 WM-MAN-2024-001235
            # 3. 2024-10-18 WM-MAN-2024-555555

            assert "WM-MAN-2024-001234" in data_lines[0]
            assert "WM-MAN-2024-001235" in data_lines[1]
            assert "WM-MAN-2024-555555" in data_lines[2]

    def test_export_includes_truck_number(self, exporter, sample_tickets):
        """Test that truck_number column is included (v1.1 field)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            exporter.export(sample_tickets, output_path)

            content = output_path.read_text()

            # Check header includes truck_number
            assert "truck_number" in content.split("\n")[0]

            # Check data includes truck numbers
            assert "1234" in content
            assert "1235" in content
            assert "2056" in content

    def test_export_includes_spoils(self, exporter):
        """Test that SPOILS material is included (also requires manifests)."""
        tickets = [
            {
                "ticket_number": "WM-50000001",
                "manifest_number": "WM-MAN-2024-999999",
                "ticket_date": "2024-10-17",
                "source": "BECK_SPOILS",
                "destination": "WASTE_MANAGEMENT_LEWISVILLE",
                "material": "SPOILS",
                "quantity": 12.0,
                "quantity_unit": "TONS",
                "truck_number": "5000",
                "file_id": "test.pdf",
                "file_page": 1
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            exporter.export(tickets, output_path)

            content = output_path.read_text()
            assert "SPOILS" in content
            assert "BECK_SPOILS" in content

    def test_format_quantity(self, exporter):
        """Test quantity formatting."""
        assert exporter._format_quantity(18.5) == "18.5"
        assert exporter._format_quantity(20.0) == "20.0"
        assert exporter._format_quantity(15) == "15.0"
        assert exporter._format_quantity("18.5") == "18.5"
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

    def test_validate_manifests_all_present(self, exporter, sample_tickets, caplog):
        """Test validation when all manifests are present."""
        import logging
        caplog.set_level(logging.INFO)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            exporter.export(sample_tickets, output_path)

            # Should log success message
            assert "All contaminated loads have manifest numbers" in caplog.text

    def test_validate_manifests_missing(self, exporter, caplog):
        """Test validation warns about missing manifests (COMPLIANCE ISSUE)."""
        import logging
        caplog.set_level(logging.WARNING)

        tickets = [
            {
                "ticket_number": "WM-60000001",
                "manifest_number": "WM-MAN-2024-111111",
                "ticket_date": "2024-10-17",
                "source": "PODIUM",
                "destination": "WASTE_MANAGEMENT_LEWISVILLE",
                "material": "CLASS_2_CONTAMINATED",
                "quantity": 15.0,
                "quantity_unit": "TONS",
                "file_id": "test.pdf",
                "file_page": 1
            },
            {
                "ticket_number": "WM-60000002",
                "manifest_number": "",  # MISSING MANIFEST
                "ticket_date": "2024-10-17",
                "source": "PIER_EX",
                "destination": "WASTE_MANAGEMENT_LEWISVILLE",
                "material": "CLASS_2_CONTAMINATED",
                "quantity": 20.0,
                "quantity_unit": "TONS",
                "file_id": "test.pdf",
                "file_page": 2
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            exporter.export(tickets, output_path)

            # Should log compliance warning
            assert "COMPLIANCE WARNING" in caplog.text
            assert "1 contaminated loads missing manifest numbers" in caplog.text

    def test_export_with_missing_fields(self, exporter):
        """Test export handles missing optional fields gracefully."""
        tickets = [
            {
                "ticket_number": "TEST-001",
                "manifest_number": "TEST-MAN-001",
                "ticket_date": "2024-10-17",
                "source": "TEST_SOURCE",
                "destination": "TEST_FACILITY",
                "material": "CLASS_2_CONTAMINATED",
                # Missing: quantity, quantity_unit, truck_number, file_id, file_page
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            # Should not raise exception
            exporter.export(tickets, output_path)

            assert output_path.exists()

            # Read and verify
            with open(output_path, "r") as f:
                lines = f.readlines()

            # Should have header + 1 data row
            assert len(lines) == 2

    def test_export_empty_tickets_list(self, exporter):
        """Test export handles empty ticket list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            exporter.export([], output_path)

            assert output_path.exists()

            # Should have header only
            with open(output_path, "r") as f:
                lines = f.readlines()

            assert len(lines) == 1  # Header only
            assert "ticket_number" in lines[0]

    def test_generate_monthly_summary(self, exporter, sample_tickets):
        """Test monthly summary generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "monthly_summary.csv"

            exporter.generate_monthly_summary(sample_tickets, output_path)

            assert output_path.exists()

            # Read and verify
            with open(output_path, "r") as f:
                lines = f.readlines()

            # Should have header + data
            assert len(lines) >= 2

            # Check header
            assert "month" in lines[0]
            assert "load_count" in lines[0]
            assert "manifest_count" in lines[0]

    def test_check_duplicate_manifests(self, exporter):
        """Test duplicate manifest detection."""
        tickets = [
            {
                "ticket_number": "WM-70000001",
                "manifest_number": "WM-MAN-2024-DUPLICATE",
                "ticket_date": "2024-10-17",
                "material": "CLASS_2_CONTAMINATED"
            },
            {
                "ticket_number": "WM-70000002",
                "manifest_number": "WM-MAN-2024-DUPLICATE",  # DUPLICATE
                "ticket_date": "2024-10-18",
                "material": "CLASS_2_CONTAMINATED"
            },
        ]

        duplicates = exporter.check_duplicate_manifests(tickets)

        assert len(duplicates) == 1
        assert duplicates[0]["manifest_number"] == "WM-MAN-2024-DUPLICATE"

    def test_export_by_source(self, exporter, sample_tickets):
        """Test export_by_source creates separate files per source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            exporter.export_by_source(sample_tickets, output_dir)

            # Should create files for each source
            files = list(output_dir.glob("manifest_log_*.csv"))
            assert len(files) >= 2  # At least PODIUM, PIER_EX, BECK_SPOILS

    def test_export_with_pathlib_path(self, exporter, sample_tickets):
        """Test export accepts Path objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "manifest_log.csv"

            # Should accept Path object
            exporter.export(sample_tickets, output_path)

            assert output_path.exists()

    def test_export_with_string_path(self, exporter, sample_tickets):
        """Test export accepts string paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "manifest_log.csv")

            # Should accept string path
            exporter.export(sample_tickets, output_path)

            assert Path(output_path).exists()

    def test_regulatory_5_year_retention_note(self, exporter):
        """Test that docstring mentions 5-year retention requirement."""
        docstring = exporter.export.__doc__
        assert "5 years" in docstring or "5-year" in docstring
        assert "EPA" in docstring or "regulatory" in docstring.lower()
