"""Comprehensive tests for OCR utilities (preprocessing functionality)."""

import importlib.util
from pathlib import Path
import pytest
import tempfile
import numpy as np
from PIL import Image
from unittest.mock import Mock, patch

# Load the ocr_utils module directly 
SPEC = importlib.util.spec_from_file_location(
    "ocr_utils",
    Path(__file__).resolve().parents[1]
    / "src"
    / "doctr_process"
    / "ocr"
    / "ocr_utils.py",
)
ocr_utils = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ocr_utils)


class TestOcrWithFallback:
    """Test the ocr_with_fallback function."""
    
    def test_ocr_with_fallback_successful_primary(self):
        """Test OCR when primary attempt succeeds."""
        # Create a mock image
        img = Image.new('RGB', (100, 50), color='white')
        
        # Create mock model and docs
        mock_block = Mock()
        mock_block.lines = [Mock()]  # Non-empty lines indicate success
        
        mock_page = Mock()
        mock_page.blocks = [mock_block]
        
        mock_docs = Mock()
        mock_docs.pages = [mock_page]
        
        mock_model = Mock(return_value=mock_docs)
        
        result = ocr_utils.ocr_with_fallback(img, mock_model)
        
        assert result == mock_docs
        assert mock_model.call_count == 1
        
    def test_ocr_with_fallback_uses_grayscale_fallback(self):
        """Test OCR fallback to grayscale when primary fails."""
        # Create a mock image
        img = Image.new('RGB', (100, 50), color='white')
        
        # Create mock model - first call returns empty, second succeeds
        empty_block = Mock()
        empty_block.lines = []  # Empty lines indicate failure
        
        empty_page = Mock()
        empty_page.blocks = [empty_block]
        
        empty_docs = Mock()
        empty_docs.pages = [empty_page]
        
        success_block = Mock()
        success_block.lines = [Mock()]
        
        success_page = Mock()
        success_page.blocks = [success_block]
        
        success_docs = Mock()
        success_docs.pages = [success_page]
        
        mock_model = Mock(side_effect=[empty_docs, success_docs])
        
        # Mock the cv2 functions that might not be available
        with patch('src.doctr_process.ocr.ocr_utils.cv2.cvtColor') as mock_cvt, \
             patch('src.doctr_process.ocr.ocr_utils.cv2.threshold') as mock_thresh:
            mock_cvt.return_value = np.zeros((50, 100), dtype=np.uint8)
            mock_thresh.return_value = (128, np.zeros((50, 100), dtype=np.uint8))
            
            result = ocr_utils.ocr_with_fallback(img, mock_model)
        
        assert result == success_docs
        assert mock_model.call_count == 2


class TestExtractImagesGenerator:
    """Test the extract_images_generator function."""
    
    def test_extract_images_generator_pdf(self):
        """Test image extraction from PDF."""
        # Create a simple test PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            # Write minimal PDF content
            tmp_file.write(b'%PDF-1.4\n%EOF')
            tmp_file.flush()
            
            # Mock pdf2image.convert_from_path
            with patch('pdf2image.convert_from_path') as mock_convert:
                # Create mock PIL images
                mock_img1 = Image.new('RGB', (100, 100), color='red')
                mock_img2 = Image.new('RGB', (100, 100), color='blue')
                mock_convert.return_value = [mock_img1, mock_img2]
                
                generator = ocr_utils.extract_images_generator(tmp_file.name)
                images = list(generator)
                
                assert len(images) == 2
                assert all(isinstance(img, np.ndarray) for img in images)
                assert images[0].shape == (100, 100, 3)
                
    def test_extract_images_generator_image_file(self):
        """Test image extraction from image file."""
        # Create a test image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            img = Image.new('RGB', (50, 50), color='green')
            img.save(tmp_file.name, 'JPEG')
            
            generator = ocr_utils.extract_images_generator(tmp_file.name)
            images = list(generator)
            
            assert len(images) == 1
            assert isinstance(images[0], np.ndarray)
            assert images[0].shape == (50, 50, 3)


class TestCorrectImageOrientation:
    """Test the correct_image_orientation function."""
    
    def test_correct_image_orientation_no_rotation(self):
        """Test orientation correction when no rotation is needed."""
        img = Image.new('RGB', (100, 50), color='white')
        
        # Mock pytesseract.image_to_osd to return 0 rotation
        with patch('pytesseract.image_to_osd') as mock_osd:
            mock_osd.return_value = "Rotate: 0\nOrientation confidence: 12.34"
            
            result = ocr_utils.correct_image_orientation(img, 1)
            
            # Should return the same image when no rotation needed
            assert result.size == img.size
            
    def test_correct_image_orientation_90_degrees(self):
        """Test orientation correction with 90 degree rotation."""
        img = Image.new('RGB', (100, 50), color='white')
        
        with patch('pytesseract.image_to_osd') as mock_osd:
            mock_osd.return_value = "Rotate: 90\nOrientation confidence: 12.34"
            
            result = ocr_utils.correct_image_orientation(img, 1)
            
            # After 90-degree rotation, dimensions should be swapped
            assert result.size == (50, 100)
            
    def test_correct_image_orientation_tesseract_error(self):
        """Test orientation correction when Tesseract fails."""
        img = Image.new('RGB', (100, 50), color='white')
        
        with patch('pytesseract.image_to_osd') as mock_osd:
            mock_osd.side_effect = Exception("Tesseract error")
            
            result = ocr_utils.correct_image_orientation(img, 1)
            
            # Should return original image when Tesseract fails
            assert result.size == img.size


class TestGetFileHash:
    """Test the get_file_hash function."""
    
    def test_get_file_hash_consistent(self):
        """Test that file hash is consistent for same content."""
        # get_file_hash actually hashes the filepath string, not the file content
        filepath = "/test/path/file.txt"
        
        hash1 = ocr_utils.get_file_hash(filepath)
        hash2 = ocr_utils.get_file_hash(filepath)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
        
    def test_get_file_hash_different_content(self):
        """Test that different paths produce different hashes."""
        filepath1 = "/test/path1/file.txt"
        filepath2 = "/test/path2/file.txt"
        
        hash1 = ocr_utils.get_file_hash(filepath1)
        hash2 = ocr_utils.get_file_hash(filepath2)
        
        assert hash1 != hash2


class TestGetImageHash:
    """Test the get_image_hash function."""
    
    def test_get_image_hash_consistent(self):
        """Test that image hash is consistent for same image."""
        img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        
        hash1 = ocr_utils.get_image_hash(img_array)
        hash2 = ocr_utils.get_image_hash(img_array)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
        
    def test_get_image_hash_different_images(self):
        """Test that different images produce different hashes."""
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.ones((100, 100, 3), dtype=np.uint8)
        
        hash1 = ocr_utils.get_image_hash(img1)
        hash2 = ocr_utils.get_image_hash(img2)
        
        assert hash1 != hash2


class TestRoiHasDigits:
    """Test the roi_has_digits function."""
    
    def test_roi_has_digits_with_digits(self):
        """Test ROI detection when digits are present."""
        # Create a mock image with digits
        img = Image.new('RGB', (100, 100), color='white')
        roi = [0, 0, 1, 1]  # Full image
        
        # Mock pytesseract to return text with digits
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Some text with 123 numbers"
            
            result = ocr_utils.roi_has_digits(img, roi)
            assert result is True
            
    def test_roi_has_digits_no_digits(self):
        """Test ROI detection when no digits are present."""
        img = Image.new('RGB', (100, 100), color='white')
        roi = [0, 0, 1, 1]
        
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Only text without numbers"
            
            result = ocr_utils.roi_has_digits(img, roi)
            assert result is False
            
    def test_roi_has_digits_tesseract_error(self):
        """Test ROI detection when Tesseract fails."""
        img = Image.new('RGB', (100, 100), color='white')
        roi = [0, 0, 1, 1]
        
        with patch('pytesseract.image_to_string') as mock_ocr:
            mock_ocr.side_effect = Exception("Tesseract error")
            
            result = ocr_utils.roi_has_digits(img, roi)
            assert result is False


class TestSaveRoiImage:
    """Test the save_roi_image function."""
    
    def test_save_roi_image_creates_file(self):
        """Test that ROI image is saved correctly."""
        img = Image.new('RGB', (100, 100), color='red')
        roi = [0.25, 0.25, 0.75, 0.75]  # Center quarter
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "test_roi.png"
            
            ocr_utils.save_roi_image(img, roi, str(output_path))
            
            assert output_path.exists()
            
            # Load and verify the saved image
            saved_img = Image.open(output_path)
            assert saved_img.size == (50, 50)  # Quarter of original size


class TestModuleConstants:
    """Test module constants and exports."""
    
    def test_all_exports_exist(self):
        """Test that all exported functions exist."""
        expected_exports = [
            "ocr_with_fallback",
            "extract_images_generator", 
            "correct_image_orientation",
            "get_file_hash",
            "get_image_hash",
            "save_roi_image",
            "roi_has_digits",
        ]
        
        for export in expected_exports:
            assert hasattr(ocr_utils, export)
            assert callable(getattr(ocr_utils, export))