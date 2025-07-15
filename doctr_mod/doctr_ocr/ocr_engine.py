"""Wrapper for various OCR engines."""

from typing import Callable, Tuple

from PIL import Image


def get_engine(name: str) -> Callable[[Image.Image], Tuple[str, object | None]]:
    """Return a callable OCR engine by name.

    The returned function yields a tuple ``(text, result)`` where ``result``
    is engine specific (``doctr`` page) or ``None``.
    """
    name = name.lower()
    if name == "tesseract":
        import pytesseract

        def _run(img: Image.Image) -> Tuple[str, object | None]:
            return pytesseract.image_to_string(img), None

        return _run
    elif name == "easyocr":
        from easyocr import Reader

        reader = Reader(["en"], gpu=False)

        def _run(img: Image.Image) -> Tuple[str, object | None]:
            result = reader.readtext(img)
            return " ".join(r[1] for r in result), None

        return _run
    else:  # doctr (default)
        from doctr.models import ocr_predictor

        if not hasattr(get_engine, "model"):
            get_engine.model = ocr_predictor(pretrained=True)

        def _run(img: Image.Image) -> Tuple[str, object | None]:
            docs = get_engine.model([img])
            text = " ".join(
                word.value
                for block in docs.pages[0].blocks
                for line in block.lines
                for word in line.words
            )
            return text, docs.pages[0]

        return _run
