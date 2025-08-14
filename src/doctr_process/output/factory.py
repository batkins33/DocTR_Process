from typing import List

from .base import OutputHandler
from .csv_output import CSVOutput
from .excel_output import ExcelOutput
from .sharepoint_output import SharePointOutput
from .vendor_doc_output import VendorDocumentOutput


def create_handlers(cfg: dict, output_dir: str) -> List[OutputHandler]:
    """Instantiate output handlers based on config."""
    handlers = []
    names = cfg.get("output_format", [])
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
