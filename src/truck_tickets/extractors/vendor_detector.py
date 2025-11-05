"""Vendor detection using keywords and logo matching."""

import logging

from ..utils import SynonymNormalizer


class VendorDetector:
    """Detects vendor from OCR text and optional logo matching."""

    def __init__(
        self, vendor_templates: dict | None = None, normalizer: SynonymNormalizer | None = None
    ):
        """Initialize vendor detector.

        Args:
            vendor_templates: Dict of vendor_name -> template_config
            normalizer: SynonymNormalizer for text canonicalization
        """
        self.vendor_templates = vendor_templates or {}
        self.normalizer = normalizer or SynonymNormalizer()
        self.logger = logging.getLogger(self.__class__.__name__)

    def detect(self, text: str, **kwargs) -> tuple[str | None, float]:
        """Detect vendor from OCR text.

        Args:
            text: Full OCR text from page
            **kwargs: Additional context (e.g., filename_vendor, image for logo matching)

        Returns:
            (canonical_vendor_name, confidence_score)
        """
        # Priority 1: Filename hint (highest confidence)
        filename_vendor = kwargs.get("filename_vendor")
        if filename_vendor:
            normalized = self.normalizer.normalize_vendor(filename_vendor)
            if normalized:
                self.logger.debug(f"Vendor from filename: {normalized}")
                return normalized, 1.0

        # Priority 2: Template-based keyword matching
        text_lower = text.lower()
        best_match = None
        best_confidence = 0.0

        for vendor_name, template in self.vendor_templates.items():
            # Check aliases
            aliases = template.get("vendor", {}).get("aliases", [])

            for alias in aliases:
                if alias.lower() in text_lower:
                    confidence = 0.95  # High confidence for alias match
                    if confidence > best_confidence:
                        best_match = vendor_name
                        best_confidence = confidence
                        self.logger.debug(
                            f"Matched vendor alias '{alias}' -> {vendor_name}"
                        )

            # Check logo text keywords
            logo_text_config = template.get("logo_text", {})
            if logo_text_config:
                keywords = logo_text_config.get("keywords", [])
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        confidence = 0.90
                        if confidence > best_confidence:
                            best_match = vendor_name
                            best_confidence = confidence
                            self.logger.debug(
                                f"Matched logo keyword '{keyword}' -> {vendor_name}"
                            )

        if best_match:
            return best_match, best_confidence

        # Priority 3: Generic keyword matching with normalization
        vendor_keywords = [
            "Waste Management",
            "WM",
            "LDI",
            "Post Oak",
            "Beck",
            "NTX",
            "UTX",
        ]

        for keyword in vendor_keywords:
            if keyword.lower() in text_lower:
                normalized = self.normalizer.normalize_vendor(keyword)
                if normalized:
                    self.logger.debug(
                        f"Generic vendor match: {keyword} -> {normalized}"
                    )
                    return normalized, 0.75

        # No vendor detected
        self.logger.warning("No vendor detected in OCR text")
        return None, 0.0

    def get_template(self, vendor_name: str) -> dict | None:
        """Get vendor template configuration.

        Args:
            vendor_name: Canonical vendor name

        Returns:
            Vendor template dict or None
        """
        return self.vendor_templates.get(vendor_name)
