"""Tests for OCR integration module."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image
from src.truck_tickets.processing.ocr_integration import OCRIntegration


class TestOCRIntegration:
    """Test suite for OCRIntegration class."""

    @pytest.fixture
    def ocr_integration(self):
        """Create OCRIntegration instance for testing."""
        return OCRIntegration(engine="doctr", pdf_dpi=300)

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        return Image.new("RGB", (800, 600), color="white")

    def test_initialization_default(self):
        """Test OCRIntegration initialization with defaults."""
        ocr = OCRIntegration()

        assert ocr.engine == "doctr"
        assert ocr.orientation_method == "tesseract"
        assert ocr.pdf_dpi == 300
        assert ocr.ocr_processor is not None
        assert ocr.pdf_processor is not None

    def test_initialization_custom(self):
        """Test OCRIntegration initialization with custom settings."""
        ocr = OCRIntegration(engine="tesseract", orientation_method="none", pdf_dpi=400)

        assert ocr.engine == "tesseract"
        assert ocr.orientation_method == "none"
        assert ocr.pdf_dpi == 400

    def test_process_image(self, ocr_integration, sample_image):
        """Test processing a single image."""
        with patch.object(
            ocr_integration.ocr_processor, "process_single_page"
        ) as mock_process:
            mock_process.return_value = {
                "text": "Test ticket text",
                "page_hash": "abc123",
                "orientation": 0,
                "timings": {"ocr": 1.5, "total": 2.0},
            }

            result = ocr_integration.process_image(sample_image, page_num=1)

            assert result["page_num"] == 1
            assert result["text"] == "Test ticket text"
            assert result["page_hash"] == "abc123"
            assert result["orientation"] == 0
            assert result["ocr_engine"] == "doctr"
            assert "confidence" in result
            assert "timings" in result

    def test_process_images_batch(self, ocr_integration):
        """Test batch processing of images."""
        images = [Image.new("RGB", (800, 600), color="white") for _ in range(3)]

        with patch.object(ocr_integration.ocr_processor, "process_batch") as mock_batch:
            mock_batch.return_value = [
                {
                    "text": f"Page {i}",
                    "page_hash": f"hash{i}",
                    "orientation": 0,
                    "timings": {"ocr": 1.0},
                }
                for i in range(3)
            ]

            results = ocr_integration.process_images_batch(images)

            assert len(results) == 3
            assert results[0]["page_num"] == 1
            assert results[1]["page_num"] == 2
            assert results[2]["page_num"] == 3
            assert all(r["ocr_engine"] == "doctr" for r in results)

    def test_process_pdf(self, ocr_integration):
        """Test processing a PDF file."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

            try:
                # Mock PDF processor
                with patch.object(
                    ocr_integration.pdf_processor, "get_pdf_metadata"
                ) as mock_metadata:
                    mock_metadata.return_value = {"num_pages": 2}

                    with patch.object(
                        ocr_integration.pdf_processor, "extract_images_from_pdf"
                    ) as mock_extract:
                        mock_extract.return_value = [
                            Image.new("RGB", (800, 600), color="white"),
                            Image.new("RGB", (800, 600), color="white"),
                        ]

                        with patch.object(
                            ocr_integration.ocr_processor, "process_batch"
                        ) as mock_batch:
                            mock_batch.return_value = [
                                {
                                    "text": "Page 1 text",
                                    "page_hash": "hash1",
                                    "orientation": 0,
                                    "timings": {"ocr": 1.0},
                                },
                                {
                                    "text": "Page 2 text",
                                    "page_hash": "hash2",
                                    "orientation": 0,
                                    "timings": {"ocr": 1.0},
                                },
                            ]

                            results = ocr_integration.process_pdf(tmp_path)

                            assert len(results) == 2
                            assert results[0]["page_num"] == 1
                            assert results[0]["text"] == "Page 1 text"
                            assert results[0]["file_name"] == tmp_path.name
                            assert results[1]["page_num"] == 2
                            assert results[1]["text"] == "Page 2 text"

            finally:
                try:
                    tmp_path.unlink()
                except PermissionError:
                    pass

    def test_process_pdf_file_not_found(self, ocr_integration):
        """Test processing non-existent PDF file."""
        with pytest.raises(FileNotFoundError):
            ocr_integration.process_pdf("/nonexistent/file.pdf")

    def test_calculate_confidence_with_result_page(self, ocr_integration):
        """Test confidence calculation with result page."""
        ocr_result = {"result_page": MagicMock(), "text": "Test"}

        confidence = ocr_integration._calculate_confidence(ocr_result)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_calculate_confidence_without_result_page(self, ocr_integration):
        """Test confidence calculation without result page."""
        ocr_result = {"text": "Test"}

        confidence = ocr_integration._calculate_confidence(ocr_result)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    def test_get_stats(self, ocr_integration):
        """Test getting OCR statistics."""
        stats = ocr_integration.get_stats()

        assert "engine" in stats
        assert "orientation_method" in stats
        assert "pdf_dpi" in stats
        assert "ocr_stats" in stats
        assert stats["engine"] == "doctr"
        assert stats["pdf_dpi"] == 300

    def test_process_image_error_handling(self, ocr_integration, sample_image):
        """Test error handling in image processing."""
        with patch.object(
            ocr_integration.ocr_processor, "process_single_page"
        ) as mock_process:
            mock_process.side_effect = Exception("OCR failed")

            with pytest.raises(Exception, match="OCR failed"):
                ocr_integration.process_image(sample_image)

    def test_process_pdf_ocr_error(self, ocr_integration):
        """Test error handling when OCR fails during PDF processing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)

            try:
                with patch.object(
                    ocr_integration.pdf_processor, "get_pdf_metadata"
                ) as mock_metadata:
                    mock_metadata.return_value = {"num_pages": 1}

                    with patch.object(
                        ocr_integration.pdf_processor, "extract_images_from_pdf"
                    ) as mock_extract:
                        mock_extract.return_value = [
                            Image.new("RGB", (800, 600), color="white")
                        ]

                        with patch.object(
                            ocr_integration.ocr_processor, "process_batch"
                        ) as mock_batch:
                            mock_batch.side_effect = Exception("OCR engine failed")

                            with pytest.raises(Exception, match="OCR engine failed"):
                                ocr_integration.process_pdf(tmp_path)

            finally:
                try:
                    tmp_path.unlink()
                except PermissionError:
                    pass

    def test_different_engines(self):
        """Test initialization with different OCR engines."""
        engines = ["doctr", "tesseract", "easyocr"]

        for engine in engines:
            ocr = OCRIntegration(engine=engine)
            assert ocr.engine == engine
            assert ocr.ocr_processor is not None

    def test_process_empty_image_batch(self, ocr_integration):
        """Test processing empty image batch."""
        with patch.object(ocr_integration.ocr_processor, "process_batch") as mock_batch:
            mock_batch.return_value = []

            results = ocr_integration.process_images_batch([])

            assert len(results) == 0
