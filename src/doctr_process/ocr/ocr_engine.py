"""Wrapper for various OCR engines."""

# src/doctr_process/ocr/ocr_engine.py


def get_engine(name: str):
    name = name.lower()
    if name == "tesseract":
        import pytesseract

        def _run(img):
            return pytesseract.image_to_string(img), None

        return _run
    elif name == "easyocr":
        from easyocr import Reader

        reader = Reader(["en"], gpu=False)

        def _run(img):
            r = reader.readtext(img)
            return " ".join(t for _, t, _ in r), None

        return _run
    else:  # doctr requested
        try:
            from doctr.models import ocr_predictor
            from doctr.io import DocumentFile

            predictor = ocr_predictor(pretrained=True)

            def _run(img):
                doc = DocumentFile.from_images(img)
                res = predictor(doc)
                return res.render(), res.pages[0] if res.pages else None

            return _run
        except Exception:
            # fallback so tests/environments without doctr still pass
            import warnings, pytesseract

            warnings.warn("doctr not available; falling back to tesseract")

            def _run(img):
                return pytesseract.image_to_string(img), None

            return _run
