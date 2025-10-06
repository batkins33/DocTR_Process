"""Tests for extract module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PIL import Image

from doctr_process.extract import ImageExtractor, OCRProcessor


class TestImageExtractor:
    """Test ImageExtractor functionality."""
    
    def test_extract_from_image(self, tmp_path):
        """Test extracting from single image file."""
        # Create a test image
        img = Image.new("RGB", (100, 100), color="red")
        img_path = tmp_path / "test.jpg"
        img.save(img_path)
        
        extractor = ImageExtractor()
        images = list(extractor.extract_from_file(img_path))
        
        assert len(images) == 1
        assert isinstance(images[0], Image.Image)
        assert images[0].mode == "RGB"
    
    def test_unsupported_format(self, tmp_path):
        """Test handling of unsupported file format."""
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("not an image")
        
        extractor = ImageExtractor()
        
        with pytest.raises(ValueError, match="Unsupported file type"):
            list(extractor.extract_from_file(txt_path))


class TestOCRProcessor:
    """Test OCRProcessor functionality."""
    
    @patch('doctr_process.extract.ocr_processor.get_engine')
    def test_process_single_page(self, mock_get_engine):
        """Test processing single page."""
        # Mock engine
        mock_engine = Mock()
        mock_engine.return_value = ("test text", None)
        mock_get_engine.return_value = mock_engine
        
        processor = OCRProcessor()
        
        # Create test image
        img = Image.new("RGB", (100, 100), color="white")
        
        result = processor.process_single_page(img)
        
        assert result["text"] == "test text"
        assert "timings" in result
        assert "page_hash" in result
    
    @patch('doctr_process.extract.ocr_processor.get_engine')
    def test_process_batch(self, mock_get_engine):
        """Test batch processing."""
        # Mock engine for batch processing
        mock_engine = Mock()
        mock_engine.return_value = (["text1", "text2"], [None, None])
        mock_get_engine.return_value = mock_engine
        
        processor = OCRProcessor()
        
        # Create test images
        images = [
            Image.new("RGB", (100, 100), color="white"),
            Image.new("RGB", (100, 100), color="black")
        ]
        
        results = processor.process_batch(images)
        
        assert len(results) == 2
        assert results[0]["text"] == "text1"
        assert results[1]["text"] == "text2"
    
    def test_get_stats(self):
        """Test statistics collection."""
        processor = OCRProcessor()
        
        stats = processor.get_stats()
        
        assert "total_pages" in stats
        assert "total_time" in stats
        assert "batch_count" in stats