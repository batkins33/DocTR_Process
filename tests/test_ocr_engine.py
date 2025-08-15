import sys
from types import ModuleType

import numpy as np
import pytest
from PIL import Image
from src.doctr_process.ocr.ocr_engine import get_engine


@pytest.mark.parametrize("engine_name,prefix", [
    ("tesseract", "tess"),
    ("easyocr", "easy"),
    ("doctr", "doctr"),
])
def test_get_engine_single_and_multi(monkeypatch, engine_name, prefix):
    if engine_name == "tesseract":
        mod = ModuleType("pytesseract")
        mod.image_to_string = lambda img: f"{prefix}_{img}"
        monkeypatch.setitem(sys.modules, "pytesseract", mod)
    elif engine_name == "easyocr":
        mod = ModuleType("easyocr")

        class Reader:
            def __init__(self, *args, **kwargs):
                pass

            def readtext(self, img):
                return [(None, f"{prefix}_{img}", None)]

        mod.Reader = Reader
        monkeypatch.setitem(sys.modules, "easyocr", mod)
    else:  # doctr
        mod_doctr = ModuleType("doctr")
        mod_models = ModuleType("doctr.models")
        mod_io = ModuleType("doctr.io")

        class DocumentFile:
            @staticmethod
            def from_images(imgs):
                return imgs

        class Page:
            def __init__(self, img):
                self._img = img

            def render(self):
                return f"{prefix}_{self._img}"

        class Result:
            def __init__(self, imgs):
                self.pages = [Page(im) for im in imgs]

        def ocr_predictor(pretrained=True):
            def _predict(imgs):
                return Result(imgs)

            return _predict

        mod_models.ocr_predictor = ocr_predictor
        mod_io.DocumentFile = DocumentFile
        monkeypatch.setitem(sys.modules, "doctr", mod_doctr)
        monkeypatch.setitem(sys.modules, "doctr.models", mod_models)
        monkeypatch.setitem(sys.modules, "doctr.io", mod_io)
        # tesseract fallback also imports pytesseract
        mod_tess = ModuleType("pytesseract")
        mod_tess.image_to_string = lambda img: f"{prefix}_{img}"
        monkeypatch.setitem(sys.modules, "pytesseract", mod_tess)

    engine = get_engine(engine_name)

    single_text, single_pages = engine("a")
    assert single_text == f"{prefix}_a"
    if engine_name == "doctr":
        assert hasattr(single_pages, "render")
    else:
        assert single_pages is None

    multi_text, multi_pages = engine(["a", "b"])
    assert multi_text == [f"{prefix}_a", f"{prefix}_b"]
    if engine_name == "doctr":
        assert [p.render() for p in multi_pages] == multi_text
    else:
        assert multi_pages is None


@pytest.mark.parametrize("engine_name,prefix", [
    ("tesseract", "tess"),
    ("easyocr", "easy"),
    ("doctr", "doctr"),
])
def test_get_engine_with_image_objects(monkeypatch, engine_name, prefix):
    if engine_name == "tesseract":
        mod = ModuleType("pytesseract")
        mod.image_to_string = lambda img: f"{prefix}"
        monkeypatch.setitem(sys.modules, "pytesseract", mod)
    elif engine_name == "easyocr":
        mod = ModuleType("easyocr")

        class Reader:
            def __init__(self, *args, **kwargs):
                pass

            def readtext(self, img):
                return [(None, f"{prefix}", None)]

        mod.Reader = Reader
        monkeypatch.setitem(sys.modules, "easyocr", mod)
    else:
        mod_doctr = ModuleType("doctr")
        mod_models = ModuleType("doctr.models")
        mod_io = ModuleType("doctr.io")

        class DocumentFile:
            @staticmethod
            def from_images(imgs):
                for im in imgs:
                    if not isinstance(im, np.ndarray):
                        raise TypeError("unsupported object type for argument 'file'")
                return imgs

        class Page:
            def __init__(self, img):
                self._img = img

            def render(self):
                return f"{prefix}"

        class Result:
            def __init__(self, imgs):
                self.pages = [Page(im) for im in imgs]

        def ocr_predictor(pretrained=True):
            def _predict(imgs):
                return Result(imgs)

            return _predict

        mod_models.ocr_predictor = ocr_predictor
        mod_io.DocumentFile = DocumentFile
        monkeypatch.setitem(sys.modules, "doctr", mod_doctr)
        monkeypatch.setitem(sys.modules, "doctr.models", mod_models)
        monkeypatch.setitem(sys.modules, "doctr.io", mod_io)
        mod_tess = ModuleType("pytesseract")
        mod_tess.image_to_string = lambda img: f"{prefix}"
        monkeypatch.setitem(sys.modules, "pytesseract", mod_tess)

    engine = get_engine(engine_name)
    img_a = Image.new("RGB", (1, 1))
    img_b = Image.new("RGB", (1, 1))

    single_text, single_pages = engine(img_a)
    assert single_text == f"{prefix}"
    if engine_name == "doctr":
        assert hasattr(single_pages, "render")
    else:
        assert single_pages is None

    multi_text, multi_pages = engine([img_a, img_b])
    assert multi_text == [f"{prefix}", f"{prefix}"]
    if engine_name == "doctr":
        assert [p.render() for p in multi_pages] == [f"{prefix}", f"{prefix}"]
    else:
        assert multi_pages is None

    img_a.close()
    img_b.close()
