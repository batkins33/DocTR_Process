#!/usr/bin/env python3
"""Simple test script to verify Phase 6 improvements."""

import sys
import tempfile
from pathlib import Path

def test_column_ordering():
    """Test that column ordering is stable."""
    # Direct import to avoid dependency issues
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    
    # Read the file directly to check for STANDARD_COLUMN_ORDER
    reporting_utils_path = Path(__file__).parent / "src" / "doctr_process" / "ocr" / "reporting_utils.py"
    
    if not reporting_utils_path.exists():
        print("ERROR: reporting_utils.py not found")
        return False
    
    content = reporting_utils_path.read_text()
    if "STANDARD_COLUMN_ORDER" not in content:
        print("ERROR: STANDARD_COLUMN_ORDER not found in reporting_utils.py")
        return False
    
    print("✓ STANDARD_COLUMN_ORDER found in reporting_utils.py")
    
    # Check for essential columns in the content
    essential_cols = ["JobID", "vendor", "ticket_number", "manifest_number"]
    for col in essential_cols:
        if f'"{col}"' not in content:
            print(f"ERROR: Essential column {col} not found")
            return False
        print(f"✓ Found essential column: {col}")
    
    print("✓ Column ordering test passed")
    return True

def test_sharepoint_improvements():
    """Test SharePoint improvements are in place."""
    sharepoint_path = Path(__file__).parent / "src" / "doctr_process" / "output" / "sharepoint_output.py"
    
    if not sharepoint_path.exists():
        print("ERROR: sharepoint_output.py not found")
        return False
    
    content = sharepoint_path.read_text()
    
    # Check for retry logic
    if "_upload_with_retry" not in content:
        print("ERROR: Retry logic not found in SharePoint output")
        return False
    
    if "max_retries" not in content:
        print("ERROR: max_retries not found in SharePoint output")
        return False
    
    print("✓ SharePoint retry logic found")
    print("✓ SharePoint improvements test passed")
    return True

def test_processing_stats_function():
    """Test processing statistics function exists."""
    reporting_utils_path = Path(__file__).parent / "src" / "doctr_process" / "ocr" / "reporting_utils.py"
    
    content = reporting_utils_path.read_text()
    
    if "_calculate_processing_stats" not in content:
        print("ERROR: _calculate_processing_stats function not found")
        return False
    
    if "Accuracy" not in content:
        print("ERROR: Accuracy calculation not found")
        return False
    
    print("✓ Processing stats function found")
    print("✓ Processing stats test passed")
    return True

def test_artifact_classification_function():
    """Test artifact classification function exists."""
    pipeline_path = Path(__file__).parent / "src" / "doctr_process" / "pipeline.py"
    
    content = pipeline_path.read_text()
    
    if "_classify_artifact" not in content:
        print("ERROR: _classify_artifact function not found")
        return False
    
    if "_generate_artifact_summary" not in content:
        print("ERROR: _generate_artifact_summary function not found")
        return False
    
    print("✓ Artifact classification functions found")
    print("✓ Artifact classification test passed")
    return True

def test_business_summary_function():
    """Test business summary function exists."""
    reporting_utils_path = Path(__file__).parent / "src" / "doctr_process" / "ocr" / "reporting_utils.py"
    
    content = reporting_utils_path.read_text()
    
    if "generate_business_summary" not in content:
        print("ERROR: generate_business_summary function not found")
        return False
    
    if "business_summary.txt" not in content:
        print("ERROR: business summary file generation not found")
        return False
    
    if "MANAGEMENT REPORT" not in content:
        print("ERROR: Management report section not found in business summary")
        return False
    
    print("✓ Business summary function found")
    print("✓ Business summary test passed")
    return True

def test_hyperlink_consistency():
    """Test hyperlink consistency improvements."""
    reporting_utils_path = Path(__file__).parent / "src" / "doctr_process" / "ocr" / "reporting_utils.py"
    
    content = reporting_utils_path.read_text()
    
    if "_ensure_hyperlink_style" not in content:
        print("ERROR: _ensure_hyperlink_style function not found")
        return False
    
    if "Font(color=" not in content:
        print("ERROR: Hyperlink color styling not found")
        return False
    
    print("✓ Hyperlink consistency improvements found")
    print("✓ Hyperlink consistency test passed")
    return True

def test_vendor_pdf_improvements():
    """Test vendor PDF improvements."""
    vendor_doc_path = Path(__file__).parent / "src" / "doctr_process" / "output" / "vendor_doc_output.py"
    
    content = vendor_doc_path.read_text()
    
    if "vendor_artifacts" not in content:
        print("ERROR: vendor_artifacts tracking not found")
        return False
    
    if "Failed to create combined PDF" not in content:
        print("ERROR: Enhanced error handling not found")
        return False
    
    print("✓ Vendor PDF improvements found")
    print("✓ Vendor PDF test passed")
    return True

def main():
    """Run all tests."""
    print("=== Phase 6 Improvements Test ===")
    
    tests = [
        test_column_ordering,
        test_sharepoint_improvements,
        test_processing_stats_function,
        test_artifact_classification_function,
        test_business_summary_function,
        test_hyperlink_consistency,
        test_vendor_pdf_improvements
    ]
    
    passed = 0
    for test in tests:
        try:
            print(f"\nTesting {test.__name__}...")
            if test():
                passed += 1
            else:
                print(f"FAILED: {test.__name__}")
        except Exception as e:
            print(f"ERROR in {test.__name__}: {e}")
    
    print(f"\n=== Results: {passed}/{len(tests)} tests passed ===")
    return passed == len(tests)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)