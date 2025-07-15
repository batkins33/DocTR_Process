import csv
import html
import atexit
from typing import List


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

