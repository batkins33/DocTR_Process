import logging
from PIL import Image

# Pillow>=10 removed the Image.ANTIALIAS constant which EasyOCR still
# references internally. Create a backwards-compatible alias so the
# library works regardless of the installed Pillow version.
if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

try:
    import easyocr

    _easy_ocr = easyocr.Reader(['en'], gpu=False)
    logging.info("✅ EasyOCR initialized successfully.")
except ImportError:
    _easy_ocr = None
    logging.warning("⚠️ EasyOCR not installed or failed to initialize.")


def is_easy_available():
    """Check if EasyOCR was successfully initialized."""
    return _easy_ocr is not None


def read_text_easy(image, **kwargs):
    """
    Perform OCR on a given image using EasyOCR.

    Args:
        image (np.ndarray or path): Image input.
        kwargs: Unused (for compatibility with other backends).

    Returns:
        dict: {'engine': 'easyocr', 'text': ..., 'confidence': ...}
    """
    if not is_easy_available():
        raise RuntimeError("EasyOCR is not available or failed to load.")

    try:
        results = _easy_ocr.readtext(image)
        all_text = []
        confidences = []

        for (_, text, conf) in results:
            all_text.append(text)
            confidences.append(conf)

        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "engine": "easyocr",
            "text": "\n".join(all_text),
            "confidence": avg_conf
        }
    except Exception as e:
        logging.exception("❌ EasyOCR exception:")
        raise RuntimeError(f"EasyOCR failed: {e}")
