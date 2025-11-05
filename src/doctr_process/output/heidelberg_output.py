"""Heidelberg-specific output handler for ticket extraction reports."""

import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .base import OutputHandler


class HeidelbergOutputHandler(OutputHandler):
    """Generates Heidelberg-specific CSV/XLSX reports when Heidelberg vendor is detected."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get("output_dir", "./outputs"))

    def write(self, results: list[dict[str, Any]], config: dict[str, Any]) -> None:
        """Write Heidelberg-specific reports for detected Heidelberg tickets."""
        # Filter for Heidelberg results
        heidelberg_results = [
            r for r in results if r.get("vendor", "").lower() == "heidelberg"
        ]

        if not heidelberg_results:
            logging.info("No Heidelberg tickets detected - skipping Heidelberg output")
            return

        logging.info(f"Found {len(heidelberg_results)} Heidelberg ticket pages")

        # Group by source file
        files_processed = {}
        for result in heidelberg_results:
            file_name = result.get("file", "unknown")
            if file_name not in files_processed:
                files_processed[file_name] = []
            files_processed[file_name].append(result)

        # Generate reports for each file
        for file_name, file_results in files_processed.items():
            self._write_file_report(file_name, file_results)

    def _write_file_report(self, file_name: str, results: list[dict[str, Any]]) -> None:
        """Write Heidelberg report for a single source file."""
        try:
            # Convert to DataFrame with Heidelberg-specific columns
            df_data = []
            for result in results:
                row = {
                    "Date": result.get("date"),
                    "Ticket": result.get("ticket_number"),
                    "Product": result.get("product"),
                    "Time In": result.get("time_in"),
                    "Time Out": result.get("time_out"),
                    "Job": result.get("job"),
                    "Tons": result.get("tons"),
                    "Source File": result.get("file"),
                    "Page": result.get("page"),
                }
                df_data.append(row)

            df = pd.DataFrame(df_data)

            # Sort by date and ticket
            df = df.sort_values(by=["Date", "Ticket"], na_position="last")

            # Generate output filename
            output_filename = self._generate_filename(file_name, results[0])

            # Write CSV
            csv_path = self.output_dir / f"{output_filename}.csv"
            df.to_csv(csv_path, index=False)
            logging.info(f"Saved Heidelberg CSV: {csv_path}")

            # Write XLSX if requested
            if self.config.get("include_xlsx", True):
                try:
                    xlsx_path = self.output_dir / f"{output_filename}.xlsx"
                    df.to_excel(xlsx_path, index=False)
                    logging.info(f"Saved Heidelberg XLSX: {xlsx_path}")
                except Exception as e:
                    logging.warning(f"Failed to write Heidelberg XLSX: {e}")

        except Exception as e:
            logging.error(f"Failed to write Heidelberg report for {file_name}: {e}")

    def _generate_filename(self, source_file: str, first_result: dict[str, Any]) -> str:
        """Generate output filename based on extracted data."""
        # Extract components for filename
        job = first_result.get("job") or "unknownjob"
        date = first_result.get("date") or "undated"
        product = first_result.get("product") or "material"

        # Sanitize filename components
        def sanitize(s: str) -> str:
            return re.sub(r"[^A-Za-z0-9_\-]", "_", str(s))

        # Build filename: job_date_heidelberg_product
        filename = f"{sanitize(job)}_{sanitize(date)}_heidelberg_{sanitize(product)}"

        return filename
