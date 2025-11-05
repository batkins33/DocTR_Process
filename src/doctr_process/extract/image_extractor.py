"""Image extraction from various document formats."""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path

from PIL import Image


class ImageExtractor:
    """Extracts images from PDFs and other document formats."""

    def __init__(self, dpi: int = 300, poppler_path: str = None):
        self.dpi = dpi
        self.poppler_path = poppler_path

    def extract_from_file(self, file_path: Path) -> Generator[Image.Image, None, None]:
        """Extract images from file path."""
        ext = file_path.suffix.lower()

        if ext == ".pdf":
            yield from self._extract_from_pdf(file_path)
        elif ext in {".tif", ".tiff"}:
            yield from self._extract_from_tiff(file_path)
        elif ext in {".jpg", ".jpeg", ".png"}:
            yield from self._extract_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def extract_from_bytes(
        self, data: bytes, filename: str
    ) -> Generator[Image.Image, None, None]:
        """Extract images from byte data."""
        ext = Path(filename).suffix.lower()

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(data)
            tmp.flush()

            try:
                yield from self.extract_from_file(Path(tmp.name))
            finally:
                os.unlink(tmp.name)

    def _extract_from_pdf(self, pdf_path: Path) -> Generator[Image.Image, None, None]:
        """Extract pages from PDF as images."""
        from pdf2image import convert_from_path, pdfinfo_from_path

        info = pdfinfo_from_path(pdf_path, poppler_path=self.poppler_path)
        total_pages = info.get("Pages", 0)

        for page_num in range(1, total_pages + 1):
            pages = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                poppler_path=self.poppler_path,
                first_page=page_num,
                last_page=page_num,
            )
            if pages:
                yield pages[0].convert("RGB")

    def _extract_from_tiff(self, tiff_path: Path) -> Generator[Image.Image, None, None]:
        """Extract frames from multi-page TIFF."""
        with Image.open(tiff_path) as img:
            for i in range(getattr(img, "n_frames", 1)):
                img.seek(i)
                yield img.copy().convert("RGB")

    def _extract_from_image(
        self, image_path: Path
    ) -> Generator[Image.Image, None, None]:
        """Load single image file."""
        with Image.open(image_path) as img:
            yield img.convert("RGB")
