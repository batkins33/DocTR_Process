from pathlib import Path
import sys
from PIL import Image
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from src.doctr_process.doctr_mod.doctr_ocr import ocr_utils


def test_orientation_180(monkeypatch):
    monkeypatch.setattr('pytesseract.image_to_osd', lambda img: 'Rotate: 180')
    img = Image.new('RGB', (10, 10), 'white')
    out = ocr_utils.correct_image_orientation(img, 1, method='tesseract')
    assert ocr_utils.correct_image_orientation.last_angle == 180
    assert out.size == img.size
