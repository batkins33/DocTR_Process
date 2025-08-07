import csv
import html
import logging
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


REPORTING_CFG = {
    "branding_company_name": "Lindamood Demolition, Inc.",
    "branding_logo_path": str(Path(__file__).parent / "assets" / "branding" / "lindamood_logo.png"),
    "report_author": "B. Atkins",
    "script_version": "1.2.0",
    "mgmt_report_xlsx": True,
    "mgmt_report_pdf": True,
    "pdf_export": {"method": "auto"},
}

def _parse_log_line(line: str) -> List[str]:
    """Parse a log line produced by doctr_ocr_to_csv."""
    parts = line.strip().split(',', 4)
    if len(parts) < 5:
        # Fallback if message contains commas or format unexpected
        dt = parts[0] if parts else ''
        level = parts[1] if len(parts) > 1 else ''
        file = parts[2] if len(parts) > 2 else ''
        lineno = parts[3] if len(parts) > 3 else ''
        msg = parts[4] if len(parts) > 4 else line.strip()
        return [dt, level, file, lineno, msg]
    return parts[:5]


def export_logs_to_csv(log_file_path: str, output_csv_path: str) -> None:
    """Convert ``error.log`` to a structured CSV."""
    rows = []
    try:
        with open(log_file_path, encoding='utf-8') as f:
            for line in f:
                dt, level, file, lineno, msg = _parse_log_line(line)
                rows.append(
                    {
                        "datetime": dt,
                        "level": level,
                        "file": file,
                        "line": lineno,
                        "message": msg,
                    }
                )
    except FileNotFoundError:
        return

    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["datetime", "level", "file", "line", "message"],
        )
        writer.writeheader()
        writer.writerows(rows)


def export_logs_to_html(log_file_path: str, output_html_path: str) -> None:
    """Convert ``error.log`` to a simple HTML table."""
    try:
        with open(log_file_path, encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write("<html><body><table border='1'>")
        f.write(
            "<tr><th>DateTime</th><th>Level</th><th>File</th><th>Line</th><th>Message</th></tr>"
        )
        for line in lines:
            dt, level, file, lineno, msg = _parse_log_line(line)
            f.write("<tr>")
            f.write(f"<td>{html.escape(dt)}</td>")
            f.write(f"<td>{html.escape(level)}</td>")
            f.write(f"<td>{html.escape(file)}</td>")
            f.write(f"<td>{html.escape(lineno)}</td>")
            f.write(f"<td>{html.escape(msg)}</td>")
            f.write("</tr>")
        f.write("</table></body></html>")


def _report_path(cfg: Dict[str, Any], key: str, sub_path: str) -> str | None:
    """Resolve a report path from ``output_dir`` and ``key``."""
    val = cfg.get(key)
    if isinstance(val, bool) or val is None:
        if not val:
            return None
        base = Path(cfg.get("output_dir", "./outputs")) / "logs" / sub_path
        return str(base)
    return str(val)


def export_log_reports(cfg: Dict[str, Any]) -> None:
    """Export ``error.log`` to CSV/HTML if enabled in ``cfg``."""
    log_file = "error.log"
    csv_path = _report_path(cfg, "log_csv", "log_report.csv")
    if csv_path:
        Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
        export_logs_to_csv(log_file, csv_path)
    html_path = _report_path(cfg, "log_html", "log_report.html")
    if html_path:
        Path(html_path).parent.mkdir(parents=True, exist_ok=True)
        export_logs_to_html(log_file, html_path)


def get_manifest_validation_status(manifest_number: str | None) -> str:
    """Return validation status for a manifest number."""
    if not manifest_number:
        return "invalid"
    manifest_number = str(manifest_number)
    if re.fullmatch(r"14\d{6}", manifest_number):
        return "valid"
    if len(manifest_number) >= 7:
        return "review"
    return "invalid"


def get_ticket_validation_status(ticket_number: str | None) -> str:
    """Return validation status for a ticket number."""
    if not ticket_number:
        return "invalid"
    ticket_number = str(ticket_number)
    if re.fullmatch(r"\d+", ticket_number):
        return "valid"
    return "review"


def _parse_filename_metadata(file_path: str) -> Dict[str, str]:
    """Extract job related fields from an input ``file_path``.

    Filenames are expected to follow the pattern
    ``JobID_ServiceDate_Material_Source_Destination[_...]``.  A trailing
    ``_NNN`` segment (original page count) is stripped if present.  Missing
    segments yield empty strings.
    """

    stem = Path(file_path).stem
    stem = re.sub(r"_(\d+)$", "", stem)
    parts = stem.split("_")
    fields = ["JobID", "Service Date", "Material", "Source", "Destination"]
    meta = {k: "" for k in fields}
    for key, value in zip(fields, parts):
        meta[key] = value
    return meta


def _make_vendor_doc_path(
        file_path: str, vendor: str, page_count: int, cfg: Dict[str, Any]
) -> str:
    """Return the expected vendor document path for ``file_path`` and ``vendor``."""

    # Import formatting helpers lazily to avoid importing optional dependencies
    # such as PyPDF2 when this function isn't used.  This keeps modules that
    # merely import ``reporting_utils`` lightweight.
    from ..processor.filename_utils import (
        format_output_filename,
        format_output_filename_camel,
        format_output_filename_lower,
        format_output_filename_snake,
        format_output_filename_preserve,
        parse_input_filename_fuzzy,
        sanitize_vendor_name,
    )

    vendor_dir = Path(cfg.get("output_dir", "./outputs")) / "vendor_docs"
    fmt_style = cfg.get("file_format", "preserve").lower()
    format_func = {
        "camel": format_output_filename_camel,
        "caps": format_output_filename,
        "lower": format_output_filename_lower,
        "snake": format_output_filename_snake,
        "preserve": format_output_filename_preserve,
    }.get(fmt_style, format_output_filename_preserve)

    meta = parse_input_filename_fuzzy(file_path)
    vendor_clean = sanitize_vendor_name(vendor)
    fmt = cfg.get("vendor_doc_format", "pdf")
    out_name = format_func(vendor_clean, page_count, meta, fmt)
    return str(vendor_dir / out_name)


def create_reports(rows: List[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    """Write combined, deduped and summary CSV reports."""
    if not rows:
        return

    # Combined OCR dump
    out_path = _report_path(cfg, "output_csv", "ocr/combined_results.csv")
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        pd.DataFrame(rows).to_csv(out_path, index=False)

    df = pd.DataFrame(rows)
    df["ticket_valid"] = df["ticket_number"].apply(get_ticket_validation_status)
    df["manifest_valid"] = df["manifest_number"].apply(get_manifest_validation_status)

    # Page-level fields with validation
    page_fields_path = _report_path(cfg, "page_fields_csv", "ocr/page_fields.csv")
    if page_fields_path:
        os.makedirs(os.path.dirname(page_fields_path), exist_ok=True)
        df.to_csv(page_fields_path, index=False)

    # Mark duplicate tickets
    ticket_counts = df.groupby(["vendor", "ticket_number"]).size().rename("count")
    df = df.join(ticket_counts, on=["vendor", "ticket_number"])
    df["duplicate_ticket"] = df["count"] > 1

    ticket_numbers_path = _report_path(cfg, "ticket_numbers_csv", "ocr/combined_ticket_numbers.csv")
    if ticket_numbers_path:
        os.makedirs(os.path.dirname(ticket_numbers_path), exist_ok=True)
        df.drop(columns=["count"]).to_csv(ticket_numbers_path, index=False)

    condensed_path = _report_path(
        cfg,
        "ticket_numbers_condensed_csv",
        "ticket_number/condensed_ticket_numbers.csv",
    )
    if condensed_path:
        os.makedirs(os.path.dirname(condensed_path), exist_ok=True)
        condensed_records: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            meta = _parse_filename_metadata(row.get("file", ""))
            record = {
                **meta,
                "page": row.get("page"),
                "vendor": row.get("vendor"),
                "ticket_number": row.get("ticket_number"),
                "ticket_number_valid": row.get("ticket_valid"),
                "manifest_number": row.get("manifest_number"),
                "manifest_number_valid": row.get("manifest_valid"),
                "truck_number": row.get("truck_number"),
                "exception_reason": row.get("exception_reason"),
                "image_path": row.get("image_path"),
                "roi_image_path": row.get("roi_image_path"),
                "manifest_roi_image_path": row.get("manifest_roi_image_path"),
            }
            condensed_records.append(record)
        columns = [
            "JobID",
            "Service Date",
            "Material",
            "Source",
            "Destination",
            "page",
            "vendor",
            "ticket_number",
            "ticket_number_valid",
            "manifest_number",
            "manifest_number_valid",
            "truck_number",
            "exception_reason",
            "image_path",
            "roi_image_path",
        ]
        condensed_df = pd.DataFrame(condensed_records)
        condensed_df[columns].to_csv(condensed_path, index=False)
        excel_path = Path(condensed_path).with_suffix(".xlsx")
        condensed_df[columns].to_excel(excel_path, index=False)
        try:
            from openpyxl import load_workbook
            from openpyxl.styles import PatternFill

            wb = load_workbook(excel_path)
            ws = wb.active
            red = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            t_col = columns.index("ticket_number") + 1
            m_col = columns.index("manifest_number") + 1
            img_col = columns.index("image_path") + 1
            roi_col = columns.index("roi_image_path") + 1

            def _set_cell(row: int, col: int, value: Any, link: str | None = None, fill=None) -> None:
                """Populate ``ws`` cell ensuring fill is applied last."""
                c = ws.cell(row=row, column=col)
                c.value = value
                if link:
                    c.hyperlink = link
                    c.style = "Hyperlink"
                if fill is not None:
                    c.fill = fill

            for idx, rec in condensed_df.iterrows():
                r = idx + 2
                # Replace image path columns with filename hyperlinks
                img = rec.get("image_path")
                if img:
                    fname = Path(img).name
                    _set_cell(r, img_col, fname, img)
                roi = rec.get("roi_image_path")
                if roi:
                    fname = Path(roi).name
                    _set_cell(r, roi_col, fname, roi)

                # Highlight invalid ticket numbers
                if rec.get("ticket_number_valid") != "valid":
                    link = roi if roi else None
                    _set_cell(r, t_col, rec.get("ticket_number"), link, red)

                # Highlight invalid manifest numbers
                if rec.get("manifest_number_valid") != "valid":
                    m_link = rec.get("manifest_roi_image_path") or roi
                    _set_cell(r, m_col, rec.get("manifest_number"), m_link, red)

            wb.save(excel_path)
        except ImportError:
            # openpyxl is an optional dependency; if it's missing we simply
            # emit the basic Excel file without hyperlink/colour enhancements.
            pass

    # Ticket/manifest exception logs
    ticket_exc = df[df["ticket_number"].isna() | (df["ticket_number"] == "")]
    ticket_exc_path = _report_path(
        cfg, "ticket_number_exceptions_csv", "ticket_number/ticket_number_exceptions.csv"
    )
    if ticket_exc_path:
        os.makedirs(os.path.dirname(ticket_exc_path), exist_ok=True)
        ticket_exc.to_csv(ticket_exc_path, index=False)

    manifest_exc = df[df["manifest_valid"] != "valid"]

    manifest_exc_path = _report_path(
        cfg, "manifest_number_exceptions_csv", "manifest_number/manifest_number_exceptions.csv"
    )

    if manifest_exc_path:
        os.makedirs(os.path.dirname(manifest_exc_path), exist_ok=True)
        manifest_exc.to_csv(manifest_exc_path, index=False)

    # Summary report
    summary_path = _report_path(cfg, "summary_report", "summary/summary.csv")
    if summary_path:
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        ticket_valid_count = int((df["ticket_valid"] == "valid").sum())
        ticket_missing_count = int(ticket_exc.shape[0])
        ticket_invalid_count = len(df) - ticket_valid_count - ticket_missing_count
        summary_csv = {
            "total_pages": len(df),
            "tickets_missing": ticket_missing_count,
            "manifest_valid": int((df["manifest_valid"] == "valid").sum()),
            "manifest_review": int((df["manifest_valid"] == "review").sum()),
            "manifest_invalid": int((df["manifest_valid"] == "invalid").sum()),
        }
        summary_df = pd.DataFrame([summary_csv])

        vendor_counts = (
            df.groupby(["file", "vendor"]).size().reset_index(name="page_count")
        )
        if not vendor_counts.empty:
            vendor_counts["vendor_doc_path"] = vendor_counts.apply(
                lambda r: _make_vendor_doc_path(
                    r["file"], r["vendor"], r["page_count"], cfg
                ),
                axis=1,
            )

        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            summary_df.to_csv(f, index=False)
            if not vendor_counts.empty:
                f.write("\n")
                vendor_counts.to_csv(f, index=False)

        summary_meta = {}
        if not df.empty:
            summary_meta = _parse_filename_metadata(df.iloc[0]["file"])
        summary_data = {
            **summary_meta,
            **summary_csv,
            "tickets_valid": ticket_valid_count,
            "tickets_invalid": ticket_invalid_count,
        }
        vendor_records = []
        if not vendor_counts.empty:
            vendor_records = vendor_counts[
                ["vendor", "page_count", "vendor_doc_path"]
            ].to_dict("records")
        report_cfg = REPORTING_CFG.copy()
        report_cfg["output_dir"] = Path(summary_path).parent
        try:
            write_management_report(summary_data, vendor_records, report_cfg)
        except Exception:
            logging.exception("Failed to write management report")


def write_management_report(summary: Dict[str, Any], vendors: List[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    """Create a formatted Excel management report and optional PDF."""
    if not cfg.get("mgmt_report_xlsx"):
        return

    output_dir = Path(cfg.get("output_dir", "./outputs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    xlsx_path = output_dir / "management_report.xlsx"

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    try:  # pragma: no cover - image support is optional
        from openpyxl.drawing.image import Image as XLImage
    except Exception:  # pragma: no cover - optional dependency
        XLImage = None

    wb = Workbook()
    ws = wb.active
    row = 1

    logo_path = cfg.get("branding_logo_path")
    if XLImage and logo_path and Path(logo_path).is_file():
        try:
            img = XLImage(logo_path)
            max_w = 600
            if img.width and img.width > max_w:
                ratio = max_w / img.width
                img.width = max_w
                img.height = img.height * ratio
            ws.add_image(img, "A1")
            row = int((img.height or 0) / 20) + 2
        except Exception:
            pass

    company = cfg.get("branding_company_name")
    if company:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
        c = ws.cell(row=row, column=1, value=company)
        c.font = Font(bold=True, size=14)
        c.alignment = Alignment(horizontal="center")
        row += 2

    header_fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
    thin = Side(style="thin", color="000000")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def write_two_col_section(title: str, items: List[tuple[str, Any]]) -> None:
        nonlocal row
        ws.cell(row=row, column=1, value=title).font = Font(bold=True, size=12)
        row += 1
        ws.cell(row=row, column=1, value="Field").font = Font(bold=True)
        ws.cell(row=row, column=2, value="Value").font = Font(bold=True)
        for col in (1, 2):
            cell = ws.cell(row=row, column=col)
            cell.fill = header_fill
            cell.border = border
        row += 1
        for field, value in items:
            ws.cell(row=row, column=1, value=field).border = border
            ws.cell(row=row, column=2, value=value).border = border
            row += 1
        row += 1

    section1 = [
        ("Job", summary.get("JobID") or summary.get("Job")),
        ("Date", summary.get("Service Date") or summary.get("Date")),
        ("Material", summary.get("Material")),
        ("Source", summary.get("Source")),
        ("Destination", summary.get("Destination")),
    ]
    write_two_col_section("Summary", section1)

    section2 = [
        ("Total Pages", summary.get("total_pages")),
        ("Valid Tickets", summary.get("tickets_valid")),
        ("Invalid Tickets", summary.get("tickets_invalid")),
        ("Missing Tickets", summary.get("tickets_missing")),
    ]
    write_two_col_section("Ticket Summary", section2)

    section3 = [
        ("Manifest Valid", summary.get("manifest_valid")),
        ("Manifest Review", summary.get("manifest_review")),
        ("Manifest Invalid", summary.get("manifest_invalid")),
    ]
    write_two_col_section("Manifest Summary", section3)

    ws.cell(row=row, column=1, value="Vendor Details").font = Font(bold=True, size=12)
    row += 1
    headers = ["Vendor", "Page Count", "Document"]
    header_row = row
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.border = border
    row += 1
    for rec in vendors:
        ws.cell(row=row, column=1, value=rec.get("vendor")).border = border
        ws.cell(row=row, column=2, value=rec.get("page_count")).border = border
        doc_path = rec.get("vendor_doc_path")
        filename = Path(doc_path).name if doc_path else ""
        cell = ws.cell(row=row, column=3, value=filename)
        if doc_path:
            cell.hyperlink = doc_path
            cell.style = "Hyperlink"
        cell.border = border
        row += 1
    ws.freeze_panes = f"A{header_row + 1}"

    for col in range(1, 4):
        max_len = 0
        for r in range(1, row + 1):
            val = ws.cell(r, col).value
            if val is not None:
                max_len = max(max_len, len(str(val)))
        ws.column_dimensions[get_column_letter(col)].width = max_len + 2

    footer = (
        f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S} • By: {cfg.get('report_author')} • Version: {cfg.get('script_version')}"
    )
    ws.merge_cells(start_row=row + 1, start_column=1, end_row=row + 1, end_column=3)
    fcell = ws.cell(row=row + 1, column=1, value=footer)
    fcell.alignment = Alignment(horizontal="center")

    wb.save(xlsx_path)

    def _export_pdf(xlsx: Path) -> None:
        method = cfg.get("pdf_export", {}).get("method", "auto")
        if method in ("auto", "excel") and sys.platform.startswith("win"):
            try:
                import win32com.client  # type: ignore

                excel = win32com.client.Dispatch("Excel.Application")
                wb = excel.Workbooks.Open(str(xlsx))
                wb.ExportAsFixedFormat(0, str(xlsx.with_suffix(".pdf")))
                wb.Close(False)
                excel.Quit()
                return
            except Exception:
                if method == "excel":
                    logging.warning("Excel PDF export failed")
        if method in ("auto", "libreoffice"):
            soffice = shutil.which("soffice")
            if soffice:
                try:
                    subprocess.run(
                        [
                            soffice,
                            "--headless",
                            "--convert-to",
                            "pdf",
                            str(xlsx),
                            "--outdir",
                            str(output_dir),
                        ],
                        check=True,
                    )
                    return
                except Exception:
                    if method == "libreoffice":
                        logging.warning("LibreOffice PDF export failed")
        logging.warning("Management report PDF export skipped; required tools not available")

    if cfg.get("mgmt_report_pdf"):
        _export_pdf(xlsx_path)


def export_preflight_exceptions(exceptions: List[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    """Write preflight exception rows to CSV if enabled."""
    if not exceptions:
        return
    out_path = _report_path(
        cfg,
        "preflight_exceptions_csv",
        "preflight/preflight_exceptions.csv",
    )
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        pd.DataFrame(exceptions).to_csv(out_path, index=False)


def export_issue_logs(
        ticket_issues: List[Dict[str, Any]],
        issues_log: List[Dict[str, Any]],
        cfg: Dict[str, Any],
) -> None:
    """Write detailed issue logs if enabled."""
    ti_path = _report_path(cfg, "ticket_issues", "ticket_issues.csv")
    if ti_path and ticket_issues:
        os.makedirs(os.path.dirname(ti_path), exist_ok=True)
        pd.DataFrame(ticket_issues).to_csv(ti_path, index=False)

    il_path = _report_path(cfg, "issues_log", "issues_log.csv")
    if il_path and issues_log:
        os.makedirs(os.path.dirname(il_path), exist_ok=True)
        pd.DataFrame(issues_log).to_csv(il_path, index=False)


def export_process_analysis(records: List[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    """Write per-page OCR timing metrics."""
    path = _report_path(cfg, "process_analysis", "process_analysis.csv")
    if not path or not records:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame(records).to_csv(path, index=False)
