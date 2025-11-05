"""Base class for field extractors."""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any


class BaseExtractor(ABC):
    """Base class for field extraction from OCR text."""

    def __init__(self, vendor_template: dict | None = None):
        """Initialize extractor with optional vendor template.

        Args:
            vendor_template: Vendor-specific extraction rules from YAML
        """
        self.vendor_template = vendor_template or {}
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract(self, text: str, **kwargs) -> tuple[str | None, float]:
        """Extract field value from OCR text.

        Args:
            text: Full OCR text from page
            **kwargs: Additional context (e.g., filename, metadata)

        Returns:
            Tuple of (extracted_value, confidence_score)
            Returns (None, 0.0) if extraction fails
        """
        pass

    def extract_with_regex(
        self, text: str, patterns: list[dict[str, Any]]
    ) -> tuple[str | None, float]:
        """Extract using multiple regex patterns with priority.

        Args:
            text: OCR text to search
            patterns: List of pattern dicts with 'pattern', 'priority', optional 'capture_group'

        Returns:
            (extracted_value, confidence_score)
        """
        # Sort by priority (lower number = higher priority)
        sorted_patterns = sorted(patterns, key=lambda p: p.get("priority", 999))

        for pattern_config in sorted_patterns:
            pattern = pattern_config["pattern"]
            capture_group = pattern_config.get("capture_group", 0)

            try:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    value = match.group(capture_group).strip()
                    if value:
                        # Higher priority = higher confidence
                        confidence = 1.0 - (pattern_config.get("priority", 1) - 1) * 0.1
                        confidence = max(0.5, min(1.0, confidence))

                        self.logger.debug(
                            f"Matched pattern '{pattern}' -> '{value}' "
                            f"(confidence: {confidence:.2f})"
                        )
                        return value, confidence
            except re.error as e:
                self.logger.error(f"Invalid regex pattern '{pattern}': {e}")
                continue

        return None, 0.0

    def extract_from_roi(
        self,
        text: str,
        roi: dict[str, int],
        full_page_dimensions: tuple[int, int] | None = None,
    ) -> str:
        """Extract text from Region of Interest.

        Note: This is a simplified version. Full implementation would use
        DocTR's word-level coordinates to filter text within ROI.

        Args:
            text: Full OCR text
            roi: Dict with x, y, width, height
            full_page_dimensions: (width, height) of page for normalization

        Returns:
            Text within ROI (approximate)
        """
        # TODO: Implement proper ROI extraction using DocTR word coordinates
        # For now, return full text (will be enhanced with DocTR integration)
        self.logger.debug("ROI extraction not yet implemented, using full text")
        return text

    def apply_validation(
        self, value: str, validation_rules: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """Apply validation rules to extracted value.

        Args:
            value: Extracted value to validate
            validation_rules: Dict with validation constraints

        Returns:
            (is_valid, error_message)
        """
        if not value:
            return True, None  # Empty values handled upstream

        # Pattern validation
        if "pattern" in validation_rules:
            if not re.match(validation_rules["pattern"], value):
                return False, f"Value '{value}' does not match pattern"

        # Length validation
        if "min_length" in validation_rules:
            if len(value) < validation_rules["min_length"]:
                return False, f"Value too short (min: {validation_rules['min_length']})"

        if "max_length" in validation_rules:
            if len(value) > validation_rules["max_length"]:
                return False, f"Value too long (max: {validation_rules['max_length']})"

        # Exclude patterns
        if "exclude_patterns" in validation_rules:
            for exclude_pattern in validation_rules["exclude_patterns"]:
                if re.match(exclude_pattern, value):
                    return False, f"Value matches excluded pattern: {exclude_pattern}"

        return True, None
