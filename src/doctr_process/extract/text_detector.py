"""Text detection in documents to avoid unnecessary OCR."""

import logging
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


class TextDetector:
    """Detects existing text in documents to avoid unnecessary OCR."""

    def __init__(self, min_text_length: int = 50):
        self.min_text_length = min_text_length

    def has_extractable_text(self, file_path: Path) -> tuple[bool, str | None]:
        """Check if document has extractable text.

        Returns:
            Tuple of (has_text, extracted_text)
        """
        return self.check_pages_for_text(file_path)[0:2]

    def check_pages_for_text(
        self, file_path: Path
    ) -> tuple[bool, str | None, list[bool]]:
        """Check each page for extractable text.

        Returns:
            Tuple of (has_text_overall, full_text, per_page_has_text)
        """
        if file_path.suffix.lower() != ".pdf":
            return False, None, []

        # Try PyMuPDF first
        if fitz:
            try:
                doc = fitz.open(str(file_path))
                full_text = ""
                page_has_text = []

                for page in doc:
                    text = page.get_text()
                    has_text = len(text.strip()) > 20
                    page_has_text.append(has_text)
                    if text:
                        full_text += text + "\n"
                doc.close()

                overall_has_text = len(full_text.strip()) >= self.min_text_length
                if overall_has_text:
                    logging.info(
                        f"Found text in {sum(page_has_text)}/{len(page_has_text)} pages of {file_path.name}"
                    )
                    return True, full_text, page_has_text
                return False, None, page_has_text
            except Exception as e:
                logging.warning(
                    f"PyMuPDF text extraction failed for {file_path.name}: {e}"
                )

        # Fallback to pdfplumber
        if pdfplumber:
            try:
                with pdfplumber.open(file_path) as pdf:
                    full_text = ""
                    page_has_text = []

                    for page in pdf.pages:
                        text = page.extract_text()
                        has_text = len(text.strip()) > 20 if text else False
                        page_has_text.append(has_text)
                        if text:
                            full_text += text + "\n"

                overall_has_text = len(full_text.strip()) >= self.min_text_length
                if overall_has_text:
                    logging.info(
                        f"Found text in {sum(page_has_text)}/{len(page_has_text)} pages of {file_path.name}"
                    )
                    return True, full_text, page_has_text
                return False, None, page_has_text
            except Exception as e:
                logging.warning(
                    f"pdfplumber text extraction failed for {file_path.name}: {e}"
                )

        return False, None, []
