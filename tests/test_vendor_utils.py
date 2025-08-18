import sys
from pathlib import Path
import pytest
import importlib.util

# Load the vendor_utils module directly to avoid tkinter dependency
SPEC = importlib.util.spec_from_file_location(
    "vendor_utils",
    Path(__file__).resolve().parents[1]
    / "src"
    / "doctr_process"
    / "ocr"
    / "vendor_utils.py",
)
vendor_utils = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vendor_utils)


class DummyWord:
    def __init__(self, value):
        self.value = value


class DummyLine:
    def __init__(self, text):
        self.words = [DummyWord(w) for w in text.split()]
        self.geometry = ((0, 0), (1, 1))


class DummyBlock:
    def __init__(self, lines):
        self.lines = [DummyLine(l) for l in lines]


class DummyPage:
    def __init__(self, lines):
        self.blocks = [DummyBlock(lines)]


class TestFindVendor:
    """Test the find_vendor function."""
    
    def test_find_vendor_basic_match(self):
        """Test basic vendor matching."""
        rules = [
            {
                "vendor_name": "ACME",
                "display_name": "ACME",
                "vendor_type": "yard",
                "match_terms": ["acme"],
                "exclude_terms": [],
            }
        ]
        vendor = vendor_utils.find_vendor("This is ACME company", rules)
        assert vendor[0] == "ACME"
        
    def test_find_vendor_case_insensitive(self):
        """Test case-insensitive vendor matching."""
        rules = [
            {
                "vendor_name": "ACME",
                "display_name": "ACME Corp",
                "vendor_type": "yard",
                "match_terms": ["acme"],
                "exclude_terms": [],
            }
        ]
        vendor = vendor_utils.find_vendor("Visit acme today", rules)
        assert vendor[0] == "ACME"  # vendor_name
        assert vendor[1] == "yard"  # vendor_type
        assert vendor[2] == "acme"  # match_term
        assert vendor[3] == "ACME Corp"  # display_name
        
    def test_find_vendor_with_exclusions(self):
        """Test vendor matching with exclusion terms."""
        rules = [
            {
                "vendor_name": "ACME",
                "display_name": "ACME",
                "vendor_type": "yard",
                "match_terms": ["acme"],
                "exclude_terms": ["warehouse"],
            }
        ]
        # Should not match when exclusion term is present
        vendor = vendor_utils.find_vendor("This is ACME warehouse", rules)
        assert vendor == ("", "", "", "")
        
        # Should match when exclusion term is not present
        vendor = vendor_utils.find_vendor("This is ACME company", rules)
        assert vendor[0] == "ACME"
        
    def test_find_vendor_multiple_rules(self):
        """Test vendor matching with multiple rules."""
        rules = [
            {
                "vendor_name": "ACME",
                "display_name": "ACME",
                "vendor_type": "yard",
                "match_terms": ["acme"],
                "exclude_terms": [],
            },
            {
                "vendor_name": "WAYNE_ENTERPRISES",
                "display_name": "Wayne Enterprises",
                "vendor_type": "company",
                "match_terms": ["wayne"],
                "exclude_terms": [],
            }
        ]
        vendor = vendor_utils.find_vendor("Wayne Industries report", rules)
        assert vendor[0] == "WAYNE_ENTERPRISES"  # vendor_name
        assert vendor[1] == "company"  # vendor_type
        assert vendor[2] == "wayne"  # match_term
        assert vendor[3] == "Wayne Enterprises"  # display_name
        
    def test_find_vendor_no_match(self):
        """Test vendor matching when no rules match."""
        rules = [
            {
                "vendor_name": "ACME",
                "display_name": "ACME",
                "vendor_type": "yard",
                "match_terms": ["acme"],
                "exclude_terms": [],
            }
        ]
        vendor = vendor_utils.find_vendor("This is XYZ company", rules)
        assert vendor == ("", "", "", "")


class TestExtractField:
    """Test the extract_field function."""
    
    def test_extract_field_roi_method(self):
        """Test field extraction using ROI method."""
        page = DummyPage(["Ticket 12345", "Other text"])
        field_rules = {
            "method": "roi",
            "roi": [0, 0, 1, 1],
            "regex": r"Ticket (\d+)"
        }
        result = vendor_utils.extract_field(page, field_rules)
        assert result == "12345"
        
    def test_extract_field_roi_method_no_regex(self):
        """Test field extraction using ROI method without regex."""
        page = DummyPage(["Ticket 12345"])
        field_rules = {
            "method": "roi",
            "roi": [0, 0, 1, 1]
        }
        result = vendor_utils.extract_field(page, field_rules)
        assert result == "Ticket 12345"
        
    def test_extract_field_below_label_method(self):
        """Test field extraction using below_label method."""
        page = DummyPage(["Ticket Number:", "12345", "Other line"])
        field_rules = {
            "method": "below_label",
            "label": "Ticket Number:",
            "regex": r"(\d+)"
        }
        result = vendor_utils.extract_field(page, field_rules)
        assert result == "12345"
        
    def test_extract_field_label_right_method(self):
        """Test field extraction using label_right method."""
        page = DummyPage(["Ticket Number: 12345"])
        field_rules = {
            "method": "label_right",
            "label": "Ticket Number:",
            "regex": r"(\d+)"
        }
        result = vendor_utils.extract_field(page, field_rules)
        assert result == "12345"
        
    def test_extract_field_invalid_method(self):
        """Test field extraction with invalid method."""
        page = DummyPage(["Some text"])
        field_rules = {
            "method": "invalid_method"
        }
        result = vendor_utils.extract_field(page, field_rules)
        assert result is None


class TestExtractVendorFields:
    """Test the extract_vendor_fields function."""
    
    def test_extract_vendor_fields_complete(self):
        """Test extraction of all vendor fields."""
        rules = {
            "ACME": {
                "ticket_number": {"method": "roi", "roi": [0, 0, 1, 1], "regex": r"Ticket (\d+)"},
                "manifest_number": {"method": "roi", "roi": [0, 0, 1, 1], "regex": r"Manifest (\d+)"},
                "material_type": {"method": "roi", "roi": [0, 0, 1, 1], "regex": r"Material: (\w+)"},
                "truck_number": {"method": "roi", "roi": [0, 0, 1, 1], "regex": r"Truck (\d+)"},
                "date": {"method": "roi", "roi": [0, 0, 1, 1], "regex": r"Date: ([\d\-]+)"},
            }
        }
        page = DummyPage([
            "Ticket 12345",
            "Manifest 9999999", 
            "Material: Gravel",
            "Truck 456",
            "Date: 2025-01-01"
        ])
        fields = vendor_utils.extract_vendor_fields(page, "ACME", rules)
        
        assert fields["ticket_number"] == "12345"
        assert fields["manifest_number"] == "9999999"
        assert fields["material_type"] == "Gravel"
        assert fields["truck_number"] == "456"
        assert fields["date"] == "2025-01-01"
        
    def test_extract_vendor_fields_fallback_to_default(self):
        """Test extraction falls back to DEFAULT rules when vendor not found."""
        rules = {
            "DEFAULT": {
                "ticket_number": {"method": "roi", "roi": [0, 0, 1, 1], "regex": r"Ticket (\d+)"},
            }
        }
        page = DummyPage(["Ticket 12345"])
        fields = vendor_utils.extract_vendor_fields(page, "UNKNOWN_VENDOR", rules)
        assert fields["ticket_number"] == "12345"
        
    def test_extract_vendor_fields_missing_rules(self):
        """Test extraction when field rules are missing."""
        rules = {
            "ACME": {
                "ticket_number": {"method": "roi", "roi": [0, 0, 1, 1], "regex": r"Ticket (\d+)"},
                # manifest_number is missing
            }
        }
        page = DummyPage(["Ticket 12345"])
        fields = vendor_utils.extract_vendor_fields(page, "ACME", rules)
        
        assert fields["ticket_number"] == "12345"
        assert fields["manifest_number"] is None
        
    def test_extract_vendor_fields_no_method(self):
        """Test extraction when method is missing from field rules."""
        rules = {
            "ACME": {
                "ticket_number": {"roi": [0, 0, 1, 1], "regex": r"Ticket (\d+)"},  # No method
            }
        }
        page = DummyPage(["Ticket 12345"])
        fields = vendor_utils.extract_vendor_fields(page, "ACME", rules)
        assert fields["ticket_number"] is None


class TestLoadVendorRulesFromCsv:
    """Test the load_vendor_rules_from_csv function."""
    
    def test_load_vendor_rules_from_csv(self, tmp_path):
        """Test loading vendor rules from CSV file."""
        csv_content = """vendor_name,display_name,vendor_type,vendor_match,vendor_excludes
ACME,ACME Corp,yard,"acme,acme corp",warehouse
WAYNE,Wayne Enterprises,company,wayne,
"""
        csv_file = tmp_path / "test_vendors.csv"
        csv_file.write_text(csv_content)
        
        rules = vendor_utils.load_vendor_rules_from_csv(str(csv_file))
        
        assert len(rules) == 2
        
        acme_rule = rules[0]
        assert acme_rule["vendor_name"] == "ACME"
        assert acme_rule["display_name"] == "ACME Corp"
        assert acme_rule["vendor_type"] == "yard"
        assert acme_rule["match_terms"] == ["acme", "acme corp"]
        assert acme_rule["exclude_terms"] == ["warehouse"]
        
        wayne_rule = rules[1]
        assert wayne_rule["vendor_name"] == "WAYNE"
        assert wayne_rule["display_name"] == "Wayne Enterprises"
        assert wayne_rule["vendor_type"] == "company"
        assert wayne_rule["match_terms"] == ["wayne"]
        assert wayne_rule["exclude_terms"] == []


class TestFieldConstants:
    """Test the FIELDS constant and related functionality."""
    
    def test_fields_constant_exists(self):
        """Test that the FIELDS constant is defined."""
        assert hasattr(vendor_utils, 'FIELDS')
        assert isinstance(vendor_utils.FIELDS, list)
        
    def test_fields_contains_expected_fields(self):
        """Test that FIELDS contains the expected field names."""
        expected_fields = ["ticket_number", "manifest_number", "material_type", "truck_number", "date"]
        for field in expected_fields:
            assert field in vendor_utils.FIELDS
