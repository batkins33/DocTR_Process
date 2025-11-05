"""Vendor detection from OCR text."""

from typing import Any

from ..ocr.vendor_utils import find_vendor


class VendorDetector:
    """Detects vendor information from OCR text."""

    def __init__(self, vendor_rules: dict[str, Any]):
        self.vendor_rules = vendor_rules

    def detect_vendor(self, text: str) -> tuple[str, str, str, str]:
        """Detect vendor from OCR text.

        Returns:
            Tuple of (vendor_name, vendor_type, confidence, display_name)
        """
        return find_vendor(text, self.vendor_rules)
