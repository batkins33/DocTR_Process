"""Tests for line items functionality."""

import json
import pytest
from unittest.mock import MagicMock

from src.doctr_process.ocr.vendor_utils import (
    detect_table_lines,
    parse_line_items,
    calculate_totals,
    extract_field,
    FIELDS
)


class MockWord:
    def __init__(self, value):
        self.value = value


class MockLine:
    def __init__(self, geometry, words):
        self.geometry = geometry
        self.words = [MockWord(w) for w in words]


class MockBlock:
    def __init__(self, lines):
        self.lines = lines


class MockPage:
    def __init__(self, blocks):
        self.blocks = blocks


def test_fields_includes_line_items():
    """Test that line_items is included in FIELDS."""
    assert "line_items" in FIELDS


def test_detect_table_lines():
    """Test table line detection functionality."""
    # Create mock OCR result with table-like structure
    lines = [
        MockLine(((0.1, 0.1), (0.9, 0.15)), ["Item", "Description", "Qty", "Amount"]),
        MockLine(((0.1, 0.2), (0.9, 0.25)), ["1", "Gravel", "10", "$100.00"]),
        MockLine(((0.1, 0.3), (0.9, 0.35)), ["2", "Sand", "5", "$50.00"]),
        MockLine(((0.1, 0.4), (0.9, 0.45)), ["Total", "", "", "$150.00"]),
    ]
    
    blocks = [MockBlock(lines)]
    result_page = MockPage(blocks)
    
    # Test detection
    detected_lines = detect_table_lines(result_page)
    
    assert len(detected_lines) == 4
    assert detected_lines[0][1] == "Item Description Qty Amount"
    assert detected_lines[1][1] == "1 Gravel 10 $100.00"


def test_detect_table_lines_with_roi():
    """Test table line detection with ROI filtering."""
    lines = [
        MockLine(((0.1, 0.1), (0.9, 0.15)), ["Header", "Outside", "ROI"]),
        MockLine(((0.5, 0.5), (0.8, 0.55)), ["Item", "Inside", "ROI"]),
    ]
    
    blocks = [MockBlock(lines)]
    result_page = MockPage(blocks)
    
    # ROI that includes only second line
    table_roi = [0.4, 0.4, 0.9, 0.6]
    detected_lines = detect_table_lines(result_page, table_roi)
    
    assert len(detected_lines) == 1
    assert detected_lines[0][1] == "Item Inside ROI"


def test_parse_line_items():
    """Test line items parsing functionality."""
    lines_with_y = [
        (0.1, "Item Description Qty Amount"),
        (0.2, "1 Gravel 10 tons $100.00"),
        (0.3, "2 Sand 5 tons $50.00"),
        (0.4, "Total $150.00"),
    ]
    
    result = parse_line_items(lines_with_y)
    
    assert result["item_count"] == 2
    assert len(result["items"]) == 2
    
    # Check first item
    item1 = result["items"][0]
    assert item1["quantity"] == 10.0
    assert item1["amount"] == 100.0
    assert item1["unit"] == "tons"
    
    # Check reconciliation
    reconciliation = result["reconciliation"]
    assert reconciliation["calculated_total"] == 150.0
    assert reconciliation["document_total"] == 150.0
    assert reconciliation["reconciled"] is True


def test_parse_line_items_partial_error():
    """Test line items parsing with malformed data."""
    lines_with_y = [
        (0.1, "Item Description Qty Amount"),
        (0.2, "1 Gravel invalid $100.00"),  # Invalid quantity
        (0.3, "2 Sand 5 tons $50.00"),      # Valid item
        (0.4, "Total $150.00"),
    ]
    
    result = parse_line_items(lines_with_y)
    
    assert result["item_count"] == 1  # Only one valid item
    assert result["parsing_status"] == "partial_error"


def test_calculate_totals():
    """Test total calculation functionality."""
    line_items_data = {
        "items": [
            {"amount": 100.0},
            {"amount": 50.0}
        ],
        "item_count": 2,
        "reconciliation": {
            "calculated_total": 150.0,
            "document_total": 150.0,
            "reconciled": True
        }
    }
    
    result = calculate_totals(line_items_data)
    
    assert result["status"] == "calculated"
    assert result["calculated_total"] == 150.0
    assert result["reconciled"] is True
    assert result["item_count"] == 2


def test_calculate_totals_no_items():
    """Test total calculation with no items."""
    result = calculate_totals({})
    
    assert result["status"] == "no_items"
    assert result["calculated_total"] == 0.0
    assert result["reconciled"] is False


def test_extract_field_line_items():
    """Test line items extraction through extract_field function."""
    # Create mock page
    lines = [
        MockLine(((0.1, 0.2), (0.9, 0.25)), ["1", "Gravel", "10", "tons", "$100.00"]),
        MockLine(((0.1, 0.3), (0.9, 0.35)), ["2", "Sand", "5", "tons", "$50.00"]),
    ]
    blocks = [MockBlock(lines)]
    result_page = MockPage(blocks)
    
    # Configure line items extraction
    field_rules = {
        "method": "line_items",
        "table_roi": [0.0, 0.0, 1.0, 1.0],
        "parsing_rules": {}
    }
    
    result = extract_field(result_page, field_rules, None, {})
    
    # Should return JSON string
    assert result is not None
    parsed_result = json.loads(result)
    assert parsed_result["item_count"] == 2
    assert len(parsed_result["items"]) == 2


def test_extract_field_line_items_no_data():
    """Test line items extraction with no table data."""
    # Create mock page with no table-like data
    lines = [
        MockLine(((0.1, 0.2), (0.9, 0.25)), ["Random", "text", "without", "amounts"]),
    ]
    blocks = [MockBlock(lines)]
    result_page = MockPage(blocks)
    
    field_rules = {
        "method": "line_items",
        "table_roi": [0.0, 0.0, 1.0, 1.0],
        "parsing_rules": {}
    }
    
    result = extract_field(result_page, field_rules, None, {})
    
    # Should return None when no line items found
    assert result is None