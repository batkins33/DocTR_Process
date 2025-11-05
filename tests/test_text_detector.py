"""Tests for text detector."""

from unittest.mock import Mock, patch

from doctr_process.extract import TextDetector


class TestTextDetector:
    """Test TextDetector functionality."""

    def test_non_pdf_file(self, tmp_path):
        """Test that non-PDF files return False."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Some text content")

        detector = TextDetector()
        has_text, text = detector.has_extractable_text(txt_file)

        assert has_text is False
        assert text is None

    @patch("doctr_process.extract.text_detector.fitz")
    def test_pymupdf_text_extraction(self, mock_fitz, tmp_path):
        """Test text extraction using PyMuPDF."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf")

        # Mock PyMuPDF
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "This is extracted text from PDF"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc

        detector = TextDetector(min_text_length=10)
        has_text, text = detector.has_extractable_text(pdf_file)

        assert has_text is True
        assert "extracted text" in text

    @patch("doctr_process.extract.text_detector.fitz", None)
    @patch("doctr_process.extract.text_detector.pdfplumber")
    def test_pdfplumber_fallback(self, mock_pdfplumber, tmp_path):
        """Test fallback to pdfplumber when PyMuPDF unavailable."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf")

        # Mock pdfplumber
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Text from pdfplumber extraction"
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__ = Mock(return_value=mock_pdf)
        mock_pdfplumber.open.return_value.__exit__ = Mock(return_value=None)

        detector = TextDetector(min_text_length=10)
        has_text, text = detector.has_extractable_text(pdf_file)

        assert has_text is True
        assert "pdfplumber" in text

    def test_insufficient_text_length(self, tmp_path):
        """Test that short text doesn't meet minimum threshold."""
        with patch("doctr_process.extract.text_detector.fitz") as mock_fitz:
            pdf_file = tmp_path / "test.pdf"
            pdf_file.write_bytes(b"fake pdf")

            mock_doc = Mock()
            mock_page = Mock()
            mock_page.get_text.return_value = "Hi"  # Too short
            mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
            mock_fitz.open.return_value = mock_doc

            detector = TextDetector(min_text_length=50)
            has_text, text = detector.has_extractable_text(pdf_file)

            assert has_text is False
