# src/doctr_process/utils/orientation.py
"""
Utility for detecting and correcting page orientation before OCR.

Contains functions to:
- Score the quality of extracted text to detect "gibberish".
- Use Tesseract OSD (Orientation and Script Detection) to guess rotation.
- Perform a "best-of-four" rotation trial for ambiguous cases.
- Process a PDF to fix orientation and save a corrected version.
"""
import io
import logging
import re
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image

log = logging.getLogger(__name__)

# A small, domain-specific dictionary for scoring
DICT = {"ticket", "tons", "gross", "tare", "net", "carrier", "vehicle", "order", "customer", "po"}


def text_quality_score(text: str) -> float:
    """
    Calculates a composite score (0.0 to 1.0) indicating text quality.

    The score is based on:
    - Ratio of letters to all alphanumeric characters.
    - Average length of tokens (words).
    - Hit rate against a small, domain-specific dictionary.

    A low score suggests non-sensical or "gibberish" text, often from
    incorrectly oriented OCR.
    """
    if not text:
        return 0.0
    tokens = re.findall(r"[A-Za-z0-9]+", text)
    if not tokens:
        return 0.0

    letters = sum(c.isalpha() for c in text)
    alnum = sum(c.isalnum() for c in text)
    letter_ratio = letters / max(alnum, 1)
    avg_len = sum(len(t) for t in tokens) / len(tokens)
    dict_hits = sum(1 for t in tokens if t.lower() in DICT)
    keyword_hit_rate = dict_hits / len(tokens)

    # Composite score weights: letter ratio is most important, then avg length, then keywords.
    score = (
        0.45 * min(1.0, letter_ratio) +
        0.25 * (1.0 - abs(5.0 - avg_len) / 5.0) +  # Prefers avg_len near 5
        0.30 * min(1.0, 5.0 * keyword_hit_rate)   # Cap influence of keywords
    )
    return max(0.0, min(1.0, score))


def page_to_png(page: fitz.Page, dpi: int = 200) -> Image.Image:
    """Converts a PyMuPDF page to a PIL Image."""
    pix = page.get_pixmap(dpi=dpi, alpha=False)
    return Image.open(io.BytesIO(pix.tobytes("png")))


def osd_guess_rotation(pil_img: Image.Image) -> int:
    """
    Uses Tesseract's Orientation and Script Detection (OSD) to find the
    required rotation angle (0, 90, 180, 270).
    """
    try:
        osd = pytesseract.image_to_osd(pil_img, config="--psm 0")
        m = re.search(r"Rotate:\s+(\d+)", osd)
        if m:
            return int(m.group(1)) % 360
    except Exception as e:
        log.warning(f"Tesseract OSD failed: {e}")
    return 0


def quick_ocr_proxy(pil_img: Image.Image) -> str:
    """
    Performs a quick, low-cost OCR pass using Tesseract.
    Used for scoring text quality during rotation trials.
    """
    try:
        return pytesseract.image_to_string(pil_img, config="--psm 6")
    except Exception:
        return ""


def best_of_four_rotation(pil_img: Image.Image) -> tuple[int, dict[int, float]]:
    """
    Finds the best rotation by scoring quick OCR at 0, 90, 180, 270 degrees.
    Returns the best angle and a dictionary of all candidate scores.
    """
    candidates = {}
    for angle in (0, 90, 180, 270):
        rotated_img = pil_img.rotate(angle, expand=True)
        text = quick_ocr_proxy(rotated_img)
        candidates[angle] = text_quality_score(text)
    
    best_angle = max(candidates, key=candidates.get)
    return best_angle, candidates


def ensure_correct_orientation(
    pdf_path: str,
    output_dir: str,
    score_threshold: float = 0.42,
    rotation_margin: float = 0.15
) -> tuple[str, dict]:
    """
    Processes a PDF to detect and correct page orientation.

    For each page, it checks for existing text. If the text is low quality,
    or if no text exists, it rasterizes the page and determines the best
    orientation. It then saves a new PDF with all pages correctly oriented.

    Args:
        pdf_path: Path to the input PDF.
        output_dir: Directory to save the oriented PDF.
        score_threshold: Text quality score below which OCR is considered gibberish.
        rotation_margin: Required score improvement to justify rotation in ambiguous cases.

    Returns:
        A tuple containing:
        - The path to the new, correctly oriented PDF.
        - A dictionary logging the rotations applied to each page number.
    """
    pdf_path = Path(pdf_path)
    output_path = Path(output_dir) / f"{pdf_path.stem}_oriented.pdf"
    
    doc = fitz.open(pdf_path)
    rotated_pages = {}
    needs_saving = False

    for i, page in enumerate(doc, start=1):
        # 1. If PDF already has text, evaluate it for gibberish.
        try:
            with pdfplumber.open(pdf_path) as p_pdf:
                p_page = p_pdf.pages[i-1]
                text = p_page.extract_text()
                if text and text_quality_score(text) >= score_threshold:
                    log.debug(f"Page {i}: Text quality is good, skipping orientation check.")
                    continue
        except Exception as e:
            log.warning(f"Could not check text layer on page {i} with pdfplumber: {e}")

        # 2. Rasterize page and try fast OSD first.
        log.debug(f"Page {i}: Checking orientation...")
        img = page_to_png(page, dpi=200)
        angle = osd_guess_rotation(img)

        # 3. If OSD is uncertain (angle=0), use the more reliable best-of-four trial.
        if angle == 0:
            best_angle, candidates = best_of_four_rotation(img)
            # Only accept the new angle if it's significantly better.
            if candidates.get(best_angle, 0) > candidates.get(0, 0) + rotation_margin:
                angle = best_angle
            log.debug(f"Page {i}: Best-of-four scores: {candidates}. Selected angle: {angle}")

        # 4. If rotation is needed, apply it.
        if angle in {90, 180, 270}:
            log.info(f"Page {i}: Applying {angle}-degree rotation.")
            page.set_rotation((page.rotation + angle) % 360)
            rotated_pages[i] = angle
            needs_saving = True

    if needs_saving:
        log.info(f"Saving orientation-corrected PDF to {output_path}")
        doc.save(str(output_path))
        final_path = str(output_path)
    else:
        log.info("No orientation changes needed. Using original file.")
        final_path = str(pdf_path)
        
    doc.close()
    return final_path, rotated_pages
