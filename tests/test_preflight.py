from pathlib import Path

import importlib.util
import sys
import pytest
from PIL import Image
import types

SPEC = importlib.util.spec_from_file_location(
    "doctr_ocr_to_csv",
    Path(__file__).resolve().parents[1]
    / "src"
    / "doctr_process"
    / "doctr_mod"
    / "doctr_ocr_to_csv.py",
)
doctr_ocr_to_csv = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "doctr_process" / "doctr_mod"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "doctr_process"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.modules.setdefault("office365", types.ModuleType("office365"))
client_mod = types.ModuleType("client_context")
client_mod.ClientContext = type("ClientContext", (), {})
sys.modules.setdefault("office365.sharepoint.client_context", client_mod)
auth_mod = types.ModuleType("user_credential")
auth_mod.UserCredential = type("UserCredential", (), {})
sys.modules.setdefault("office365.runtime.auth.user_credential", auth_mod)
SPEC.loader.exec_module(doctr_ocr_to_csv)


def test_process_file_skips_pages(monkeypatch, tmp_path):
    # create dummy images
    img1 = Image.new("RGB", (10, 10), color="white")
    img2 = Image.new("RGB", (10, 10), color="white")

    monkeypatch.setattr(
        doctr_ocr_to_csv,
        "extract_images_generator",
        lambda path, poppler_path=None: [img1, img2],
    )

    def fake_run_preflight(path, cfg):
        return {1}, [{"file": path, "page": 1, "error": "bad", "extract": "out.pdf"}]

    monkeypatch.setattr(doctr_ocr_to_csv, "run_preflight", fake_run_preflight)
    monkeypatch.setattr(doctr_ocr_to_csv, "count_total_pages", lambda pdfs, cfg: 2)

    calls = []

    def fake_engine(name):
        def run(img):
            calls.append(img)
            return "TEXT", None

        return run

    monkeypatch.setattr(doctr_ocr_to_csv, "get_engine", fake_engine)
    def fake_correct(img, page_num, method=None):
        return img
    fake_correct.last_angle = 0
    monkeypatch.setattr(doctr_ocr_to_csv, "correct_image_orientation", fake_correct)
    monkeypatch.setattr(doctr_ocr_to_csv, "save_page_image", lambda img, pdf, idx, cfg, vendor=None, ticket_number=None: str(tmp_path / f"{idx}.png"))

    rows, perf, exc, *_ = doctr_ocr_to_csv.process_file(
        "sample.pdf",
        {"preflight": {"enabled": True}, "output_dir": str(tmp_path)},
        [],
        {},
    )

    assert len(calls) == 1  # second page only
    assert len(rows) == 1
    assert rows[0]["page"] == 2
    assert exc[0]["page"] == 1
import os
import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from src.doctr_process.doctr_mod.doctr_ocr.preflight import is_page_ocrable
from src.doctr_process.doctr_mod.doctr_ocr import ocr_utils

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
        sys.modules["doctr_process.doctr_mod.doctr_ocr.preflight"],
        "correct_image_orientation",
        fake_correct,
    )
    cfg["orientation_check"] = "tesseract"
    assert is_page_ocrable(pdf_path, 1, cfg)
    assert called.get("method") == "tesseract"

    os.remove(pdf_path)
