"""Ticket number extraction."""

from .base_extractor import BaseExtractor


class TicketNumberExtractor(BaseExtractor):
    """Extracts ticket numbers from OCR text."""

    def extract(self, text: str, **kwargs) -> tuple[str | None, float]:
        """Extract ticket number using vendor template or fallback patterns.

        Args:
            text: Full OCR text from page
            **kwargs: Additional context

        Returns:
            (ticket_number, confidence_score)
        """
        # Try vendor-specific patterns first
        if self.vendor_template:
            ticket_config = self.vendor_template.get("ticket_number", {})

            # Extract from ROI if specified
            if "roi" in ticket_config:
                roi_text = self.extract_from_roi(text, ticket_config["roi"])
                text = roi_text or text

            # Try vendor-specific regex patterns
            if "regex" in ticket_config:
                patterns = ticket_config["regex"]
                if isinstance(patterns, dict):
                    patterns = [patterns]

                value, confidence = self.extract_with_regex(text, patterns)

                if value:
                    # Apply validation if specified
                    if "validation" in ticket_config:
                        is_valid, error = self.apply_validation(
                            value, ticket_config["validation"]
                        )
                        if not is_valid:
                            self.logger.warning(
                                f"Ticket number '{value}' failed validation: {error}"
                            )
                            # Continue to fallback
                        else:
                            return value, confidence
                    else:
                        return value, confidence

        # Fallback: Generic ticket number patterns
        fallback_patterns = [
            {"pattern": r"\bWM-\d{8}\b", "priority": 1, "capture_group": 0},
            {"pattern": r"\b\d{10}\b", "priority": 2, "capture_group": 0},
            {"pattern": r"\b\d{7,9}\b", "priority": 3, "capture_group": 0},
        ]

        value, confidence = self.extract_with_regex(text, fallback_patterns)

        if value:
            # Additional filtering: exclude date-like patterns
            if self._is_date_like(value):
                self.logger.debug(f"Rejecting date-like ticket number: {value}")
                return None, 0.0

            # Confidence penalty for fallback
            confidence *= 0.8
            return value, confidence

        return None, 0.0

    def _is_date_like(self, value: str) -> bool:
        """Check if value looks like a date (e.g., 20241017)."""
        # 8-digit numbers starting with 20 are likely dates
        if len(value) == 8 and value.startswith("20"):
            year = int(value[:4])
            if 2020 <= year <= 2030:
                return True
        return False
