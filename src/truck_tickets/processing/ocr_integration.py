"""OCR integration bridge between doctr_process and truck_tickets modules.

Provides a unified interface for OCR processing that bridges the existing
DocTR OCR infrastructure with the truck tickets processing pipeline.
"""

import logging
from pathlib import Path
from typing import Any

from PIL import Image

from ...doctr_process.extract.ocr_processor import OCRProcessor as DocTROCRProcessor
from .pdf_utils import PDFProcessor


class OCRIntegration:
    """Unified OCR interface for truck ticket processing.

    Bridges the doctr_process OCR infrastructure with the truck_tickets
    processing pipeline, providing a clean interface for PDF OCR operations.

    Example:
        ```python
        ocr = OCRIntegration(engine="doctr")

        # Process single PDF
        results = ocr.process_pdf("/path/to/ticket.pdf")
        for result in results:
            print(f"Page {result['page_num']}: {result['text'][:100]}...")

        # Process single image
        from PIL import Image
        image = Image.open("ticket.jpg")
        result = ocr.process_image(image)
        print(result['text'])
        ```
    """

    def __init__(
        self,
        engine: str = "doctr",
        orientation_method: str = "tesseract",
        pdf_dpi: int = 300,
    ):
        """Initialize OCR integration.

        Args:
            engine: OCR engine to use ("doctr", "tesseract", "easyocr")
            orientation_method: Method for orientation correction
            pdf_dpi: Resolution for PDF to image conversion
        """
        self.engine = engine
        self.orientation_method = orientation_method
        self.pdf_dpi = pdf_dpi
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.ocr_processor = DocTROCRProcessor(
            engine_name=engine, orientation_method=orientation_method
        )
        self.pdf_processor = PDFProcessor(dpi=pdf_dpi)

    def process_pdf(self, pdf_path: str | Path) -> list[dict[str, Any]]:
        """Process entire PDF file with OCR.

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of OCR results, one per page

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is invalid
        """
        pdf_path = Path(pdf_path)
        self.logger.info(f"Processing PDF: {pdf_path.name}")

        # Extract PDF metadata
        try:
            metadata = self.pdf_processor.get_pdf_metadata(pdf_path)
            self.logger.debug(f"PDF has {metadata['num_pages']} pages")
        except Exception as e:
            self.logger.error(f"Error reading PDF metadata: {e}")
            raise

        # Extract pages as images
        try:
            images = self.pdf_processor.extract_images_from_pdf(pdf_path, self.pdf_dpi)
            self.logger.debug(f"Extracted {len(images)} page images")
        except Exception as e:
            self.logger.error(f"Error extracting PDF pages: {e}")
            raise

        # Process with OCR in batch
        try:
            ocr_results = self.ocr_processor.process_batch(images)
            self.logger.info(
                f"OCR completed for {len(ocr_results)} pages from {pdf_path.name}"
            )
        except Exception as e:
            self.logger.error(f"Error during OCR processing: {e}")
            raise

        # Combine results with page numbers and metadata
        results = []
        for page_num, ocr_result in enumerate(ocr_results, start=1):
            result = {
                "page_num": page_num,
                "file_path": str(pdf_path),
                "file_name": pdf_path.name,
                "text": ocr_result.get("text", ""),
                "confidence": self._calculate_confidence(ocr_result),
                "page_hash": ocr_result.get("page_hash"),
                "orientation": ocr_result.get("orientation", 0),
                "timings": ocr_result.get("timings", {}),
                "ocr_engine": self.engine,
            }
            results.append(result)

        return results

    def process_image(self, image: Image.Image, page_num: int = 1) -> dict[str, Any]:
        """Process single image with OCR.

        Args:
            image: PIL Image object
            page_num: Page number for tracking

        Returns:
            OCR result dictionary
        """
        self.logger.debug(f"Processing image page {page_num}")

        try:
            ocr_result = self.ocr_processor.process_single_page(image, page_num)

            result = {
                "page_num": page_num,
                "text": ocr_result.get("text", ""),
                "confidence": self._calculate_confidence(ocr_result),
                "page_hash": ocr_result.get("page_hash"),
                "orientation": ocr_result.get("orientation", 0),
                "timings": ocr_result.get("timings", {}),
                "ocr_engine": self.engine,
            }

            return result

        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            raise

    def process_images_batch(self, images: list[Image.Image]) -> list[dict[str, Any]]:
        """Process multiple images in batch.

        Args:
            images: List of PIL Image objects

        Returns:
            List of OCR result dictionaries
        """
        self.logger.info(f"Processing batch of {len(images)} images")

        try:
            ocr_results = self.ocr_processor.process_batch(images)

            results = []
            for page_num, ocr_result in enumerate(ocr_results, start=1):
                result = {
                    "page_num": page_num,
                    "text": ocr_result.get("text", ""),
                    "confidence": self._calculate_confidence(ocr_result),
                    "page_hash": ocr_result.get("page_hash"),
                    "orientation": ocr_result.get("orientation", 0),
                    "timings": ocr_result.get("timings", {}),
                    "ocr_engine": self.engine,
                }
                results.append(result)

            return results

        except Exception as e:
            self.logger.error(f"Error processing image batch: {e}")
            raise

    def _calculate_confidence(self, ocr_result: dict[str, Any]) -> float:
        """Calculate confidence score from OCR result.

        Args:
            ocr_result: OCR result dictionary

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # For now, return a placeholder confidence
        # In production, this would extract actual confidence from OCR result
        result_page = ocr_result.get("result_page")
        if result_page:
            # DocTR provides confidence scores - extract if available
            # This is a simplified placeholder
            return 0.85

        # Default confidence for engines without confidence scores
        return 0.75

    def get_stats(self) -> dict[str, Any]:
        """Get OCR processing statistics.

        Returns:
            Dictionary with processing statistics
        """
        return {
            "engine": self.engine,
            "orientation_method": self.orientation_method,
            "pdf_dpi": self.pdf_dpi,
            "ocr_stats": self.ocr_processor._stats,
        }
