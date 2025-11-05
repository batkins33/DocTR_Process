"""Tests for parse module."""

from unittest.mock import Mock, patch

from doctr_process.parse import FieldExtractor, VendorDetector


class TestFieldExtractor:
    """Test FieldExtractor functionality."""

    def test_extract_fields_with_result(self):
        """Test field extraction with OCR result."""
        extraction_rules = {"test_vendor": {"ticket_number": {"pattern": r"TKT-(\d+)"}}}

        extractor = FieldExtractor(extraction_rules)

        with patch(
            "doctr_process.parse.field_extractor.extract_vendor_fields"
        ) as mock_extract:
            mock_extract.return_value = {
                "ticket_number": "12345",
                "vendor": "test_vendor",
            }

            mock_result = Mock()
            fields = extractor.extract_fields(mock_result, "test_vendor")

            assert fields["ticket_number"] == "12345"
            assert fields["vendor"] == "test_vendor"

    def test_extract_fields_no_result(self):
        """Test field extraction with no OCR result."""
        extractor = FieldExtractor({})

        fields = extractor.extract_fields(None, "test_vendor")

        # Should return None for all fields
        assert all(value is None for value in fields.values())

    def test_validate_fields(self):
        """Test field validation."""
        extractor = FieldExtractor({})

        # Test missing critical fields
        fields = {"ticket_number": None, "vendor": None}
        issues = extractor.validate_fields(fields)

        assert "ticket_number" in issues
        assert "vendor" in issues
        assert issues["ticket_number"] == "missing"
        assert issues["vendor"] == "missing"

        # Test valid fields
        fields = {"ticket_number": "12345", "vendor": "test_vendor"}
        issues = extractor.validate_fields(fields)

        assert len(issues) == 0


class TestVendorDetector:
    """Test VendorDetector functionality."""

    def test_detect_vendor(self):
        """Test vendor detection."""
        vendor_rules = {"test_vendor": {"keywords": ["TEST", "VENDOR"]}}

        detector = VendorDetector(vendor_rules)

        with patch("doctr_process.parse.vendor_detector.find_vendor") as mock_find:
            mock_find.return_value = ("test_vendor", "type1", "high", "Test Vendor")

            result = detector.detect_vendor("This is a TEST document")

            assert result[0] == "test_vendor"
            assert result[3] == "Test Vendor"
