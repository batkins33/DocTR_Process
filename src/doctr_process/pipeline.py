"""Unified OCR pipeline entry point."""

from __future__ import annotations

import csv
import io
import logging
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Tuple

import fitz  # PyMuPDF
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm

from doctr_process.ocr import reporting_utils
from doctr_process.ocr.config_utils import count_total_pages
from doctr_process.ocr.config_utils import load_config
from doctr_process.ocr.config_utils import load_extraction_rules
from doctr_process.ocr.file_utils import zip_folder
from doctr_process.ocr.input_picker import resolve_input
from doctr_process.ocr.ocr_engine import get_engine
from doctr_process.ocr.ocr_utils import (
    extract_images_generator,
    correct_image_orientation,
    get_image_hash,
    roi_has_digits,
    save_crop_and_thumbnail,
)
from doctr_process.ocr.preflight import run_preflight
from doctr_process.ocr.vendor_utils import (
    load_vendor_rules_from_csv,
    find_vendor,
    extract_vendor_fields,
    FIELDS,
)
from doctr_process.output.factory import create_handlers

# Project root used for trimming paths in logs and locating default configs
ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "configs"

ROI_SUFFIXES = {
    "ticket_number": "TicketNum",
    "manifest_number": "Manifest",
    "material_type": "MaterialType",
    "truck_number": "TruckNum",
    "date": "Date",
}


## Logging is now handled by logging_setup.py


def process_file(
        pdf_path: str, cfg: dict, vendor_rules, extraction_rules
) -> Tuple[List[Dict], Dict, List[Dict], List[Dict], List[Dict]]:
    """Process ``pdf_path`` and return rows, performance stats and preflight exceptions."""

    logging.info("Processing: %s", pdf_path)

    engine = get_engine(cfg.get("ocr_engine", "tesseract"))
    rows: List[Dict] = []
    roi_exceptions: List[Dict] = []
    ticket_issues: List[Dict] = []
    issue_log: List[Dict] = []
    page_analysis: List[Dict] = []
    thumbnail_log: List[Dict] = []
    orient_method = cfg.get("orientation_check", "tesseract")
    total_pages = count_total_pages([pdf_path], cfg)

    corrected_doc = None
    corrected_pdf_path = None
    if cfg.get("save_corrected_pdf"):
        corrected_pdf_path = _get_corrected_pdf_path(pdf_path, cfg)
        if corrected_pdf_path:
            os.makedirs(os.path.dirname(corrected_pdf_path), exist_ok=True)
            corrected_doc = fitz.open()
    draw_roi = cfg.get("draw_roi")

    skip_pages, preflight_excs = run_preflight(pdf_path, cfg)

    # Stream page images to avoid storing the entire document in memory
    ext = os.path.splitext(pdf_path)[1].lower()
    logging.info("Extracting images from: %s (ext: %s)", pdf_path, ext)
    images = extract_images_generator(
        pdf_path, cfg.get("poppler_path"), cfg.get("dpi", 300)
    )
    logging.info("Starting OCR processing for %d pages...", total_pages)

    start = time.perf_counter()
    for i, page in enumerate(
            tqdm(images, total=total_pages, desc=os.path.basename(pdf_path), unit="page")
    ):
        page_num = i + 1
        if page_num in skip_pages:
            logging.info("Skipping page %d due to preflight", page_num)
            continue
        if isinstance(page, np.ndarray):
            img = Image.fromarray(page)
        elif isinstance(page, Image.Image):
            img = page
        else:
            raise TypeError(f"Unsupported page type: {type(page)!r}")
        orient_start = time.perf_counter()
        img = correct_image_orientation(img, page_num, method=orient_method)
        orient_time = time.perf_counter() - orient_start
        if corrected_doc is not None:
            # Normalize mode → RGB to avoid palette/alpha/CMYK issues,
            # then embed as a PNG (lossless, OCR-friendly).
            page_pdf = corrected_doc.new_page(width=img.width, height=img.height)
            rect = fitz.Rect(0, 0, img.width, img.height)

            rgb = img.convert("RGB")  # handles P/LA/RGBA/CMYK/etc.
            with io.BytesIO() as bio:
                rgb.save(bio, format="PNG", optimize=True)
                page_pdf.insert_image(rect, stream=bio.getvalue())

            # no leaks: bio auto-closes; 'rgb' is a PIL Image and will be GC’d

        page_hash = get_image_hash(img)
        page_start = time.perf_counter()
        text, result_page = engine(img)
        ocr_time = time.perf_counter() - page_start
        logging.info("Page %d OCR time: %.2fs", page_num, ocr_time)

        vendor_name, vendor_type, _, display_name = find_vendor(text, vendor_rules)
        if result_page is not None:
            fields = extract_vendor_fields(result_page, vendor_name, extraction_rules)
        else:
            fields = {f: None for f in FIELDS}

        roi = extraction_rules.get(vendor_name, {}).get("ticket_number", {}).get("roi")
        if roi is None:
            roi = (
                extraction_rules.get("DEFAULT", {})
                .get("ticket_number", {})
                .get("roi", [0.65, 0.0, 0.99, 0.25])
            )
        if not roi_has_digits(img, roi):
            roi_exceptions.append(
                {
                    "file": pdf_path,
                    "page": i + 1,
                    "error": "ticket-number missing/obscured",
                }
            )
            exception_reason = "ticket-number missing/obscured"
        else:
            exception_reason = None

        for field_name in FIELDS:
            if not fields.get(field_name):
                issue_log.append(
                    {
                        "page": page_num,
                        "issue_type": "missing_field",
                        "field": field_name,
                    }
                )
                if field_name == "ticket_number":
                    ticket_issues.append({"page": page_num, "issue": "missing ticket"})

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
            "orientation": correct_image_orientation.last_angle,
            "ocr_time": round(ocr_time, 3),
            "orientation_time": round(orient_time, 3),
        }
        if cfg.get("crops") or cfg.get("thumbnails"):
            for fname in FIELDS:
                roi_field = (
                    extraction_rules.get(vendor_name, {}).get(fname, {}).get("roi")
                )
                if roi_field:
                    base = f"{Path(pdf_path).stem}_{page_num:03d}_{fname}"
                    crop_dir = Path(cfg.get("output_dir", "./outputs")) / "crops"
                    thumb_dir = Path(cfg.get("output_dir", "./outputs")) / "thumbnails"
                    save_crop_and_thumbnail(
                        img,
                        roi_field,
                        str(crop_dir),
                        base,
                        str(thumb_dir),
                        thumbnail_log,
                    )
        if draw_roi:
            for fname in FIELDS:
                roi_field = (
                    extraction_rules.get(vendor_name, {}).get(fname, {}).get("roi")
                )
                if roi_field:
                    roi_type = ROI_SUFFIXES.get(fname, fname.replace("_", "").title())
                    key = (
                        "roi_image_path"
                        if fname == "ticket_number"
                        else (
                            "manifest_roi_image_path"
                            if fname == "manifest_number"
                            else f"{fname}_roi_image_path"
                        )
                    )
                    row[key] = _save_roi_page_image(
                        img,
                        roi_field,
                        pdf_path,
                        i,
                        cfg,
                        vendor=display_name,
                        ticket_number=fields.get("ticket_number"),
                        roi_type=roi_type,
                    )
        rows.append(row)
        page_analysis.append(
            {
                "file": pdf_path,
                "page": page_num,
                "ocr_time": round(ocr_time, 3),
                "orientation_time": round(orient_time, 3),
                "orientation": correct_image_orientation.last_angle,
            }
        )

        img.close()

    # Free memory from any accumulated page images
    try:
        images.clear()  # if it's a list
    except Exception:
        pass
    try:
        del images
    except Exception:
        pass

    # Save & close the corrected PDF (only if it has pages and a path)
    if corrected_doc is not None:
        try:
            if corrected_pdf_path and len(corrected_doc) > 0:
                parent = os.path.dirname(corrected_pdf_path) or "."
                os.makedirs(parent, exist_ok=True)
                corrected_doc.save(corrected_pdf_path)
                logging.info("Corrected PDF saved to %s", corrected_pdf_path)
            elif len(corrected_doc) == 0:
                logging.info("Skipped saving corrected PDF: document has no pages.")
            else:
                logging.info("Skipped saving corrected PDF: no output path provided.")
        finally:
            corrected_doc.close()

    logging.info("Finished running OCR")

    duration = time.perf_counter() - start
    perf = {
        "file": os.path.basename(pdf_path),
        "pages": len(rows),
        "duration_sec": round(duration, 2),
    }
    return (
        rows,
        perf,
        preflight_excs,
        ticket_issues,
        issue_log,
        page_analysis,
        thumbnail_log,
    )


# ``multiprocessing`` workers need to be able to pickle the function they
# execute.  If a helper is defined inside ``run_pipeline`` it becomes a local
# (non-picklable) object and ``Pool`` will fail with
# ``Can't pickle local object 'run_pipeline.<locals>.proc'``.  Define a module-
# level wrapper that unpacks arguments and forwards them to ``process_file`` so
# it can safely be used with ``Pool.imap`` or similar.
def _proc(args: Tuple[str, dict, dict, dict]):
    """Unpack the arguments tuple and call :func:`process_file`.

    This function exists solely to provide a picklable entry point for worker
    processes on platforms like Windows that use the ``spawn`` start method.
    """

    return process_file(*args)


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

    out_dir = Path(cfg.get("output_dir", "./outputs")) / "images" / "page"
    out_dir.mkdir(parents=True, exist_ok=True)

    if ticket_number:
        v = vendor or "unknown"
        v = re.sub(r"\W+", "_", v).strip("_")
        t = re.sub(r"\W+", "_", str(ticket_number)).strip("_")
        base_name = f"{t}_{v}_{idx + 1:03d}"
    else:
        base_name = f"{Path(pdf_path).stem}_{idx + 1:03d}"

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
        roi_type: str = "TicketNum",
) -> str:
    """Crop ``roi`` from ``img`` and save it to the images directory."""
    out_dir = Path(cfg.get("output_dir", "./outputs")) / "images" / roi_type
    out_dir.mkdir(parents=True, exist_ok=True)

    if ticket_number:
        v = vendor or "unknown"
        v = re.sub(r"\W+", "_", v).strip("_")
        t = re.sub(r"\W+", "_", str(ticket_number)).strip("_")
        base_name = f"{t}_{v}_{idx + 1:03d}_{roi_type}"
    else:
        base_name = f"{Path(pdf_path).stem}_{idx + 1:03d}_{roi_type}"

    width, height = img.size
    if max(roi) <= 1:
        box = (
            int(roi[0] * width),
            int(roi[1] * height),
            int(roi[2] * width),
            int(roi[3] * height),
        )
    else:
        box = (int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))
    crop = img.crop(box)
    out_path = out_dir / f"{base_name}.jpg"
    crop.save(out_path, format="JPEG")
    crop.close()
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
    df[
        [
            "page_hash",
            "vendor",
            "ticket_number",
            "manifest_number",
            "file",
            "page",
        ]
    ].to_csv(path, mode=mode, header=header, index=False)
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


def run_pipeline(config_path=None):
    """
    Main entry point for running the OCR pipeline from GUI or CLI.
    Loads config, determines batch/single mode, processes files, and outputs results.
    """
    import logging
    if config_path is None:
        config_path = CONFIG_DIR / "config.yaml"
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    cfg = load_config(config_path)

    # Load vendor and extraction rules
    vendor_rules = load_vendor_rules_from_csv(cfg.get("vendor_rules_csv", str(CONFIG_DIR / "ocr_keywords.csv")))
    extraction_rules = load_extraction_rules(cfg.get("extraction_rules_yaml", str(CONFIG_DIR / "extraction_rules.yaml")))

    # Determine input(s)
    input_pdf = cfg.get("input_pdf")
    input_dir = cfg.get("input_dir")
    batch_mode = cfg.get("batch_mode", False)
    output_dir = cfg.get("output_dir", "./outputs")
    os.makedirs(output_dir, exist_ok=True)

    if batch_mode and input_dir:
        pdf_files = [str(p) for p in Path(input_dir).glob("*.pdf")]
        logging.info(f"Batch mode: {len(pdf_files)} PDF files found in {input_dir}")
    elif input_pdf:
        pdf_files = [input_pdf]
        logging.info(f"Single file mode: {input_pdf}")
    else:
        raise ValueError("No input_pdf or input_dir specified in config.")

    all_rows = []
    all_perf = []
    all_preflight = []
    all_issues = []
    all_ticket_issues = []

    for pdf_path in pdf_files:
        rows, perf, preflight, issues, ticket_issues = process_file(
            pdf_path, cfg, vendor_rules, extraction_rules
        )
        all_rows.extend(rows)
        all_perf.extend(perf if isinstance(perf, list) else [perf])
        all_preflight.extend(preflight)
        all_issues.extend(issues)
        all_ticket_issues.extend(ticket_issues)

    # Output results
    handlers = create_handlers(cfg, output_dir)
    for handler in handlers:
        handler.write(all_rows)
        logging.info(f"Output written by handler: {handler.__class__.__name__}")

    # Optionally log performance, issues, etc.
    if cfg.get("log_performance"):
        perf_path = os.path.join(output_dir, "performance_log.csv")
        pd.DataFrame(all_perf).to_csv(perf_path, index=False)
        logging.info(f"Performance log written: {perf_path}")
    if cfg.get("log_issues"):
        issues_path = os.path.join(output_dir, "issues_log.csv")
        pd.DataFrame(all_issues).to_csv(issues_path, index=False)
        logging.info(f"Issues log written: {issues_path}")
    if cfg.get("log_preflight"):
        preflight_path = os.path.join(output_dir, "preflight_log.csv")
        pd.DataFrame(all_preflight).to_csv(preflight_path, index=False)
        logging.info(f"Preflight log written: {preflight_path}")
    if cfg.get("log_ticket_issues"):
        ticket_path = os.path.join(output_dir, "ticket_issues_log.csv")
        pd.DataFrame(all_ticket_issues).to_csv(ticket_path, index=False)
        logging.info(f"Ticket issues log written: {ticket_path}")

    logging.info("Pipeline run complete.")


def main() -> None:
    """CLI entry point for running the OCR pipeline."""
    run_pipeline()


if __name__ == "__main__":
    main()
