"""Image preprocessing module for enhancing OCR quality.

This module provides configurable image preprocessing functions including:
- Grayscale conversion
- Adaptive thresholding
- Denoising  
- Deskewing
- Perspective correction

All functions are designed to be configurable via YAML settings.
"""

import logging
import math
from typing import Dict, Any, Tuple, Optional

import cv2
import numpy as np
from PIL import Image


def apply_preprocessing(image: Image.Image, config: Dict[str, Any]) -> Image.Image:
    """Apply configured preprocessing steps to an image.
    
    Args:
        image: PIL Image to preprocess
        config: Preprocessing configuration from YAML
        
    Returns:
        Preprocessed PIL Image
    """
    preprocess_config = config.get("preprocessing", {})
    if not preprocess_config.get("enabled", False):
        return image
    
    # Convert PIL to OpenCV format
    img_cv = np.array(image)
    if len(img_cv.shape) == 3:
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)
    
    original_was_grayscale = len(img_cv.shape) == 2
    
    # Apply preprocessing steps in order
    if preprocess_config.get("grayscale", {}).get("enabled", False):
        img_cv = apply_grayscale(img_cv, preprocess_config["grayscale"])
        
    if preprocess_config.get("denoise", {}).get("enabled", False):
        img_cv = apply_denoise(img_cv, preprocess_config["denoise"])
        
    if preprocess_config.get("deskew", {}).get("enabled", False):
        img_cv = apply_deskew(img_cv, preprocess_config["deskew"])
        
    if preprocess_config.get("adaptive_threshold", {}).get("enabled", False):
        img_cv = apply_adaptive_threshold(img_cv, preprocess_config["adaptive_threshold"])
        
    if preprocess_config.get("perspective_correction", {}).get("enabled", False):
        img_cv = apply_perspective_correction(img_cv, preprocess_config["perspective_correction"])
    
    # Convert back to PIL format
    if len(img_cv.shape) == 2:  # Grayscale
        return Image.fromarray(img_cv, mode='L')
    else:
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        return Image.fromarray(img_cv)


def apply_grayscale(img: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
    """Convert image to grayscale.
    
    Args:
        img: Input image array
        config: Grayscale configuration
        
    Returns:
        Grayscale image array
    """
    if len(img.shape) == 2:
        # Already grayscale
        return img
    
    method = config.get("method", "cv2")
    
    if method == "cv2":
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif method == "weighted":
        # Custom weighted average
        weights = config.get("weights", [0.299, 0.587, 0.114])  # Standard luminance weights
        return np.average(img, axis=2, weights=weights).astype(np.uint8)
    else:
        logging.warning(f"Unknown grayscale method: {method}, using cv2")
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def apply_adaptive_threshold(img: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
    """Apply adaptive thresholding to enhance text contrast.
    
    Args:
        img: Input image array
        config: Adaptive threshold configuration
        
    Returns:
        Thresholded image array
    """
    # Ensure grayscale
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    method = config.get("method", "gaussian")
    block_size = config.get("block_size", 11)
    c_constant = config.get("c_constant", 2)
    
    # Ensure block_size is odd and >= 3
    if block_size % 2 == 0:
        block_size += 1
    block_size = max(3, block_size)
    
    if method == "gaussian":
        adaptive_method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    elif method == "mean":
        adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C
    else:
        logging.warning(f"Unknown adaptive threshold method: {method}, using gaussian")
        adaptive_method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    
    return cv2.adaptiveThreshold(
        img, 255, adaptive_method, cv2.THRESH_BINARY, block_size, c_constant
    )


def apply_denoise(img: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
    """Apply denoising to reduce image noise.
    
    Args:
        img: Input image array
        config: Denoise configuration
        
    Returns:
        Denoised image array
    """
    method = config.get("method", "bilateral")
    
    if method == "bilateral":
        d = config.get("d", 9)
        sigma_color = config.get("sigma_color", 75)
        sigma_space = config.get("sigma_space", 75)
        
        if len(img.shape) == 3:
            return cv2.bilateralFilter(img, d, sigma_color, sigma_space)
        else:
            return cv2.bilateralFilter(img, d, sigma_color, sigma_space)
            
    elif method == "gaussian":
        kernel_size = config.get("kernel_size", 5)
        sigma = config.get("sigma", 1.0)
        
        # Ensure kernel_size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
            
        return cv2.GaussianBlur(img, (kernel_size, kernel_size), sigma)
        
    elif method == "median":
        kernel_size = config.get("kernel_size", 5)
        
        # Ensure kernel_size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1
            
        return cv2.medianBlur(img, kernel_size)
        
    elif method == "morphological":
        # Morphological opening to remove noise
        kernel_size = config.get("kernel_size", 3)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        return cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel)
        
    else:
        logging.warning(f"Unknown denoise method: {method}, using bilateral")
        return cv2.bilateralFilter(img, 9, 75, 75)


def apply_deskew(img: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
    """Apply deskewing to correct image rotation.
    
    Args:
        img: Input image array
        config: Deskew configuration
        
    Returns:
        Deskewed image array
    """
    method = config.get("method", "hough")
    max_angle = config.get("max_angle", 45)
    
    if method == "hough":
        angle = _detect_skew_hough(img, max_angle)
    elif method == "projection":
        angle = _detect_skew_projection(img, max_angle)
    else:
        logging.warning(f"Unknown deskew method: {method}, using hough")
        angle = _detect_skew_hough(img, max_angle)
    
    # Only correct if angle is significant
    min_angle_threshold = config.get("min_angle_threshold", 0.5)
    if abs(angle) < min_angle_threshold:
        return img
    
    logging.info(f"Deskewing image by {angle:.2f} degrees")
    return _rotate_image(img, angle)


def _detect_skew_hough(img: np.ndarray, max_angle: float) -> float:
    """Detect skew angle using Hough line transform."""
    # Ensure grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Hough line detection
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=100, maxLineGap=10)
    
    if lines is None:
        return 0.0
    
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 - x1 != 0:  # Avoid division by zero
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            # Normalize angle to [-45, 45] range
            if angle > 45:
                angle -= 90
            elif angle < -45:
                angle += 90
            if abs(angle) <= max_angle:
                angles.append(angle)
    
    if not angles:
        return 0.0
    
    # Return median angle to reduce outlier impact
    return np.median(angles)


def _detect_skew_projection(img: np.ndarray, max_angle: float) -> float:
    """Detect skew angle using projection profile method."""
    # Ensure grayscale
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Binarize
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    best_angle = 0
    max_variance = 0
    
    # Test angles from -max_angle to +max_angle
    angles_to_test = np.arange(-max_angle, max_angle + 1, 0.5)
    
    for angle in angles_to_test:
        rotated = _rotate_image(binary, angle)
        
        # Calculate horizontal projection
        h_projection = np.sum(rotated, axis=1)
        
        # Calculate variance (higher variance means better alignment)
        variance = np.var(h_projection)
        
        if variance > max_variance:
            max_variance = variance
            best_angle = angle
    
    return best_angle


def _rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by given angle."""
    if abs(angle) < 0.01:  # No rotation needed
        return img
    
    h, w = img.shape[:2]
    center = (w // 2, h // 2)
    
    # Get rotation matrix
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Calculate new image dimensions
    cos_angle = abs(M[0, 0])
    sin_angle = abs(M[0, 1])
    new_w = int((h * sin_angle) + (w * cos_angle))
    new_h = int((h * cos_angle) + (w * sin_angle))
    
    # Adjust rotation matrix for new center
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]
    
    # Apply rotation
    return cv2.warpAffine(img, M, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def apply_perspective_correction(img: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
    """Apply perspective correction to straighten document.
    
    Args:
        img: Input image array
        config: Perspective correction configuration
        
    Returns:
        Perspective corrected image array
    """
    method = config.get("method", "auto")
    
    if method == "auto":
        return _auto_perspective_correction(img, config)
    else:
        logging.warning(f"Unknown perspective correction method: {method}")
        return img


def _auto_perspective_correction(img: np.ndarray, config: Dict[str, Any]) -> np.ndarray:
    """Automatically detect and correct perspective distortion."""
    # Ensure grayscale for edge detection
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img.copy()
    
    # Edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Find the largest rectangular contour
    largest_contour = None
    max_area = 0
    
    for contour in contours:
        # Approximate contour to polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Check if it's roughly rectangular (4 corners)
        if len(approx) == 4:
            area = cv2.contourArea(approx)
            if area > max_area:
                max_area = area
                largest_contour = approx
    
    if largest_contour is None:
        return img
    
    # Check if the area is significant enough
    img_area = img.shape[0] * img.shape[1]
    min_area_ratio = config.get("min_area_ratio", 0.1)
    if max_area < img_area * min_area_ratio:
        return img
    
    # Get corner points
    corners = largest_contour.reshape(4, 2)
    
    # Order corners: top-left, top-right, bottom-right, bottom-left
    corners = _order_corners(corners)
    
    # Calculate destination rectangle dimensions
    width_a = np.sqrt(((corners[2][0] - corners[3][0]) ** 2) + ((corners[2][1] - corners[3][1]) ** 2))
    width_b = np.sqrt(((corners[1][0] - corners[0][0]) ** 2) + ((corners[1][1] - corners[0][1]) ** 2))
    max_width = max(int(width_a), int(width_b))
    
    height_a = np.sqrt(((corners[1][0] - corners[2][0]) ** 2) + ((corners[1][1] - corners[2][1]) ** 2))
    height_b = np.sqrt(((corners[0][0] - corners[3][0]) ** 2) + ((corners[0][1] - corners[3][1]) ** 2))
    max_height = max(int(height_a), int(height_b))
    
    # Define destination points
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")
    
    # Calculate perspective transform matrix
    M = cv2.getPerspectiveTransform(corners.astype("float32"), dst)
    
    # Apply perspective correction
    return cv2.warpPerspective(img, M, (max_width, max_height))


def _order_corners(pts: np.ndarray) -> np.ndarray:
    """Order corner points in clockwise order starting from top-left."""
    # Sort by y-coordinate
    y_sorted = pts[np.argsort(pts[:, 1])]
    
    # Get top and bottom pairs
    top = y_sorted[:2]
    bottom = y_sorted[2:]
    
    # Sort top pair by x-coordinate (left to right)
    top = top[np.argsort(top[:, 0])]
    
    # Sort bottom pair by x-coordinate (right to left for clockwise order)
    bottom = bottom[np.argsort(bottom[:, 0])[::-1]]
    
    return np.array([top[0], top[1], bottom[0], bottom[1]])