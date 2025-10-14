"""Test Heidelberg integration in DocTR Process."""

import pytest
from unittest.mock import Mock, MagicMock

from doctr_process.ocr.vendor_utils import extract_vendor_fields, HEIDELBERG_FIELDS
from doctr_process.parse.vendor_detector import VendorDetector
from doctr_process.parse.field_extractor import FieldExtractor
from doctr_process.output.heidelberg_output import HeidelbergOutputHandler


def test_heidelberg_vendor_detection():
    """Test that Heidelberg vendor is detected correctly."""
    vendor_rules = [
        {
            "vendor_name": "Heidelberg",
            "display_name": "Heidelberg",
            "vendor_type": "Materials",
            "match_terms": ["heidelberg"],
            "exclude_terms": []
        }
    ]
    
    detector = VendorDetector(vendor_rules)
    
    # Test text containing Heidelberg
    test_text = "This is a Heidelberg ticket with BOL: 123456"
    vendor_name, vendor_type, confidence, display_name = detector.detect_vendor(test_text)
    
    assert vendor_name == "Heidelberg"
    assert vendor_type == "Materials"
    assert display_name == "Heidelberg"


def test_heidelberg_field_extraction():
    """Test Heidelberg-specific field extraction."""
    # Mock OCR result page
    mock_result_page = Mock()
    mock_result_page.blocks = []
    
    # Mock block with Heidelberg ticket data
    mock_block = Mock()
    mock_line = Mock()
    mock_word1 = Mock()
    mock_word1.value = "Date: 12/15/2023 BOL: 123456 Product: Concrete Time In: 08:30 Time Out: 16:45 P.O.: 24-105 Tons: 25.50"
    mock_line.words = [mock_word1]
    mock_block.lines = [mock_line]
    mock_result_page.blocks = [mock_block]
    
    # Test extraction rules for Heidelberg
    extraction_rules = {
        "Heidelberg": {
            "date": {
                "method": "text_regex",
                "regex": r"(?<!\d)(\d{1,2}/\d{1,2}/\d{4})(?!\d)"
            },
            "ticket_number": {
                "method": "text_regex",
                "regex": r"\bBOL:\s*(\d{6,})",
                "regex_flags": "IGNORECASE"
            },
            "product": {
                "method": "text_regex",
                "regex": r"Product:\s*([^\s]+)",
                "regex_flags": "IGNORECASE"
            },
            "tons": {
                "method": "text_regex",
                "regex": r"Tons:\s*(\d+\.\d{2})",
                "regex_flags": "IGNORECASE"
            }
        }
    }
    
    result = extract_vendor_fields(mock_result_page, "Heidelberg", extraction_rules)
    
    assert result["date"] == "12/15/2023"
    assert result["ticket_number"] == "123456"
    assert result["product"] == "Concrete"
    assert result["tons"] == 25.50  # Should be converted to float


def test_heidelberg_output_handler():
    """Test Heidelberg output handler generates reports correctly."""
    config = {
        "output_dir": "./test_outputs",
        "include_xlsx": True
    }
    
    handler = HeidelbergOutputHandler(config)
    
    # Mock results with Heidelberg data
    results = [
        {
            "file": "test.pdf",
            "page": 1,
            "vendor": "Heidelberg",
            "date": "12/15/2023",
            "ticket_number": "123456",
            "product": "Concrete",
            "time_in": "08:30",
            "time_out": "16:45",
            "job": "24-105",
            "tons": 25.50
        },
        {
            "file": "test.pdf",
            "page": 2,
            "vendor": "Other",
            "ticket_number": "789012"
        }
    ]
    
    # Mock pandas and file operations
    with pytest.MonkeyPatch().context() as m:
        mock_df = Mock()
        mock_df.to_csv = Mock()
        mock_df.to_excel = Mock()
        mock_df.sort_values = Mock(return_value=mock_df)
        
        mock_pd = Mock()
        mock_pd.DataFrame = Mock(return_value=mock_df)
        m.setattr("doctr_process.output.heidelberg_output.pd", mock_pd)
        
        # Test write method
        handler.write(results, config)
        
        # Verify DataFrame was created with Heidelberg data only
        mock_pd.DataFrame.assert_called_once()
        call_args = mock_pd.DataFrame.call_args[0][0]
        assert len(call_args) == 1  # Only one Heidelberg result
        assert call_args[0]["Ticket"] == "123456"


def test_heidelberg_fields_list():
    """Test that Heidelberg fields are properly defined."""
    expected_fields = ["date", "ticket_number", "product", "time_in", "time_out", "job", "tons"]
    assert HEIDELBERG_FIELDS == expected_fields


if __name__ == "__main__":
    pytest.main([__file__])