import os
import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doctr_mod.doctr_ocr.preflight import is_page_ocrable
from doctr_mod.doctr_ocr import ocr_utils

def create_rotated_pdf(text="Test", angle=90, font=None):
    img = Image.new("RGB", (400, 200), "white")
    draw = ImageDraw.Draw(img)
    if font is None:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", 50)
        except Exception:
            font = ImageFont.load_default()
    draw.text((20, 60), text * 3, fill="black", font=font)
    rot = img.rotate(angle, expand=True)
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    rot.save(path, format="PDF", resolution=300)
    return path

def test_is_page_ocrable_rotated(monkeypatch):
    pdf_path = create_rotated_pdf()
    cfg = {"preflight": {"dpi_threshold": 150, "min_chars": 4}, "poppler_path": None}

    called = {}
    def fake_correct(img, page_num=None, method="tesseract"):
        called["method"] = method
        return img.rotate(-90, expand=True)

    monkeypatch.setattr(
        sys.modules["doctr_mod.doctr_ocr.preflight"],
        "correct_image_orientation",
        fake_correct,
    )
    cfg["orientation_check"] = "tesseract"
    assert is_page_ocrable(pdf_path, 1, cfg)
    assert called.get("method") == "tesseract"

    os.remove(pdf_path)

