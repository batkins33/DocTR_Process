"""Tests for the image preprocessing module."""

import numpy as np
import pytest
from PIL import Image

# Import the preprocessing functions directly to avoid tkinter dependency
from doctr_process.ocr.preprocess import (
    apply_preprocessing,
    apply_grayscale,
    apply_adaptive_threshold,
    apply_denoise,
    apply_deskew,
    apply_perspective_correction,
    _detect_skew_hough,
    _detect_skew_projection,
    _rotate_image,
    _order_corners,
)


@pytest.fixture
def sample_rgb_image():
    """Create a simple RGB test image."""
    # Create a 100x100 RGB image with some text-like pattern
    img_array = np.zeros((100, 100, 3), dtype=np.uint8)
    img_array.fill(255)  # White background
    # Add some black rectangular "text" areas
    img_array[20:30, 10:80] = [0, 0, 0]
    img_array[40:50, 10:80] = [0, 0, 0]
    img_array[60:70, 10:80] = [0, 0, 0]
    return Image.fromarray(img_array)


@pytest.fixture
def sample_grayscale_image():
    """Create a simple grayscale test image."""
    img_array = np.zeros((100, 100), dtype=np.uint8)
    img_array.fill(255)  # White background
    # Add some black rectangular "text" areas
    img_array[20:30, 10:80] = 0
    img_array[40:50, 10:80] = 0
    img_array[60:70, 10:80] = 0
    return Image.fromarray(img_array, mode='L')


@pytest.fixture
def rotated_image():
    """Create a rotated test image for deskewing tests."""
    img_array = np.zeros((200, 200), dtype=np.uint8)
    img_array.fill(255)
    # Add horizontal lines that will be rotated
    for i in range(5):
        y = 40 + i * 30
        img_array[y:y+5, 20:180] = 0
    
    # Rotate the image by 5 degrees
    img = Image.fromarray(img_array, mode='L')
    return img.rotate(5, fillcolor=255, expand=True)


class TestPreprocessingConfig:
    """Test preprocessing configuration handling."""
    
    def test_preprocessing_disabled(self, sample_rgb_image):
        """Test that preprocessing is skipped when disabled."""
        config = {"preprocessing": {"enabled": False}}
        result = apply_preprocessing(sample_rgb_image, config)
        
        # Should return the same image
        assert result.size == sample_rgb_image.size
        assert result.mode == sample_rgb_image.mode
        assert np.array(result).shape == np.array(sample_rgb_image).shape
    
    def test_preprocessing_enabled_but_no_steps(self, sample_rgb_image):
        """Test preprocessing enabled but no individual steps enabled."""
        config = {
            "preprocessing": {
                "enabled": True,
                "grayscale": {"enabled": False},
                "denoise": {"enabled": False},
                "deskew": {"enabled": False},
                "adaptive_threshold": {"enabled": False},
                "perspective_correction": {"enabled": False}
            }
        }
        result = apply_preprocessing(sample_rgb_image, config)
        
        # Should return the same image
        assert result.size == sample_rgb_image.size
        assert result.mode == sample_rgb_image.mode
    
    def test_missing_preprocessing_config(self, sample_rgb_image):
        """Test behavior when preprocessing config is missing."""
        config = {}
        result = apply_preprocessing(sample_rgb_image, config)
        
        # Should return the same image
        assert result.size == sample_rgb_image.size
        assert result.mode == sample_rgb_image.mode


class TestGrayscaleConversion:
    """Test grayscale conversion functionality."""
    
    def test_apply_grayscale_cv2_method(self, sample_rgb_image):
        """Test grayscale conversion using cv2 method."""
        config = {"method": "cv2"}
        
        # Convert PIL to cv2 format
        img_cv = np.array(sample_rgb_image)
        img_cv = img_cv[:, :, ::-1]  # RGB to BGR
        
        result = apply_grayscale(img_cv, config)
        
        assert len(result.shape) == 2  # Should be grayscale
        assert result.dtype == np.uint8
    
    def test_apply_grayscale_weighted_method(self, sample_rgb_image):
        """Test grayscale conversion using weighted method."""
        config = {"method": "weighted", "weights": [0.299, 0.587, 0.114]}
        
        img_cv = np.array(sample_rgb_image)
        img_cv = img_cv[:, :, ::-1]  # RGB to BGR
        
        result = apply_grayscale(img_cv, config)
        
        assert len(result.shape) == 2  # Should be grayscale
        assert result.dtype == np.uint8
    
    def test_grayscale_already_grayscale(self, sample_grayscale_image):
        """Test grayscale conversion on already grayscale image."""
        config = {"method": "cv2"}
        
        img_cv = np.array(sample_grayscale_image)
        result = apply_grayscale(img_cv, config)
        
        # Should return the same image
        assert np.array_equal(result, img_cv)
    
    def test_grayscale_integration(self, sample_rgb_image):
        """Test grayscale conversion through main preprocessing function."""
        config = {
            "preprocessing": {
                "enabled": True,
                "grayscale": {"enabled": True, "method": "cv2"}
            }
        }
        
        result = apply_preprocessing(sample_rgb_image, config)
        
        assert result.mode == 'L'  # Should be grayscale


class TestAdaptiveThreshold:
    """Test adaptive thresholding functionality."""
    
    def test_apply_adaptive_threshold_gaussian(self, sample_grayscale_image):
        """Test adaptive thresholding with Gaussian method."""
        config = {
            "method": "gaussian",
            "block_size": 11,
            "c_constant": 2
        }
        
        img_cv = np.array(sample_grayscale_image)
        result = apply_adaptive_threshold(img_cv, config)
        
        assert len(result.shape) == 2  # Should be grayscale
        assert result.dtype == np.uint8
        assert np.all((result == 0) | (result == 255))  # Should be binary
    
    def test_apply_adaptive_threshold_mean(self, sample_grayscale_image):
        """Test adaptive thresholding with mean method."""
        config = {
            "method": "mean",
            "block_size": 11,
            "c_constant": 2
        }
        
        img_cv = np.array(sample_grayscale_image)
        result = apply_adaptive_threshold(img_cv, config)
        
        assert len(result.shape) == 2  # Should be grayscale
        assert result.dtype == np.uint8
        assert np.all((result == 0) | (result == 255))  # Should be binary
    
    def test_adaptive_threshold_block_size_adjustment(self, sample_grayscale_image):
        """Test that even block sizes are adjusted to odd."""
        config = {
            "method": "gaussian",
            "block_size": 10,  # Even number, should be adjusted to 11
            "c_constant": 2
        }
        
        img_cv = np.array(sample_grayscale_image)
        result = apply_adaptive_threshold(img_cv, config)
        
        # Should work without error (block_size adjusted internally)
        assert result is not None
        assert len(result.shape) == 2
    
    def test_adaptive_threshold_integration(self, sample_rgb_image):
        """Test adaptive thresholding through main preprocessing function."""
        config = {
            "preprocessing": {
                "enabled": True,
                "adaptive_threshold": {
                    "enabled": True,
                    "method": "gaussian",
                    "block_size": 11,
                    "c_constant": 2
                }
            }
        }
        
        result = apply_preprocessing(sample_rgb_image, config)
        
        # Result should be binary (grayscale with only 0 and 255 values)
        assert result.mode == 'L'
        result_array = np.array(result)
        unique_values = np.unique(result_array)
        assert len(unique_values) <= 2  # Should be mostly binary


class TestDenoise:
    """Test denoising functionality."""
    
    def test_apply_denoise_bilateral(self, sample_rgb_image):
        """Test bilateral denoising."""
        config = {
            "method": "bilateral",
            "d": 9,
            "sigma_color": 75,
            "sigma_space": 75
        }
        
        img_cv = np.array(sample_rgb_image)
        img_cv = img_cv[:, :, ::-1]  # RGB to BGR
        
        result = apply_denoise(img_cv, config)
        
        assert result.shape == img_cv.shape
        assert result.dtype == np.uint8
    
    def test_apply_denoise_gaussian(self, sample_rgb_image):
        """Test Gaussian denoising."""
        config = {
            "method": "gaussian",
            "kernel_size": 5,
            "sigma": 1.0
        }
        
        img_cv = np.array(sample_rgb_image)
        img_cv = img_cv[:, :, ::-1]  # RGB to BGR
        
        result = apply_denoise(img_cv, config)
        
        assert result.shape == img_cv.shape
        assert result.dtype == np.uint8
    
    def test_apply_denoise_median(self, sample_rgb_image):
        """Test median denoising."""
        config = {
            "method": "median",
            "kernel_size": 5
        }
        
        img_cv = np.array(sample_rgb_image)
        img_cv = img_cv[:, :, ::-1]  # RGB to BGR
        
        result = apply_denoise(img_cv, config)
        
        assert result.shape == img_cv.shape
        assert result.dtype == np.uint8
    
    def test_apply_denoise_morphological(self, sample_grayscale_image):
        """Test morphological denoising."""
        config = {
            "method": "morphological",
            "kernel_size": 3
        }
        
        img_cv = np.array(sample_grayscale_image)
        result = apply_denoise(img_cv, config)
        
        assert result.shape == img_cv.shape
        assert result.dtype == np.uint8
    
    def test_denoise_integration(self, sample_rgb_image):
        """Test denoising through main preprocessing function."""
        config = {
            "preprocessing": {
                "enabled": True,
                "denoise": {
                    "enabled": True,
                    "method": "bilateral",
                    "d": 9,
                    "sigma_color": 75,
                    "sigma_space": 75
                }
            }
        }
        
        result = apply_preprocessing(sample_rgb_image, config)
        
        assert result.size == sample_rgb_image.size
        # Image should be slightly different due to denoising
        assert not np.array_equal(np.array(result), np.array(sample_rgb_image))


class TestDeskew:
    """Test deskewing functionality."""
    
    def test_rotate_image(self, sample_grayscale_image):
        """Test basic image rotation."""
        img_cv = np.array(sample_grayscale_image)
        angle = 5.0
        
        result = _rotate_image(img_cv, angle)
        
        assert result.dtype == np.uint8
        # Rotated image should be larger due to expand=True equivalent
        assert result.shape[0] >= img_cv.shape[0] or result.shape[1] >= img_cv.shape[1]
    
    def test_rotate_image_zero_angle(self, sample_grayscale_image):
        """Test that zero rotation returns the same image."""
        img_cv = np.array(sample_grayscale_image)
        angle = 0.0
        
        result = _rotate_image(img_cv, angle)
        
        assert np.array_equal(result, img_cv)
    
    def test_detect_skew_hough_no_lines(self):
        """Test skew detection when no lines are found."""
        # Create an image with no clear lines
        img = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        
        angle = _detect_skew_hough(img, 45)
        
        assert angle == 0.0  # Should return 0 when no lines found
    
    def test_apply_deskew_small_angle(self, sample_grayscale_image):
        """Test that small angles below threshold are not corrected."""
        config = {
            "method": "hough",
            "max_angle": 45,
            "min_angle_threshold": 1.0  # Higher threshold
        }
        
        img_cv = np.array(sample_grayscale_image)
        result = apply_deskew(img_cv, config)
        
        # Should return the same image if detected angle is small
        assert result.shape == img_cv.shape
    
    def test_deskew_integration(self, sample_rgb_image):
        """Test deskewing through main preprocessing function."""
        config = {
            "preprocessing": {
                "enabled": True,
                "deskew": {
                    "enabled": True,
                    "method": "hough",
                    "max_angle": 45,
                    "min_angle_threshold": 0.5
                }
            }
        }
        
        result = apply_preprocessing(sample_rgb_image, config)
        
        assert isinstance(result, Image.Image)
        assert result.mode in ['RGB', 'L']


class TestPerspectiveCorrection:
    """Test perspective correction functionality."""
    
    def test_order_corners(self):
        """Test corner ordering functionality."""
        # Create four corner points in random order
        corners = np.array([
            [100, 100],  # bottom-right
            [0, 0],      # top-left
            [100, 0],    # top-right
            [0, 100]     # bottom-left
        ])
        
        ordered = _order_corners(corners)
        
        # Should be ordered as: top-left, top-right, bottom-right, bottom-left
        expected = np.array([
            [0, 0],      # top-left
            [100, 0],    # top-right
            [100, 100],  # bottom-right
            [0, 100]     # bottom-left
        ])
        
        np.testing.assert_array_equal(ordered, expected)
    
    def test_perspective_correction_no_contours(self, sample_grayscale_image):
        """Test perspective correction when no suitable contours are found."""
        config = {"method": "auto", "min_area_ratio": 0.1}
        
        img_cv = np.array(sample_grayscale_image)
        result = apply_perspective_correction(img_cv, config)
        
        # Should return the same image if no contours found
        assert np.array_equal(result, img_cv)
    
    def test_perspective_correction_integration(self, sample_rgb_image):
        """Test perspective correction through main preprocessing function."""
        config = {
            "preprocessing": {
                "enabled": True,
                "perspective_correction": {
                    "enabled": True,
                    "method": "auto",
                    "min_area_ratio": 0.1
                }
            }
        }
        
        result = apply_preprocessing(sample_rgb_image, config)
        
        assert isinstance(result, Image.Image)
        assert result.mode in ['RGB', 'L']


class TestFullPreprocessingPipeline:
    """Test the full preprocessing pipeline with multiple steps."""
    
    def test_full_pipeline_rgb_to_binary(self, sample_rgb_image):
        """Test full pipeline converting RGB to binary."""
        config = {
            "preprocessing": {
                "enabled": True,
                "grayscale": {"enabled": True, "method": "cv2"},
                "denoise": {"enabled": True, "method": "bilateral", "d": 9},
                "adaptive_threshold": {
                    "enabled": True,
                    "method": "gaussian",
                    "block_size": 11,
                    "c_constant": 2
                }
            }
        }
        
        result = apply_preprocessing(sample_rgb_image, config)
        
        assert result.mode == 'L'  # Should be grayscale
        # Should be mostly binary after adaptive threshold
        result_array = np.array(result)
        unique_values = np.unique(result_array)
        assert len(unique_values) <= 2
    
    def test_pipeline_order_matters(self, sample_rgb_image):
        """Test that the preprocessing steps are applied in the correct order."""
        config = {
            "preprocessing": {
                "enabled": True,
                "grayscale": {"enabled": True, "method": "cv2"},
                "adaptive_threshold": {
                    "enabled": True,
                    "method": "gaussian",
                    "block_size": 11,
                    "c_constant": 2
                },
                "denoise": {"enabled": True, "method": "bilateral", "d": 9}
            }
        }
        
        result = apply_preprocessing(sample_rgb_image, config)
        
        # Should complete without error
        assert isinstance(result, Image.Image)
        assert result.mode == 'L'
    
    def test_unknown_methods_fallback(self, sample_rgb_image):
        """Test that unknown methods fall back to defaults."""
        config = {
            "preprocessing": {
                "enabled": True,
                "grayscale": {"enabled": True, "method": "unknown_method"},
                "denoise": {"enabled": True, "method": "unknown_method"},
                "deskew": {"enabled": True, "method": "unknown_method"},
                "adaptive_threshold": {"enabled": True, "method": "unknown_method"}
            }
        }
        
        # Should not raise an exception, but fall back to default methods
        result = apply_preprocessing(sample_rgb_image, config)
        
        assert isinstance(result, Image.Image)
        # Should still process the image despite unknown methods
        assert result.size == sample_rgb_image.size


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_config(self, sample_rgb_image):
        """Test handling of empty configuration."""
        config = {}
        result = apply_preprocessing(sample_rgb_image, config)
        
        # Should return original image
        assert result.size == sample_rgb_image.size
        assert result.mode == sample_rgb_image.mode
    
    def test_none_config(self, sample_rgb_image):
        """Test handling of None configuration."""
        with pytest.raises(AttributeError):
            apply_preprocessing(sample_rgb_image, None)
    
    def test_invalid_image_input(self):
        """Test handling of invalid image input."""
        config = {"preprocessing": {"enabled": True}}
        
        with pytest.raises((AttributeError, TypeError)):
            apply_preprocessing(None, config)
    
    def test_very_small_image(self):
        """Test preprocessing on very small images."""
        # Create a tiny 5x5 image
        tiny_img = Image.fromarray(np.zeros((5, 5, 3), dtype=np.uint8))
        
        config = {
            "preprocessing": {
                "enabled": True,
                "grayscale": {"enabled": True},
                "denoise": {"enabled": True, "method": "gaussian", "kernel_size": 3}
            }
        }
        
        result = apply_preprocessing(tiny_img, config)
        
        assert isinstance(result, Image.Image)
        assert result.size[0] >= 5 and result.size[1] >= 5


if __name__ == "__main__":
    pytest.main([__file__])