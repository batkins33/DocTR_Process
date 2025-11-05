"""Invoice matching CSV exporter for Issue #17.

Generates pipe-delimited CSV for accounting team to match against vendor invoices.
Sorted by vendor, then date, then ticket number for easy reconciliation.

Per Spec v1.1 Section 5.2:
- Pipe-delimited format for Excel compatibility
- Includes truck_number field (v1.1 addition)
- Sort order: vendor → date → ticket_number
"""

import csv
import logging
from pathlib import Path
from typing import Optional


class InvoiceMatchingExporter:
    """Exports ticket data for invoice matching and reconciliation (Issue #17)."""

    def __init__(self):
        """Initialize invoice matching exporter."""
        self.logger = logging.getLogger(__name__)

    def export(self, tickets: list[dict], output_path: str | Path):
        """Export tickets to invoice matching CSV.

        Args:
            tickets: List of ticket dictionaries with keys:
                - ticket_number: Unique ticket identifier
                - vendor: Vendor name (normalized)
                - ticket_date: Ticket date (YYYY-MM-DD format)
                - material: Material type
                - quantity: Load quantity (optional)
                - quantity_unit: Quantity units (optional)
                - truck_number: Truck ID (optional, v1.1 field)
                - file_ref: Path to source PDF + page number
            output_path: Path to output CSV file

        CSV Format (pipe-delimited):
            ticket_number|vendor|date|material|quantity|units|truck_number|file_ref

        Example:
            WM12345678|WASTE_MANAGEMENT_LEWISVILLE|2024-10-17|CLASS_2_CONTAMINATED|18.5|TONS|1234|file1.pdf-p1
        """
        output_path = Path(output_path)
        self.logger.info(f"Generating invoice matching CSV: {output_path}")

        # Sort tickets by vendor, date, ticket number (per spec)
        sorted_tickets = sorted(
            tickets,
            key=lambda t: (
                t.get("vendor", "UNKNOWN"),
                t.get("ticket_date", ""),
                t.get("ticket_number", "")
            )
        )

        # Write CSV with pipe delimiter
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="|")

            # Header row (per spec v1.1)
            writer.writerow([
                "ticket_number",
                "vendor",
                "date",
                "material",
                "quantity",
                "units",
                "truck_number",  # NEW in v1.1
                "file_ref"
            ])

            # Data rows
            for ticket in sorted_tickets:
                writer.writerow([
                    ticket.get("ticket_number", ""),
                    ticket.get("vendor", ""),
                    ticket.get("ticket_date", ""),
                    ticket.get("material", ""),
                    self._format_quantity(ticket.get("quantity")),
                    ticket.get("quantity_unit", ""),
                    ticket.get("truck_number", ""),  # NEW in v1.1
                    self._format_file_ref(ticket)
                ])

        self.logger.info(f"✓ Invoice matching CSV saved: {output_path} ({len(sorted_tickets)} tickets)")

    def _format_quantity(self, quantity: Optional[float | str]) -> str:
        """Format quantity for CSV output.

        Args:
            quantity: Quantity value (float, str, or None)

        Returns:
            Formatted quantity string (empty if None)
        """
        if quantity is None or quantity == "":
            return ""
        try:
            return f"{float(quantity):.1f}"
        except (ValueError, TypeError):
            return str(quantity)

    def _format_file_ref(self, ticket: dict) -> str:
        """Format file reference as 'filename-pN'.

        Args:
            ticket: Ticket dictionary

        Returns:
            Formatted file reference (e.g., "file1.pdf-p1")
        """
        file_id = ticket.get("file_id", "")
        file_page = ticket.get("file_page", "")

        if file_id and file_page:
            return f"{file_id}-p{file_page}"
        elif file_id:
            return file_id
        else:
            return ticket.get("file_ref", "")

    def export_by_vendor(self, tickets: list[dict], output_dir: str | Path):
        """Export separate CSV files per vendor for easier invoice matching.

        Args:
            tickets: List of ticket dictionaries
            output_dir: Directory to write vendor-specific CSV files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Group tickets by vendor
        vendor_tickets = {}
        for ticket in tickets:
            vendor = ticket.get("vendor", "UNKNOWN")
            if vendor not in vendor_tickets:
                vendor_tickets[vendor] = []
            vendor_tickets[vendor].append(ticket)

        # Export one file per vendor
        for vendor, vendor_ticket_list in vendor_tickets.items():
            vendor_filename = f"invoice_match_{vendor}.csv"
            vendor_path = output_dir / vendor_filename
            self.export(vendor_ticket_list, vendor_path)

        self.logger.info(
            f"✓ Exported {len(vendor_tickets)} vendor-specific invoice files to {output_dir}"
        )

    def generate_summary_report(self, tickets: list[dict], output_path: str | Path):
        """Generate summary report showing ticket counts and totals by vendor.

        Args:
            tickets: List of ticket dictionaries
            output_path: Path to output summary CSV
        """
        output_path = Path(output_path)
        self.logger.info(f"Generating invoice summary report: {output_path}")

        # Group and summarize by vendor
        vendor_summary = {}
        for ticket in tickets:
            vendor = ticket.get("vendor", "UNKNOWN")
            if vendor not in vendor_summary:
                vendor_summary[vendor] = {
                    "ticket_count": 0,
                    "total_quantity": 0.0,
                    "unit": None,
                }

            vendor_summary[vendor]["ticket_count"] += 1

            # Sum quantities if available
            quantity = ticket.get("quantity")
            if quantity:
                try:
                    vendor_summary[vendor]["total_quantity"] += float(quantity)
                    vendor_summary[vendor]["unit"] = ticket.get(
                        "quantity_unit", "LOADS"
                    )
                except (ValueError, TypeError):
                    pass

        # Write summary CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(["vendor", "ticket_count", "total_quantity", "unit"])

            for vendor in sorted(vendor_summary.keys()):
                summary = vendor_summary[vendor]
                writer.writerow(
                    [
                        vendor,
                        summary["ticket_count"],
                        (
                            f"{summary['total_quantity']:.2f}"
                            if summary["total_quantity"]
                            else "0"
                        ),
                        summary["unit"] or "LOADS",
                    ]
                )

        self.logger.info(f"✓ Invoice summary report saved: {output_path}")
