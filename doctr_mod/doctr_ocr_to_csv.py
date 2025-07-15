"""Unified OCR pipeline entry point."""

from pathlib import Path
from typing import List, Dict

from doctr_ocr.config_utils import load_config, load_extraction_rules
from doctr_ocr.input_picker import resolve_input
from doctr_ocr.ocr_engine import get_engine
from doctr_ocr.vendor_utils import (
    load_vendor_rules_from_csv,
    find_vendor,
    extract_vendor_fields,
)
from doctr_ocr.ocr_utils import extract_images_generator, correct_image_orientation
from output.factory import create_handlers


def process_file(pdf_path: str, cfg: dict, vendor_rules, extraction_rules) -> List[Dict]:
    """Extract configured fields from ``pdf_path``.

    Returns a list of dictionaries containing the extracted values and the
    path to the saved page image.
    """
    engine = get_engine(cfg.get("ocr_engine", "doctr"))
    rows: List[Dict] = []
    orient_method = cfg.get("orientation_check", "tesseract")
    for i, img in enumerate(extract_images_generator(pdf_path, cfg.get("poppler_path"))):
        img = correct_image_orientation(img, i + 1, method=orient_method)
        text, result_page = engine(img)
        vendor_name, vendor_type, matched = find_vendor(text, vendor_rules)
        if result_page is not None:
            fields = extract_vendor_fields(result_page, vendor_name, extraction_rules)
        else:
            fields = {f: None for f in ["ticket_number", "manifest_number", "material_type", "truck_number", "date"]}
        row = {
            "file": pdf_path,
            "page": i + 1,
            "vendor": vendor_name,
            **fields,
            "image_path": save_page_image(img, pdf_path, i, cfg),
            "ocr_text": text,
        }
        rows.append(row)
    return rows


def save_page_image(img, pdf_path: str, idx: int, cfg: dict) -> str:
    """Save ``img`` to the configured image directory and return its path."""
    out_dir = Path(cfg.get("output_dir", "./outputs")) / "images"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{Path(pdf_path).stem}_{idx+1:03d}.png"
    img.save(out_path)
    return str(out_path)


def run_pipeline():
    """Execute the OCR pipeline using ``config.yaml``."""
    cfg = load_config()
    cfg = resolve_input(cfg)
    extraction_rules = load_extraction_rules(cfg.get("extraction_rules_yaml", "extraction_rules.yaml"))
    vendor_rules = load_vendor_rules_from_csv(cfg.get("vendor_keywords_csv", "ocr_keywords.csv"))
    output_handlers = create_handlers(cfg.get("output_format", ["csv"]), cfg)

    files = []
    if cfg.get("batch_mode"):
        path = Path(cfg["input_dir"])
        files = sorted(str(p) for p in path.glob("*.pdf"))
    else:
        files = [cfg["input_pdf"]]

    all_rows: List[Dict] = []
    for f in files:
        all_rows.extend(process_file(f, cfg, vendor_rules, extraction_rules))

    for handler in output_handlers:
        handler.write(all_rows, cfg)


if __name__ == "__main__":
    run_pipeline()
