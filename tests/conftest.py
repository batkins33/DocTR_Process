import logging
import os
import sys
import types
from pathlib import Path
from PIL import Image, ImageDraw

# Stub OpenCV
cv2_mod = types.ModuleType("cv2")


def _cv2_threshold(arr, thresh, maxval, threshold_type):
    return 0, arr


cv2_mod.threshold = _cv2_threshold
cv2_mod.THRESH_BINARY = 0
cv2_mod.THRESH_OTSU = 0
sys.modules.setdefault("cv2", cv2_mod)

# Stub pytesseract with minimal functions used in tests
pytesseract_mod = types.ModuleType("pytesseract")
pytesseract_mod.image_to_osd = lambda *a, **k: "Rotate: 0"
pytesseract_mod.image_to_string = lambda *a, **k: "12345"
sys.modules.setdefault("pytesseract", pytesseract_mod)

# Stub pdf2image and its exceptions
pdf2image_mod = types.ModuleType("pdf2image")


def _dummy_convert_from_path(*args, **kwargs):
    img = Image.new("RGB", (200, 200), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill="black")
    return [img]


pdf2image_mod.convert_from_path = _dummy_convert_from_path
pdf2image_mod.pdfinfo_from_path = lambda *a, **k: {"Pages": 1}
pdf2image_ex = types.ModuleType("pdf2image.exceptions")
pdf2image_ex.PDFInfoNotInstalledError = Exception
pdf2image_mod.exceptions = pdf2image_ex
sys.modules.setdefault("pdf2image", pdf2image_mod)
sys.modules.setdefault("pdf2image.exceptions", pdf2image_ex)

# Stub PyMuPDF (fitz)
fitz_mod = types.ModuleType("fitz")
sys.modules.setdefault("fitz", fitz_mod)

# pytest configuration for integration tests

# Ensure test fixtures directory exists
FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)
PDF_FIXTURES_DIR = FIXTURES_DIR / "pdfs"
PDF_FIXTURES_DIR.mkdir(exist_ok=True)
SNAPSHOTS_DIR = FIXTURES_DIR / "snapshots"
SNAPSHOTS_DIR.mkdir(exist_ok=True)

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Suppress noisy loggers during tests
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)

# Environment variables for tests
os.environ["TEST_MODE"] = "1"
os.environ["LOG_LEVEL"] = "DEBUG"
