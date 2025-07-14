# PATCHED: processor/image_ops.py
import logging
import re
from pathlib import Path

import pytesseract
from PIL import Image


def extract_images_from_file(filepath, poppler_path):
    from pdf2image import convert_from_path

    ext = Path(filepath).suffix.lower()
    logging.info(f"📄 Extracting images from: {filepath} (ext: {ext})")

    try:
        if ext in [".tif", ".tiff"]:
            img = Image.open(filepath)
            pages = []
            while True:
                pages.append(img.copy())
                try:
                    img.seek(img.tell() + 1)
                except EOFError:
                    break
            return pages

        elif ext == ".pdf":
            return convert_from_path(filepath, dpi=300, poppler_path=poppler_path)

        elif ext in [".png", ".jpg", ".jpeg"]:
            return [Image.open(filepath)]

        return []

    except Exception as e:
        logging.error(f"❌ Failed to extract images: {e}")
        return []


def correct_image_orientation(pil_img):
    try:
        osd = pytesseract.image_to_osd(pil_img)
        rotation_match = re.search(r"Rotate: (\d+)", osd)
        if rotation_match:
            rotation = int(rotation_match.group(1))
            if rotation == 90:
                return pil_img.rotate(-90, expand=True)
            elif rotation == 180:
                return pil_img.rotate(180, expand=True)
            elif rotation == 270:
                return pil_img.rotate(-270, expand=True)
    except pytesseract.TesseractError as e:
        print(f"Tesseract error during orientation detection: {e}")
    except Exception as e:
        print(f"Unexpected error in orientation correction: {e}")

    return pil_img


def apply_grayscale(pil_img):
    return pil_img.convert("L")


def extract_ticket_number(pil_img):
    text = pytesseract.image_to_string(pil_img)
    text = text.replace("\n", " ").strip()
    match = re.search(r"(A[\s\-:]?\d{5,})", text, re.IGNORECASE)
    if match:
        ticket_number = match.group(1).replace(" ", "").replace("-", "")
        return ticket_number
    # """
    # page_image: full page (RGB or grayscale) as np.array
    # template_dict: {"VENDOR": [template_image1, template_image2, ...]}
    # Returns: best matched vendor and score
    # """


def run_template_matching(page_image, template_dict, threshold=0.85, preview=True):
    import cv2
    import os
    import shutil

    if page_image is None or not hasattr(page_image, "shape"):
        raise ValueError("Invalid page image passed to run_template_matching")

    if page_image.ndim == 3 and page_image.shape[2] == 3:
        page_gray = cv2.cvtColor(page_image, cv2.COLOR_RGB2GRAY)
    else:
        page_gray = page_image

    best_score = -1
    best_vendor = "Unknown"
    best_location = None
    best_template = None

    # Clear old match previews
    preview_dir = "match_previews"
    if os.path.exists(preview_dir):
        shutil.rmtree(preview_dir)
    os.makedirs(preview_dir, exist_ok=True)

    for vendor, templates in template_dict.items():
        for template in templates:
            if template.ndim == 3 and template.shape[2] == 3:
                temp_gray = cv2.cvtColor(template, cv2.COLOR_RGB2GRAY)
            else:
                temp_gray = template

            # Skip template if it's larger than the page
            if (
                    temp_gray.shape[0] > page_gray.shape[0]
                    or temp_gray.shape[1] > page_gray.shape[1]
            ):
                print(f"⚠️ Skipped oversized template for vendor '{vendor}'")
                continue

            result = cv2.matchTemplate(page_gray, temp_gray, cv2.TM_CCOEFF_NORMED)
            min_val, score, min_loc, max_loc = cv2.minMaxLoc(result)

            print(f"🔍 Vendor: {vendor} | Score: {score:.3f}")

            if score > best_score:
                best_score = score
                best_vendor = vendor
                best_location = max_loc
                best_template = temp_gray

    if best_score >= threshold:
        try:
            import matplotlib.pyplot as plt

            h, w = best_template.shape[:2]
            vis_img = page_gray.copy()
            vis_img = cv2.cvtColor(vis_img, cv2.COLOR_GRAY2BGR)
            cv2.rectangle(
                vis_img,
                best_location,
                (best_location[0] + w, best_location[1] + h),
                (0, 255, 0),
                2,
            )

            save_path = os.path.join(
                preview_dir, f"match_{best_vendor}_{round(best_score * 100)}.png"
            )
            if preview:
                cv2.imwrite(save_path, vis_img)
                print(f"💾 Match preview saved: {save_path}")

                plt.figure(figsize=(10, 6))
                plt.title(f"Matched: {best_vendor} ({best_score:.3f})")
                plt.imshow(cv2.cvtColor(vis_img, cv2.COLOR_BGR2RGB))
                plt.axis("off")
                plt.show()

        except Exception as e:
            print(f"⚠️ Could not display/save match visualization: {e}")
        return best_vendor, round(best_score, 3)
    else:
        return "Unknown", round(best_score, 3)
