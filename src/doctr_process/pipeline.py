# Unified OCR pipeline entry point.

from __future__ import annotations

import csv
import io
import logging
import os
import re
import time
from pathlib import Path
from typing import List, Dict, Tuple, NamedTuple

import fitz  # PyMuPDF
from PIL import Image
from numpy import ndarray
from pandas import DataFrame, read_csv
from tqdm import tqdm

from doctr_process.ocr import reporting_utils
from doctr_process.ocr.config_utils import count_total_pages
from doctr_process.ocr.config_utils import load_config
from doctr_process.ocr.config_utils import load_extraction_rules
from doctr_process.ocr.input_picker import resolve_input
from doctr_process.ocr.ocr_engine import get_engine
from doctr_process.ocr.ocr_utils import (
    extract_images_generator,
    correct_image_orientation,
    get_image_hash,
    roi_has_digits,
    save_crop_and_thumbnail,
)
from ocr.preflight import run_preflight
from ocr.vendor_utils import (
    load_vendor_rules_from_csv,
    find_vendor,
    extract_vendor_fields,
    FIELDS,
)
from output.factory import create_handlers
from path_utils import normalize_single_path, guard_call

try:
    from doctr_process.logging_setup import setup_logging as _setup_logging
except ModuleNotFoundError:
    pass  # Logging setup is optional or handled elsewhere

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
    normalized = os.path.normpath(path)
    if '..' in normalized:
        raise ValueError(f"Invalid path detected: {path}")
    if base_dir:
        base_abs = os.path.abspath(base_dir)
        path_abs = os.path.abspath(os.path.join(base_dir, normalized))
        if not path_abs.startswith(base_abs):
            raise ValueError(f"Path outside base directory: {path}")
    return normalized


def _setup_corrected_pdf(pdf_str: str, cfg: dict):
    """Setup corrected PDF document if needed."""
    if not cfg.get("save_corrected_pdf"):
        return None, None
    corrected_pdf_path = _get_corrected_pdf_path(pdf_str, cfg)
    if corrected_pdf_path:
        parent_dir = os.path.dirname(corrected_pdf_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        return fitz.open(), corrected_pdf_path
    return None, None


def _process_page_ocr(img, engine, page_num: int, corrected_doc):
    """Process OCR for a single page."""
    if corrected_doc is not None:
        page_pdf = corrected_doc.new_page(width=img.width, height=img.height)
        rgb = img.convert("RGB")
        with io.BytesIO() as bio:
            rgb.save(bio, format="PNG", optimize=True)
            page_pdf.insert_image(fitz.Rect(0, 0, img.width, img.height), stream=bio.getvalue())
    
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
        if cfg.get("save_corrected_pdf"):
            corrected_pdf_path = _get_corrected_pdf_path(pdf_str, cfg)
            if corrected_pdf_path:
                parent_dir = os.path.dirname(corrected_pdf_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                corrected_doc = fitz.open()
        return corrected_doc, corrected_pdf_path

    def _process_single_page(
        i, page, skip_pages, engine, orient_method, corrected_doc, pdf_str, vendor_rules, extraction_rules, cfg, draw_roi, thumbnail_log
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

        if corrected_doc is not None:
            page_pdf = corrected_doc.new_page(width=img.width, height=img.height)
            rect = fitz.Rect(0, 0, img.width, img.height)
            rgb = img.convert("RGB")
            with io.BytesIO() as bio:
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
                    base = f"{Path(pdf_path).stem}_{page_num:03d}_{fname}"
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

    pdf_path = normalize_single_path(pdf_path)
    logging.debug("process_file path=%s type=%s", pdf_path, type(pdf_path).__name__)
    pdf_str = str(pdf_path)
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

    skip_pages, preflight_excs = guard_call("run_preflight", run_preflight, pdf_str, cfg)

    ext = os.path.splitext(pdf_str)[1].lower()
    logging.info("Extracting images from: %s (ext: %s)", _sanitize_for_log(pdf_str), _sanitize_for_log(ext))
    images = guard_call(
        "extract_images_generator", extract_images_generator, pdf_str, cfg.get("poppler_path"), cfg.get("dpi", 300)
    )
    logging.info("Starting OCR processing for %d pages...", total_pages)

    start = time.perf_counter()
    for i, page in enumerate(
            tqdm(images, total=total_pages, desc=os.path.basename(pdf_str), unit="page")
    ):
        result = _process_single_page(
            i, page, skip_pages, engine, orient_method, corrected_doc, pdf_str, vendor_rules, extraction_rules, cfg, draw_roi, thumbnail_log
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
        logging.debug("Could not clear images list: %s", e)
    try:
        del images
    except (NameError, UnboundLocalError) as e:
        logging.debug("Could not delete images: %s", e)

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
        "file": os.path.basename(pdf_str),
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
        base_name = f"{Path(pdf_path).stem}_{idx + 1:03d}"
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
        base_name = f"{Path(pdf_path).stem}_{idx + 1:03d}_{safe_roi_type}"
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
    df = DataFrame(rows)
    if df.empty:
        return
    parent_dir = os.path.dirname(path)
    if parent_dir:
        _validate_path(parent_dir)
        os.makedirs(parent_dir, exist_ok=True)
    mode = "a" if os.path.exists(path) else "w"
    header = not os.path.exists(path)
    columns = ["page_hash", "vendor", "ticket_number", "manifest_number", "file", "page"]
    df[columns].to_csv(path, mode=mode, header=header, index=False)
    logging.info("Hash DB updated: %s", _sanitize_for_log(path))


def _validate_with_hash_db(rows: List[Dict], cfg: dict) -> None:
    """Validate pages against the stored hash database."""
    path = cfg.get("hash_db_csv")
    out_path = cfg.get("validation_output_csv", "validation_mismatches.csv")
    if not path or not os.path.exists(path):
        logging.warning("Hash DB not found for validation run")
        return
    _validate_path(out_path)
    df_ref = read_csv(path)
    df_new = DataFrame(rows)
    merged = df_new.merge(
        df_ref,
        on=["vendor", "ticket_number"],
        suffixes=("_new", "_ref"),
        how="left",
    )
    merged["hash_match"] = merged["page_hash_new"] == merged["page_hash_ref"]
    mismatches = merged[(~merged["hash_match"]) | (merged["page_hash_ref"].isna())]
    parent_dir = os.path.dirname(out_path)
    if parent_dir:
        _validate_path(parent_dir)
        os.makedirs(parent_dir, exist_ok=True)
    mismatches.to_csv(out_path, index=False)
    logging.info("Validation results written to %s", _sanitize_for_log(out_path))


def _load_pipeline_config(config_path: str | Path | None):
    """Load and prepare pipeline configuration."""
    if config_path is None:
        config_path = CONFIG_DIR / "config.yaml"
    cfg = load_config(str(config_path))
    cfg = resolve_input(cfg)
    extraction_rules = load_extraction_rules(cfg.get("extraction_rules_yaml", str(CONFIG_DIR / "extraction_rules.yaml")))
    vendor_rules = load_vendor_rules_from_csv(cfg.get("vendor_keywords_csv", str(CONFIG_DIR / "ocr_keywords.csv")))
    output_handlers = create_handlers(cfg.get("output_format", ["csv"]), cfg)
    return cfg, extraction_rules, vendor_rules, output_handlers


def _get_input_files(cfg: dict):
    """Get list of input files based on configuration."""
    if cfg.get("batch_mode"):
        path = Path(cfg["input_dir"])
        return sorted(str(p) for p in path.glob("*.pdf"))
    return [cfg["input_pdf"]]


def _process_files(tasks: list, cfg: dict):
    """Process files either in parallel or sequentially."""
    if cfg.get("parallel"):
        from multiprocessing import Pool
        with Pool(cfg.get("num_workers", os.cpu_count())) as pool:
            results = []
            with tqdm(total=len(tasks), desc="Files") as pbar:
                for res in pool.imap(_proc, tasks):
                    results.append(res)
                    pbar.update()
        return results
    return [_proc(t) for t in tqdm(tasks, desc="Files", total=len(tasks))]


def _aggregate_results(tasks: list, results: list):
    """Aggregate processing results from all files."""
    all_rows, perf_records, ticket_issues, issues_log, analysis_records, preflight_exceptions = [], [], [], [], [], []
    for (f, *_), res in zip(tasks, results):
        rows, perf, pf_exc, t_issues, i_log, analysis, thumbs = res
        perf_records.append(perf)
        all_rows.extend(rows)
        ticket_issues.extend(t_issues)
        issues_log.extend(i_log)
        analysis_records.extend(analysis)
        preflight_exceptions.extend(pf_exc)
    return all_rows, preflight_exceptions


def _generate_artifact_summary(cfg: dict) -> None:
    """Generate a summary of all artifacts produced by the pipeline."""
    output_dir = Path(cfg.get("output_dir", "./outputs"))
    summary_path = output_dir / "artifact_summary.json"
    
    artifacts = cfg.get('generated_artifacts', [])
    vendor_artifacts = cfg.get('vendor_artifacts', [])
    
    # Scan for generated files
    file_artifacts = []
    if output_dir.exists():
        for pattern in ["*.csv", "*.xlsx", "*.pdf"]:
            for file_path in output_dir.rglob(pattern):
                file_artifacts.append({
                    'type': 'file',
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': file_path.stat().st_size if file_path.exists() else 0,
                    'category': _classify_artifact(file_path.name)
                })
    
    summary = {
        'pipeline_completed': datetime.now().isoformat(),
        'output_directory': str(output_dir),
        'total_artifacts': len(artifacts) + len(vendor_artifacts) + len(file_artifacts),
        'artifacts': artifacts,
        'vendor_artifacts': vendor_artifacts,
        'file_artifacts': file_artifacts
    }
    
    try:
        import json
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logging.info("Generated artifact summary: %s", summary_path)
    except Exception as e:
        logging.error("Failed to generate artifact summary: %s", str(e))


def _classify_artifact(filename: str) -> str:
    """Classify artifact by filename pattern."""
    filename_lower = filename.lower()
    if 'management_report' in filename_lower:
        return 'management_report'
    elif 'combined' in filename_lower and filename_lower.endswith('.pdf'):
        return 'combined_pdf'
    elif filename_lower.endswith('.csv'):
        return 'data_export'
    elif filename_lower.endswith('.xlsx'):
        return 'excel_report'
    elif filename_lower.endswith('.pdf'):
        return 'vendor_document'
    else:
        return 'other'


def run_pipeline(config_path: str | Path | None = None) -> None:
    """Execute the OCR pipeline using ``config_path`` configuration."""
    cfg, extraction_rules, vendor_rules, output_handlers = _load_pipeline_config(config_path)
    files = _get_input_files(cfg)
    tasks = [(f, cfg, vendor_rules, extraction_rules) for f in files]
    results = _process_files(tasks, cfg)
    all_rows, preflight_exceptions = _aggregate_results(tasks, results)
    
    # Initialize artifact tracking
    cfg.setdefault('generated_artifacts', [])
    
    # Generate output files using handlers
    for handler in output_handlers:
        try:
            handler.write(all_rows, cfg)
            logging.info("Completed output handler: %s", handler.__class__.__name__)
        except Exception as e:
            logging.error("Output handler %s failed: %s", handler.__class__.__name__, str(e))
            # Continue with other handlers rather than failing completely
    
    # Generate all reports
    try:
        reporting_utils.create_reports(all_rows, cfg)
        logging.info("Generated standard reports")
    except Exception as e:
        logging.error("Failed to create reports: %s", str(e))
    
    try:
        reporting_utils.export_preflight_exceptions(preflight_exceptions, cfg)
        logging.info("Exported preflight exceptions")
    except Exception as e:
        logging.error("Failed to export preflight exceptions: %s", str(e))
    
    try:
        reporting_utils.export_log_reports(cfg)
        logging.info("Exported log reports")
    except Exception as e:
        logging.error("Failed to export log reports: %s", str(e))
    
    # Generate final artifact summary
    _generate_artifact_summary(cfg)
    
    if cfg.get("run_type", "initial") == "validation":
        _validate_with_hash_db(all_rows, cfg)


def main() -> None:
    """CLI entry point for running the OCR pipeline."""
    try:
        run_pipeline()
    except (FileNotFoundError, ValueError, OSError) as e:
        logging.error("Pipeline failed: %s", _sanitize_for_log(str(e)))
        raise SystemExit(1) from e
    except Exception as e:
        logging.exception("Unexpected error in pipeline: %s", _sanitize_for_log(str(e)))
        raise SystemExit(2) from e


if __name__ == "__main__":
    main()
