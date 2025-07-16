"""Vendor document output handler."""

from typing import List, Dict, Any
import os
import logging
from PIL import Image
from .base import OutputHandler


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
        total = len(vendor_map)
        for idx, (vendor, paths) in enumerate(vendor_map.items(), 1):
            logging.info("📝 Exporting %d/%d (%d%%) - Vendor: %s", idx, total, int(idx / total * 100), vendor)
        pdf_scale = float(cfg.get("pdf_scale", 1.0))
        pdf_res = int(cfg.get("pdf_resolution", 150))

        for vendor, paths in vendor_map.items():
            images = [Image.open(p).convert("RGB") for p in paths if p and os.path.isfile(p)]
            if not images:
                continue

            if pdf_scale != 1.0 and self.fmt == "pdf":
                scaled = [img.resize((int(img.width * pdf_scale), int(img.height * pdf_scale)), Image.LANCZOS) for img in images]
            else:
                scaled = images

            outfile = os.path.join(out_dir, f"{vendor}.{self.fmt}")
            if self.fmt == "tiff":
                scaled[0].save(outfile, save_all=True, append_images=scaled[1:])
            else:  # pdf
                images[0].save(outfile, save_all=True, append_images=images[1:], format="PDF")
            logging.info("📄 Saved %s group to: %s", vendor, outfile)
                scaled[0].save(
                    outfile,
                    save_all=True,
                    append_images=scaled[1:],
                    format="PDF",
                    resolution=pdf_res,
                )
