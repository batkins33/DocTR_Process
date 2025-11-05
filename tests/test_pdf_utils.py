"""Tests for PDF utilities module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image
from pypdf import PdfWriter
from src.truck_tickets.processing.pdf_utils import PDFProcessor


class TestPDFProcessor:
    """Test suite for PDFProcessor class."""

    @pytest.fixture
    def pdf_processor(self):
        """Create PDFProcessor instance for testing."""
        return PDFProcessor(dpi=300)

    @pytest.fixture
    def sample_pdf(self):
        """Create a sample PDF file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

            # Create a simple PDF with 2 pages
            writer = PdfWriter()
            writer.add_blank_page(width=612, height=792)  # Letter size
            writer.add_blank_page(width=612, height=792)

            with open(tmp_path, "wb") as f:
                writer.write(f)

            yield tmp_path

            # Cleanup
            try:
                tmp_path.unlink()
            except (PermissionError, FileNotFoundError):
                pass

    def test_initialization_default(self):
        """Test PDFProcessor initialization with defaults."""
        processor = PDFProcessor()

        assert processor.dpi == 300

    def test_initialization_custom_dpi(self):
        """Test PDFProcessor initialization with custom DPI."""
        processor = PDFProcessor(dpi=400)

        assert processor.dpi == 400

    def test_extract_pages(self, pdf_processor, sample_pdf):
        """Test extracting pages from PDF."""
        pages = pdf_processor.extract_pages(sample_pdf)

        assert len(pages) == 2
        assert pages[0]["page_num"] == 1
        assert pages[1]["page_num"] == 2
        assert "page_obj" in pages[0]
        assert "width" in pages[0]
        assert "height" in pages[0]
        assert "rotation" in pages[0]

    def test_extract_pages_file_not_found(self, pdf_processor):
        """Test extracting pages from non-existent PDF."""
        with pytest.raises(FileNotFoundError):
            pdf_processor.extract_pages("/nonexistent/file.pdf")

    def test_extract_pages_invalid_pdf(self, pdf_processor):
        """Test extracting pages from invalid PDF."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"Not a valid PDF")

            try:
                with pytest.raises(ValueError, match="Invalid or corrupted PDF"):
                    pdf_processor.extract_pages(tmp_path)
            finally:
                try:
                    tmp_path.unlink()
                except PermissionError:
                    pass

    def test_page_to_image(self, pdf_processor, sample_pdf):
        """Test converting PDF page to image."""
        pages = pdf_processor.extract_pages(sample_pdf)
        page_obj = pages[0]["page_obj"]

        image = pdf_processor.page_to_image(page_obj)

        assert isinstance(image, Image.Image)
        assert image.mode == "RGB"
        assert image.width > 0
        assert image.height > 0

    def test_page_to_image_custom_dpi(self, pdf_processor, sample_pdf):
        """Test converting PDF page to image with custom DPI."""
        pages = pdf_processor.extract_pages(sample_pdf)
        page_obj = pages[0]["page_obj"]

        image_300 = pdf_processor.page_to_image(page_obj, dpi=300)
        image_600 = pdf_processor.page_to_image(page_obj, dpi=600)

        # Higher DPI should produce larger image
        assert image_600.width > image_300.width
        assert image_600.height > image_300.height

    def test_extract_images_from_pdf(self, pdf_processor, sample_pdf):
        """Test extracting all pages as images."""
        images = pdf_processor.extract_images_from_pdf(sample_pdf)

        assert len(images) == 2
        assert all(isinstance(img, Image.Image) for img in images)
        assert all(img.mode == "RGB" for img in images)

    def test_extract_images_from_pdf_custom_dpi(self, pdf_processor, sample_pdf):
        """Test extracting images with custom DPI."""
        images_300 = pdf_processor.extract_images_from_pdf(sample_pdf, dpi=300)
        images_600 = pdf_processor.extract_images_from_pdf(sample_pdf, dpi=600)

        # Higher DPI should produce larger images
        assert images_600[0].width > images_300[0].width

    def test_get_pdf_metadata(self, pdf_processor, sample_pdf):
        """Test extracting PDF metadata."""
        metadata = pdf_processor.get_pdf_metadata(sample_pdf)

        assert "num_pages" in metadata
        assert "file_size" in metadata
        assert "file_name" in metadata
        assert "file_path" in metadata
        assert metadata["num_pages"] == 2
        assert metadata["file_name"] == sample_pdf.name
        assert metadata["file_size"] > 0

    def test_get_pdf_metadata_file_not_found(self, pdf_processor):
        """Test getting metadata from non-existent PDF."""
        with pytest.raises(FileNotFoundError):
            pdf_processor.get_pdf_metadata("/nonexistent/file.pdf")

    def test_get_pdf_metadata_invalid_pdf(self, pdf_processor):
        """Test getting metadata from invalid PDF."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"Not a valid PDF")

            try:
                with pytest.raises(ValueError, match="Invalid PDF"):
                    pdf_processor.get_pdf_metadata(tmp_path)
            finally:
                try:
                    tmp_path.unlink()
                except PermissionError:
                    pass

    def test_extract_pages_with_rotation(self, pdf_processor):
        """Test extracting pages with rotation."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

            # Create PDF with rotated page
            writer = PdfWriter()
            page = writer.add_blank_page(width=612, height=792)
            page.rotate(90)

            with open(tmp_path, "wb") as f:
                writer.write(f)

            try:
                pages = pdf_processor.extract_pages(tmp_path)

                assert len(pages) == 1
                assert "rotation" in pages[0]
                # Rotation should be recorded
                assert pages[0]["rotation"] in [0, 90, 180, 270]

            finally:
                try:
                    tmp_path.unlink()
                except PermissionError:
                    pass

    def test_extract_images_error_handling(self, pdf_processor, sample_pdf):
        """Test error handling during image extraction."""
        with patch.object(pdf_processor, "page_to_image") as mock_convert:
            # First page succeeds, second fails
            mock_convert.side_effect = [
                Image.new("RGB", (800, 600), color="white"),
                Exception("Conversion failed"),
            ]

            images = pdf_processor.extract_images_from_pdf(sample_pdf)

            # Should continue despite error
            assert len(images) == 1

    def test_page_dimensions(self, pdf_processor, sample_pdf):
        """Test that page dimensions are correctly extracted."""
        pages = pdf_processor.extract_pages(sample_pdf)

        # Letter size is 612x792 points
        assert pages[0]["width"] == 612
        assert pages[0]["height"] == 792

    def test_multiple_pdf_processing(self, pdf_processor):
        """Test processing multiple PDFs sequentially."""
        pdfs = []

        try:
            # Create multiple PDFs
            for _ in range(3):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                    writer = PdfWriter()
                    writer.add_blank_page(width=612, height=792)

                    with open(tmp_path, "wb") as f:
                        writer.write(f)

                    pdfs.append(tmp_path)

            # Process all PDFs
            for pdf_path in pdfs:
                pages = pdf_processor.extract_pages(pdf_path)
                assert len(pages) == 1

                images = pdf_processor.extract_images_from_pdf(pdf_path)
                assert len(images) == 1

        finally:
            # Cleanup
            for pdf_path in pdfs:
                try:
                    pdf_path.unlink()
                except (PermissionError, FileNotFoundError):
                    pass
