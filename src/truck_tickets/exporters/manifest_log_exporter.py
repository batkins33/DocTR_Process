"""Manifest compliance log exporter.

Generates CSV log of all contaminated material manifests for EPA/state regulatory compliance.
This log must be maintained for minimum 5 years per EPA requirements.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path


class ManifestLogExporter:
    """Exports manifest tracking log for contaminated material compliance."""

    def __init__(self):
        """Initialize manifest log exporter."""
        self.logger = logging.getLogger(__name__)

    def export(self, tickets: list[dict], output_path: str | Path):
        """Export contaminated material manifests to compliance log.

        Args:
            tickets: List of ticket dictionaries
            output_path: Path to output CSV file

        CSV Format:
            ticket_number,manifest_number,date,source,waste_facility,
            material,quantity,units,file_ref
        """
        output_path = Path(output_path)
        self.logger.info(f"Generating manifest compliance log: {output_path}")

        # Filter to contaminated material only
        contaminated_tickets = [
            t
            for t in tickets
            if t.get("material") == "CLASS_2_CONTAMINATED"
            or t.get("material_class") == "CONTAMINATED"
        ]

        # Sort by date, then manifest number
        sorted_tickets = sorted(
            contaminated_tickets,
            key=lambda t: (t.get("ticket_date", ""), t.get("manifest_number", "")),
        )

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header row
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
                        ticket.get("quantity", ""),
                        ticket.get("quantity_unit", ""),
                        ticket.get("file_ref", ""),
                    ]
                )

        self.logger.info(
            f"✓ Manifest log saved: {output_path} ({len(sorted_tickets)} contaminated loads)"
        )

        # Validate manifest completeness
        self._validate_manifests(sorted_tickets)

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
