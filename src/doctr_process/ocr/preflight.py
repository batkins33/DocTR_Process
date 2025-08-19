import logging
from os.path import basename, join, abspath, exists
from os import makedirs
import re

import cv2

try:
    import fitz  # PyMuPDF
except ImportError:
    try:
        import pymupdf as fitz  # newer PyMuPDF versions
    except ImportError:
        fitz = None
import numpy as np
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path, pdfinfo_from_path
from pdf2image.exceptions import PDFInfoNotInstalledError
from tqdm import tqdm

from doctr_process.ocr.ocr_utils import correct_image_orientation
from doctr_process.path_utils import guard_call


def count_total_pages(pdf_files, cfg):
    """
    Return the total number of pages across all pdf_files.
    """
    total = 0
    for p in pdf_files:
        info = pdfinfo_from_path(p, poppler_path=cfg.get("poppler_path"))
        total += info["Pages"]
    return total


def is_page_ocrable(pdf_path, page_no, cfg):
    """
    Render page_no (1-based) at cfg["preflight"]["dpi_threshold"],
    convert to grayscale, Otsu-binarize a center crop, and see if
    we get at least cfg["preflight"]["min_chars"] from Tesseract.
    """
    pf_cfg = cfg.get("preflight", {})
    dpi = pf_cfg.get("dpi_threshold", 150)
    min_chars = pf_cfg.get("min_chars", 5)
    blank_std = pf_cfg.get("blank_std_threshold", 3.0)
    # allow tests to run without requiring high resolution pages
    min_res = pf_cfg.get("min_resolution", 0)
    pdf_path = str(pdf_path)
    poppler = cfg.get("poppler_path")

    # 1) Rasterize just that page
    try:
        imgs = convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=page_no,
            last_page=page_no,
            poppler_path=poppler,
        )
        # Ensure imgs is always a list
        if isinstance(imgs, Image.Image):
            imgs = [imgs]
        img = imgs[0] if imgs else None
    except (PDFInfoNotInstalledError, OSError):
        if fitz is None:
            logging.error("PyMuPDF not available and pdf2image failed")
            return False
        doc = guard_call("fitz_open_preflight", fitz.open, pdf_path)
        page = doc.load_page(page_no - 1)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    if img is None:
        return False

    # Resolution check
    # Correct orientation before analyzing the page
    orient_method = cfg.get("orientation_check", "tesseract")
    img = correct_image_orientation(img, page_no, method=orient_method)

    w, h = img.size
    if w < min_res or h < min_res:
        logging.info(
            "Preflight: page %d below min_resolution %d (%dx%d)", page_no, min_res, w, h
        )
        img.close()
        return False

    gray_full_img = img.convert("L")
    gray_full = np.array(gray_full_img)
    gray_full_img.close()
    if gray_full.std() < blank_std:
        sanitized_page = re.sub(r'[\r\n\x00-\x1f]', '', str(page_no))
        sanitized_std = re.sub(r'[\r\n\x00-\x1f]', '', f"{gray_full.std():.2f}")
        logging.info(
            "Preflight: page %s appears blank (std=%s)", sanitized_page, sanitized_std
        )
        img.close()
        return False

    gray_crop = img.convert("L").crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
    arr = np.array(gray_crop)
    gray_crop.close()

    _, th = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    test_img = Image.fromarray(th)

    try:
        txt = pytesseract.image_to_string(test_img, config="--psm 6").strip()
        result = len(txt) >= min_chars
    except pytesseract.TesseractNotFoundError:
        logging.warning("Tesseract not found; skipping OCR check")
        result = True
    finally:
        test_img.close()
        img.close()

    return result


def preflight_pages(pdf_path, cfg):
    """
    Return a list of (page_no, reason) for pages that fail OCRability.
    """
    bad = []
    total = count_total_pages([pdf_path], cfg)
    for p in tqdm(range(1, total + 1), desc="Preflight", unit="page"):
        if not is_page_ocrable(pdf_path, p, cfg):
            bad.append((p, "preflight-OCR failed"))
    return bad


def extract_page(pdf_path, page_no, out_path):
    """
    Write just that one page into a new single-page PDF at out_path.
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.add_page(reader.pages[page_no - 1])

    makedirs(dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        writer.write(f)


def run_preflight(pdf_path, cfg):
    """
    If cfg["preflight"]["enabled"], run the OCRability check on each page,
    dump any bad pages out as single-page PDFs under cfg["exceptions_dir"],
    and return (skip_pages_set, exception_dicts_list).
    """
    pdf_path = str(pdf_path)
    skip_pages = set()
    exceptions = []

    pf = cfg.get("preflight", {})
    if not pf.get("enabled", False):
        return skip_pages, exceptions

    bad = preflight_pages(pdf_path, cfg)
    exc_dir = cfg.get("preflight_exceptions_dir", "./output/exceptions/preflight")

    for page, reason in bad:
        stem = basename(pdf_path).rsplit('.', 1)[0]
        out_pdf = join(exc_dir, f"{stem}_page{page:03d}_preflight.pdf")
        extract_page(pdf_path, page, out_pdf)

        logging.warning("Preflight: page %d => %s, saved to %s", page, reason, out_pdf)

        # Optional: also save a PNG image of the failed page
        try:
            dpi = pf.get("dpi_threshold", 150)
            poppler = cfg.get("poppler_path")
            imgs = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=page,
                last_page=page,
                poppler_path=poppler,
            )
            if imgs:
                img = imgs[0]
                err_img_dir = cfg.get(
                    "preflight_error_images", "./output/exceptions/preflight_images"
                )
                makedirs(err_img_dir, exist_ok=True)
                out_img_path = join(err_img_dir, f"{stem}_page{page:03d}.png")
                # Validate path to prevent traversal attacks
                if not abspath(out_img_path).startswith(abspath(err_img_dir)):
                    logging.error("Invalid output path detected: %s", out_img_path)
                    continue
                img.save(out_img_path)
                for im in imgs:
                    try:
                        im.close()
                    except Exception as close_exc:
                        logging.warning("Failed to close image: %s", str(close_exc).replace('\n', ' '))
        except Exception as e:
            logging.warning("Could not save preflight image for page %d: %s", page, str(e).replace('\n', ' '))

        skip_pages.add(page)
        exceptions.append(
            {
                "file": pdf_path,
                "page": page,
                "error": reason,
                "extract": out_pdf,
            }
        )

    return skip_pages, exceptions
