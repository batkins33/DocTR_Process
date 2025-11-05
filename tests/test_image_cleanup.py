import gc
import os
import sys
import types
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# Make package modules importable and stub SharePoint client
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

from doctr_process import pipeline as pipeline
from doctr_process.ocr.ocr_utils import extract_images_generator

process_file = pipeline.process_file


def _create_sample(path: Path, ext: str) -> Path:
    path = path.with_suffix("." + ext)
    img1 = Image.new("RGB", (10, 10), "white")
    img2 = Image.new("RGB", (10, 10), "black")
    try:
        if ext in {"tiff", "tif"}:
            img1.save(path, save_all=True, append_images=[img2])
        elif ext == "pdf":
            img1.save(path, format="PDF", save_all=True, append_images=[img2])
        else:
            img1.save(path)
    finally:
        img1.close()
        img2.close()
    return path


def _has_open_handle(path: Path) -> bool:
    target = os.path.realpath(path)
    fd_dir = Path("/proc") / str(os.getpid()) / "fd"
    for fd in fd_dir.iterdir():
        try:
            if os.path.realpath(fd.resolve()) == target:
                return True
        except FileNotFoundError:
            continue
    return False


@pytest.mark.parametrize("ext", ["tiff", "png", "jpg", "pdf"])
def test_extract_images_generator_closes_files(ext, tmp_path):
    file_path = _create_sample(tmp_path / "sample", ext)
    imgs = list(extract_images_generator(str(file_path)))
    for img in imgs:
        if hasattr(img, "close"):
            img.close()
            assert getattr(img, "fp", None) is None
    gc.collect()
    assert not _has_open_handle(file_path)


@pytest.mark.parametrize("ext", ["tiff", "png", "jpg", "pdf"])
def test_extract_images_generator_returns_ndarray(ext, tmp_path):
    file_path = _create_sample(tmp_path / "sample", ext)
    imgs = list(extract_images_generator(str(file_path)))
    assert all(isinstance(img, np.ndarray) for img in imgs)
    gc.collect()
    assert not _has_open_handle(file_path)


@pytest.mark.parametrize("ext", ["tiff", "png", "jpg", "pdf"])
def test_process_file_closes_images(ext, tmp_path, monkeypatch):
    file_path = _create_sample(tmp_path / "sample", ext)
    out_pdf = tmp_path / "corrected.pdf"
    cfg = {
        "ocr_engine": "tesseract",
        "save_corrected_pdf": True,
        "corrected_pdf_path": str(out_pdf),
        "crops": True,
        "thumbnails": True,
        "orientation_check": "none",
        "output_dir": str(tmp_path / "out"),
        "preflight": {"enabled": False},
    }
    vendor_rules = {}
    extraction_rules = {"DEFAULT": {"ticket_number": {"roi": [0, 0, 1, 1]}}}
    monkeypatch.setattr(pipeline, "get_engine", lambda name: lambda img: ("", None))

    result = process_file(str(file_path), cfg, vendor_rules, extraction_rules)
    if not result or len(result) == 0:
        pytest.fail("process_file returned empty result")
    rows = result[0] if len(result) > 0 else []
    thumb_log = result[-1] if len(result) > 0 else []
    gc.collect()

    out_dir = Path(cfg["output_dir"])
    crop_paths = list((out_dir / "crops").glob("*.png"))
    thumb_paths = [Path(t["thumbnail"]) for t in thumb_log if "thumbnail" in t]
    page_paths = [Path(r["image_path"]) for r in rows]

    for p in [file_path, out_pdf, *page_paths, *crop_paths, *thumb_paths]:
        assert p.exists()
        assert not _has_open_handle(p)


def test_multipage_tiff_processed(tmp_path, monkeypatch):
    file_path = _create_sample(tmp_path / "multi", "tiff")
    imgs = list(extract_images_generator(str(file_path)))
    assert len(imgs) == 2
    for img in imgs:
        if hasattr(img, "close"):
            img.close()

    cfg = {
        "ocr_engine": "tesseract",
        "save_corrected_pdf": False,
        "orientation_check": "none",
        "output_dir": str(tmp_path / "out"),
        "preflight": {"enabled": False},
    }
    vendor_rules = {}
    extraction_rules = {"DEFAULT": {"ticket_number": {"roi": [0, 0, 1, 1]}}}
    monkeypatch.setattr(pipeline, "get_engine", lambda name: lambda img: ("", None))
    rows, *_ = process_file(str(file_path), cfg, vendor_rules, extraction_rules)
    assert len(rows) == 2
