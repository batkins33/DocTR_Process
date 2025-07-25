import csv
import html
import os
import re
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd


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

    # Ticket/manifest exception logs
    ticket_exc = df[df["ticket_number"].isna() | (df["ticket_number"] == "")]
    ticket_exc_path = _report_path(cfg, "ticket_number_exceptions_csv", "ticket_number/ticket_number_exceptions.csv")
    if ticket_exc_path:
        os.makedirs(os.path.dirname(ticket_exc_path), exist_ok=True)
        ticket_exc.to_csv(ticket_exc_path, index=False)

    manifest_exc = df[df["manifest_valid"] != "valid"]
    manifest_exc_path = _report_path(cfg, "manifest_number_exceptions_csv", "manifest_number/manifest_number_exceptions.csv")
    if manifest_exc_path:
        os.makedirs(os.path.dirname(manifest_exc_path), exist_ok=True)
        manifest_exc.to_csv(manifest_exc_path, index=False)

    # Summary report
    summary_path = _report_path(cfg, "summary_report", "summary/summary.csv")
    if summary_path:
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)
        summary = {
            "total_pages": len(df),
            "tickets_missing": int(ticket_exc.shape[0]),
            "manifest_valid": int((df["manifest_valid"] == "valid").sum()),
            "manifest_review": int((df["manifest_valid"] == "review").sum()),
            "manifest_invalid": int((df["manifest_valid"] == "invalid").sum()),
        }
        summary_df = pd.DataFrame([summary])

        vendor_counts = (
            df.groupby(["file", "vendor"]).size().reset_index(name="page_count")
        )

        with open(summary_path, "w", newline="", encoding="utf-8") as f:
            summary_df.to_csv(f, index=False)
            if not vendor_counts.empty:
                f.write("\n")
                vendor_counts.to_csv(f, index=False)


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


