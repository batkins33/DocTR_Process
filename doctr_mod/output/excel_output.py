"""Excel log output handler."""

from typing import List, Dict, Any
import os
from openpyxl import Workbook
from .base import OutputHandler


class ExcelOutput(OutputHandler):
    """Write extracted rows to an Excel workbook."""

    def __init__(self, filename: str = "log.xlsx"):
        self.filename = filename

    def write(self, rows: List[Dict[str, Any]], cfg: dict) -> None:
        if not rows:
            return
        out_dir = cfg.get("output_dir", "./outputs")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, self.filename)
        wb = Workbook()
        ws = wb.active
        headers = list(rows[0].keys())
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h) for h in headers])
        wb.save(path)
