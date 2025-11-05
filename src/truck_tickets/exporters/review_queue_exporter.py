"""Review queue exporter.

Exports pages/tickets that require manual review due to:
- Missing required fields
- Low confidence OCR
- Validation failures
- Ambiguous data
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path


class ReviewQueueExporter:
    """Exports review queue items for manual correction."""

    def __init__(self):
        """Initialize review queue exporter."""
        self.logger = logging.getLogger(__name__)

    def export(self, review_items: list[dict], output_path: str | Path):
        """Export review queue to CSV.

        Args:
            review_items: List of review item dictionaries
            output_path: Path to output CSV file

        CSV Format:
            page_id,reason,severity,file_path,page_num,detected_fields,
            suggested_fixes,created_at
        """
        output_path = Path(output_path)
        self.logger.info(f"Generating review queue CSV: {output_path}")

        # Sort by severity (CRITICAL first), then by creation time
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        sorted_items = sorted(
            review_items,
            key=lambda item: (
                severity_order.get(item.get("severity", "INFO"), 3),
                item.get("created_at", ""),
            ),
        )

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header row
            writer.writerow(
                [
                    "page_id",
                    "reason",
                    "severity",
                    "file_path",
                    "page_num",
                    "detected_fields",
                    "suggested_fixes",
                    "created_at",
                ]
            )

            # Data rows
            for item in sorted_items:
                writer.writerow(
                    [
                        item.get("page_id", ""),
                        item.get("reason", ""),
                        item.get("severity", "INFO"),
                        item.get("file_path", ""),
                        item.get("page_num", ""),
                        json.dumps(item.get("detected_fields", {})),
                        json.dumps(item.get("suggested_fixes", {})),
                        item.get("created_at", datetime.now().isoformat()),
                    ]
                )

        self.logger.info(
            f"✓ Review queue saved: {output_path} ({len(sorted_items)} items)"
        )

        # Log summary by severity
        self._log_severity_summary(sorted_items)

    def _log_severity_summary(self, review_items: list[dict]):
        """Log summary of review items by severity level."""
        severity_counts = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}

        for item in review_items:
            severity = item.get("severity", "INFO")
            if severity in severity_counts:
                severity_counts[severity] += 1

        self.logger.info(
            f"Review queue summary: "
            f"{severity_counts['CRITICAL']} critical, "
            f"{severity_counts['WARNING']} warnings, "
            f"{severity_counts['INFO']} info"
        )

        if severity_counts["CRITICAL"] > 0:
            self.logger.warning(
                f"⚠️ {severity_counts['CRITICAL']} CRITICAL items require immediate attention"
            )

    def export_by_reason(self, review_items: list[dict], output_dir: str | Path):
        """Export separate CSV files grouped by review reason.

        Args:
            review_items: List of review item dictionaries
            output_dir: Directory to write reason-specific CSV files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Group by reason
        reason_items = {}
        for item in review_items:
            reason = item.get("reason", "UNKNOWN")
            if reason not in reason_items:
                reason_items[reason] = []
            reason_items[reason].append(item)

        # Export one file per reason
        for reason, items in reason_items.items():
            reason_filename = f"review_queue_{reason}.csv"
            reason_path = output_dir / reason_filename
            self.export(items, reason_path)

        self.logger.info(
            f"✓ Exported {len(reason_items)} reason-specific review queues to {output_dir}"
        )

    def generate_summary_report(
        self, review_items: list[dict], output_path: str | Path
    ):
        """Generate summary report of review queue statistics.

        Args:
            review_items: List of review item dictionaries
            output_path: Path to output summary CSV
        """
        output_path = Path(output_path)
        self.logger.info(f"Generating review queue summary: {output_path}")

        # Group by reason and severity
        summary_data = {}
        for item in review_items:
            reason = item.get("reason", "UNKNOWN")
            severity = item.get("severity", "INFO")

            key = (reason, severity)
            if key not in summary_data:
                summary_data[key] = {"count": 0, "files": set()}

            summary_data[key]["count"] += 1

            file_path = item.get("file_path")
            if file_path:
                summary_data[key]["files"].add(file_path)

        # Write summary CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            writer.writerow(["reason", "severity", "item_count", "affected_files"])

            for (reason, severity), data in sorted(summary_data.items()):
                writer.writerow([reason, severity, data["count"], len(data["files"])])

        self.logger.info(f"✓ Review queue summary saved: {output_path}")

    def export_critical_only(self, review_items: list[dict], output_path: str | Path):
        """Export only CRITICAL severity items for immediate attention.

        Args:
            review_items: List of review item dictionaries
            output_path: Path to output CSV file
        """
        critical_items = [
            item for item in review_items if item.get("severity") == "CRITICAL"
        ]

        if critical_items:
            self.export(critical_items, output_path)
            self.logger.warning(
                f"⚠️ {len(critical_items)} CRITICAL items exported to {output_path}"
            )
        else:
            self.logger.info("✓ No critical review items found")

    def check_missing_manifests(self, review_items: list[dict]) -> list[dict]:
        """Extract review items related to missing manifests (compliance issue).

        Args:
            review_items: List of review item dictionaries

        Returns:
            List of items with missing manifest numbers
        """
        missing_manifests = [
            item for item in review_items if item.get("reason") == "MISSING_MANIFEST"
        ]

        if missing_manifests:
            self.logger.warning(
                f"⚠️ COMPLIANCE ISSUE: {len(missing_manifests)} contaminated loads "
                f"missing manifest numbers"
            )

        return missing_manifests

    def export_for_gui(self, review_items: list[dict], output_path: str | Path):
        """Export review queue in JSON format for GUI application.

        Args:
            review_items: List of review item dictionaries
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        self.logger.info(f"Generating review queue JSON for GUI: {output_path}")

        # Sort by severity
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        sorted_items = sorted(
            review_items,
            key=lambda item: severity_order.get(item.get("severity", "INFO"), 3),
        )

        # Write JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sorted_items, f, indent=2, default=str)

        self.logger.info(f"✓ Review queue JSON saved: {output_path}")
