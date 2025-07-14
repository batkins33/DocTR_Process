# PATCHED: processor/hybrid_ocr.py
# ✅ PaddleOCR only mode

import hashlib
import io
import logging
import re
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from processor.file_handler import export_grouped_output
from processor.filename_utils import parse_input_filename, format_output_filename_camel
from processor.image_ops import (
    correct_image_orientation,
    apply_grayscale,
    extract_ticket_number,
    run_template_matching,
)
from rapidfuzz.fuzz import partial_ratio
from utils.loader import load_ocr_configs_from_excel, load_templates
from utils.ocr_wrapper import read_text

OCR_THRESHOLD = 80
MAX_TEMPLATE_WIDTH = 1200
MAX_TEMPLATE_HEIGHT = 800


def hash_image(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return hashlib.md5(buf.getvalue()).hexdigest()


def is_oversized_template(img: np.ndarray) -> bool:
    h, w = img.shape[:2]
    return w > MAX_TEMPLATE_WIDTH or h > MAX_TEMPLATE_HEIGHT


def get_sequenced_log_dir(base_path, base_name):
    logs_root = Path(base_path) / "logs"
    logs_root.mkdir(exist_ok=True)
    seq = 0
    while True:
        log_dir = logs_root / f"{base_name}_{seq}" if seq > 0 else logs_root / base_name
        if not log_dir.exists():
            log_dir.mkdir(parents=True)
            return log_dir
        seq += 1


def get_sequenced_file_path(base_path, filename):
    base = Path(base_path) / filename
    stem = base.stem
    suffix = base.suffix
    counter = 1
    while base.exists():
        base = base.with_name(f"{stem}_{counter}{suffix}")
        counter += 1
    return base


def process_single_page(args):
    i, page, filepath, config, templates, ocr_config, expected_vendor, ocr_cache = args
    row_log = {"page": i + 1, "filename": str(filepath), "expected": expected_vendor}

    try:
        raw_result = read_text(image=page.convert("L"))
        raw_ocr_text = raw_result.get("text", "")
    except Exception as e:
        raw_ocr_text = f"[OCR Failed: {e}]"

    w, h = page.size
    use_roi = config.get("use_roi", True)
    if use_roi:
        crop_percent = config.get("ocr_crop_top_percent", 25) / 100
        roi = page.crop((0, 0, w, int(h * crop_percent)))
    else:
        roi = page

    if config.get("preprocess", {}).get("downscale", True):
        roi = roi.resize((roi.width // 2, roi.height // 2), Image.LANCZOS)

    roi_hash = hash_image(roi)
    if roi_hash in ocr_cache:
        comp, matched, kw, preview, ocr_score = ocr_cache[roi_hash]
        logging.info(f"🔁 OCR cache hit on page {i + 1}")
    else:
        comp, matched, kw, preview, ocr_score = ocr_match_company(
            roi, ocr_config, config, log_row=row_log
        )
        ocr_cache[roi_hash] = (comp, matched, kw, preview, ocr_score)

    method = "OCR (ROI)"
    was_rotated = was_grayscaled = False
    if config["preprocess"].get("rotate", True):
        page = correct_image_orientation(page)
        was_rotated = True
    if config["preprocess"].get("grayscale", True):
        page = apply_grayscale(page)
        was_grayscaled = True

    if not matched:
        full_comp, full_matched, full_kw, full_preview, full_score = ocr_match_company(
            page, ocr_config, config, log_row=row_log
        )
        if full_matched:
            comp = full_comp
            matched = True
            kw = full_kw
            preview = full_preview
            ocr_score = full_score
            method = "OCR (full page)"

    if not matched and config.get("use_template_fallback", False):
        try:
            roi_np = np.array(roi)
            if is_oversized_template(roi_np):
                logging.warning(
                    f"⚠️ Skipped oversized ROI template match on page {i + 1}"
                )
            else:
                result = run_template_matching(
                    roi_np,
                    templates,
                    config.get("template_threshold", 0.85),
                    preview=False,
                )
                if result:
                    template_vendor, score = result
                    if score >= config.get("template_threshold", 0.85):
                        comp = template_vendor.upper()
                        matched = True
                        method = f"Template ({score:.2f})"
        except Exception as e:
            logging.error(f"⚠️ Template fallback failed on page {i + 1}: {e}")

    try:
        ticket = extract_ticket_number(page)
    except Exception as e:
        logging.error(f"❌ Ticket extraction failed on page {i + 1}: {e}")
        ticket = ""

    return {
        "page": i,
        "page_image": page,
        "vendor": comp,
        "matched": matched,
        "ticket": ticket,
        "method": method,
        "keyword": kw,
        "rotated": was_rotated,
        "grayscale": was_grayscaled,
        "ocr_score": ocr_score,
        "expected_vendor": expected_vendor,
        "preview": preview,
        "ocr_text": raw_ocr_text.strip(),
    }, roi_hash


def ocr_match_company(pil_img, ocr_config, config, threshold=80, log_row=None):
    try:
        max_w = config.get("ocr_resize_max_width", 1200)
        if pil_img.width > max_w:
            pil_img = pil_img.resize(
                (max_w, int(pil_img.height * max_w / pil_img.width))
            )

        raw_result = read_text(pil_img)
        ocr_text = raw_result.get("text", "")
        ocr_text = re.sub(r"[^a-z0-9]+", "", ocr_text.lower())
        if config.get("debug"):
            print("🧠 OCR PREVIEW:", ocr_text[:200])
    except Exception as e:
        print("❌ OCR Exception:", e)
        return "Unknown", False, "", "[OCR failed]", 0

    def best_match(companies):
        scored_matches = []
        for company, data in companies:
            for kw in data.get("keywords", []):
                kw_clean = re.sub(r"[^a-z0-9]+", "", kw.lower())
                if (
                    kw_clean in config.get("exclude_keywords", [])
                    and company.lower() != kw_clean
                ):
                    continue
                score = partial_ratio(kw_clean, ocr_text)
                scored_matches.append((company, score, kw))

        top_matches = sorted(scored_matches, key=lambda x: x[1], reverse=True)[:5]
        if log_row is not None:
            for idx, (comp, sc, term) in enumerate(top_matches):
                log_row[f"match_{idx + 1}_company"] = comp
                log_row[f"match_{idx + 1}_score"] = sc
                log_row[f"match_{idx + 1}_kw"] = term
        return max(top_matches, key=lambda x: x[1], default=("Unknown", 0, ""))

    for group_name in ["trucking", "materials"]:
        group = [
            (c, d)
            for c, d in ocr_config.items()
            if d.get("vendor_type", "").lower() == group_name
        ]
        comp, score, kw = best_match(group)
        if comp != "Unknown" and score >= threshold:
            return comp, True, kw, ocr_text[:300], score

    others = [
        (c, d)
        for c, d in ocr_config.items()
        if d.get("vendor_type", "").lower() not in ("trucking", "materials")
    ]
    comp, score, kw = best_match(others)
    if comp != "Unknown" and score >= threshold:
        return comp, True, kw, ocr_text[:300], score

    return "Unknown", False, "", ocr_text[:300], 0


def process_pages(
    pages: list[Image.Image], filepath: str, config: dict, suffix: str = ""
) -> list[str]:
    logging.info(f"🧠 Starting OCR processing for {len(pages)} pages...")
    templates = (
        load_templates(config["template_dir"])
        if config.get("use_template_fallback", True)
        else {}
    )
    base_name = Path(filepath).stem.upper()
    file_metadata = parse_input_filename(filepath)
    ocr_config = load_ocr_configs_from_excel(config["keyword_file"])
    ocr_cache = {}

    pages_by_vendor = defaultdict(list)
    log_entries = []
    match_stats = Counter()
    unmatched_pages = []
    expected_list = config.get("expected_vendors", [])
    crop_pct = config.get("ocr_crop_top_percent", 25) / 100
    ocr_text_log = []

    tasks = [
        (
            i,
            page,
            filepath,
            config,
            templates,
            ocr_config,
            expected_list[i] if i < len(expected_list) else "",
            ocr_cache,
        )
        for i, page in enumerate(pages)
    ]

    executor_cls = (
        ProcessPoolExecutor if config.get("use_process_pool") else ThreadPoolExecutor
    )
    with executor_cls(max_workers=config.get("num_workers", 4)) as executor:
        results = list(executor.map(process_single_page, tasks))

    for res, roi_hash in results:
        i, page, comp, matched = (
            res["page"],
            res["page_image"],
            res["vendor"],
            res["matched"],
        )
        pages_by_vendor[comp].append(page)
        log_entries.append(
            {
                "Filename": base_name,
                "Page": i + 1,
                "Vendor": comp,
                "Ticket Number": res["ticket"],
                "Matched Keyword": res["keyword"],
                "Method": res["method"],
                "Rotated": res["rotated"],
                "Grayscale": res["grayscale"],
            }
        )
        ocr_text_log.append(
            {
                "Filename": base_name,
                "Page": i + 1,
                "Vendor": comp,
                "OCR Text": res["ocr_text"],
            }
        )
        match_stats[comp] += 1
        if not matched:
            unmatched_pages.append(page)

    from datetime import datetime

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ocr_log_path = Path(filepath).parent / f"ocr_text_log_{ts}.csv"

    try:
        pd.DataFrame(ocr_text_log).to_csv(ocr_log_path, index=False)
        logging.info(f"📤 OCR text log saved: {ocr_log_path}")
    except Exception as e:
        logging.warning(f"⚠️ Failed to save OCR text log: {e}")

    output_paths = export_grouped_output(
        pages_by_vendor, config["output_format"], file_metadata, filepath, config
    )

    if config["output_format"].lower() == "pdf":
        combined_name = (
            format_output_filename_camel(
                vendor="",
                page_count=len(pages),
                meta=file_metadata,
                output_format="pdf",
            )
            .replace("__", "_")
            .replace("._", ".")
        )
        combined_path = get_sequenced_file_path(Path(filepath).parent, combined_name)

        compressed_pages = []
        pdf_scale = config.get("pdf_resize_scale", 0.5)  # Default to 50% if not defined
        pdf_resolution = config.get("pdf_resolution", 150)  # Default to 150 DPI

        for vendor, imgs in pages_by_vendor.items():
            for p in imgs:
                try:
                    rgb = p.convert("RGB")
                    if pdf_scale < 1.0:
                        rgb = rgb.resize(
                            (int(rgb.width * pdf_scale), int(rgb.height * pdf_scale)),
                            Image.LANCZOS,
                        )
                    compressed_pages.append(rgb)
                except Exception as e:
                    logging.error(f"Failed to prepare image for PDF: {e}")

        if compressed_pages:
            try:
                compressed_pages[0].save(
                    combined_path,
                    save_all=True,
                    append_images=compressed_pages[1:],
                    format="PDF",
                    resolution=pdf_resolution,
                )
                logging.info(f"📎 Compressed combined PDF saved: {combined_path}")
            except Exception as e:
                logging.error(f"❌ Failed to save combined compressed PDF: {e}")

    # ⬇️ PATCH: Add material, source, destination from parsed filename into each log row
    material = file_metadata.get("MATERIAL", "")
    source = file_metadata.get("SOURCE", "")
    destination = file_metadata.get("DESTINATION", "")
    job_id = file_metadata.get("JOB_ID", "")
    job_date = file_metadata.get("DATE", "")

    for row in log_entries:
        reordered = {
            "Filename": row["Filename"],
            "Page": row["Page"],
            "Vendor": row["Vendor"],
            "Ticket Number": row["Ticket Number"],
            "material": material,
            "source": source,
            "destination": destination,
            "Matched Keyword": row["Matched Keyword"],
            "Method": row["Method"],
            "Rotated": row["Rotated"],
            "Grayscale": row["Grayscale"],
        }
        row.clear()
        row.update(reordered)

    log_dir = Path(filepath).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{job_id}_{job_date}_TruckingLog.xlsx"

    if log_file.exists():
        try:
            existing = pd.read_excel(log_file)
            new = pd.DataFrame(log_entries)
            combined = pd.concat([existing, new], ignore_index=True)
        except Exception as e:
            logging.error(f"❌ Failed to load/append to existing log file: {e}")
            combined = pd.DataFrame(log_entries)
    else:
        combined = pd.DataFrame(log_entries)

    try:
        combined.to_excel(log_file, index=False)
        logging.info(f"📝 Log saved to: {log_file}")
    except PermissionError:
        logging.warning(f"🔒 Log file locked: {log_file}, saving backup copy...")
        seq = 1
        while True:
            fallback_log_file = log_file.with_name(
                log_file.stem + f"_{seq}" + log_file.suffix
            )
            if not fallback_log_file.exists():
                try:
                    combined.to_excel(fallback_log_file, index=False)
                    logging.info(f"📝 Backup log saved to: {fallback_log_file}")
                    break
                except Exception as e:
                    logging.error(f"❌ Failed to save fallback log: {e}")
                    break
            seq += 1
    except Exception as e:
        logging.error(f"❌ Failed to write Excel log: {e}")

    logging.info(
        f"✅ Processed {len(pages)} pages. Vendors matched: {dict(match_stats)}"
    )
    if unmatched_pages:
        logging.warning(f"⚠️ {len(unmatched_pages)} pages unmatched.")

    logging.info("✅ Vendor match breakdown:")
    for vendor, count in match_stats.most_common():
        logging.info(f"   • {vendor}: {count}")

    return output_paths
