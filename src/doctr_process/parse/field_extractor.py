"""Field extraction from OCR results."""

from typing import Dict, Any, Optional

from ..ocr.vendor_utils import extract_vendor_fields, FIELDS, HEIDELBERG_FIELDS


class FieldExtractor:
    """Extracts structured fields from OCR results."""
    
    def __init__(self, extraction_rules: Dict[str, Any]):
        self.extraction_rules = extraction_rules
    
    def extract_fields(self, ocr_result: Any, vendor_name: str) -> Dict[str, Optional[str]]:
        """Extract fields from OCR result based on vendor rules."""
        if ocr_result is not None:
            return extract_vendor_fields(ocr_result, vendor_name, self.extraction_rules)
        else:
            # Use appropriate field set based on vendor
            fields_to_use = HEIDELBERG_FIELDS if vendor_name == "Heidelberg" else FIELDS
            return {field: None for field in fields_to_use}
    
    def validate_fields(self, fields: Dict[str, Optional[str]]) -> Dict[str, str]:
        """Validate extracted fields and return issues."""
        issues = {}
        
        # Check for missing critical fields
        if not fields.get("ticket_number"):
            issues["ticket_number"] = "missing"
        
        if not fields.get("vendor"):
            issues["vendor"] = "missing"
        
        # Add more validation rules as needed
        return issues