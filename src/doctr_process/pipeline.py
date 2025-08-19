# Unified OCR pipeline entry point.

from __future__ import annotations

import csv
import logging
import os
import re
import time
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Tuple, NamedTuple

try:
    from fitz import open as fitz_open, Rect as fitz_Rect  # PyMuPDF

    fitz = True
except ImportError:
    try:
        from pymupdf import open as fitz_open, Rect as fitz_Rect  # newer PyMuPDF versions

        fitz = True
    except ImportError:
        fitz_open = fitz_Rect = None
        fitz = None

from PIL import Image
from numpy import ndarray
from pandas import DataFrame, read_csv
from tqdm import tqdm

from doctr_process.ocr import reporting_utils
from doctr_process.ocr.config_utils import count_total_pages
from doctr_process.ocr.config_utils import load_config
from doctr_process.ocr.config_utils import load_extraction_rules
from doctr_process.resources import get_config_path
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
except ModuleNotFoundError:
    pass  # Logging setup is optional or handled elsewhere

# Legacy constants - now using importlib.resources for packaged configs
# Kept for backward compatibility with existing code
ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "configs"

ROI_SUFFIXES = {
    "ticket_number": "TicketNum",
    "manifest_number": "Manifest",
    "material_type": "MaterialType",
    "truck_number": "TruckNum",
    "date": "Date",
}


class ProcessResult(NamedTuple):
    """Result of processing a single file."""
    rows: List[Dict]
    perf: Dict
    preflight_excs: List[Dict]
    ticket_issues: List[Dict]
    issue_log: List[Dict]
    page_analysis: List[Dict]
    thumbnail_log: List[Dict]


def _sanitize_for_log(text: str) -> str:
    """Sanitize text for safe logging by removing newlines and control characters."""
    if not isinstance(text, str):
        text = str(text)
    return re.sub(r'[\r\n\x00-\x1f\x7f-\x9f]', '_', text)


def _validate_path(path: str, base_dir: str = None) -> str:
    """Validate and normalize path to prevent traversal attacks."""
    if not path:
        raise ValueError("Path cannot be empty")

    try:
        normalized = os.path.normpath(path)
        if base_dir:
            base_abs = os.path.abspath(base_dir)
            path_abs = os.path.abspath(os.path.join(base_dir, normalized))
            try:
                common = os.path.commonpath([base_abs, path_abs])
                if common != base_abs:
                    raise ValueError(f"Path outside base directory: {path}")
            except ValueError:
                # Handle Windows drive mismatch
                raise ValueError(f"Path outside base directory: {path}")
        return normalized
    except (OSError, ValueError) as e:
        raise ValueError(f"Invalid path: {path}") from e


def _setup_corrected_pdf(pdf_str: str, cfg: dict):
    """Setup corrected PDF document if needed."""
    if not cfg.get("save_corrected_pdf") or fitz is None:
        return None, None
    corrected_pdf_path = _get_corrected_pdf_path(pdf_str, cfg)
    if corrected_pdf_path:
        parent_dir = os.path.dirname(corrected_pdf_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        return fitz_open(), corrected_pdf_path
    return None, None


def _process_page_ocr(img, engine, page_num: int, corrected_doc):
    """Process OCR for a single page."""
    if corrected_doc is not None:
        page_pdf = corrected_doc.new_page(width=img.width, height=img.height)
        rgb = img.convert("RGB")
        with BytesIO() as bio:
            rgb.save(bio, format="PNG", optimize=True)
            page_pdf.insert_image(fitz_Rect(0, 0, img.width, img.height), stream=bio.getvalue())

    page_hash = get_image_hash(img)
    page_start = time.perf_counter()
    text, result_page = engine(img)
    ocr_time = time.perf_counter() - page_start
    logging.info("Page %d OCR time: %.2fs", page_num, ocr_time)
    return text, result_page, page_hash, ocr_time


def process_file(
        pdf_path: str, cfg: dict, vendor_rules, extraction_rules
) -> ProcessResult:
    """Process ``pdf_path`` and return rows, performance stats and preflight exceptions."""

    def _init_corrected_doc(pdf_str, cfg):
        corrected_doc = None
        corrected_pdf_path = None
        if cfg.get("save_corrected_pdf") and fitz is not None:
            corrected_pdf_path = _get_corrected_pdf_path(pdf_str, cfg)
            if corrected_pdf_path:
                parent_dir = os.path.dirname(corrected_pdf_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                corrected_doc = fitz_open()
        return corrected_doc, corrected_pdf_path

    def _process_single_page(
            i, page, skip_pages, engine, orient_method, corrected_doc, pdf_str,
            vendor_rules, extraction_rules, cfg, draw_roi, thumbnail_log
    ):
        page_num = i + 1
        if page_num in skip_pages:
            logging.info("Skipping page %d due to preflight", page_num)
            return None

        if isinstance(page, ndarray):
            img = Image.fromarray(page)
        elif isinstance(page, Image.Image):
            img = page
        else:
            raise TypeError(f"Unsupported page type: {type(page)!r}")

        orient_start = time.perf_counter()
        img = correct_image_orientation(img, page_num, method=orient_method)
        orient_time = time.perf_counter() - orient_start

        if corrected_doc is not None and fitz is not None:
            page_pdf = corrected_doc.new_page(width=img.width, height=img.height)
            rect = fitz_Rect(0, 0, img.width, img.height)
            rgb = img.convert("RGB")
            with BytesIO() as bio:
                rgb.save(bio, format="PNG", optimize=True)
                page_pdf.insert_image(rect, stream=bio.getvalue())

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
            exception_reason = "ticket-number missing/obscured"
        else:
            exception_reason = None

        missing_fields = []
        ticket_issue = None
        for field_name in FIELDS:
            if not fields.get(field_name):
                missing_fields.append(field_name)
                if field_name == "ticket_number":
                    ticket_issue = {"page": page_num, "issue": "missing ticket"}

        row = {
            "file": pdf_str,
            "page": page_num,
            "vendor": display_name,
            **fields,
            "image_path": save_page_image(
                img,
                pdf_str,
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
                    # Sanitize PDF filename to prevent path traversal
                    safe_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(pdf_path).stem)
                    base = f"{safe_stem}_{page_num:03d}_{fname}"
                    output_dir = cfg.get("output_dir", "./outputs")
                    _validate_path(output_dir)
                    crop_dir = Path(output_dir) / "crops"
                    thumb_dir = Path(output_dir) / "thumbnails"
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
                    # Path validation already done in process_file
                    row[key] = _save_roi_page_image(
                        img,
                        roi_field,
                        pdf_str,
                        i,
                        cfg,
                        vendor=display_name,
                        ticket_number=fields.get("ticket_number"),
                        roi_type=roi_type,
                    )
        analysis = {
            "file": pdf_str,
            "page": page_num,
            "ocr_time": round(ocr_time, 3),
            "orientation_time": round(orient_time, 3),
            "orientation": correct_image_orientation.last_angle,
        }
        img.close()
        return {
            "row": row,
            "missing_fields": missing_fields,
            "ticket_issue": ticket_issue,
            "exception_reason": exception_reason,
            "analysis": analysis,
        }

    pdf_str = str(pdf_path)
    logging.debug("process_file path=%s type=%s", pdf_str, type(pdf_path).__name__)
    logging.info("Processing: %s", _sanitize_for_log(pdf_str))

    engine = get_engine(cfg.get("ocr_engine", "tesseract"))
    rows: List[Dict] = []
    roi_exceptions: List[Dict] = []
    ticket_issues: List[Dict] = []
    issue_log: List[Dict] = []
    page_analysis: List[Dict] = []
    thumbnail_log: List[Dict] = []
    orient_method = cfg.get("orientation_check", "tesseract")
    total_pages = count_total_pages([pdf_str], cfg)

    corrected_doc, corrected_pdf_path = _init_corrected_doc(pdf_str, cfg)
    draw_roi = cfg.get("draw_roi")

    skip_pages, preflight_excs = run_preflight(pdf_str, cfg)

    ext = os.path.splitext(pdf_str)[1].lower()
    logging.info("Extracting images from: %s (ext: %s)", _sanitize_for_log(pdf_str), _sanitize_for_log(ext))
    images = extract_images_generator(pdf_str, cfg.get("poppler_path"), cfg.get("dpi", 300))
    logging.info("Starting OCR processing for %d pages...", total_pages)

    start = time.perf_counter()
    for i, page in enumerate(
            tqdm(images, total=total_pages, desc=_sanitize_for_log(os.path.basename(pdf_str)), unit="page")
    ):
        result = _process_single_page(
            i, page, skip_pages, engine, orient_method, corrected_doc, pdf_str, vendor_rules, extraction_rules, cfg,
            draw_roi, thumbnail_log
        )
        if result is None:
            continue
        rows.append(result["row"])
        page_analysis.append(result["analysis"])
        if result["exception_reason"]:
            roi_exceptions.append(
                {
                    "file": pdf_str,
                    "page": i + 1,
                    "error": result["exception_reason"],
                }
            )
        for field_name in result["missing_fields"]:
            issue_log.append(
                {
                    "page": i + 1,
                    "issue_type": "missing_field",
                    "field": field_name,
                }
            )
        if result["ticket_issue"]:
            ticket_issues.append(result["ticket_issue"])

    try:
        if hasattr(images, 'clear'):
            images.clear()
    except (AttributeError, TypeError) as e:
        logging.debug("Could not clear images list: %s", _sanitize_for_log(str(e)))
    try:
        del images
    except (NameError, UnboundLocalError) as e:
        logging.debug("Could not delete images: %s", _sanitize_for_log(str(e)))

    if corrected_doc is not None:
        try:
            if corrected_pdf_path and len(corrected_doc) > 0:
                _validate_path(corrected_pdf_path)
                parent = os.path.dirname(corrected_pdf_path) or "."
                os.makedirs(parent, exist_ok=True)
                corrected_doc.save(corrected_pdf_path)
                logging.info("Corrected PDF saved to %s", _sanitize_for_log(corrected_pdf_path))
            elif not corrected_doc:
                logging.info("Skipped saving corrected PDF: document has no pages.")
            else:
                logging.info("Skipped saving corrected PDF: no output path provided.")
        finally:
            corrected_doc.close()

    logging.info("Finished running OCR")

    duration = time.perf_counter() - start
    perf = {
        "file": _sanitize_for_log(os.path.basename(pdf_str)),
        "pages": len(rows),
        "duration_sec": round(duration, 2),
    }
    return ProcessResult(
        rows=rows,
        perf=perf,
        preflight_excs=preflight_excs,
        ticket_issues=ticket_issues,
        issue_log=issue_log,
        page_analysis=page_analysis,
        thumbnail_log=thumbnail_log,
    )


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
    """Save ``img`` to the configured image directory and return its path."""
    base_output = cfg.get("output_dir", "./outputs")
    _validate_path(base_output)
    out_dir = Path(base_output) / "images" / "page"
    # Validate the output directory to prevent path traversal
    _validate_path(str(out_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    if ticket_number:
        v = vendor or "unknown"
        v = re.sub(r"\W+", "_", v).strip("_")
        t = re.sub(r"\W+", "_", str(ticket_number)).strip("_")
        base_name = f"{t}_{v}_{idx + 1:03d}"
    else:
        # Sanitize PDF filename to prevent path traversal
        safe_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(pdf_path).stem)
        base_name = f"{safe_stem}_{idx + 1:03d}"
    out_path = out_dir / f"{base_name}.png"
    # Validate the output path to prevent path traversal
    _validate_path(str(out_path), base_dir=str(out_dir))
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
    if not roi:
        raise ValueError("ROI cannot be empty")
    base_output = cfg.get("output_dir", "./outputs")
    _validate_path(base_output)
    # Sanitize roi_type to prevent path traversal
    safe_roi_type = re.sub(r'[^a-zA-Z0-9_-]', '_', roi_type)
    out_dir = Path(base_output) / "images" / safe_roi_type
    out_dir.mkdir(parents=True, exist_ok=True)
    if ticket_number:
        v = vendor or "unknown"
        v = re.sub(r"\W+", "_", v).strip("_")
        t = re.sub(r"\W+", "_", str(ticket_number)).strip("_")
        base_name = f"{t}_{v}_{idx + 1:03d}_{safe_roi_type}"
    else:
        # Sanitize PDF filename to prevent path traversal
        safe_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(pdf_path).stem)
        base_name = f"{safe_stem}_{idx + 1:03d}_{safe_roi_type}"
    width, height = img.size
    if roi and max(roi) <= 1:
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
    # Validate the output path to prevent path traversal
    _validate_path(str(out_path), base_dir=str(out_dir))
    return str(out_path)


def _get_corrected_pdf_path(pdf_path: str, cfg: dict) -> str | None:
    """Return the output path for the corrected PDF for ``pdf_path``."""
    base = cfg.get("corrected_pdf_path")
    if not base:
        return None
    _validate_path(base)
    _validate_path(pdf_path)  # Validate input path to prevent traversal
    base_p = Path(base)
    # Sanitize the PDF filename to prevent path traversal
    safe_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(pdf_path).stem)
    if base_p.suffix.lower() == ".pdf":
        if cfg.get("batch_mode"):
            return str(base_p.parent / f"{base_p.stem}_{safe_stem}.pdf")
        return str(base_p)
    base_p.mkdir(parents=True, exist_ok=True)
    return str(base_p / f"{safe_stem}_corrected.pdf")


def _write_performance_log(records: List[Dict], cfg: dict) -> None:
    """Save performance metrics to ``performance_log.csv`` in ``output_dir``."""
    if not records:
        return
    out_dir = cfg.get("output_dir", "./outputs")
    _validate_path(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "performance_log.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "pages", "duration_sec"])
        writer.writeheader()
        writer.writerows(records)
    logging.info("Performance log written to %s", _sanitize_for_log(path))


def _append_hash_db(rows: List[Dict], cfg: dict) -> None:
    """Append page hashes to the hash database CSV."""
    path = cfg.get("hash_db_csv")
    if not path:
        return
    try:
        _validate_path(path)  # Validate path to prevent traversal
        df = DataFrame(rows)
        if df.empty:
            return
        parent_dir = os.path.dirname(path)
        if parent_dir:
            _validate_path(parent_dir)
            os.makedirs(parent_dir, exist_ok=True)
        path_exists = os.path.exists(path)
        mode = "a" if path_exists else "w"
        header = not path_exists
        columns = ["page_hash", "vendor", "ticket_number", "manifest_number", "file", "page"]
        df[columns].to_csv(path, mode=mode, header=header, index=False)
        logging.info("Hash DB updated: %s", _sanitize_for_log(path))
    except (IOError, OSError, PermissionError) as e:
        logging.error("Failed to update hash DB %s: %s", _sanitize_for_log(path), _sanitize_for_log(str(e)))
    except Exception as e:
        logging.error("Unexpected error updating hash DB: %s", _sanitize_for_log(str(e)))


def _validate_with_hash_db(rows: List[Dict], cfg: dict) -> None:
    """Validate pages against the stored hash database."""
    path = cfg.get("hash_db_csv")
    out_path = cfg.get("validation_output_csv", "validation_mismatches.csv")
    if not path or not os.path.exists(path):
        logging.warning("Hash DB not found for validation run")
        return
    try:
        # Validate both input and output paths to prevent traversal
        _validate_path(path)
        _validate_path(out_path)
        df_ref = read_csv(path)
        df_new = DataFrame(rows)
    except Exception as e:
        logging.error("Validation setup failed: %s", _sanitize_for_log(str(e)))
        return
    merged = df_new.merge(
        df_ref,
        on=["vendor", "ticket_number"],
        suffixes=("_new", "_ref"),
        how="left",
    )
    merged["hash_match"] = merged["page_hash_new"] == merged["page_hash_ref"]
    mismatches = merged[(~merged["hash_match"]) | (merged["page_hash_ref"].isna())]
    try:
        parent_dir = os.path.dirname(out_path)
        if parent_dir:
            _validate_path(parent_dir)
            os.makedirs(parent_dir, exist_ok=True)
        # Validate output path to prevent traversal
        safe_out_path = _validate_path(out_path)
        mismatches.to_csv(safe_out_path, index=False)
        logging.info("Validation results written to %s", _sanitize_for_log(str(safe_out_path)))
    except Exception as e:
        logging.error("Failed to write validation results: %s", _sanitize_for_log(str(e)))


def _load_pipeline_config(config_path: str | Path | None):
    """Load and prepare pipeline configuration."""
    # Load main config - uses packaged resource if config_path is None
    if config_path:
        _validate_path(str(config_path))  # Validate path to prevent traversal
    cfg = load_config(str(config_path) if config_path else None)
    cfg = resolve_input(cfg)

    # Load extraction rules - use packaged resource if not specified
    extraction_rules_path = cfg.get("extraction_rules_yaml")
    if extraction_rules_path:
        extraction_rules = load_extraction_rules(extraction_rules_path)
    else:
        extraction_rules = load_extraction_rules()  # Uses packaged resource

    # Load vendor rules - use packaged resource if not specified
    vendor_csv_path = cfg.get("vendor_keywords_csv")
    if vendor_csv_path:
        vendor_rules = load_vendor_rules_from_csv(vendor_csv_path)
    else:
        try:
            vendor_rules = load_vendor_rules_from_csv(str(get_config_path("ocr_keywords.csv")))
        except FileNotFoundError:
            # Fallback to legacy path for backward compatibility
            vendor_rules = load_vendor_rules_from_csv(str(CONFIG_DIR / "ocr_keywords.csv"))

    output_format = cfg.get("output_format", ["csv"])
    output_handlers = create_handlers(output_format, cfg)
    return cfg, extraction_rules, vendor_rules, output_handlers


def _get_input_files(cfg: dict):
    """Get list of input files based on configuration."""
    try:
        if cfg.get("batch_mode"):
            input_dir = cfg.get("input_dir")
            if not input_dir:
                raise KeyError("input_dir required for batch mode")
            _validate_path(input_dir)
            path = Path(input_dir).resolve()
            if not path.exists():
                raise FileNotFoundError(f"Input directory not found: {input_dir}")

            # Collect all supported file types
            files = []
            for pattern in ["*.pdf", "*.tif", "*.tiff", "*.jpg", "*.jpeg", "*.png"]:
                files.extend(path.glob(pattern))

            if not files:
                logging.warning("No supported files found in directory: %s", input_dir)
                return []

            return sorted(str(p) for p in files)

        input_pdf = cfg.get("input_pdf")
        if not input_pdf:
            raise KeyError("input_pdf required for single file mode")
        _validate_path(input_pdf)
        return [input_pdf]
    except KeyError as e:
        raise ValueError(f"Missing required configuration: {e}") from e


def _process_files(tasks: list, cfg: dict):
    """Process files sequentially to avoid serialization issues."""
    # Disable parallel processing to avoid pickle serialization errors
    return [_proc(t) for t in tqdm(tasks, desc="Files", total=len(tasks))]


def _aggregate_results(tasks: list, results: list):
    """Aggregate processing results from all files."""
    all_rows = []
    perf_records = []
    ticket_issues = []
    issues_log = []
    analysis_records = []
    preflight_exceptions = []

    for (f, *_), res in zip(tasks, results):
        rows, perf, pf_exc, t_issues, i_log, analysis, thumbs = res
        perf_records.append(perf)
        all_rows.extend(rows)
        ticket_issues.extend(t_issues)
        issues_log.extend(i_log)
        analysis_records.extend(analysis)
        preflight_exceptions.extend(pf_exc)
    return all_rows, preflight_exceptions


def run_pipeline(config_path: str | Path | None = None) -> None:
    """Execute the OCR pipeline using ``config_path`` configuration."""
    cfg, extraction_rules, vendor_rules, output_handlers = _load_pipeline_config(config_path)
    files = _get_input_files(cfg)
    tasks = [(f, cfg, vendor_rules, extraction_rules) for f in files]
    results = _process_files(tasks, cfg)
    all_rows, preflight_exceptions = _aggregate_results(tasks, results)

    for handler in output_handlers:
        handler.write(all_rows, cfg)

    reporting_utils.create_reports(all_rows, cfg)
    reporting_utils.export_preflight_exceptions(preflight_exceptions, cfg)
    reporting_utils.export_log_reports(cfg)

    if cfg.get("run_type", "initial") == "validation":
        _validate_with_hash_db(all_rows, cfg)


def main() -> None:
    """CLI entry point for running the OCR pipeline."""
    import argparse
    parser = argparse.ArgumentParser(description="OCR pipeline")
    parser.add_argument("--config", help="Path to config file")

    args = parser.parse_args()

    try:
        run_pipeline(args.config)
    except (FileNotFoundError, ValueError, OSError) as e:
        logging.error("Pipeline failed: %s", _sanitize_for_log(str(e)))
        raise SystemExit(1) from e
    except KeyboardInterrupt:
        logging.info("Pipeline interrupted by user")
        raise SystemExit(130) from None
    except Exception as e:
        logging.exception("Unexpected error in pipeline: %s", _sanitize_for_log(str(e)))
        raise SystemExit(2) from e


if __name__ == "__main__":
    main()
