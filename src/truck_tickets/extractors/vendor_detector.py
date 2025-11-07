"""Vendor detection using keywords and logo matching."""

import logging

from ..utils import SynonymNormalizer
from .logo_detector import LogoDetector


class VendorDetector:
    """Detects vendor from OCR text and optional logo matching."""

    def __init__(
        self,
        vendor_templates: dict | None = None,
        normalizer: SynonymNormalizer | None = None,
        logo_detector: LogoDetector | None = None,
        enable_logo_detection: bool = True,
    ):
        """Initialize vendor detector.

        Args:
            vendor_templates: Dict of vendor_name -> template_config
            normalizer: SynonymNormalizer for text canonicalization
            logo_detector: LogoDetector instance (created if None)
            enable_logo_detection: Whether to use logo detection (default: True)
        """
        self.vendor_templates = vendor_templates or {}
        self.normalizer = normalizer or SynonymNormalizer()
        self.enable_logo_detection = enable_logo_detection
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize logo detector if enabled
        if self.enable_logo_detection:
            self.logo_detector = logo_detector or LogoDetector()
            # Load templates from vendor configs
            if self.vendor_templates:
                self.logo_detector.load_templates_from_config(self.vendor_templates)
        else:
            self.logo_detector = None

    def detect(self, text: str, **kwargs) -> tuple[str | None, float]:
        """Detect vendor from OCR text and optional logo matching.

        Args:
            text: Full OCR text from page
            **kwargs: Additional context:
                - filename_vendor: Vendor hint from filename
                - image: PIL Image or numpy array for logo detection
                - vendor_filter: List of vendor names to check

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

        # Priority 2: Logo detection (if enabled and image provided)
        if self.enable_logo_detection and self.logo_detector:
            image = kwargs.get("image")
            if image is not None:
                vendor_filter = kwargs.get("vendor_filter")
                logo_vendor, logo_confidence = self.logo_detector.detect(
                    image, vendor_filter=vendor_filter
                )

                if logo_vendor and logo_confidence >= 0.85:
                    self.logger.info(
                        f"Vendor from logo detection: {logo_vendor} "
                        f"(confidence: {logo_confidence:.3f})"
                    )
                    return logo_vendor, logo_confidence

        # Priority 3: Template-based keyword matching
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

        # Priority 4: Generic keyword matching with normalization
        # Note: This is a fallback. Landfill vendors should be detected via:
        #   1. Logo detection (Priority 2) - preferred for invoices
        #   2. Template keywords (Priority 3) - from vendor YAML aliases
        vendor_keywords = [
            "Waste Management",
            "WM",
            "Republic Services",
            "Republic",
            "Skyline",
            "DFW",
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
