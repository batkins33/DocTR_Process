"""Unit tests for filename parser."""
import pytest
from src.truck_tickets.utils.filename_parser import parse_filename, parse_structured, FilenameMeta


def test_parse_structured_full_format():
    """Test parsing a fully structured filename."""
    stem = "24-105__2025-10-17__SPG__EXPORT__CLASS_2_CONTAMINATED__WASTE_MANAGEMENT_LEWISVILLE"
    meta = parse_structured(stem)
    
    assert meta.job_code == "24-105"
    assert meta.date == "2025-10-17"
    assert meta.area == "SPG"
    assert meta.flow == "EXPORT"
    assert meta.material == "CLASS_2_CONTAMINATED"
    assert meta.vendor == "WASTE_MANAGEMENT_LEWISVILLE"


def test_parse_structured_minimal():
    """Test parsing with only job and date."""
    stem = "24-105__2025-10-17"
    meta = parse_structured(stem)
    
    assert meta.job_code == "24-105"
    assert meta.date == "2025-10-17"
    assert meta.area is None
    assert meta.flow is None
    assert meta.material is None
    assert meta.vendor is None


def test_parse_structured_partial():
    """Test parsing with some fields present."""
    stem = "24-105__2025-10-17__SPG__EXPORT"
    meta = parse_structured(stem)
    
    assert meta.job_code == "24-105"
    assert meta.date == "2025-10-17"
    assert meta.area == "SPG"
    assert meta.flow == "EXPORT"
    assert meta.material is None
    assert meta.vendor is None


def test_parse_structured_invalid_job_code():
    """Test that invalid job codes are rejected."""
    stem = "INVALID__2025-10-17__SPG"
    meta = parse_structured(stem)
    
    assert meta.job_code is None  # Invalid format
    assert meta.date == "2025-10-17"


def test_parse_structured_invalid_date():
    """Test that invalid dates are rejected."""
    stem = "24-105__not-a-date__SPG"
    meta = parse_structured(stem)
    
    assert meta.job_code == "24-105"
    assert meta.date is None  # Invalid date format


def test_parse_structured_date_out_of_range():
    """Test that dates outside reasonable range are rejected."""
    stem = "24-105__2050-10-17__SPG"  # Year 2050 is outside 2020-2030 range
    meta = parse_structured(stem)
    
    assert meta.job_code == "24-105"
    assert meta.date is None  # Out of range


def test_parse_structured_empty_components():
    """Test that empty components are handled correctly."""
    stem = "24-105__2025-10-17____EXPORT"  # Empty area field
    meta = parse_structured(stem)
    
    assert meta.job_code == "24-105"
    assert meta.date == "2025-10-17"
    assert meta.area is None  # Empty string treated as None
    assert meta.flow == "EXPORT"


def test_parse_structured_case_normalization():
    """Test that flow, material, and vendor are uppercased."""
    stem = "24-105__2025-10-17__spg__export__class_2_contaminated__waste_management"
    meta = parse_structured(stem)
    
    assert meta.area == "spg"  # Area not uppercased
    assert meta.flow == "EXPORT"  # Flow uppercased
    assert meta.material == "CLASS_2_CONTAMINATED"  # Material uppercased
    assert meta.vendor == "WASTE_MANAGEMENT"  # Vendor uppercased


def test_parse_filename_with_path():
    """Test parsing a full file path."""
    file_path = "batch1/24-105__2025-10-17__SPG__EXPORT__CLASS_2_CONTAMINATED__WM.pdf"
    result = parse_filename(file_path)
    
    assert result['job_code'] == "24-105"
    assert result['date'] == "2025-10-17"
    assert result['area'] == "SPG"
    assert result['flow'] == "EXPORT"
    assert result['material'] == "CLASS_2_CONTAMINATED"
    assert result['vendor'] == "WM"


def test_parse_filename_windows_path():
    """Test parsing a Windows-style path."""
    file_path = r"C:\batch\24-105__2025-10-17__SPG.pdf"
    result = parse_filename(file_path)
    
    assert result['job_code'] == "24-105"
    assert result['date'] == "2025-10-17"
    assert result['area'] == "SPG"


def test_parse_filename_no_extension():
    """Test parsing without file extension."""
    file_path = "24-105__2025-10-17__SPG"
    result = parse_filename(file_path)
    
    assert result['job_code'] == "24-105"
    assert result['date'] == "2025-10-17"
    assert result['area'] == "SPG"


def test_parse_filename_unstructured():
    """Test parsing an unstructured filename returns empty dict."""
    file_path = "random_file_name.pdf"
    result = parse_filename(file_path)
    
    # Should return dict with all None values
    assert result['job_code'] is None
    assert result['date'] is None
    assert result['area'] is None
    assert result['flow'] is None
    assert result['material'] is None
    assert result['vendor'] is None


def test_filemeta_as_dict():
    """Test FilenameMeta.as_dict() method."""
    meta = FilenameMeta(
        job_code="24-105",
        date="2025-10-17",
        area="SPG",
        flow="EXPORT",
        material="CLASS_2_CONTAMINATED",
        vendor="WM"
    )
    
    result = meta.as_dict()
    
    assert result == {
        'job_code': "24-105",
        'date': "2025-10-17",
        'area': "SPG",
        'flow': "EXPORT",
        'material': "CLASS_2_CONTAMINATED",
        'vendor': "WM"
    }


def test_parse_filename_graceful_error_handling():
    """Test that parser doesn't raise on invalid input."""
    # Should not raise, just return empty dict
    result = parse_filename(None)
    assert all(v is None for v in result.values())
    
    result = parse_filename("")
    assert all(v is None for v in result.values())
