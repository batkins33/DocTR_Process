"""Unified OCR pipeline entry point."""

from pathlib import Path
from typing import List, Dict, Tuple
import logging
import time
import csv
import os

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
)
from doctr_ocr.ocr_utils import extract_images_generator, correct_image_orientation
from tqdm import tqdm
from output.factory import create_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,%(levelname)s,%(message)s",
    filename="error.log",
)


def process_file(
    pdf_path: str, cfg: dict, vendor_rules, extraction_rules
) -> Tuple[List[Dict], Dict]:
    """Process ``pdf_path`` and return rows and performance stats."""

    engine = get_engine(cfg.get("ocr_engine", "doctr"))
    rows: List[Dict] = []
    orient_method = cfg.get("orientation_check", "tesseract")
    total_pages = count_total_pages([pdf_path], cfg)
    start = time.perf_counter()

    for i, img in enumerate(
        tqdm(
            extract_images_generator(pdf_path, cfg.get("poppler_path")),
            total=total_pages,
            desc=os.path.basename(pdf_path),
            unit="page",
        )
    ):
        img = correct_image_orientation(img, i + 1, method=orient_method)
        text, result_page = engine(img)
        vendor_name, vendor_type, _ = find_vendor(text, vendor_rules)
        if result_page is not None:
            fields = extract_vendor_fields(result_page, vendor_name, extraction_rules)
        else:
            fields = {
                f: None
                for f in ["ticket_number", "manifest_number", "material_type", "truck_number", "date"]
            }
        row = {
            "file": pdf_path,
            "page": i + 1,
            "vendor": vendor_name,
            **fields,
            "image_path": save_page_image(img, pdf_path, i, cfg),
            "ocr_text": text,
        }
        rows.append(row)

    duration = time.perf_counter() - start
    perf = {
        "file": os.path.basename(pdf_path),
        "pages": total_pages,
        "duration_sec": round(duration, 2),
    }
    return rows, perf


def save_page_image(img, pdf_path: str, idx: int, cfg: dict) -> str:
    """Save ``img`` to the configured image directory and return its path."""
    out_dir = Path(cfg.get("output_dir", "./outputs")) / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{Path(pdf_path).stem}_{idx+1:03d}.png"
    img.save(out_path)
    return str(out_path)


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
    output_handlers = create_handlers(cfg.get("output_format", ["csv"]), cfg)

    if cfg.get("batch_mode"):
        path = Path(cfg["input_dir"])
        files = sorted(str(p) for p in path.glob("*.pdf"))
    else:
        files = [cfg["input_pdf"]]

    all_rows: List[Dict] = []
    perf_records: List[Dict] = []
    for idx, f in enumerate(files, 1):
        logging.info("Processing %s (%d/%d)", os.path.basename(f), idx, len(files))
        rows, perf = process_file(f, cfg, vendor_rules, extraction_rules)
        perf_records.append(perf)
        all_rows.extend(rows)

    for handler in output_handlers:
        handler.write(all_rows, cfg)

    if cfg.get("profile"):
        _write_performance_log(perf_records, cfg)


if __name__ == "__main__":
    run_pipeline()
