"""Excel log output handler."""

import logging
import os
from typing import Any

from openpyxl import Workbook

from doctr_process.output.base import OutputHandler


class ExcelOutput(OutputHandler):
    """Write extracted rows to an Excel workbook."""

    def __init__(self, filename: str = "log.xlsx"):
        self.filename = filename

    def write(self, rows: list[dict[str, Any]], cfg: dict) -> None:
        if not rows:
            return
        out_dir = os.path.abspath(cfg.get("output_dir", "./outputs"))
        os.makedirs(out_dir, exist_ok=True)
        # Validate filename to prevent path traversal
        safe_filename = os.path.basename(self.filename)
        path = os.path.join(out_dir, safe_filename)
        # Ensure path is within output directory
        if not os.path.abspath(path).startswith(out_dir + os.sep):
            raise ValueError(f"Invalid path: {path}")
        wb = Workbook()
        ws = wb.active
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h) for h in headers])
        wb.save(path)
        logging.info("Log saved to: %s", path)
