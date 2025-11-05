"""OCR helper utilities for the Doctr OCR pipeline."""

import logging
import os
import re
from collections.abc import Generator
from io import BytesIO

import cv2
import numpy as np
import pytesseract
from PIL import Image

__all__ = [
    "ocr_with_fallback",
    "extract_images_generator",
    "correct_image_orientation",
    "get_file_hash",
    "get_image_hash",
    "save_roi_image",
    "roi_has_digits",
]


def ocr_with_fallback(pil_img: Image.Image, model):
    """Run Doctr OCR and fall back to grayscale if no text is detected."""
    img_np = np.array(pil_img)
    docs = model([img_np])
    if any(block.lines for block in docs.pages[0].blocks):
        return docs

    gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    gray3 = cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)
    logging.info("Fallback OCR: using grayscale+Otsu")
    return model([gray3])


def extract_images_generator(
    filepath: str, poppler_path: str | None = None, dpi: int = 300
) -> Generator[np.ndarray, None, None]:
    """Yield RGB ``numpy.ndarray`` pages for ``filepath``.

    Parameters
    ----------
    filepath:
        Path to the input file.
    poppler_path:
        Optional path to the poppler binaries used by ``pdf2image``.
    dpi:
        Rendering resolution for PDF files. Ignored for image inputs.
    """

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        from pdf2image import convert_from_path, pdfinfo_from_path

        info = pdfinfo_from_path(filepath, userpw=None, poppler_path=poppler_path)
        for page_num in range(1, info.get("Pages", 0) + 1):
            page = convert_from_path(
                filepath,
                dpi=dpi,
                poppler_path=poppler_path,
                first_page=page_num,
                last_page=page_num,
            )[0]
            arr = np.array(page.convert("RGB"))
            page.close()
            yield arr
    elif ext in {".tif", ".tiff"}:
        # PIL's ImageSequence.Iterator returns frame objects that
        # reference the same underlying image.  By seeking to each
        # frame and copying we ensure each page is an independent
        # Image instance, preventing "Image object not iterable" errors
        # when downstream code attempts to process multi‑page TIFFs.
        with Image.open(filepath) as img:
            for i in range(getattr(img, "n_frames", 1)):
                img.seek(i)
                frame = img.copy().convert("RGB")
                arr = np.array(frame)
                frame.close()
                yield arr
    elif ext in {".jpg", ".jpeg", ".png"}:
        with Image.open(filepath) as img:
            yield np.array(img.convert("RGB"))
    else:
        raise ValueError("Unsupported file type")


def correct_image_orientation(
    pil_img: Image.Image, page_num: int | None = None, method: str = "tesseract"
) -> Image.Image:
    """Rotate ``pil_img`` based on OCR orientation detection."""
    if method == "none":
        correct_image_orientation.last_angle = 0
        return pil_img

    # skip orientation detection for blank or tiny images
    try:
        if pil_img.getbbox() is None or min(pil_img.size) < 10:
            correct_image_orientation.last_angle = 0
            return pil_img
    except (AttributeError, ValueError) as exc:
        logging.warning(
            "Image bbox or size error: %s",
            str(exc).replace("\n", " ").replace("\r", " "),
        )

    try:
        if method == "doctr":
            try:
                # Newer versions of doctr may not expose angle_predictor; try import
                if correct_image_orientation.angle_model is None:
                    from doctr.models import angle_predictor

                    correct_image_orientation.angle_model = angle_predictor(
                        pretrained=True
                    )
                angle = correct_image_orientation.angle_model([pil_img])[0]
                rotation = int(round(angle / 90.0)) * 90 % 360
            except Exception as e:
                # Fallback: doctr's angle_predictor not available in this environment.
                # Use Tesseract OSD as a reliable fallback and log the reason.
                logging.info(
                    "doctr.angle_predictor unavailable, falling back to Tesseract OSD: %s",
                    str(e).replace("\n", " ").replace("\r", " "),
                )
                osd = pytesseract.image_to_osd(pil_img)
                match = re.search(r"Rotate: (\d+)", osd)
                rotation = int(match.group(1)) if match else 0
        else:  # tesseract
            osd = pytesseract.image_to_osd(pil_img)
            match = re.search(r"Rotate: (\d+)", osd)
            rotation = int(match.group(1)) if match else 0

        correct_image_orientation.last_angle = rotation
        if rotation == 180:
            logging.info("Page %d: 180-degree rotation detected", page_num or 0)
        elif rotation != 0:
            logging.info("Page %d: rotation = %d degrees", page_num or 0, rotation)
        else:
            logging.debug("Page %d: no rotation needed", page_num or 0)
        if rotation in {90, 180, 270}:
            return pil_img.rotate(-rotation, expand=True)
    except Exception as exc:
        logging.warning(
            "Orientation error (page %d): %s",
            page_num or 0,
            str(exc).replace("\n", " ").replace("\r", " "),
        )
        correct_image_orientation.last_angle = 0

    return pil_img


correct_image_orientation.angle_model = None
correct_image_orientation.last_angle = 0


def get_file_hash(filepath: str) -> str:
    """Return a SHA256 hash for ``filepath``."""
    import hashlib

    return hashlib.sha256(filepath.encode("utf-8")).hexdigest()


def get_image_hash(pil_img: Image.Image) -> str:
    """Return a SHA256 hash of the image contents."""
    import hashlib

    with BytesIO() as buf:
        pil_img.save(buf, format="PNG")
        return hashlib.sha256(buf.getvalue()).hexdigest()


def save_roi_image(pil_img: Image.Image, roi, out_path: str, page_num: int) -> None:
    """Draw ``roi`` rectangle on a copy of ``pil_img`` and save it."""
    arr = np.array(pil_img)
    if roi and len(roi) == 4:
        try:
            if max(roi) <= 1:
                width, height = pil_img.size
                pt1 = (int(roi[0] * width), int(roi[1] * height))
                pt2 = (int(roi[2] * width), int(roi[3] * height))
            else:
                pt1 = (int(roi[0]), int(roi[1]))
                pt2 = (int(roi[2]), int(roi[3]))
            cv2.rectangle(arr, pt1, pt2, (255, 0, 0), 2)
        except Exception as exc:
            safe_roi = str(roi).replace("\n", "\\n").replace("\r", "\\r")
            safe_exc = str(exc).replace("\n", "\\n").replace("\r", "\\r")
            logging.warning(
                "ROI rectangle error on page %d: %s (roi=%s)",
                page_num,
                safe_exc,
                safe_roi,
            )
    else:
        safe_roi = str(roi).replace("\n", "\\n").replace("\r", "\\r")
        logging.warning(
            "ROI not defined or wrong length on page %d: %s", page_num, safe_roi
        )

    cv2.imwrite(out_path, arr[..., ::-1])


def roi_has_digits(pil_img: Image.Image, roi) -> bool:
    """Return ``True`` if OCR of ``roi`` contains digits."""
    try:
        width, height = pil_img.size
        if max(roi) <= 1:
            box = (
                int(roi[0] * width),
                int(roi[1] * height),
                int(roi[2] * width),
                int(roi[3] * height),
            )
        else:
            box = (int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))
        crop = pil_img.crop(box)
        txt = pytesseract.image_to_string(crop, config="--psm 6 digits").strip()
        return bool(re.search(r"\d", txt))
    except Exception:
        return False
    finally:
        try:
            crop.close()
        except Exception:
            pass


def save_crop_and_thumbnail(
    pil_img: Image.Image,
    roi,
    crops_dir: str,
    base_name: str,
    thumbs_dir: str,
    thumb_log: list | None = None,
) -> tuple[str, str]:
    """Save ROI crop and thumbnail images."""
    # Validate and sanitize paths
    crops_dir = os.path.abspath(crops_dir)
    thumbs_dir = os.path.abspath(thumbs_dir)
    base_name = os.path.basename(base_name)  # Prevent path traversal

    width, height = pil_img.size

    # Validate ROI before processing
    try:
        if not roi or len(roi) != 4:
            raise ValueError("ROI must be a list/tuple of 4 values")
        if max(roi) <= 1:
            box = (
                int(roi[0] * width),
                int(roi[1] * height),
                int(roi[2] * width),
                int(roi[3] * height),
            )
        else:
            box = (int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))
    except (ValueError, TypeError) as e:
        logging.warning("Invalid ROI: %s", str(e).replace("\n", " ").replace("\r", " "))
        raise

    crop = None
    thumb = None
    try:
        crop = pil_img.crop(box)
        try:
            os.makedirs(crops_dir, exist_ok=True)
            os.makedirs(thumbs_dir, exist_ok=True)
        except OSError as e:
            logging.warning(
                "Failed to create directories: %s",
                str(e).replace("\n", " ").replace("\r", " "),
            )
            raise

        crop_path = os.path.join(crops_dir, f"{base_name}.png")
        # Validate crop path to prevent traversal
        if not os.path.abspath(crop_path).startswith(crops_dir + os.sep):
            raise ValueError(f"Invalid crop path: {crop_path}")
        try:
            crop.save(crop_path)
        except OSError as e:
            logging.warning(
                "Failed to save crop image: %s",
                str(e).replace("\n", " ").replace("\r", " "),
            )
            raise

        thumb = crop.copy()
        thumb.thumbnail((128, 128))
        thumb_path = os.path.join(thumbs_dir, f"{base_name}.png")
        # Validate thumb path to prevent traversal
        if not os.path.abspath(thumb_path).startswith(thumbs_dir + os.sep):
            raise ValueError(f"Invalid thumbnail path: {thumb_path}")
        try:
            thumb.save(thumb_path)
        except OSError as e:
            logging.warning(
                "Failed to save thumbnail image: %s",
                str(e).replace("\n", " ").replace("\r", " "),
            )
            raise

        if thumb_log is not None:
            thumb_log.append({"field": base_name, "thumbnail": thumb_path})
        return crop_path, thumb_path
    finally:
        if crop:
            crop.close()
        if thumb:
            thumb.close()
