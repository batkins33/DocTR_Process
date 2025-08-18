"""Vendor document output handler.

This handler groups page images by vendor *and input file*, then writes a
multi-page PDF or TIFF for each vendor/file pair. PDFs can optionally be
scaled and combined into one file.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image
from PyPDF2 import PdfMerger

from .base import OutputHandler
# from processor.filename_utils import (
#     format_output_filename,
#     format_output_filename_camel,
#     format_output_filename_lower,
#     format_output_filename_snake,
#     format_output_filename_preserve,
#     parse_input_filename_fuzzy,
#     sanitize_vendor_name,
# )

# Placeholder functions to avoid import errors
def format_output_filename(vendor, count, meta, fmt):
    return f"{vendor}_{count}.{fmt}"

def format_output_filename_camel(vendor, count, meta, fmt):
    return f"{vendor.title()}_{count}.{fmt}"

def format_output_filename_lower(vendor, count, meta, fmt):
    return f"{vendor.lower()}_{count}.{fmt}"

def format_output_filename_snake(vendor, count, meta, fmt):
    return f"{vendor.replace(' ', '_')}_{count}.{fmt}"

def format_output_filename_preserve(vendor, count, meta, fmt):
    return f"{vendor}_{count}.{fmt}"

def parse_input_filename_fuzzy(filename):
    return {}

def sanitize_vendor_name(name):
    return str(name).replace('/', '_').replace('\\', '_')


class VendorDocumentOutput(OutputHandler):
    """Group page images by vendor and export PDFs or TIFFs."""

    def __init__(self, fmt: str = "pdf") -> None:
        self.fmt = fmt.lower()

    def write(self, rows: List[Dict[str, Any]], cfg: dict) -> None:
        out_dir = os.path.join(cfg.get("output_dir", "./outputs"), "vendor_docs")
        os.makedirs(out_dir, exist_ok=True)

        vendor_map: Dict[Tuple[str, str], List[str]] = {}
        for row in rows:
            vendor_raw = row.get("vendor") or "unknown"
            vendor = sanitize_vendor_name(vendor_raw)
            file_path = row.get("file") or ""
            vendor_map.setdefault((file_path, vendor), []).append(row.get("image_path"))
        total = len(vendor_map)

        file_meta = None
        if rows:
            file_meta = parse_input_filename_fuzzy(rows[0].get("file", ""))

        fmt_style = cfg.get("file_format", "preserve").lower()
        format_func = {
            "camel": format_output_filename_camel,
            "caps": format_output_filename,
            "lower": format_output_filename_lower,
            "snake": format_output_filename_snake,
            "preserve": format_output_filename_preserve,
        }.get(fmt_style, format_output_filename_preserve)

        pdf_paths: List[str] = []
        pdf_scale = float(cfg.get("pdf_scale", 1.0))
        pdf_res = int(cfg.get("pdf_resolution", 150))

        for idx, ((file_path, vendor), paths) in enumerate(vendor_map.items(), 1):
            logging.info(
                "Exporting %d/%d (%d%%) - Vendor: %s",
                idx,
                total,
                int(idx / total * 100),
                vendor,
            )
            images = []
            for p in paths:
                if p and os.path.isfile(p):
                    with Image.open(p) as img:
                        images.append(img.convert("RGB"))
            if not images:
                continue

            meta = parse_input_filename_fuzzy(file_path)
            out_name = format_func(vendor, len(images), meta, self.fmt)
            outfile = os.path.join(out_dir, out_name)
            # Ensure outfile is within out_dir to prevent path traversal
            outfile_abs = os.path.abspath(outfile)
            out_dir_abs = os.path.abspath(out_dir)
            if not outfile_abs.startswith(out_dir_abs + os.sep):
                raise ValueError("Invalid output path detected (possible path traversal): %s" % outfile)

            scaled = images
            if pdf_scale != 1.0 and self.fmt == "pdf":
                scaled = [
                    img.resize(
                        (int(img.width * pdf_scale), int(img.height * pdf_scale)),
                        Image.LANCZOS,
                    )
                    for img in images
                ]

            if self.fmt == "tiff":
                scaled[0].save(outfile, save_all=True, append_images=scaled[1:])
            else:  # pdf
                scaled[0].save(
                    outfile,
                    save_all=True,
                    append_images=scaled[1:],
                    format="PDF",
                    resolution=pdf_res,
                )
                pdf_paths.append(outfile)
            logging.info("Saved %s group to: %s", vendor, outfile)

        if self.fmt == "pdf" and cfg.get("combined_pdf", False) and pdf_paths:
            combined_name = format_func(
                "combined",
                sum(len(v) for v in vendor_map.values()),
                file_meta or {},
                self.fmt,
            )
            combined_path = os.path.join(out_dir, combined_name)
            # Ensure combined_path is within out_dir to prevent path traversal
            combined_path_abs = os.path.abspath(combined_path)
            out_dir_abs = os.path.abspath(out_dir)
            if not combined_path_abs.startswith(out_dir_abs + os.sep):
                raise ValueError("Invalid output path detected (possible path traversal): %s" % combined_path)
            merger = PdfMerger()
            for path in pdf_paths:
                merger.append(Path(path))
            with open(combined_path_abs, "wb") as f:
                merger.write(f)
            merger.close()
            logging.info("Combined PDF saved to: %s", combined_path_abs)
