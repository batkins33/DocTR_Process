"""IO module for DocTR Process - handles file operations, configuration, and reporting."""

from .file_utils import zip_folder
from .input_picker import parse_args, pick_file_or_folder, resolve_input
from .config_utils import load_config, load_extraction_rules, count_total_pages
from .excel_utils import color_code_excel
from .reporting_utils import (
    export_logs_to_csv,
    export_logs_to_html,
    export_log_reports,
    get_manifest_validation_status,
    get_ticket_validation_status,
    create_reports,
    write_management_report,
    export_preflight_exceptions,
    export_issue_logs,
    export_process_analysis,
)

__all__ = [
    "zip_folder",
    "parse_args",
    "pick_file_or_folder", 
    "resolve_input",
    "load_config",
    "load_extraction_rules",
    "count_total_pages",
    "color_code_excel",
    "export_logs_to_csv",
    "export_logs_to_html",
    "export_log_reports", 
    "get_manifest_validation_status",
    "get_ticket_validation_status",
    "create_reports",
    "write_management_report",
    "export_preflight_exceptions",
    "export_issue_logs",
    "export_process_analysis",
]