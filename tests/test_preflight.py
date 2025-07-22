from pathlib import Path

import importlib.util
import sys
import pytest
from PIL import Image
import types

SPEC = importlib.util.spec_from_file_location(
    "doctr_ocr_to_csv",
    Path(__file__).resolve().parents[1] / "doctr_mod" / "doctr_ocr_to_csv.py",
)
doctr_ocr_to_csv = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "doctr_mod"))
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
    monkeypatch.setattr(doctr_ocr_to_csv, "correct_image_orientation", lambda img, page_num, method=None: img)
    monkeypatch.setattr(doctr_ocr_to_csv, "save_page_image", lambda img, pdf, idx, cfg, vendor=None, ticket_number=None: str(tmp_path / f"{idx}.png"))

    rows, perf, exc = doctr_ocr_to_csv.process_file(
        "sample.pdf",
        {"preflight": {"enabled": True}, "output_dir": str(tmp_path)},
        [],
        {},
    )

    assert len(calls) == 1  # second page only
    assert len(rows) == 1
    assert rows[0]["page"] == 2
    assert exc[0]["page"] == 1
