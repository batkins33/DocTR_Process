# utils/ocr_wrapper.py

import logging
import numpy as np
from PIL import Image

# Pillow>=10 removed the Image.ANTIALIAS constant which EasyOCR still
# references internally. Provide a backwards-compatible alias so EasyOCR
# works regardless of the installed Pillow version.
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import easyocr

# Initialize once with GPU disabled by default for broader compatibility
_easyocr_reader = easyocr.Reader(['en'], gpu=False)


def read_text(image: Image.Image) -> dict:
    """Run EasyOCR on an image and return combined text and confidence."""
    try:
        result = _easyocr_reader.readtext(np.array(image))
        text = " ".join([r[1] for r in result])
        confs = [r[2] for r in result]
        avg_conf = sum(confs) / len(confs) if confs else 0
        return {"engine": "easyocr", "text": text, "confidence": avg_conf}
    except Exception as e:
        logging.error(f"❌ EasyOCR failed: {e}")
        return {"engine": "easyocr", "text": "", "confidence": 0}
