"""Unified OCR pipeline entry point."""

from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Tuple
import logging
import time
import csv
import os
import re
import sys

# When this module is imported directly (e.g. via ``gui.py``), the parent
# ``doctr_process`` directory is not automatically added to ``sys.path``.
# Insert it here so that imports such as ``processor.filename_utils`` used by
# the output handlers resolve correctly.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from doctr_ocr.config_utils import (
    load_config,
    load_extraction_rules,
    count_total_pages,
)
from doctr_ocr.input_picker import resolve_input
from doctr_ocr.ocr_engine import get_engine
from doctr_ocr.vendor_utils import (
    load_vendor_rules_from_csv,
    find_vendor,
    extract_vendor_fields,
    FIELDS,
)
from doctr_ocr.ocr_utils import (
    extract_images_generator,
    correct_image_orientation,
    get_image_hash,
    roi_has_digits,
    save_roi_image,
)
from doctr_ocr.preflight import run_preflight
from tqdm import tqdm
from output.factory import create_handlers
from doctr_ocr import reporting_utils
import pandas as pd

# Log to both console and a file using a simple format so messages match
# the original ticket_sorter console output style.
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
    handlers=[
        logging.FileHandler("error.log", mode="w", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)


def process_file(
    pdf_path: str, cfg: dict, vendor_rules, extraction_rules
) -> Tuple[List[Dict], Dict, List[Dict]]:

    """Process ``pdf_path`` and return rows, performance stats and preflight exceptions."""

    logging.info("🚀 Processing: %s", pdf_path)

    engine = get_engine(cfg.get("ocr_engine", "doctr"))
    rows: List[Dict] = []
    roi_exceptions: List[Dict] = []
    orient_method = cfg.get("orientation_check", "tesseract")
    total_pages = count_total_pages([pdf_path], cfg)

    corrected_pages = [] if cfg.get("save_corrected_pdf") else None
    draw_roi = cfg.get("draw_roi")

    skip_pages, preflight_excs = run_preflight(pdf_path, cfg)

    # Extract all pages first so we can time the extraction step
    ext = os.path.splitext(pdf_path)[1].lower()
    logging.info("📄 Extracting images from: %s (ext: %s)", pdf_path, ext)
    start_extract = time.perf_counter()
    images = list(extract_images_generator(pdf_path, cfg.get("poppler_path")))
    extract_time = time.perf_counter() - start_extract
    logging.info(
        "Extracted %d pages from %s in %.2fs", len(images), pdf_path, extract_time
    )
    logging.info("Finished extracting images")
    logging.info("🧠 Starting OCR processing for %d pages...", len(images))

    start = time.perf_counter()
    for i, img in enumerate(
        tqdm(images, total=len(images), desc=os.path.basename(pdf_path), unit="page")
    ):
        page_num = i + 1
        if page_num in skip_pages:
            logging.info("🚫 Skipping page %d due to preflight", page_num)
            continue
        img = correct_image_orientation(img, page_num, method=orient_method)
        if corrected_pages is not None:
            corrected_pages.append(img)
        page_hash = get_image_hash(img)
        page_start = time.perf_counter()
        text, result_page = engine(img)
        ocr_time = time.perf_counter() - page_start
        logging.info("⏱️ Page %d OCR time: %.2fs", page_num, ocr_time)

        vendor_name, vendor_type, _, display_name = find_vendor(text, vendor_rules)
        if result_page is not None:
            fields = extract_vendor_fields(result_page, vendor_name, extraction_rules)
        else:
            fields = {f: None for f in FIELDS}

        roi = (
            extraction_rules.get(vendor_name, {})
            .get("ticket_number", {})
            .get("roi")
        )
        if roi is None:
            roi = (
                extraction_rules.get("DEFAULT", {})
                .get("ticket_number", {})
                .get("roi", [0.65, 0.0, 0.99, 0.25])
            )
        if not roi_has_digits(img, roi):
            roi_exceptions.append(
                {"file": pdf_path, "page": i + 1, "error": "ticket-number missing/obscured"}
            )
            exception_reason = "ticket-number missing/obscured"
        else:
            exception_reason = None
        row = {
            "file": pdf_path,
            "page": page_num,
            "vendor": display_name,
            **fields,
            "image_path": save_page_image(
                img,
                pdf_path,
                i,
                cfg,
                vendor=display_name,
                ticket_number=fields.get("ticket_number"),
            ),
            "ocr_text": text,
            "page_hash": page_hash,
            "exception_reason": exception_reason,
        }
        if draw_roi:
            row["roi_image_path"] = _save_roi_page_image(
                img,
                roi,
                pdf_path,
                i,
                cfg,
                vendor=display_name,
                ticket_number=fields.get("ticket_number"),
            )
        rows.append(row)

    if corrected_pages:
        out_pdf = _get_corrected_pdf_path(pdf_path, cfg)
        if out_pdf and corrected_pages:
            os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
            corrected_pages[0].save(
                out_pdf,
                save_all=True,
                append_images=corrected_pages[1:],
                format="PDF",
                resolution=int(cfg.get("pdf_resolution", 150)),
            )
            logging.info("Corrected PDF saved to %s", out_pdf)

    logging.info("Finished running OCR")

    duration = time.perf_counter() - start
    perf = {
        "file": os.path.basename(pdf_path),
        "pages": len(rows),
        "duration_sec": round(duration, 2),
    }
    return rows, perf, preflight_excs


def save_page_image(
    img,
    pdf_path: str,
    idx: int,
    cfg: dict,
    vendor: str | None = None,
    ticket_number: str | None = None,
) -> str:
    """Save ``img`` to the configured image directory and return its path.

    If ``ticket_number`` is provided, the filename will be formatted as
    ``{ticket_number}_{vendor}_{page}`` using underscores for separators.
    Otherwise, the PDF stem is used as the base name.
    """

    out_dir = Path(cfg.get("output_dir", "./outputs")) / "images"
    out_dir.mkdir(parents=True, exist_ok=True)

    if ticket_number:
        v = vendor or "unknown"
        v = re.sub(r"\W+", "_", v).strip("_")
        t = re.sub(r"\W+", "_", str(ticket_number)).strip("_")
        base_name = f"{t}_{v}_{idx+1:03d}"
    else:
        base_name = f"{Path(pdf_path).stem}_{idx+1:03d}"

    out_path = out_dir / f"{base_name}.png"
    img.save(out_path)
    return str(out_path)


def _save_roi_page_image(
    img,
    roi,
    pdf_path: str,
    idx: int,
    cfg: dict,
    vendor: str | None = None,
    ticket_number: str | None = None,
) -> str:
    """Draw ROI on ``img`` and save it to the images directory."""
    out_dir = Path(cfg.get("output_images_dir", Path(cfg.get("output_dir", "./outputs")) / "images"))
    out_dir.mkdir(parents=True, exist_ok=True)

    if ticket_number:
        v = vendor or "unknown"
        v = re.sub(r"\W+", "_", v).strip("_")
        t = re.sub(r"\W+", "_", str(ticket_number)).strip("_")
        base_name = f"{t}_{v}_{idx+1:03d}_roi"
    else:
        base_name = f"{Path(pdf_path).stem}_{idx+1:03d}_roi"

    out_path = out_dir / f"{base_name}.png"
    save_roi_image(img, roi, str(out_path), idx + 1)
    return str(out_path)


def _get_corrected_pdf_path(pdf_path: str, cfg: dict) -> str | None:
    """Return the output path for the corrected PDF for ``pdf_path``."""
    base = cfg.get("corrected_pdf_path")
    if not base:
        return None
    base_p = Path(base)
    if base_p.suffix.lower() == ".pdf":
        if cfg.get("batch_mode"):
            return str(base_p.parent / f"{base_p.stem}_{Path(pdf_path).stem}.pdf")
        return str(base_p)
    base_p.mkdir(parents=True, exist_ok=True)
    return str(base_p / f"{Path(pdf_path).stem}_corrected.pdf")


def _write_performance_log(records: List[Dict], cfg: dict) -> None:
    """Save performance metrics to ``performance_log.csv`` in ``output_dir``."""
    if not records:
        return
    out_dir = cfg.get("output_dir", "./outputs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "performance_log.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "pages", "duration_sec"])
        writer.writeheader()
        writer.writerows(records)
    logging.info("Performance log written to %s", path)


def _append_hash_db(rows: List[Dict], cfg: dict) -> None:
    """Append page hashes to the hash database CSV."""
    path = cfg.get("hash_db_csv")
    if not path:
        return
    df = pd.DataFrame(rows)
    if df.empty:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "a" if os.path.exists(path) else "w"
    header = not os.path.exists(path)
    df[[
        "page_hash",
        "vendor",
        "ticket_number",
        "manifest_number",
        "file",
        "page",
    ]].to_csv(path, mode=mode, header=header, index=False)
    logging.info("Hash DB updated: %s", path)


def _validate_with_hash_db(rows: List[Dict], cfg: dict) -> None:
    """Validate pages against the stored hash database."""
    path = cfg.get("hash_db_csv")
    out_path = cfg.get("validation_output_csv", "validation_mismatches.csv")
    if not path or not os.path.exists(path):
        logging.warning("Hash DB not found for validation run")
        return
    df_ref = pd.read_csv(path)
    df_new = pd.DataFrame(rows)
    merged = df_new.merge(
        df_ref,
        on=["vendor", "ticket_number"],
        suffixes=("_new", "_ref"),
        how="left",
    )
    merged["hash_match"] = merged["page_hash_new"] == merged["page_hash_ref"]
    mismatches = merged[(~merged["hash_match"]) | (merged["page_hash_ref"].isna())]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    mismatches.to_csv(out_path, index=False)
    logging.info("Validation results written to %s", out_path)


def run_pipeline():
    """Execute the OCR pipeline using ``config.yaml``."""
    cfg = load_config()
    cfg = resolve_input(cfg)
    extraction_rules = load_extraction_rules(
        cfg.get("extraction_rules_yaml", "extraction_rules.yaml")
    )
    vendor_rules = load_vendor_rules_from_csv(
        cfg.get("vendor_keywords_csv", "ocr_keywords.csv")
    )
    logging.info("📦 Total vendors loaded: %d", len(vendor_rules))
    output_handlers = create_handlers(cfg.get("output_format", ["csv"]), cfg)

    if cfg.get("batch_mode"):
        path = Path(cfg["input_dir"])
        files = sorted(str(p) for p in path.glob("*.pdf"))
    else:
        files = [cfg["input_pdf"]]

    logging.info("🗂️ Batch processing %d file(s)...", len(files))
    batch_start = time.perf_counter()

    all_rows: List[Dict] = []
    perf_records: List[Dict] = []

    preflight_exceptions: List[Dict] = []
    all_exceptions: List[Dict] = []
    for idx, f in enumerate(files, 1):
        logging.info("📄 %d/%d Processing: %s", idx, len(files), os.path.basename(f))
        file_start = time.perf_counter()
        rows, perf, pf_exc = process_file(f, cfg, vendor_rules, extraction_rules)
        file_time = time.perf_counter() - file_start
        perf_records.append(perf)
        all_rows.extend(rows)
        preflight_exceptions.extend(pf_exc)

        vendor_counts = {}
        for r in rows:
            v = r.get("vendor") or ""
            vendor_counts[v] = vendor_counts.get(v, 0) + 1
        logging.info(
            "✅ Processed %d pages. Vendors matched: %s", perf["pages"], vendor_counts
        )
        if vendor_counts:
            logging.info("✅ Vendor match breakdown:")
            for v, c in vendor_counts.items():
                logging.info("   • %s: %d", v, c)
        logging.info("⏱️ %s processed in %.2fs", os.path.basename(f), file_time)

    for handler in output_handlers:
        handler.write(all_rows, cfg)

    reporting_utils.create_reports(all_rows, cfg)
    reporting_utils.export_preflight_exceptions(preflight_exceptions, cfg)
    reporting_utils.export_log_reports(cfg)

    if cfg.get("run_type", "initial") == "validation":
        _validate_with_hash_db(all_rows, cfg)
    else:
        _append_hash_db(all_rows, cfg)

    if cfg.get("profile"):
        _write_performance_log(perf_records, cfg)

    if all_exceptions:
        exc_dir = Path(cfg.get("output_dir", "./outputs")) / "logs" / "ticket_number"
        exc_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(all_exceptions).to_csv(exc_dir / "roi_exceptions.csv", index=False)

    logging.info("✅ Output written to: %s", cfg.get("output_dir", "./outputs"))
    logging.info("🕒 Total batch time: %.2fs", time.perf_counter() - batch_start)


if __name__ == "__main__":
    run_pipeline()
