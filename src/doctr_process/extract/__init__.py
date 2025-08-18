"""Extraction module for DocTR Process - handles OCR, vendor detection, and field extraction."""

from .vendor_utils import (
    load_vendor_rules_from_csv,
    find_vendor,
    extract_field,
    extract_vendor_fields,
    FIELDS,
)
from .ocr_utils import (
    ocr_with_fallback,
    extract_images_generator,
    correct_image_orientation,
    get_file_hash,
    get_image_hash,
    save_roi_image,
    roi_has_digits,
    save_crop_and_thumbnail,
)
from .ocr_engine import get_engine
from .preflight import (
    count_total_pages,
    is_page_ocrable,
    preflight_pages,
    extract_page,
    run_preflight,
)

__all__ = [
    "load_vendor_rules_from_csv",
    "find_vendor", 
    "extract_field",
    "extract_vendor_fields",
    "FIELDS",
    "ocr_with_fallback",
    "extract_images_generator", 
    "correct_image_orientation",
    "get_file_hash",
    "get_image_hash",
    "save_roi_image",
    "roi_has_digits",
    "save_crop_and_thumbnail",
    "get_engine",
    "count_total_pages",
    "is_page_ocrable",
    "preflight_pages",
    "extract_page",
    "run_preflight",
]