"""Unified OCR pipeline entry point."""

from __future__ import annotations

import csv
import io
import json
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

try:
    from doctr_process.logging_setup import setup_logging as _setup_logging
except ModuleNotFoundError:  # pragma: no cover - for direct script execution
    from logging_setup import setup_logging as _setup_logging  # type: ignore

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



def setup_logging(log_dir: str) -> str:
    """Initialise logging and record the run identifier.

    Parameters
    ----------
    log_dir: str
        Directory in which log files should be written.

    Returns
    -------
    str
        The generated run identifier.
    """

    run_id = _setup_logging(log_dir=log_dir)
    run_file = Path(log_dir) / f"run_{run_id}.json"
    run_file.write_text(json.dumps({"run_id": run_id}))
    return run_id


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


def run_pipeline(config_path: str | Path | None = None) -> None:
    """Execute the OCR pipeline using ``config_path`` configuration."""

    if config_path is None:
        config_path = CONFIG_DIR / "config.yaml"

    cfg = load_config(str(config_path))
    # Logging is now handled by __main__.py and logging_setup.py
    cfg = resolve_input(cfg)
    extraction_rules = load_extraction_rules(
        cfg.get("extraction_rules_yaml", str(CONFIG_DIR / "extraction_rules.yaml"))
    )
    vendor_rules = load_vendor_rules_from_csv(
        cfg.get("vendor_keywords_csv", str(CONFIG_DIR / "ocr_keywords.csv"))
    )
    logging.info("Total vendors loaded: %d", len(vendor_rules))
    output_handlers = create_handlers(cfg.get("output_format", ["csv"]), cfg)

    if cfg.get("batch_mode"):
        path = Path(cfg["input_dir"])
        files = sorted(str(p) for p in path.glob("*.pdf"))
    else:
        files = [cfg["input_pdf"]]

    logging.info("Batch processing %d file(s)...", len(files))
    batch_start = time.perf_counter()

    all_rows: List[Dict] = []
    perf_records: List[Dict] = []
    ticket_issues: List[Dict] = []
    issues_log: List[Dict] = []
    analysis_records: List[Dict] = []
    preflight_exceptions: List[Dict] = []

    tasks = [(f, cfg, vendor_rules, extraction_rules) for f in files]

    if cfg.get("parallel"):
        from multiprocessing import Pool

        with Pool(cfg.get("num_workers", os.cpu_count())) as pool:
            results = []
            with tqdm(total=len(tasks), desc="Files") as pbar:
                for res in pool.imap(_proc, tasks):
                    results.append(res)
                    pbar.update()
    else:
        results = [_proc(t) for t in tqdm(tasks, desc="Files", total=len(tasks))]

    for (f, *_), res in zip(tasks, results):
        rows, perf, pf_exc, t_issues, i_log, analysis, thumbs = res

        perf_records.append(perf)
        all_rows.extend(rows)
        ticket_issues.extend(t_issues)
        issues_log.extend(i_log)
        analysis_records.extend(analysis)
        preflight_exceptions.extend(pf_exc)

        vendor_counts = {}
        for r in rows:
            v = r.get("vendor") or ""
            vendor_counts[v] = vendor_counts.get(v, 0) + 1
        logging.info(
            "Processed %d pages. Vendors matched: %s", perf["pages"], vendor_counts
        )
        if vendor_counts:
            logging.info("Vendor match breakdown:")
            for v, c in vendor_counts.items():
                logging.info("   - %s: %d", v, c)

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

    reporting_utils.export_issue_logs(ticket_issues, issues_log, cfg)
    reporting_utils.export_process_analysis(analysis_records, cfg)

    if cfg.get("valid_pages_zip"):
        vendor_dir = os.path.join(cfg.get("output_dir", "./outputs"), "vendor_docs")
        zip_folder(
            vendor_dir,
            os.path.join(cfg.get("output_dir", "./outputs"), "valid_pages.zip"),
        )

    logging.info("Output written to: %s", cfg.get("output_dir", "./outputs"))
    logging.info("Total batch time: %.2fs", time.perf_counter() - batch_start)


def main() -> None:
    """CLI entry point for running the OCR pipeline."""
    run_pipeline()


if __name__ == "__main__":
    main()
