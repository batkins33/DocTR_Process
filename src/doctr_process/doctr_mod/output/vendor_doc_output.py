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
from src.doctr_process.processor.filename_utils import (
    format_output_filename,
    format_output_filename_camel,
    format_output_filename_lower,
    format_output_filename_snake,
    format_output_filename_preserve,
    parse_input_filename_fuzzy,
    sanitize_vendor_name,
)


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
            images = [Image.open(p).convert("RGB") for p in paths if p and os.path.isfile(p)]
            if not images:
                continue

            meta = parse_input_filename_fuzzy(file_path)
            out_name = format_func(vendor, len(images), meta, self.fmt)
            outfile = os.path.join(out_dir, out_name)

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
                "combined", sum(len(v) for v in vendor_map.values()), file_meta or {}, self.fmt
            )
            combined_path = os.path.join(out_dir, combined_name)
            merger = PdfMerger()
            for path in pdf_paths:
                merger.append(Path(path))
            with open(combined_path, "wb") as f:
                merger.write(f)
            merger.close()
            logging.info("Combined PDF saved to: %s", combined_path)
