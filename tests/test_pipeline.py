import os
from pathlib import Path

import fitz
from PIL import Image

import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from doctr_process import pipeline


def test_process_file_writes_corrected_pdf(tmp_path, monkeypatch):
    pdf_path = tmp_path / "in.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%EOF")

    imgs = [Image.new("RGB", (60, 40), "white"), Image.new("RGB", (40, 80), "black")]

    def fake_extract_images_generator(*args, **kwargs):
        for im in imgs:
            yield im

    def fake_correct_image_orientation(img, page_num, method=None):
        fake_correct_image_orientation.last_angle = 90
        return img.rotate(90, expand=True)

    fake_correct_image_orientation.last_angle = 0

    def fake_engine(_):
        return "", None

    monkeypatch.setattr(pipeline, "extract_images_generator", fake_extract_images_generator)
    monkeypatch.setattr(pipeline, "correct_image_orientation", fake_correct_image_orientation)
    monkeypatch.setattr(pipeline, "get_engine", lambda *_: fake_engine)
    monkeypatch.setattr(pipeline, "find_vendor", lambda *_: ("", "", "", ""))
    monkeypatch.setattr(
        pipeline,
        "extract_vendor_fields",
        lambda *a, **k: {f: None for f in pipeline.FIELDS},
    )
    monkeypatch.setattr(pipeline, "save_page_image", lambda *a, **k: "")
    monkeypatch.setattr(pipeline, "roi_has_digits", lambda img, roi: True)
    monkeypatch.setattr(pipeline, "count_total_pages", lambda files, cfg: 2)
    monkeypatch.setattr(pipeline, "run_preflight", lambda path, cfg: ([], []))

    cfg = {
        "save_corrected_pdf": True,
        "corrected_pdf_path": str(tmp_path / "corrected"),
        "output_dir": str(tmp_path / "out"),
    }

    pipeline.process_file(str(pdf_path), cfg, [], {})

    corrected_path = pipeline._get_corrected_pdf_path(str(pdf_path), cfg)
    assert os.path.exists(corrected_path)

    doc = fitz.open(corrected_path)
    assert doc.page_count == 2

    expected = [im.rotate(90, expand=True) for im in imgs]
    for page, exp in zip(doc, expected):
        pix = page.get_pixmap()
        assert (pix.width, pix.height) == exp.size
        page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        assert list(page_img.getdata()) == list(exp.getdata())
        page_img.close()
        exp.close()

    doc.close()
    for im in imgs:
        im.close()
