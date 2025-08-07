import os
import sys
import gc
import importlib.util
import types
from pathlib import Path

import pytest
from PIL import Image

# Make package modules importable
MOD_DIR = Path(__file__).resolve().parents[1] / "src" / "doctr_process" / "doctr_mod"
sys.path.insert(0, str(MOD_DIR))
sys.modules.setdefault("doctr_ocr.reporting_utils", types.ModuleType("reporting_utils"))

spec = importlib.util.spec_from_file_location("doctr_ocr_to_csv", MOD_DIR / "doctr_ocr_to_csv.py")
doctr_ocr_to_csv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctr_ocr_to_csv)

from doctr_ocr.ocr_utils import extract_images_generator
process_file = doctr_ocr_to_csv.process_file


def _create_sample(path: Path, ext: str) -> Path:
    path = path.with_suffix('.' + ext)
    img1 = Image.new('RGB', (10, 10), 'white')
    img2 = Image.new('RGB', (10, 10), 'black')
    if ext in {"tiff", "tif"}:
        img1.save(path, save_all=True, append_images=[img2])
    elif ext == 'pdf':
        img1.save(path, format='PDF', save_all=True, append_images=[img2])
    else:
        img1.save(path)
    img1.close()
    img2.close()
    return path


def _has_open_handle(path: Path) -> bool:
    target = os.path.realpath(path)
    fd_dir = Path('/proc') / str(os.getpid()) / 'fd'
    for fd in fd_dir.iterdir():
        try:
            if os.path.realpath(fd.resolve()) == target:
                return True
        except FileNotFoundError:
            continue
    return False


@pytest.mark.parametrize('ext', ['tiff', 'png', 'jpg', 'pdf'])
def test_extract_images_generator_closes_files(ext, tmp_path):
    file_path = _create_sample(tmp_path / 'sample', ext)
    imgs = list(extract_images_generator(str(file_path)))
    for img in imgs:
        img.close()
        assert getattr(img, 'fp', None) is None
    gc.collect()
    assert not _has_open_handle(file_path)


@pytest.mark.parametrize('ext', ['tiff', 'png', 'jpg', 'pdf'])
def test_process_file_closes_images(ext, tmp_path):
    file_path = _create_sample(tmp_path / 'sample', ext)
    out_pdf = tmp_path / 'corrected.pdf'
    cfg = {
        'ocr_engine': 'tesseract',
        'save_corrected_pdf': True,
        'corrected_pdf_path': str(out_pdf),
        'orientation_check': 'none',
        'output_dir': str(tmp_path / 'out'),
        'preflight': {'enabled': False},
    }
    vendor_rules = {}
    extraction_rules = {'DEFAULT': {'ticket_number': {'roi': [0, 0, 1, 1]}}}

    process_file(str(file_path), cfg, vendor_rules, extraction_rules)
    gc.collect()
    assert not _has_open_handle(file_path)
    assert not _has_open_handle(out_pdf)
