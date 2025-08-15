"""CSV output handler."""

import csv
import logging
import os
from typing import List, Dict, Any

from .base import OutputHandler


class CSVOutput(OutputHandler):
    """Write extracted rows to a CSV file."""

    def __init__(self, filename: str = "output.csv"):
        # Only allow basename, disallow directory traversal
        self.filename = os.path.basename(filename)

    def write(self, rows: List[Dict[str, Any]], cfg: dict) -> None:
        """Write rows to a CSV file while preserving column order.

        Keys from all rows are scanned in the order they are first encountered
        to build the list of field names. This guarantees that columns in the
        resulting CSV appear in the same order that keys are introduced across
        the input rows, with new keys appended as they appear. It also prevents
        ``DictWriter`` errors when some rows contain additional fields.
        """
        out_dir = cfg.get("output_dir", "./outputs")
        out_dir_abs = os.path.abspath(out_dir)
        # Ensure output directory exists
        os.makedirs(out_dir_abs, exist_ok=True)
        path = os.path.abspath(os.path.join(out_dir_abs, self.filename))
        # Prevent path traversal by ensuring the file is inside out_dir using os.path.commonpath
        if os.path.commonpath([out_dir_abs, path]) != out_dir_abs or not path.startswith(out_dir_abs + os.sep):
            raise ValueError("Invalid filename: Path traversal detected.")
        if not rows:
            return
        # Collect all field names across rows in encounter order to avoid
        # ``DictWriter`` errors and to maintain the column order guarantee.
        fieldnames: List[str] = []
        for row in rows:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logging.info("OCR text log saved: %s", path)
