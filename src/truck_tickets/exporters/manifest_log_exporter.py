"""Manifest compliance log exporter for Issue #18.

Generates CSV log of all contaminated material manifests for EPA/state regulatory compliance.

CRITICAL REGULATORY REQUIREMENT:
- This log must be maintained for minimum 5 years per EPA requirements
- 100% recall required - all contaminated loads must have manifest numbers
- Missing manifests trigger compliance warnings

Per Spec v1.1 Section 5.3:
- CSV format (comma-delimited)
- Includes truck_number field (v1.1 addition)
- Sort order: date → manifest_number
- Only contaminated material (CLASS_2_CONTAMINATED, SPOILS)
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class ManifestLogExporter:
    """Exports manifest tracking log for contaminated material compliance (Issue #18)."""

    def __init__(self):
        """Initialize manifest log exporter."""
        self.logger = logging.getLogger(__name__)

    def export(self, tickets: list[dict], output_path: str | Path):
        """Export contaminated material manifests to compliance log.

        Args:
            tickets: List of ticket dictionaries with keys:
                - ticket_number: Truck ticket number
                - manifest_number: Regulatory manifest number (REQUIRED)
                - ticket_date: Disposal date (YYYY-MM-DD)
                - source: Source location on site
                - destination: Waste facility name
                - material: Material type
                - quantity: Load quantity (optional)
                - quantity_unit: Quantity units (optional)
                - truck_number: Truck ID (optional, v1.1 field)
                - file_id: Source PDF filename
                - file_page: Page number in PDF
            output_path: Path to output CSV file

        CSV Format (comma-delimited):
            ticket_number,manifest_number,date,source,waste_facility,material,quantity,units,truck_number,file_ref

        Example:
            WM12345678,WM-MAN-2024-001234,2024-10-17,PIER_EX,WASTE_MANAGEMENT_LEWISVILLE,CLASS_2_CONTAMINATED,18.5,TONS,1234,file1.pdf-p1

        Regulatory Note:
            This log must be maintained for minimum 5 years per EPA requirements.
        """
        output_path = Path(output_path)
        self.logger.info(f"Generating manifest compliance log: {output_path}")

        # Filter to contaminated material only (CLASS_2_CONTAMINATED or SPOILS)
        contaminated_tickets = [
            t
            for t in tickets
            if t.get("material") in ["CLASS_2_CONTAMINATED", "SPOILS"]
            or t.get("material_class") == "CONTAMINATED"
        ]

        # Sort by date, then manifest number (per spec)
        sorted_tickets = sorted(
            contaminated_tickets,
            key=lambda t: (t.get("ticket_date", ""), t.get("manifest_number", "")),
        )

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header row (per spec v1.1)
            writer.writerow(
                [
                    "ticket_number",
                    "manifest_number",
                    "date",
                    "source",
                    "waste_facility",
                    "material",
                    "quantity",
                    "units",
                    "truck_number",  # NEW in v1.1
                    "file_ref",
                ]
            )

            # Data rows
            for ticket in sorted_tickets:
                writer.writerow(
                    [
                        ticket.get("ticket_number", ""),
                        ticket.get("manifest_number", ""),
                        ticket.get("ticket_date", ""),
                        ticket.get("source", ""),
                        ticket.get("destination", ""),
                        ticket.get("material", ""),
                        self._format_quantity(ticket.get("quantity")),
                        ticket.get("quantity_unit", ""),
                        ticket.get("truck_number", ""),  # NEW in v1.1
                        self._format_file_ref(ticket),
                    ]
                )

        self.logger.info(
            f"✓ Manifest log saved: {output_path} ({len(sorted_tickets)} contaminated loads)"
        )

        # Validate manifest completeness (CRITICAL for compliance)
        self._validate_manifests(sorted_tickets)

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

    def _validate_manifests(self, tickets: list[dict]):
        """Validate that all contaminated tickets have manifest numbers.

        Logs warnings for any missing manifests (regulatory compliance issue).
        """
        missing_manifests = [t for t in tickets if not t.get("manifest_number")]

        if missing_manifests:
            self.logger.warning(
                f"⚠️ COMPLIANCE WARNING: {len(missing_manifests)} contaminated loads "
                f"missing manifest numbers!"
            )
            for ticket in missing_manifests[:5]:  # Show first 5
                self.logger.warning(
                    f"  - Ticket {ticket.get('ticket_number', 'UNKNOWN')} "
                    f"on {ticket.get('ticket_date', 'UNKNOWN')}"
                )
            if len(missing_manifests) > 5:
                self.logger.warning(f"  ... and {len(missing_manifests) - 5} more")
        else:
            self.logger.info("✓ All contaminated loads have manifest numbers")

    def generate_monthly_summary(self, tickets: list[dict], output_path: str | Path):
        """Generate monthly summary of contaminated material disposal.

        Args:
            tickets: List of ticket dictionaries
            output_path: Path to output summary CSV
        """
        output_path = Path(output_path)
        self.logger.info(f"Generating monthly manifest summary: {output_path}")

        # Filter contaminated tickets
        contaminated_tickets = [
            t for t in tickets if t.get("material") == "CLASS_2_CONTAMINATED"
        ]

        # Group by month
        monthly_data = {}
        for ticket in contaminated_tickets:
            date_str = ticket.get("ticket_date")
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    month_key = date_obj.strftime("%Y-%m")  # e.g., "2024-10"

                    if month_key not in monthly_data:
                        monthly_data[month_key] = {
                            "load_count": 0,
                            "total_quantity": 0.0,
                            "manifest_count": 0,
                            "sources": set(),
                        }

                    monthly_data[month_key]["load_count"] += 1

                    # Sum quantity
                    quantity = ticket.get("quantity")
                    if quantity:
                        try:
                            monthly_data[month_key]["total_quantity"] += float(quantity)
                        except (ValueError, TypeError):
                            pass

                    # Count unique manifests
                    manifest = ticket.get("manifest_number")
                    if manifest:
                        monthly_data[month_key]["manifest_count"] += 1

                    # Track sources
                    source = ticket.get("source")
                    if source:
                        monthly_data[month_key]["sources"].add(source)

                except ValueError:
                    pass

        # Write summary CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(
                ["month", "load_count", "total_tons", "manifest_count", "sources"]
            )

            for month in sorted(monthly_data.keys()):
                data = monthly_data[month]
                writer.writerow(
                    [
                        month,
                        data["load_count"],
                        f"{data['total_quantity']:.2f}",
                        data["manifest_count"],
                        ", ".join(sorted(data["sources"])),
                    ]
                )

        self.logger.info(f"✓ Monthly manifest summary saved: {output_path}")

    def check_duplicate_manifests(self, tickets: list[dict]) -> list[dict]:
        """Check for duplicate manifest numbers (potential data entry error).

        Args:
            tickets: List of ticket dictionaries

        Returns:
            List of duplicate manifest entries
        """
        manifest_usage = {}
        duplicates = []

        for ticket in tickets:
            manifest = ticket.get("manifest_number")
            if manifest:
                if manifest in manifest_usage:
                    # Duplicate found
                    duplicates.append(
                        {
                            "manifest_number": manifest,
                            "first_ticket": manifest_usage[manifest],
                            "duplicate_ticket": ticket.get("ticket_number"),
                            "first_date": manifest_usage[manifest].get("ticket_date"),
                            "duplicate_date": ticket.get("ticket_date"),
                        }
                    )
                else:
                    manifest_usage[manifest] = ticket

        if duplicates:
            self.logger.warning(f"⚠️ Found {len(duplicates)} duplicate manifest numbers")
            for dup in duplicates[:5]:
                self.logger.warning(
                    f"  - Manifest {dup['manifest_number']} used on "
                    f"{dup['first_date']} and {dup['duplicate_date']}"
                )

        return duplicates

    def export_by_source(self, tickets: list[dict], output_dir: str | Path):
        """Export separate manifest logs per source location.

        Args:
            tickets: List of ticket dictionaries
            output_dir: Directory to write source-specific manifest logs
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Filter contaminated tickets
        contaminated_tickets = [
            t for t in tickets if t.get("material") == "CLASS_2_CONTAMINATED"
        ]

        # Group by source
        source_tickets = {}
        for ticket in contaminated_tickets:
            source = ticket.get("source", "UNKNOWN")
            if source not in source_tickets:
                source_tickets[source] = []
            source_tickets[source].append(ticket)

        # Export one file per source
        for source, source_ticket_list in source_tickets.items():
            source_filename = f"manifest_log_{source}.csv"
            source_path = output_dir / source_filename
            self.export(source_ticket_list, source_path)

        self.logger.info(
            f"✓ Exported {len(source_tickets)} source-specific manifest logs to {output_dir}"
        )
