"""OCR helper utilities for the Doctr OCR pipeline."""

import io
import logging
import os
import re
from typing import Generator

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
) -> Generator[Image.Image, None, None]:
    """Yield RGB ``PIL.Image`` objects for each page of ``filepath``.

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
        from pdf2image import convert_from_path

        for page in convert_from_path(
            filepath, dpi=dpi, poppler_path=poppler_path
        ):
            yield page.convert("RGB")
    elif ext in {".tif", ".tiff"}:
        # PIL's ImageSequence.Iterator returns frame objects that
        # reference the same underlying image.  By seeking to each
        # frame and copying we ensure each page is an independent
        # Image instance, preventing "Image object not iterable" errors
        # when downstream code attempts to process multi‑page TIFFs.
        with Image.open(filepath) as img:
            for i in range(getattr(img, "n_frames", 1)):
                img.seek(i)
                # ``copy`` detaches the frame from the source file so it
                # can be used after the context manager closes.
                yield img.copy().convert("RGB")
    elif ext in {".jpg", ".jpeg", ".png"}:
        with Image.open(filepath) as img:
            yield img.convert("RGB")
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
    except Exception:
        pass

    try:
        if method == "doctr":
            if correct_image_orientation.angle_model is None:
                from doctr.models import angle_predictor

                correct_image_orientation.angle_model = angle_predictor(pretrained=True)
            angle = correct_image_orientation.angle_model([pil_img])[0]
            rotation = int(round(angle / 90.0)) * 90 % 360
        else:  # tesseract
            osd = pytesseract.image_to_osd(pil_img)
            match = re.search(r"Rotate: (\d+)", osd)
            rotation = int(match.group(1)) if match else 0

        correct_image_orientation.last_angle = rotation
        if rotation == 180:
            logging.info(f"Page {page_num}: 180-degree rotation detected")
        else:
            logging.info(f"Page {page_num}: rotation = {rotation} degrees")
        if rotation in {90, 180, 270}:
            return pil_img.rotate(-rotation, expand=True)
    except Exception as exc:
        logging.warning(f"Orientation error (page {page_num}): {exc}")
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

    buf = io.BytesIO()
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
            logging.warning(f"ROI rectangle error on page {page_num}: {exc} (roi={roi})")
    else:
        logging.warning(f"ROI not defined or wrong length on page {page_num}: {roi}")

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


def save_crop_and_thumbnail(
        pil_img: Image.Image,
        roi,
        crops_dir: str,
        base_name: str,
        thumbs_dir: str,
        thumb_log: list | None = None,
) -> tuple[str, str]:
    """Save ROI crop and thumbnail images."""
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
    os.makedirs(crops_dir, exist_ok=True)
    os.makedirs(thumbs_dir, exist_ok=True)
    crop_path = os.path.join(crops_dir, f"{base_name}.png")
    crop.save(crop_path)
    thumb = crop.copy()
    thumb.thumbnail((128, 128))
    thumb_path = os.path.join(thumbs_dir, f"{base_name}.png")
    thumb.save(thumb_path)
    if thumb_log is not None:
        thumb_log.append({"field": base_name, "thumbnail": thumb_path})
    return crop_path, thumb_path
