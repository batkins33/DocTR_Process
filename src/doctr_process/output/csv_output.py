"""CSV output handler."""

import csv
import logging
import os
from typing import List, Dict, Any

from .base import OutputHandler


class CSVOutput(OutputHandler):
    """Write extracted rows to a CSV file."""

    def __init__(self, filename: str = "output.csv"):
        self.filename = filename

    def write(self, rows: List[Dict[str, Any]], cfg: dict) -> None:
        out_dir = cfg.get("output_dir", "./outputs")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, self.filename)
        if not rows:
            return
        # Collect all field names across rows to avoid ``DictWriter`` errors when
        # some rows contain additional keys. This preserves the order of keys as
        # they appear and appends unseen keys as they are encountered.
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
