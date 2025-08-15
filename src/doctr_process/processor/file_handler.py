"""Functions for writing logs and combined output artifacts."""

import io
import logging
import shutil
from pathlib import Path
from typing import Dict, List

import pandas as pd
import pytesseract
from PIL import Image
from PyPDF2 import PdfMerger
from src.doctr_process.processor.filename_utils import (
    format_output_filename,
    format_output_filename_camel,
    parse_input_filename_fuzzy,
    format_output_filename_lower,
    format_output_filename_snake,
)


def get_dynamic_paths(base_file: str, combined_name: str | None = None):
    """Return output, log and combined directories for ``base_file``."""
    source_dir = Path(base_file).parent
    if combined_name:
        base_stem = Path(combined_name).stem
    else:
        base_stem = Path(base_file).stem
    out_dir = source_dir / "processed" / base_stem / "Vendor"
    log_dir = source_dir / "logs" / base_stem
    combined_dir = source_dir / "processed" / base_stem / "Combined"
    return out_dir, log_dir, combined_dir


def write_excel_log(log_entries: List[Dict], base_name: str, log_dir: Path) -> None:
    """Write ``log_entries`` to an Excel file in ``log_dir``."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(log_entries)
    output_path = Path(log_dir) / f"{base_name}_log.xlsx"
    df.to_excel(output_path, index=False)
    logging.info(f"\U0001f4ca Log saved: {output_path}")


def export_grouped_output(
        pages_by_vendor: Dict[str, List[Image.Image]],
        output_format: str,
        file_metadata: Dict[str, str] | None,
        filepath: str | Path,
        config: Dict,
) -> List[str]:
    """Export grouped images by vendor to individual and combined documents."""
    output_paths: List[str] = []

    if not file_metadata:
        file_metadata = parse_input_filename_fuzzy(filepath)

    format_style = config.get("file_format", "camel").lower()
    format_func = {
        "camel": format_output_filename_camel,
        "caps": format_output_filename,
        "lower": format_output_filename_lower,
        "snake": format_output_filename_snake,
    }.get(format_style, format_output_filename_camel)

    total_pages = sum(len(imgs) for imgs in pages_by_vendor.values())
    base_meta = file_metadata.copy()
    combined_name = (
        format_func(
            vendor="",
            page_count=total_pages,
            meta=base_meta,
            output_format=output_format,
        )
        .replace("__", "_")
        .replace("._", ".")
    )

    out_dir, log_dir, combined_dir = get_dynamic_paths(filepath, combined_name)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    Path(combined_dir).mkdir(parents=True, exist_ok=True)

    total_vendors = len(pages_by_vendor)
    for i, (vendor, imgs) in enumerate(pages_by_vendor.items(), start=1):
        percent = int((i / total_vendors) * 100)
        logging.info(
            f"\U0001f4dd Exporting {i}/{total_vendors} ({percent}%) - Vendor: {vendor}"
        )

        vendor_dir = out_dir / vendor.upper()
        vendor_dir.mkdir(parents=True, exist_ok=True)

        out_name = format_func(vendor, len(imgs), file_metadata, output_format)
        out_path = vendor_dir / out_name

        if output_format == "tif":
            imgs[0].save(out_path, save_all=True, append_images=imgs[1:])
            output_paths.append(str(out_path))

        elif output_format == "pdf":
            merger = PdfMerger()
            for p in imgs:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(p, extension="pdf")
                merger.append(io.BytesIO(pdf_bytes))
            buffer = io.BytesIO()
            merger.write(buffer)
            merger.close()
            buffer.seek(0)
            with open(out_path, "wb") as f:
                f.write(buffer.read())
            output_paths.append(str(out_path))

        logging.info(f"\U0001f4c4 Saved {vendor} group to: {out_path}")

    if output_format == "pdf":
        combined_path = combined_dir / combined_name
        merger = PdfMerger()
        for pdf_path in output_paths:
            merger.append(Path(pdf_path))
        with open(combined_path, "wb") as f:
            merger.write(f)
        merger.close()
        logging.info(f"\U0001f4ce Combined PDF saved: {combined_path}")

    return output_paths


def archive_original(original_path: str) -> None:
    """Move ``original_path`` into an 'Original Scans' archive directory."""
    original_path_obj = Path(original_path)
    archive_dir = original_path_obj.parent / "Original Scans"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_path = archive_dir / original_path_obj.name
    try:
        shutil.move(str(original_path_obj), str(archive_path))
        logging.info(f"Moved original to archive: {archive_path}")
    except Exception as e:
        logging.warning(f"Failed to move original: {e}")
