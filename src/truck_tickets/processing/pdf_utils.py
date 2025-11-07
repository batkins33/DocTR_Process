"""PDF utilities for page extraction and image conversion.

Provides utilities for extracting pages from PDF files and converting
them to images for OCR processing.
"""

import logging
from pathlib import Path
from typing import Any

from PIL import Image
from pypdf import PdfReader

try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

logger = logging.getLogger(__name__)


class PDFProcessor:
    """Handles PDF file operations and page extraction."""

    def __init__(self, dpi: int = 300):
        """Initialize PDF processor.

        Args:
            dpi: Resolution for PDF to image conversion (default: 300)
        """
        self.dpi = dpi
        self.logger = logging.getLogger(self.__class__.__name__)

    def extract_pages(self, pdf_path: str | Path) -> list[dict[str, Any]]:
        """Extract all pages from a PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of page dictionaries with metadata

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is invalid or corrupted
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            reader = PdfReader(str(pdf_path))
            pages = []

            for page_num, page in enumerate(reader.pages, start=1):
                page_info = {
                    "page_num": page_num,
                    "page_obj": page,
                    "width": float(page.mediabox.width),
                    "height": float(page.mediabox.height),
                    "rotation": int(page.get("/Rotate", 0)),
                }
                pages.append(page_info)

            self.logger.info(f"Extracted {len(pages)} pages from {pdf_path.name}")
            return pages

        except Exception as e:
            self.logger.error(f"Error reading PDF {pdf_path}: {e}")
            raise ValueError(f"Invalid or corrupted PDF: {e}") from e

    def page_to_image(self, page_obj: Any, dpi: int | None = None) -> Image.Image:
        """Convert a PDF page to a PIL Image.

        Args:
            page_obj: PyPDF page object
            dpi: Resolution override (default: use instance dpi)

        Returns:
            PIL Image object

        Note:
            This method is deprecated. Use extract_images_from_pdf() instead
            which renders the entire PDF at once for better performance.
        """
        dpi = dpi or self.dpi

        if not PDF2IMAGE_AVAILABLE:
            self.logger.warning(
                "pdf2image not available - using placeholder image. "
                "Install with: pip install pdf2image"
            )
            # Create a blank image as fallback
            width = int(page_obj.mediabox.width * dpi / 72)
            height = int(page_obj.mediabox.height * dpi / 72)
            return Image.new("RGB", (width, height), color="white")

        # Note: This is inefficient as it renders the entire PDF
        # Use extract_images_from_pdf() for better performance
        self.logger.warning(
            "page_to_image() renders entire PDF - use extract_images_from_pdf() instead"
        )

        # Create a blank image as placeholder since we can't render a single page efficiently
        width = int(page_obj.mediabox.width * dpi / 72)
        height = int(page_obj.mediabox.height * dpi / 72)
        return Image.new("RGB", (width, height), color="white")

    def extract_images_from_pdf(
        self, pdf_path: str | Path, dpi: int | None = None
    ) -> list[Image.Image]:
        """Extract all pages from PDF as images using pdf2image.

        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for conversion (default: use instance dpi)

        Returns:
            List of PIL Image objects, one per page

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            RuntimeError: If pdf2image is not available or poppler is not installed
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        dpi = dpi or self.dpi

        if not PDF2IMAGE_AVAILABLE:
            self.logger.error(
                "pdf2image is not installed. Install with: pip install pdf2image"
            )
            raise RuntimeError(
                "pdf2image is required for PDF rendering. "
                "Install with: pip install pdf2image\n"
                "Also ensure poppler is installed on your system."
            )

        try:
            self.logger.info(f"Converting PDF to images: {pdf_path.name} at {dpi} DPI")
            images = convert_from_path(
                str(pdf_path),
                dpi=dpi,
                fmt="RGB",
                thread_count=1,  # Single thread for stability
            )
            self.logger.info(f"Successfully converted {len(images)} pages to images")
            return images

        except Exception as e:
            self.logger.error(f"Error converting PDF to images: {e}")
            # Fallback: try to extract pages and create placeholder images
            self.logger.warning("Falling back to placeholder images")
            pages = self.extract_pages(pdf_path)
            images = []

            for page_info in pages:
                width = int(page_info["width"] * dpi / 72)
                height = int(page_info["height"] * dpi / 72)
                image = Image.new("RGB", (width, height), color="white")
                images.append(image)

            return images

    def get_pdf_metadata(self, pdf_path: str | Path) -> dict[str, Any]:
        """Extract metadata from PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with PDF metadata
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            reader = PdfReader(str(pdf_path))

            metadata = {
                "num_pages": len(reader.pages),
                "file_size": pdf_path.stat().st_size,
                "file_name": pdf_path.name,
                "file_path": str(pdf_path),
            }

            # Add PDF metadata if available
            if reader.metadata:
                metadata.update(
                    {
                        "title": reader.metadata.get("/Title"),
                        "author": reader.metadata.get("/Author"),
                        "subject": reader.metadata.get("/Subject"),
                        "creator": reader.metadata.get("/Creator"),
                        "producer": reader.metadata.get("/Producer"),
                        "creation_date": reader.metadata.get("/CreationDate"),
                    }
                )

            return metadata

        except Exception as e:
            self.logger.error(f"Error reading PDF metadata {pdf_path}: {e}")
            raise ValueError(f"Invalid PDF: {e}") from e
