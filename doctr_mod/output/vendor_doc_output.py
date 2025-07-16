"""Vendor document output handler."""

from typing import List, Dict, Any
import os
from pathlib import Path
from PIL import Image
from PyPDF2 import PdfMerger

from .base import OutputHandler
from processor.filename_utils import (
    format_output_filename_camel,
    format_output_filename,
    format_output_filename_lower,
    format_output_filename_snake,
    parse_input_filename_fuzzy,
)


class VendorDocumentOutput(OutputHandler):
    """Group page images by vendor and export a multi-page PDF or TIFF."""

    def __init__(self, fmt: str = "pdf"):
        self.fmt = fmt.lower()

    def write(self, rows: List[Dict[str, Any]], cfg: dict) -> None:
        out_dir = os.path.join(cfg.get("output_dir", "./outputs"), "vendor_docs")
        os.makedirs(out_dir, exist_ok=True)

        vendor_map: Dict[str, List[str]] = {}
        for row in rows:
            vendor = row.get("vendor") or "unknown"
            vendor_map.setdefault(vendor, []).append(row.get("image_path"))

        file_meta = None
        if rows:
            file_meta = parse_input_filename_fuzzy(rows[0].get("file", ""))

        format_style = cfg.get("file_format", "camel").lower()
        format_func = {
            "camel": format_output_filename_camel,
            "caps": format_output_filename,
            "lower": format_output_filename_lower,
            "snake": format_output_filename_snake,
        }.get(format_style, format_output_filename_camel)

        pdf_paths = []
        for vendor, paths in vendor_map.items():
            images = [Image.open(p).convert("RGB") for p in paths if p and os.path.isfile(p)]
            if not images:
                continue

            out_name = format_func(vendor, len(images), file_meta or {}, self.fmt)
            outfile = os.path.join(out_dir, out_name)

            if self.fmt == "tiff":
                images[0].save(outfile, save_all=True, append_images=images[1:])
            else:  # pdf
                images[0].save(outfile, save_all=True, append_images=images[1:], format="PDF")
                pdf_paths.append(outfile)

        if self.fmt == "pdf" and cfg.get("combined_pdf", False) and pdf_paths:
            combined_name = format_func("combined", sum(len(v) for v in vendor_map.values()), file_meta or {}, self.fmt)
            combined_path = os.path.join(out_dir, combined_name)
            merger = PdfMerger()
            for p in pdf_paths:
                merger.append(Path(p))
            with open(combined_path, "wb") as f:
                merger.write(f)
            merger.close()
