import csv
import html
import os
import re
import atexit
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


def auto_export_logs() -> None:
    log_file = "error.log"
    export_logs_to_csv(log_file, "log_report.csv")
    export_logs_to_html(log_file, "log_report.html")


atexit.register(auto_export_logs)


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
    out_path = cfg.get("output_csv")
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        pd.DataFrame(rows).to_csv(out_path, index=False)

    df = pd.DataFrame(rows)
    df["ticket_valid"] = df["ticket_number"].apply(get_ticket_validation_status)
    df["manifest_valid"] = df["manifest_number"].apply(get_manifest_validation_status)

    # Page-level fields with validation
    page_fields_path = cfg.get("page_fields_csv")
    if page_fields_path:
        os.makedirs(os.path.dirname(page_fields_path), exist_ok=True)
        df.to_csv(page_fields_path, index=False)

    # Mark duplicate tickets
    ticket_counts = df.groupby(["vendor", "ticket_number"]).size().rename("count")
    df = df.join(ticket_counts, on=["vendor", "ticket_number"])
    df["duplicate_ticket"] = df["count"] > 1

    ticket_numbers_path = cfg.get("ticket_numbers_csv")
    if ticket_numbers_path:
        os.makedirs(os.path.dirname(ticket_numbers_path), exist_ok=True)
        df.drop(columns=["count"]).to_csv(ticket_numbers_path, index=False)

    # Ticket/manifest exception logs
    ticket_exc = df[df["ticket_number"].isna() | (df["ticket_number"] == "")]
    ticket_exc_path = cfg.get("ticket_number_exceptions_csv")
    if ticket_exc_path:
        os.makedirs(os.path.dirname(ticket_exc_path), exist_ok=True)
        ticket_exc.to_csv(ticket_exc_path, index=False)

    manifest_exc = df[df["manifest_valid"] != "valid"]
    manifest_exc_path = cfg.get("manifest_number_exceptions_csv")
    if manifest_exc_path:
        os.makedirs(os.path.dirname(manifest_exc_path), exist_ok=True)
        manifest_exc.to_csv(manifest_exc_path, index=False)

    # Summary report
    summary_dir = cfg.get("summary_report_dir")
    if summary_dir:
        os.makedirs(summary_dir, exist_ok=True)
        summary_path = os.path.join(summary_dir, "summary.csv")
        summary = {
            "total_pages": len(df),
            "tickets_missing": int(ticket_exc.shape[0]),
            "manifest_valid": int((df["manifest_valid"] == "valid").sum()),
            "manifest_review": int((df["manifest_valid"] == "review").sum()),
            "manifest_invalid": int((df["manifest_valid"] == "invalid").sum()),
        }
        pd.DataFrame([summary]).to_csv(summary_path, index=False)


