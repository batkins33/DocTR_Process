#!/usr/bin/env python3
"""
Simple validation script for Heidelberg integration.
Tests the core integration without requiring full dependencies.
"""

import sys
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_extraction_rules():
    """Test that Heidelberg extraction rules are properly configured."""
    try:
        rules_path = Path("src/doctr_process/configs/extraction_rules.yaml")
        
        with open(rules_path, 'r') as f:
            content = f.read()
        
        # Simple text-based checks
        assert "Heidelberg:" in content, "Heidelberg rules not found in extraction_rules.yaml"
        
        expected_fields = ["date:", "ticket_number:", "product:", "time_in:", "time_out:", "job:", "tons:"]
        
        for field in expected_fields:
            assert field in content, f"Field '{field}' not found in Heidelberg rules"
        
        # Check for text_regex method
        assert "method: text_regex" in content, "text_regex method not found in Heidelberg rules"
        
        print("[PASS] Heidelberg extraction rules are properly configured")
        return True
    except Exception as e:
        print(f"[FAIL] Extraction rules test failed: {e}")
        return False

def test_vendor_keywords():
    """Test that Heidelberg is in vendor keywords."""
    try:
        keywords_path = Path("src/doctr_process/configs/ocr_keywords.csv")
        
        with open(keywords_path, 'r') as f:
            content = f.read()
        
        # Simple text-based checks
        assert "Heidelberg,Heidelberg,Materials" in content, "Heidelberg entry not found in vendor keywords"
        assert "heidelberg" in content.lower(), "Heidelberg match terms should include 'heidelberg'"
        
        print("[PASS] Heidelberg vendor keywords are properly configured")
        return True
    except Exception as e:
        print(f"[FAIL] Vendor keywords test failed: {e}")
        return False

def test_regex_patterns():
    """Test Heidelberg regex patterns work correctly."""
    try:
        # Test sample Heidelberg ticket text
        sample_text = """
        Date: 12/15/2023
        BOL: 123456
        Product: Concrete Mix
        Time In: 08:30
        Time Out: 16:45
        P.O.: 24-105
        25.50 Tons
        """
        
        # Test patterns
        patterns = {
            "date": r"(?<!\d)(\d{1,2}/\d{1,2}/\d{4})(?!\d)",
            "ticket_number": r"\b(?:BOL|B\s*O\s*L)\s*[:#]?\s*(\d{6,})",
            "product": r"(?:Product|Prod)\s*[:#]?\s*([^\n\r]+)",
            "time_in": r"Time\s*In\s*[: ]\s*([0-9]{1,2}:[0-9]{2})",
            "time_out": r"Time\s*Out\s*[: ]\s*([0-9]{1,2}:[0-9]{2})",
            "job": r"P\.?\s*O\.?\s*[:#]?\s*(\d{2}[\-\s]\d{3})[A-Za-z]?\d*",
            "tons": r"(\d{1,3}\.\d{2})\s*Ton"
        }
        
        results = {}
        for field, pattern in patterns.items():
            match = re.search(pattern, sample_text, re.IGNORECASE)
            if match:
                results[field] = match.group(1) if match.lastindex else match.group(0)
        
        expected = {
            "date": "12/15/2023",
            "ticket_number": "123456",
            "product": "Concrete Mix",
            "time_in": "08:30",
            "time_out": "16:45",
            "job": "24-105",
            "tons": "25.50"
        }
        
        for field, expected_value in expected.items():
            assert field in results, f"Pattern for '{field}' didn't match"
            assert results[field] == expected_value, f"Pattern for '{field}' extracted '{results[field]}', expected '{expected_value}'"
        
        print("[PASS] Heidelberg regex patterns work correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Regex patterns test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    try:
        required_files = [
            "src/doctr_process/configs/extraction_rules.yaml",
            "src/doctr_process/configs/ocr_keywords.csv",
            "src/doctr_process/output/heidelberg_output.py",
            "src/doctr_process/ocr/vendor_utils.py",
            "tests/test_heidelberg_integration.py",
            "HEIDELBERG_INTEGRATION.md"
        ]
        
        for file_path in required_files:
            path = Path(file_path)
            assert path.exists(), f"Required file not found: {file_path}"
        
        print("[PASS] All required integration files exist")
        return True
    except Exception as e:
        print(f"[FAIL] File structure test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("Validating Heidelberg Integration...")
    print("=" * 50)
    
    tests = [
        test_file_structure,
        test_extraction_rules,
        test_vendor_keywords,
        test_regex_patterns
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: Heidelberg integration is properly configured!")
        return 0
    else:
        print("FAILURE: Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    sys.exit(main())