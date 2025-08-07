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
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        logging.info("OCR text log saved: %s", path)
