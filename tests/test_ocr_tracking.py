"""Tests for OCR tracking functionality."""

from unittest.mock import Mock, patch

from doctr_process.extract import TextDetector


class TestOCRTracking:
    """Test OCR vs text extraction tracking."""

    @patch("doctr_process.extract.text_detector.fitz")
    def test_page_level_text_detection(self, mock_fitz, tmp_path):
        """Test per-page text detection tracking."""
        pdf_file = tmp_path / "mixed.pdf"
        pdf_file.write_bytes(b"fake pdf")

        # Mock pages with different text content
        mock_doc = Mock()
        mock_page1 = Mock()
        mock_page1.get_text.return_value = "This page has plenty of text content"
        mock_page2 = Mock()
        mock_page2.get_text.return_value = ""  # No text
        mock_page3 = Mock()
        mock_page3.get_text.return_value = "Another page with text"

        mock_doc.__iter__ = Mock(
            return_value=iter([mock_page1, mock_page2, mock_page3])
        )
        mock_fitz.open.return_value = mock_doc

        detector = TextDetector(min_text_length=10)
        has_text, full_text, page_status = detector.check_pages_for_text(pdf_file)

        assert has_text is True
        assert len(page_status) == 3
        assert page_status[0] is True  # Page 1 has text
        assert page_status[1] is False  # Page 2 no text
        assert page_status[2] is True  # Page 3 has text

    def test_processing_method_tracking(self):
        """Test that processing method is correctly tracked."""
        from doctr_process.pipeline_v2 import RefactoredPipeline

        config = {"skip_ocr": True, "output_dir": "./test"}

        with patch.multiple(
            "doctr_process.pipeline_v2",
            load_extraction_rules=Mock(return_value={}),
            load_vendor_rules_from_csv=Mock(return_value={}),
            get_config_path=Mock(return_value="test.csv"),
        ):
            pipeline = RefactoredPipeline(config)

            # Test existing text processing
            results = pipeline._process_existing_text(
                "test.pdf",
                "Sample text",
                [True, False, True],  # Page 1&3 have text, page 2 doesn't
            )

            assert len(results) == 3
            assert results[0]["processing_method"] == "text_extraction"
            assert results[0]["had_extractable_text"] is True
            assert results[1]["processing_method"] == "no_processing"
            assert results[1]["had_extractable_text"] is False
            assert results[2]["processing_method"] == "text_extraction"
            assert results[2]["had_extractable_text"] is True
