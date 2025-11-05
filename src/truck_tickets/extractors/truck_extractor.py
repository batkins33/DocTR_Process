"""Truck number extraction - NEW v1.1 requirement."""

from .base_extractor import BaseExtractor


class TruckNumberExtractor(BaseExtractor):
    """Extracts truck numbers for cross-reference with accounting data.

    This is a non-critical field added in spec v1.1.
    """

    def extract(self, text: str, **kwargs) -> tuple[str | None, float]:
        """Extract truck number using vendor template or fallback patterns.

        Args:
            text: Full OCR text from page
            **kwargs: Additional context

        Returns:
            (truck_number, confidence_score)
        """
        # Try vendor-specific patterns first
        if self.vendor_template:
            truck_config = self.vendor_template.get("truck_number", {})

            # Extract from ROI if specified
            if "roi" in truck_config:
                roi_text = self.extract_from_roi(text, truck_config["roi"])
                text = roi_text or text

            # Try vendor-specific regex patterns
            if "regex" in truck_config:
                patterns = truck_config["regex"]
                if isinstance(patterns, dict):
                    patterns = [patterns]

                value, confidence = self.extract_with_regex(text, patterns)

                if value:
                    return value, confidence

        # Fallback: Generic truck number patterns
        fallback_patterns = [
            {
                "pattern": r"\bTruck\s*#?\s*:?\s*(\d{1,4})\b",
                "priority": 1,
                "capture_group": 1,
            },
            {
                "pattern": r"\bVehicle\s*#?\s*:?\s*(\d{1,4})\b",
                "priority": 2,
                "capture_group": 1,
            },
            {
                "pattern": r"\bUnit\s*#?\s*:?\s*(\d{1,4})\b",
                "priority": 3,
                "capture_group": 1,
            },
            {
                "pattern": r"\bTruck\s+(\d{1,4})\b",
                "priority": 4,
                "capture_group": 1,
            },
        ]

        value, confidence = self.extract_with_regex(text, fallback_patterns)

        if value:
            # Confidence penalty for fallback
            confidence *= 0.8
            return value, confidence

        # Truck number is optional - not finding it is OK
        self.logger.debug("No truck number found (optional field)")
        return None, 0.0
