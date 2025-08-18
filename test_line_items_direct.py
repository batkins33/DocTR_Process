#!/usr/bin/env python3
"""Direct test of line items functionality without importing ocr module."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import json
from doctr_process.ocr.vendor_utils import detect_table_lines, parse_line_items, calculate_totals, FIELDS

# Mock classes for testing
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
    print("Testing FIELDS includes line_items...")
    assert "line_items" in FIELDS
    print("✓ FIELDS includes line_items")

def test_detect_table_lines():
    """Test table line detection functionality."""
    print("Testing table line detection...")
    
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
    print(f"✓ Detected {len(detected_lines)} table lines")

def test_parse_line_items():
    """Test line items parsing functionality."""
    print("Testing line items parsing...")
    
    lines_with_y = [
        (0.1, "Item Description Qty Amount"),
        (0.2, "1 Gravel 10 tons $100.00"),
        (0.3, "2 Sand 5 tons $50.00"),
        (0.4, "Total $150.00"),
    ]
    
    try:
        result = parse_line_items(lines_with_y)
        print(f"Parsed result: {result}")
        
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
        
        print(f"✓ Parsed {result['item_count']} line items")
        print(f"✓ Total reconciled: {reconciliation['reconciled']}")
    except Exception as e:
        print(f"Error in parsing: {e}")
        raise

def test_calculate_totals():
    """Test total calculation functionality."""
    print("Testing total calculation...")
    
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
    
    print(f"✓ Calculated totals: ${result['calculated_total']}")

if __name__ == "__main__":
    print("Running line items tests...")
    try:
        test_fields_includes_line_items()
        test_detect_table_lines()
        test_parse_line_items()
        test_calculate_totals()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)