#!/usr/bin/env python3
"""Test Heidelberg vendor detection with sample text."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from doctr_process.ocr.vendor_utils import load_vendor_rules_from_csv, find_vendor

def test_heidelberg_detection():
    """Test Heidelberg detection with sample ticket text."""
    
    # Load vendor rules
    vendor_rules = load_vendor_rules_from_csv("src/doctr_process/configs/ocr_keywords.csv")
    
    # Sample Heidelberg ticket text
    sample_texts = [
        # Test 1: Contains "heidelberg"
        "This is a Heidelberg Materials ticket with BOL: 123456",
        
        # Test 2: Contains "bridgeport" 
        "Bridgeport Materials BOL: 789012 Date: 12/15/2023",
        
        # Test 3: Contains "BOL:" pattern
        "Material Delivery BOL: 456789 Time In: 08:30 Time Out: 16:45",
        
        # Test 4: Contains "Time In:" pattern
        "Delivery Receipt Time In: 09:15 Time Out: 17:30 Product: Concrete",
        
        # Test 5: Contains "Time Out:" pattern  
        "Ticket #123 Time Out: 15:45 Job: 24-105 Tons: 25.50",
        
        # Test 6: Typical Heidelberg ticket
        """
        Date: 12/15/2023
        BOL: 123456
        Product: Concrete Mix
        Time In: 08:30
        Time Out: 16:45
        P.O.: 24-105
        25.50 Tons
        """,
        
        # Test 7: Non-Heidelberg ticket (should not match)
        "Lindamood Demolition Ticket #789 Material: Dirt"
    ]
    
    print("Testing Heidelberg vendor detection...")
    print("=" * 50)
    
    for i, text in enumerate(sample_texts, 1):
        vendor_name, vendor_type, matched_term, display_name = find_vendor(text, vendor_rules)
        
        print(f"Test {i}:")
        print(f"  Text: {text[:50]}...")
        print(f"  Detected: {vendor_name} ({vendor_type}) - matched: '{matched_term}'")
        print(f"  Display: {display_name}")
        print()

if __name__ == "__main__":
    test_heidelberg_detection()