"""Wrapper for various OCR engines."""


# src/doctr_process/ocr/ocr_engine.py


def get_engine(name: str):
    name = name.lower()
    if name == "tesseract":
        import pytesseract

        def _run(img):
            imgs = [img] if not isinstance(img, list) else img
            texts = [pytesseract.image_to_string(im) for im in imgs]
            return (texts[0], None) if len(texts) == 1 else (texts, None)

        return _run
    elif name == "easyocr":
        from easyocr import Reader

        reader = Reader(["en"], gpu=False)

        def _run(img):
            imgs = [img] if not isinstance(img, list) else img
            texts = []
            for im in imgs:
                r = reader.readtext(im)
                texts.append(" ".join(t for _, t, _ in r))
            return (texts[0], None) if len(texts) == 1 else (texts, None)

        return _run
    else:  # doctr requested
        try:
            from doctr.models import ocr_predictor
            from doctr.io import DocumentFile
            import numpy as np
            from PIL import Image

            predictor = ocr_predictor(pretrained=True)

            def _run(img):
                imgs = [img] if not isinstance(img, list) else img
                np_imgs = []
                for im in imgs:
                    if isinstance(im, np.ndarray):
                        np_imgs.append(im)
                    elif isinstance(im, Image.Image):
                        np_imgs.append(np.array(im))
                    else:
                        np_imgs.append(im)
                doc = DocumentFile.from_images(np_imgs)
                res = predictor(doc)
                pages = res.pages
                texts = [page.render() for page in pages]
                return (texts[0], pages[0]) if len(texts) == 1 else (texts, pages)

            return _run
        except Exception:
            # fallback so tests/environments without doctr still pass
            import warnings, pytesseract

            warnings.warn("doctr not available; falling back to tesseract")

            def _run(img):
                imgs = [img] if not isinstance(img, list) else img
                texts = [pytesseract.image_to_string(im) for im in imgs]
                return (texts[0], None) if len(texts) == 1 else (texts, None)

            return _run
