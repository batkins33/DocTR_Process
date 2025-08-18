from typing import List, Sequence

from doctr_process.output.base import OutputHandler
from doctr_process.output.csv_output import CSVOutput
from doctr_process.output.excel_output import ExcelOutput
from doctr_process.output.sharepoint_output import SharePointOutput
from doctr_process.output.vendor_doc_output import VendorDocumentOutput


def create_handlers(names: Sequence[str], cfg: dict) -> List[OutputHandler]:
    """Instantiate output handlers listed in ``names`` using ``cfg`` options."""
    handlers: List[OutputHandler] = []
    for name in names:
        if name == "csv":
            handlers.append(CSVOutput(cfg.get("csv_filename", "results.csv")))
        elif name == "excel":
            handlers.append(ExcelOutput(cfg.get("excel_filename", "log.xlsx")))
        elif name == "vendor_pdf":
            handlers.append(VendorDocumentOutput("pdf"))
        elif name == "vendor_tiff":
            handlers.append(VendorDocumentOutput("tiff"))
        elif name == "sharepoint":
            sp_cfg = cfg.get("sharepoint_config", {})
            handlers.append(
                SharePointOutput(
                    sp_cfg.get("site_url"),
                    sp_cfg.get("library"),
                    sp_cfg.get("folder"),
                    sp_cfg.get("credentials"),
                )
            )
    return handlers
