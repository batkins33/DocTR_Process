"""Tests for logo detection functionality."""

import numpy as np
import pytest
from PIL import Image, ImageDraw

from truck_tickets.extractors import LogoDetector, VendorDetector


class TestLogoDetector:
    """Test suite for LogoDetector class."""

    @pytest.fixture
    def logo_detector(self, tmp_path):
        """Create LogoDetector instance with temp directory."""
        return LogoDetector(templates_dir=tmp_path)

    @pytest.fixture
    def sample_logo_image(self):
        """Create a sample logo image for testing."""
        # Create a simple test logo (100x50 white rectangle with black text)
        img = Image.new("RGB", (100, 50), color="white")
        draw = ImageDraw.Draw(img)

        # Draw simple text as "logo"
        draw.rectangle([10, 10, 90, 40], outline="black", width=2)
        draw.text((30, 20), "WM", fill="black")

        return img

    @pytest.fixture
    def sample_ticket_image(self, sample_logo_image):
        """Create a sample ticket image with logo in top-left."""
        # Create ticket image (800x1000)
        ticket = Image.new("RGB", (800, 1000), color="white")

        # Paste logo in top-left corner
        ticket.paste(sample_logo_image, (10, 10))

        # Add some text content
        draw = ImageDraw.Draw(ticket)
        draw.text((100, 200), "Ticket Number: WM-12345678", fill="black")
        draw.text((100, 250), "Date: 2024-10-17", fill="black")

        return ticket

    def test_initialization(self, tmp_path):
        """Test LogoDetector initialization."""
        detector = LogoDetector(templates_dir=tmp_path)
        assert detector.templates_dir == tmp_path
        assert detector.logo_templates == {}

    def test_load_template_nonexistent_file(self, logo_detector):
        """Test loading a nonexistent template file."""
        logo_detector.load_template(
            vendor_name="TEST_VENDOR",
            template_path="nonexistent_logo.png",
        )
        # Should not raise error, just log warning
        assert "TEST_VENDOR" not in logo_detector.logo_templates

    def test_load_template_success(self, logo_detector, sample_logo_image, tmp_path):
        """Test successful template loading."""
        # Save sample logo to temp path
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        logo_detector.load_template(
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            template_path=logo_path,
            roi={"x": 0, "y": 0, "width": 200, "height": 100},
            threshold=0.85,
        )

        assert "WASTE_MANAGEMENT_LEWISVILLE" in logo_detector.logo_templates
        template_data = logo_detector.logo_templates["WASTE_MANAGEMENT_LEWISVILLE"]
        assert template_data["template"] is not None
        assert template_data["threshold"] == 0.85
        assert template_data["roi"] == {"x": 0, "y": 0, "width": 200, "height": 100}

    def test_detect_no_templates_loaded(self, logo_detector, sample_ticket_image):
        """Test detection with no templates loaded."""
        vendor, confidence = logo_detector.detect(sample_ticket_image)
        assert vendor is None
        assert confidence == 0.0

    def test_detect_with_matching_logo(
        self, logo_detector, sample_logo_image, sample_ticket_image, tmp_path
    ):
        """Test detection with matching logo."""
        # Save and load template
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        logo_detector.load_template(
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            template_path=logo_path,
            roi={"x": 0, "y": 0, "width": 200, "height": 100},
            threshold=0.7,  # Lower threshold for test
        )

        # Detect logo
        vendor, confidence = logo_detector.detect(sample_ticket_image)

        # Should detect the vendor
        assert vendor == "WASTE_MANAGEMENT_LEWISVILLE"
        assert confidence > 0.7

    def test_detect_with_numpy_array(
        self, logo_detector, sample_logo_image, sample_ticket_image, tmp_path
    ):
        """Test detection with numpy array input."""
        # Save and load template
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        logo_detector.load_template(
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            template_path=logo_path,
            roi={"x": 0, "y": 0, "width": 200, "height": 100},
            threshold=0.7,
        )

        # Convert to numpy array
        image_array = np.array(sample_ticket_image)

        # Detect logo
        vendor, confidence = logo_detector.detect(image_array)

        assert vendor == "WASTE_MANAGEMENT_LEWISVILLE"
        assert confidence > 0.7

    def test_detect_with_vendor_filter(
        self, logo_detector, sample_logo_image, sample_ticket_image, tmp_path
    ):
        """Test detection with vendor filter."""
        # Load template for WM
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        logo_detector.load_template(
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            template_path=logo_path,
            roi={"x": 0, "y": 0, "width": 200, "height": 100},
            threshold=0.7,
        )

        # Also load a dummy template for LDI
        logo_detector.logo_templates["LDI_YARD"] = {
            "template": np.zeros((50, 100), dtype=np.uint8),
            "roi": {"x": 0, "y": 0, "width": 200, "height": 100},
            "threshold": 0.85,
            "method": "template_match",
        }

        # Detect with filter for only LDI (should not match)
        vendor, confidence = logo_detector.detect(
            sample_ticket_image, vendor_filter=["LDI_YARD"]
        )
        assert vendor is None

        # Detect with filter including WM (should match)
        vendor, confidence = logo_detector.detect(
            sample_ticket_image,
            vendor_filter=["WASTE_MANAGEMENT_LEWISVILLE", "LDI_YARD"],
        )
        assert vendor == "WASTE_MANAGEMENT_LEWISVILLE"

    def test_detect_multi_scale(
        self, logo_detector, sample_logo_image, sample_ticket_image, tmp_path
    ):
        """Test multi-scale detection."""
        # Save and load template
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        logo_detector.load_template(
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            template_path=logo_path,
            roi={"x": 0, "y": 0, "width": 200, "height": 100},
            threshold=0.7,
        )

        # Test multi-scale detection
        vendor, confidence = logo_detector.detect_multi_scale(
            sample_ticket_image,
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            scales=[0.8, 1.0, 1.2],
        )

        assert vendor == "WASTE_MANAGEMENT_LEWISVILLE"
        assert confidence > 0.7

    def test_load_templates_from_config(
        self, logo_detector, sample_logo_image, tmp_path
    ):
        """Test loading templates from vendor config."""
        # Save logo
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        # Create vendor config
        vendor_configs = {
            "WASTE_MANAGEMENT_LEWISVILLE": {
                "logo": {
                    "path": str(logo_path),
                    "roi": {"x": 0, "y": 0, "width": 200, "height": 100},
                    "threshold": 0.85,
                    "method": "template_match",
                }
            },
            "LDI_YARD": {
                # No logo config
            },
        }

        logo_detector.load_templates_from_config(vendor_configs)

        # Should have loaded WM template
        assert "WASTE_MANAGEMENT_LEWISVILLE" in logo_detector.logo_templates
        # Should not have loaded LDI (no config)
        assert "LDI_YARD" not in logo_detector.logo_templates

    def test_get_loaded_vendors(self, logo_detector, sample_logo_image, tmp_path):
        """Test getting list of loaded vendors."""
        assert logo_detector.get_loaded_vendors() == []

        # Load a template
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        logo_detector.load_template(
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            template_path=logo_path,
        )

        vendors = logo_detector.get_loaded_vendors()
        assert vendors == ["WASTE_MANAGEMENT_LEWISVILLE"]

    def test_clear_templates(self, logo_detector, sample_logo_image, tmp_path):
        """Test clearing all templates."""
        # Load a template
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        logo_detector.load_template(
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            template_path=logo_path,
        )

        assert len(logo_detector.logo_templates) == 1

        # Clear templates
        logo_detector.clear_templates()

        assert len(logo_detector.logo_templates) == 0


class TestVendorDetectorWithLogo:
    """Test VendorDetector integration with logo detection."""

    @pytest.fixture
    def sample_logo_image(self):
        """Create a sample logo image."""
        img = Image.new("RGB", (100, 50), color="white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([10, 10, 90, 40], outline="black", width=2)
        draw.text((30, 20), "WM", fill="black")
        return img

    @pytest.fixture
    def sample_ticket_image(self, sample_logo_image):
        """Create a sample ticket image with logo."""
        ticket = Image.new("RGB", (800, 1000), color="white")
        ticket.paste(sample_logo_image, (10, 10))
        return ticket

    def test_vendor_detector_with_logo_detection_disabled(self):
        """Test VendorDetector with logo detection disabled."""
        detector = VendorDetector(enable_logo_detection=False)
        assert detector.logo_detector is None

    def test_vendor_detector_with_logo_detection_enabled(self):
        """Test VendorDetector with logo detection enabled."""
        detector = VendorDetector(enable_logo_detection=True)
        assert detector.logo_detector is not None

    def test_detection_priority_filename_first(self, sample_ticket_image):
        """Test that filename hint has highest priority."""
        detector = VendorDetector(enable_logo_detection=True)

        # Filename should override everything
        vendor, confidence = detector.detect(
            text="Some random text",
            filename_vendor="WM",
            image=sample_ticket_image,
        )

        assert vendor == "WASTE_MANAGEMENT_LEWISVILLE"
        assert confidence == 1.0

    def test_detection_priority_logo_second(
        self, sample_logo_image, sample_ticket_image, tmp_path
    ):
        """Test that logo detection is second priority."""
        # Create logo detector with template
        logo_detector = LogoDetector(templates_dir=tmp_path)
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        logo_detector.load_template(
            vendor_name="WASTE_MANAGEMENT_LEWISVILLE",
            template_path=logo_path,
            roi={"x": 0, "y": 0, "width": 200, "height": 100},
            threshold=0.7,
        )

        # Create vendor detector with logo detector
        detector = VendorDetector(
            enable_logo_detection=True, logo_detector=logo_detector
        )

        # No filename, should use logo detection
        vendor, confidence = detector.detect(
            text="Some random text without vendor keywords", image=sample_ticket_image
        )

        assert vendor == "WASTE_MANAGEMENT_LEWISVILLE"
        assert confidence > 0.7

    def test_detection_fallback_to_keywords(self):
        """Test fallback to keyword matching when logo detection fails."""
        detector = VendorDetector(enable_logo_detection=True)

        # No image provided, should fall back to keywords
        vendor, confidence = detector.detect(
            text="This ticket is from Waste Management Lewisville"
        )

        assert vendor == "WASTE_MANAGEMENT_LEWISVILLE"
        assert confidence == 0.75

    def test_detection_with_vendor_templates(
        self, sample_logo_image, sample_ticket_image, tmp_path
    ):
        """Test detection with vendor templates loaded."""
        # Save logo
        logo_path = tmp_path / "wm_logo.png"
        sample_logo_image.save(logo_path)

        # Create vendor templates
        vendor_templates = {
            "WASTE_MANAGEMENT_LEWISVILLE": {
                "vendor": {
                    "name": "WASTE_MANAGEMENT_LEWISVILLE",
                    "aliases": ["Waste Management", "WM"],
                },
                "logo": {
                    "path": str(logo_path),
                    "roi": {"x": 0, "y": 0, "width": 200, "height": 100},
                    "threshold": 0.7,
                },
            }
        }

        detector = VendorDetector(
            vendor_templates=vendor_templates, enable_logo_detection=True
        )

        # Should detect via logo
        vendor, confidence = detector.detect(
            text="Random text", image=sample_ticket_image
        )

        assert vendor == "WASTE_MANAGEMENT_LEWISVILLE"
        assert confidence > 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
