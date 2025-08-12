import os
import sys
import tempfile
import types
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Stub SharePoint modules before importing pipeline
sys.modules.setdefault("office365", types.ModuleType("office365"))
sharepoint = types.ModuleType("office365.sharepoint")
client_context = types.ModuleType("office365.sharepoint.client_context")
client_context.ClientContext = type("ClientContext", (), {})
sharepoint.client_context = client_context
sys.modules.setdefault("office365.sharepoint", sharepoint)
sys.modules.setdefault("office365.sharepoint.client_context", client_context)
runtime = types.ModuleType("office365.runtime")
auth = types.ModuleType("office365.runtime.auth")
user_cred = types.ModuleType("office365.runtime.auth.user_credential")
user_cred.UserCredential = type("UserCredential", (), {})
auth.user_credential = user_cred
runtime.auth = auth
sys.modules.setdefault("office365.runtime", runtime)
sys.modules.setdefault("office365.runtime.auth", auth)
sys.modules.setdefault("office365.runtime.auth.user_credential", user_cred)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from doctr_process from doctr_process import pipeline as pipeline


def test_process_file_skips_pages(monkeypatch, tmp_path):
    # create dummy images
    img1 = Image.new("RGB", (10, 10), color="white")
    img2 = Image.new("RGB", (10, 10), color="white")

    monkeypatch.setattr(
        pipeline,
        "extract_images_generator",
        lambda path, poppler_path=None, dpi=300: [img1, img2],
    )

    def fake_run_preflight(path, cfg):
        return {1}, [{"file": path, "page": 1, "error": "bad", "extract": "out.pdf"}]

    monkeypatch.setattr(pipeline, "run_preflight", fake_run_preflight)
    monkeypatch.setattr(pipeline, "count_total_pages", lambda pdfs, cfg: 2)

    calls = []

    def fake_engine(name):
        def run(img):
            calls.append(img)
            return "TEXT", None

        return run

    monkeypatch.setattr(pipeline, "get_engine", fake_engine)

    def fake_correct(img, page_num, method=None):
        return img

    fake_correct.last_angle = 0
    monkeypatch.setattr(pipeline, "correct_image_orientation", fake_correct)
    monkeypatch.setattr(
        pipeline,
        "save_page_image",
        lambda img, pdf, idx, cfg, vendor=None, ticket_number=None: str(
            tmp_path / f"{idx}.png"
        ),
    )

    rows, perf, exc, *_ = pipeline.process_file(
        "sample.pdf",
        {"preflight": {"enabled": True}, "output_dir": str(tmp_path)},
        [],
        {},
    )

    assert len(calls) == 1  # second page only
    assert len(rows) == 1
    assert rows[0]["page"] == 2
    assert exc[0]["page"] == 1


from doctr_process.ocr.preflight import is_page_ocrable


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
        sys.modules["doctr_process.ocr.preflight"],
        "correct_image_orientation",
        fake_correct,
    )
    cfg["orientation_check"] = "tesseract"
    assert is_page_ocrable(pdf_path, 1, cfg)
    assert called.get("method") == "tesseract"

    os.remove(pdf_path)
