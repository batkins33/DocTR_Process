"""Tests for refactored pipeline."""

from unittest.mock import Mock, patch

from doctr_process.pipeline_v2 import RefactoredPipeline


class TestRefactoredPipeline:
    """Test RefactoredPipeline functionality."""

    @patch("doctr_process.pipeline_v2.load_config")
    @patch("doctr_process.pipeline_v2.load_extraction_rules")
    @patch("doctr_process.pipeline_v2.load_vendor_rules_from_csv")
    def test_setup_components(
        self, mock_vendor_rules, mock_extraction_rules, mock_config
    ):
        """Test component setup."""
        config = {
            "output_dir": "./test_output",
            "input_pdf": "test.pdf",
            "ocr_engine": "tesseract",
        }

        mock_extraction_rules.return_value = {}
        mock_vendor_rules.return_value = {}

        pipeline = RefactoredPipeline(config)

        assert pipeline.config == config
        assert hasattr(pipeline, "input_handler")
        assert hasattr(pipeline, "output_manager")
        assert hasattr(pipeline, "ocr_processor")

    @patch("doctr_process.pipeline_v2.RefactoredPipeline.setup_components")
    def test_process_file_error_handling(self, mock_setup):
        """Test error handling in file processing."""
        config = {"output_dir": "./test_output"}
        pipeline = RefactoredPipeline(config)

        # Mock components to raise exception
        pipeline.image_extractor = Mock()
        pipeline.image_extractor.extract_from_bytes.side_effect = Exception(
            "Test error"
        )
        pipeline.output_manager = Mock()
        pipeline.output_manager.get_input_subdir.return_value = Mock()

        results = pipeline.process_file("test.pdf", Mock(), b"fake data")

        assert results == []
