"""OCR processing with batch support and model reuse."""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
from PIL import Image

from ..ocr.ocr_engine import get_engine
from ..ocr.ocr_utils import correct_image_orientation, get_image_hash


class OCRProcessor:
    """Handles OCR processing with batch support and model reuse."""
    
    def __init__(self, engine_name: str = "doctr", orientation_method: str = "tesseract"):
        self.engine_name = engine_name
        self.orientation_method = orientation_method
        self._engine = None
        self._stats = {"total_pages": 0, "total_time": 0.0, "batch_count": 0}
    
    @property
    def engine(self):
        """Lazy-load and reuse OCR engine instance."""
        if self._engine is None:
            self._engine = get_engine(self.engine_name)
        return self._engine
    
    def process_single_page(self, image: Image.Image, page_num: int = 1) -> Dict[str, Any]:
        """Process single page with OCR."""
        start_time = time.perf_counter()
        
        # Orientation correction
        orient_start = time.perf_counter()
        corrected_image = correct_image_orientation(
            image, page_num, method=self.orientation_method
        )
        orient_time = time.perf_counter() - orient_start
        
        # OCR processing
        ocr_start = time.perf_counter()
        text, result_page = self.engine(corrected_image)
        ocr_time = time.perf_counter() - ocr_start
        
        total_time = time.perf_counter() - start_time
        
        # Update stats
        self._stats["total_pages"] += 1
        self._stats["total_time"] += total_time
        
        return {
            "text": text,
            "result_page": result_page,
            "page_hash": get_image_hash(corrected_image),
            "orientation": getattr(correct_image_orientation, 'last_angle', 0),
            "timings": {
                "orientation": round(orient_time, 3),
                "ocr": round(ocr_time, 3),
                "total": round(total_time, 3)
            }
        }
    
    def process_batch(self, images: List[Image.Image]) -> List[Dict[str, Any]]:
        """Process multiple pages in batch for better efficiency."""
        if not images:
            return []
        
        start_time = time.perf_counter()
        results = []
        
        # Process orientation correction in batch
        corrected_images = []
        orient_times = []
        
        for i, image in enumerate(images):
            orient_start = time.perf_counter()
            corrected = correct_image_orientation(
                image, i + 1, method=self.orientation_method
            )
            orient_time = time.perf_counter() - orient_start
            
            corrected_images.append(corrected)
            orient_times.append(orient_time)
        
        # Batch OCR processing
        ocr_start = time.perf_counter()
        
        try:
            # Try batch processing if engine supports it
            if len(corrected_images) > 1:
                batch_text, batch_pages = self.engine(corrected_images)
                if isinstance(batch_text, list):
                    texts = batch_text
                    pages = batch_pages if batch_pages else [None] * len(texts)
                else:
                    # Fallback to single processing
                    texts, pages = [], []
                    for img in corrected_images:
                        text, page = self.engine(img)
                        texts.append(text)
                        pages.append(page)
            else:
                text, page = self.engine(corrected_images[0])
                texts = [text]
                pages = [page]
        except Exception as e:
            logging.warning(f"Batch OCR failed, falling back to individual processing: {e}")
            texts, pages = [], []
            for img in corrected_images:
                try:
                    text, page = self.engine(img)
                    texts.append(text)
                    pages.append(page)
                except Exception as page_e:
                    logging.error(f"Page OCR failed: {page_e}")
                    texts.append("")
                    pages.append(None)
        
        ocr_time = time.perf_counter() - ocr_start
        total_batch_time = time.perf_counter() - start_time
        
        # Build results
        for i, (text, page, corrected_img, orient_time) in enumerate(
            zip(texts, pages, corrected_images, orient_times)
        ):
            results.append({
                "text": text,
                "result_page": page,
                "page_hash": get_image_hash(corrected_img),
                "orientation": getattr(correct_image_orientation, 'last_angle', 0),
                "timings": {
                    "orientation": round(orient_time, 3),
                    "ocr": round(ocr_time / len(images), 3),  # Average OCR time per page
                    "total": round(total_batch_time / len(images), 3)
                }
            })
        
        # Update stats
        self._stats["total_pages"] += len(images)
        self._stats["total_time"] += total_batch_time
        self._stats["batch_count"] += 1
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self._stats.copy()
        if stats["total_pages"] > 0:
            stats["avg_time_per_page"] = round(stats["total_time"] / stats["total_pages"], 3)
        return stats