import importlib.util
from pathlib import Path
import pytest

# Load the module directly to avoid importing heavy dependencies from package __init__
SPEC = importlib.util.spec_from_file_location(
    "filename_utils",
    Path(__file__).resolve().parents[1]
    / "src"
    / "doctr_process"
    / "processor"
    / "filename_utils.py",
)
filename_utils = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(filename_utils)


def test_format_output_filename_strips_trailing_count():
    meta = filename_utils.parse_input_filename_fuzzy(
        "24-105_2025-07-30_Class2_Podium_WM_145.pdf"
    )
    assert meta["base_name"] == "24-105_2025-07-30_Class2_Podium_WM"
    name = filename_utils.format_output_filename_camel("Roadstar", 52, meta, "pdf")
    assert name == "24-105_2025-07-30_Roadstar_Class2_Podium_WM_52.pdf"


class TestParseInputFilenameFuzzy:
    """Test the parse_input_filename_fuzzy function."""
    
    def test_parses_standard_format_with_count(self):
        """Test parsing of standard filename format with trailing count."""
        result = filename_utils.parse_input_filename_fuzzy("24-105_2025-07-30_Class2_Podium_WM_145.pdf")
        expected = {"base_name": "24-105_2025-07-30_Class2_Podium_WM"}
        assert result == expected
        
    def test_parses_standard_format_without_count(self):
        """Test parsing of standard filename format without trailing count."""
        result = filename_utils.parse_input_filename_fuzzy("24-105_2025-07-30_Class2_Podium_WM.pdf")
        expected = {"base_name": "24-105_2025-07-30_Class2_Podium_WM"}
        assert result == expected
        
    def test_handles_insufficient_segments(self):
        """Test handling of filenames with insufficient segments."""
        result = filename_utils.parse_input_filename_fuzzy("24-105_2025-07-30.pdf")
        assert result["base_name"] == "24-105_2025-07-30"
        
    def test_handles_no_extension(self):
        """Test handling of filenames without extension."""
        result = filename_utils.parse_input_filename_fuzzy("24-105_2025-07-30_Class2_Podium_WM")
        assert result["base_name"] == "24-105_2025-07-30_Class2_Podium_WM"
        
    def test_strips_trailing_numeric_segment(self):
        """Test that trailing numeric segments are stripped."""
        result = filename_utils.parse_input_filename_fuzzy("test_file_123.pdf")
        assert result["base_name"] == "test_file"
        
    def test_preserves_non_trailing_numbers(self):
        """Test that non-trailing numbers are preserved."""
        result = filename_utils.parse_input_filename_fuzzy("24-105_2025_more_text.pdf")
        assert result["base_name"] == "24-105_2025_more_text"


class TestSanitizeVendorName:
    """Test the sanitize_vendor_name function."""
    
    def test_replaces_underscores_with_periods(self):
        """Test replacement of underscores with periods."""
        result = filename_utils.sanitize_vendor_name("WL_Reid")
        assert result == "WL.Reid"
        
    def test_handles_multiple_underscores(self):
        """Test handling of multiple underscores."""
        result = filename_utils.sanitize_vendor_name("Test_Company_Name")
        assert result == "Test.Company.Name"
        
    def test_preserves_other_characters(self):
        """Test that other characters are preserved."""
        result = filename_utils.sanitize_vendor_name("Test-Company123")
        assert result == "Test-Company123"
        
    def test_handles_empty_string(self):
        """Test handling of empty string."""
        result = filename_utils.sanitize_vendor_name("")
        assert result == ""


class TestInsertVendor:
    """Test the _insert_vendor internal function."""
    
    def test_inserts_after_first_two_segments(self):
        """Test insertion after the first two underscore-separated segments."""
        result = filename_utils._insert_vendor("24-105_2025-07-30_Class2_Podium_WM", "Roadstar")
        assert result == "24-105_2025-07-30_Roadstar_Class2_Podium_WM"
        
    def test_handles_wm_suffix_insertion(self):
        """Test insertion before WM suffix for backwards compatibility."""
        result = filename_utils._insert_vendor("document_test_WM", "Vendor")
        assert result == "document_test_Vendor_WM"
        
    def test_fallback_concatenation(self):
        """Test fallback to simple concatenation when patterns don't match."""
        result = filename_utils._insert_vendor("simple_name", "Vendor")
        assert result == "simple_name_Vendor"
        
    def test_sanitizes_input(self):
        """Test that inputs are sanitized for filesystem safety."""
        result = filename_utils._insert_vendor("test<file>", "bad*vendor")
        assert result == "testfile_badvendor"
        
    def test_handles_empty_base(self):
        """Test handling of empty base name."""
        result = filename_utils._insert_vendor("", "Vendor")
        assert result == "Vendor"
        
    def test_case_insensitive_wm_matching(self):
        """Test case-insensitive matching of WM suffix."""
        result = filename_utils._insert_vendor("test_doc_wm", "Vendor")
        assert result == "test_doc_Vendor_wm"


class TestFormatOutputFilename:
    """Test the various format_output_filename functions."""
    
    def test_format_output_filename_basic(self):
        """Test basic output filename formatting."""
        meta = {"base_name": "24-105_2025-07-30_Class2_Podium_WM"}
        result = filename_utils.format_output_filename("roadstar", 52, meta, "pdf")
        assert result == "24-105_2025-07-30_ROADSTAR_Class2_Podium_WM_52.pdf"
        
    def test_format_output_filename_camel(self):
        """Test camel case output filename formatting."""
        meta = {"base_name": "24-105_2025-07-30_Class2_Podium_WM"}
        result = filename_utils.format_output_filename_camel("road star", 52, meta, "pdf")
        assert result == "24-105_2025-07-30_RoadStar_Class2_Podium_WM_52.pdf"
        
    def test_format_output_filename_lower(self):
        """Test lowercase output filename formatting."""
        meta = {"base_name": "24-105_2025-07-30_Class2_Podium_WM"}
        result = filename_utils.format_output_filename_lower("Road Star", 52, meta, "pdf")
        assert result == "24-105_2025-07-30_road_star_class2_podium_wm_52.pdf"
        
    def test_format_output_filename_snake(self):
        """Test snake case output filename formatting."""
        meta = {"base_name": "24-105_2025-07-30_Class2_Podium_WM"}
        result = filename_utils.format_output_filename_snake("Road Star", 52, meta, "pdf")
        assert result == "24-105_2025-07-30_road_star_class2_podium_wm_52.pdf"
        
    def test_format_output_filename_preserve(self):
        """Test preserve case output filename formatting."""
        meta = {"base_name": "24-105_2025-07-30_Class2_Podium_WM"}
        result = filename_utils.format_output_filename_preserve("Road Star", 52, meta, "pdf")
        assert result == "24-105_2025-07-30_Road Star_Class2_Podium_WM_52.pdf"
        
    def test_handles_missing_base_name(self):
        """Test handling when base_name is missing from meta."""
        meta = {}
        result = filename_utils.format_output_filename("vendor", 10, meta, "pdf")
        assert result == "VENDOR_10.pdf"


class TestJoinUtility:
    """Test the _join utility function."""
    
    def test_joins_with_underscores(self):
        """Test joining parts with underscores."""
        result = filename_utils._join(["part1", "part2", "part3"])
        assert result == "part1_part2_part3"
        
    def test_filters_empty_parts(self):
        """Test filtering of empty parts."""
        result = filename_utils._join(["part1", "", "part3", None])
        assert result == "part1_part3"
