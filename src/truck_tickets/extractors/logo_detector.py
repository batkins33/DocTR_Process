"""Logo detection using OpenCV template matching for vendor identification."""

import logging
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image


class LogoDetector:
    """Detects vendor logos in ticket images using template matching.

    Uses OpenCV template matching to identify vendor logos in specific
    regions of interest (ROI) on truck ticket images. Provides confidence
    scores for integration with fallback detection methods.
    """

    def __init__(self, templates_dir: Path | str | None = None):
        """Initialize logo detector.

        Args:
            templates_dir: Directory containing logo template images.
                          Defaults to src/truck_tickets/templates/vendors/assets/
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        if templates_dir is None:
            # Default to templates/vendors/assets/
            templates_dir = (
                Path(__file__).parent.parent / "templates" / "vendors" / "assets"
            )

        self.templates_dir = Path(templates_dir)
        self.logo_templates: dict[str, dict[str, Any]] = {}

        self.logger.debug(
            f"LogoDetector initialized with templates_dir: {self.templates_dir}"
        )

    def load_template(
        self,
        vendor_name: str,
        template_path: str | Path,
        roi: dict[str, int] | None = None,
        threshold: float = 0.85,
        method: str = "template_match",
    ) -> None:
        """Load a logo template for a vendor.

        Args:
            vendor_name: Canonical vendor name (e.g., "WASTE_MANAGEMENT_LEWISVILLE")
            template_path: Path to logo template image (relative to templates_dir or absolute)
            roi: Region of interest dict with keys: x, y, width, height
            threshold: Confidence threshold for matching (0.0-1.0)
            method: Matching method ("template_match" or "feature_match")
        """
        # Resolve template path
        if not Path(template_path).is_absolute():
            template_path = self.templates_dir / template_path
        else:
            template_path = Path(template_path)

        if not template_path.exists():
            self.logger.warning(
                f"Logo template not found for {vendor_name}: {template_path}"
            )
            return

        # Load template image
        try:
            template_img = cv2.imread(str(template_path), cv2.IMREAD_GRAYSCALE)
            if template_img is None:
                self.logger.error(f"Failed to load template image: {template_path}")
                return

            self.logo_templates[vendor_name] = {
                "template": template_img,
                "path": template_path,
                "roi": roi or {"x": 0, "y": 0, "width": 400, "height": 200},
                "threshold": threshold,
                "method": method,
            }

            self.logger.info(
                f"Loaded logo template for {vendor_name}: {template_path.name}"
            )

        except Exception as e:
            self.logger.error(
                f"Error loading logo template for {vendor_name}: {e}",
                exc_info=True,
            )

    def load_templates_from_config(self, vendor_configs: dict[str, dict]) -> None:
        """Load logo templates from vendor configuration dictionaries.

        Args:
            vendor_configs: Dict of vendor_name -> vendor_config
                           Each config should have a "logo" section with:
                           - path: Template image path
                           - roi: Region of interest
                           - threshold: Confidence threshold
                           - method: Matching method
        """
        for vendor_name, config in vendor_configs.items():
            logo_config = config.get("logo", {})

            if not logo_config or not logo_config.get("path"):
                self.logger.debug(f"No logo config for {vendor_name}, skipping")
                continue

            self.load_template(
                vendor_name=vendor_name,
                template_path=logo_config.get("path"),
                roi=logo_config.get("roi"),
                threshold=logo_config.get("threshold", 0.85),
                method=logo_config.get("method", "template_match"),
            )

    def detect(
        self,
        image: np.ndarray | Image.Image,
        vendor_filter: list[str] | None = None,
    ) -> tuple[str | None, float]:
        """Detect vendor logo in an image.

        Args:
            image: Input image (numpy array or PIL Image)
            vendor_filter: Optional list of vendor names to check (checks all if None)

        Returns:
            Tuple of (vendor_name, confidence_score)
            Returns (None, 0.0) if no logo detected above threshold
        """
        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            image = np.array(image)

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray_image = image

        best_match = None
        best_confidence = 0.0

        # Filter vendors if specified
        vendors_to_check = (
            {
                v: self.logo_templates[v]
                for v in vendor_filter
                if v in self.logo_templates
            }
            if vendor_filter
            else self.logo_templates
        )

        for vendor_name, template_data in vendors_to_check.items():
            confidence = self._match_template(gray_image, template_data)

            if (
                confidence > best_confidence
                and confidence >= template_data["threshold"]
            ):
                best_match = vendor_name
                best_confidence = confidence
                self.logger.debug(
                    f"Logo match: {vendor_name} (confidence: {confidence:.3f})"
                )

        if best_match:
            self.logger.info(
                f"Detected vendor logo: {best_match} (confidence: {best_confidence:.3f})"
            )
        else:
            self.logger.debug("No vendor logo detected above threshold")

        return best_match, best_confidence

    def _match_template(
        self,
        image: np.ndarray,
        template_data: dict[str, Any],
    ) -> float:
        """Perform template matching on an image.

        Args:
            image: Grayscale input image
            template_data: Template data dict with template, roi, method

        Returns:
            Confidence score (0.0-1.0)
        """
        try:
            # Extract ROI from image
            roi = template_data["roi"]
            x, y = roi["x"], roi["y"]
            w, h = roi["width"], roi["height"]

            # Ensure ROI is within image bounds
            img_h, img_w = image.shape[:2]
            x = max(0, min(x, img_w - 1))
            y = max(0, min(y, img_h - 1))
            w = min(w, img_w - x)
            h = min(h, img_h - y)

            roi_image = image[y : y + h, x : x + w]

            # Get template
            template = template_data["template"]

            # Check if template fits in ROI
            if (
                template.shape[0] > roi_image.shape[0]
                or template.shape[1] > roi_image.shape[1]
            ):
                self.logger.debug(
                    f"Template larger than ROI, resizing template "
                    f"from {template.shape} to fit {roi_image.shape}"
                )
                # Resize template to fit ROI
                scale = min(
                    roi_image.shape[0] / template.shape[0],
                    roi_image.shape[1] / template.shape[1],
                )
                new_size = (
                    int(template.shape[1] * scale),
                    int(template.shape[0] * scale),
                )
                template = cv2.resize(template, new_size)

            # Perform template matching
            method = cv2.TM_CCOEFF_NORMED  # Normalized cross-correlation
            result = cv2.matchTemplate(roi_image, template, method)

            # Get best match location and confidence
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # For TM_CCOEFF_NORMED, max_val is the confidence
            confidence = float(max_val)

            return confidence

        except Exception as e:
            self.logger.error(f"Error in template matching: {e}", exc_info=True)
            return 0.0

    def detect_multi_scale(
        self,
        image: np.ndarray | Image.Image,
        vendor_name: str,
        scales: list[float] | None = None,
    ) -> tuple[str | None, float]:
        """Detect logo at multiple scales (for varying image resolutions).

        Args:
            image: Input image
            vendor_name: Vendor to detect
            scales: List of scale factors to try (default: [0.8, 1.0, 1.2])

        Returns:
            Tuple of (vendor_name, confidence_score)
        """
        if vendor_name not in self.logo_templates:
            self.logger.warning(f"No template loaded for {vendor_name}")
            return None, 0.0

        if scales is None:
            scales = [0.8, 1.0, 1.2]

        # Convert PIL Image to numpy array if needed
        if isinstance(image, Image.Image):
            image = np.array(image)

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray_image = image

        best_confidence = 0.0
        template_data = self.logo_templates[vendor_name]
        original_template = template_data["template"].copy()

        for scale in scales:
            # Scale the template
            if scale != 1.0:
                new_size = (
                    int(original_template.shape[1] * scale),
                    int(original_template.shape[0] * scale),
                )
                scaled_template = cv2.resize(original_template, new_size)
                template_data["template"] = scaled_template
            else:
                template_data["template"] = original_template

            # Perform matching
            confidence = self._match_template(gray_image, template_data)

            if confidence > best_confidence:
                best_confidence = confidence

            self.logger.debug(
                f"Scale {scale:.2f}: confidence {confidence:.3f} for {vendor_name}"
            )

        # Restore original template
        template_data["template"] = original_template

        if best_confidence >= template_data["threshold"]:
            return vendor_name, best_confidence
        else:
            return None, best_confidence

    def get_loaded_vendors(self) -> list[str]:
        """Get list of vendors with loaded logo templates.

        Returns:
            List of vendor names
        """
        return list(self.logo_templates.keys())

    def clear_templates(self) -> None:
        """Clear all loaded logo templates."""
        self.logo_templates.clear()
        self.logger.info("Cleared all logo templates")
