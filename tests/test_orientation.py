import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from doctr_process import ocr as ocr_utils


def test_orientation_180(monkeypatch):
    monkeypatch.setattr('pytesseract.image_to_osd', lambda img: 'Rotate: 180')
    img = Image.new('RGB', (10, 10), 'white')
    out = ocr_utils.correct_image_orientation(img, 1, method='tesseract')
    assert ocr_utils.correct_image_orientation.last_angle == 180
    assert out.size == img.size
