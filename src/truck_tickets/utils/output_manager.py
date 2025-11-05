"""Output manager for flexible database and file output control."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


class OutputManager:
    """Manages output destinations for ticket processing results.
    
    Supports flexible configuration to write to:
    - SQL Server database
    - CSV files
    - Excel workbooks
    - JSON files
    - Any combination of the above
    """

    def __init__(self, config_path: str | None = None):
        """Initialize output manager with configuration.
        
        Args:
            config_path: Path to output_config.yml (default: config/output_config.yml)
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "output_config.yml"
        
        self.config = self._load_config(config_path)
        self.db_connection = None
        
        # Initialize output directories if file outputs enabled
        if self.config["file_outputs"]["enabled"]:
            self._setup_output_directories()
    
    def _load_config(self, config_path: Path | str) -> dict:
        """Load output configuration from YAML file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._default_config()
        
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        
        self.logger.info(f"Loaded output configuration from {config_path}")
        return config
    
    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "database": {"enabled": False},
            "file_outputs": {
                "enabled": True,
                "base_directory": "outputs",
                "csv_exports": {"enabled": True},
                "excel_exports": {"enabled": True},
                "json_exports": {"enabled": True},
            },
            "logging": {"log_output_operations": True, "log_level": "INFO"},
        }
    
    def _setup_output_directories(self):
        """Create output directory structure."""
        base_dir = Path(self.config["file_outputs"]["base_directory"])
        
        # Create subdirectories
        subdirs = ["csv", "excel", "json"]
        for subdir in subdirs:
            (base_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Output directories ready at {base_dir.absolute()}")
    
    @property
    def database_enabled(self) -> bool:
        """Check if database output is enabled."""
        return self.config.get("database", {}).get("enabled", False)
    
    @property
    def file_outputs_enabled(self) -> bool:
        """Check if file outputs are enabled."""
        return self.config.get("file_outputs", {}).get("enabled", False)
    
    def get_database_connection(self):
        """Get database connection if enabled.
        
        Returns:
            DatabaseConnection instance or None if database disabled
        """
        if not self.database_enabled:
            return None
        
        if self.db_connection is None:
            from ..database import DatabaseConnection
            
            db_config = self.config["database"]["connection"]
            
            if db_config.get("use_env_vars", True):
                self.db_connection = DatabaseConnection.from_env()
            else:
                self.db_connection = DatabaseConnection(
                    server=db_config["server"],
                    database=db_config["database"],
                    trusted_connection=db_config.get("trusted_connection", True),
                )
            
            self.logger.info("Database connection established")
        
        return self.db_connection
    
    def write_tickets(self, tickets: list[dict], job_code: str | None = None):
        """Write tickets to configured outputs.
        
        Args:
            tickets: List of ticket dictionaries
            job_code: Optional job code for file naming
        """
        if not tickets:
            self.logger.warning("No tickets to write")
            return
        
        # Write to database if enabled
        if self.database_enabled:
            self._write_tickets_to_database(tickets)
        
        # Write to files if enabled
        if self.file_outputs_enabled:
            self._write_tickets_to_files(tickets, job_code)
    
    def _write_tickets_to_database(self, tickets: list[dict]):
        """Write tickets to SQL Server database."""
        try:
            db = self.get_database_connection()
            if db is None:
                return
            
            # TODO: Implement database insertion via TicketRepository
            # This will be implemented when database operations are complete
            self.logger.info(f"Would write {len(tickets)} tickets to database (not yet implemented)")
            
        except Exception as e:
            self.logger.error(f"Failed to write tickets to database: {e}")
    
    def _write_tickets_to_files(self, tickets: list[dict], job_code: str | None):
        """Write tickets to file outputs."""
        base_dir = Path(self.config["file_outputs"]["base_directory"])
        timestamp = datetime.now().strftime(
            self.config["file_outputs"]["naming"]["timestamp_format"]
        )
        
        # Generate filename suffix
        suffix = ""
        if self.config["file_outputs"]["naming"]["use_job_code"] and job_code:
            suffix += f"_{job_code}"
        if self.config["file_outputs"]["naming"]["use_timestamps"]:
            suffix += f"_{timestamp}"
        
        # Write JSON if enabled
        if self.config["file_outputs"]["json_exports"]["enabled"]:
            if self.config["file_outputs"]["json_exports"]["processed_tickets"]:
                json_path = base_dir / "json" / f"processed_tickets{suffix}.json"
                self._write_json(tickets, json_path)
        
        # Write CSV if enabled
        if self.config["file_outputs"]["csv_exports"]["enabled"]:
            self._write_csv_exports(tickets, base_dir / "csv", suffix)
        
        # Write Excel if enabled
        if self.config["file_outputs"]["excel_exports"]["enabled"]:
            if self.config["file_outputs"]["excel_exports"]["tracking_workbook"]:
                excel_path = base_dir / "excel" / f"tracking_export{suffix}.xlsx"
                self._write_excel_workbook(tickets, excel_path)
    
    def _write_json(self, data: Any, path: Path):
        """Write data to JSON file."""
        try:
            with open(path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            
            if self.config["logging"]["log_output_operations"]:
                self.logger.info(f"✓ Wrote JSON: {path}")
        except Exception as e:
            self.logger.error(f"Failed to write JSON to {path}: {e}")
    
    def _write_csv_exports(self, tickets: list[dict], csv_dir: Path, suffix: str):
        """Write CSV exports (invoice matching, manifest log, etc.)."""
        csv_config = self.config["file_outputs"]["csv_exports"]
        
        # Invoice matching CSV
        if csv_config.get("invoice_matching", True):
            csv_path = csv_dir / f"invoice_match{suffix}.csv"
            self._write_invoice_csv(tickets, csv_path)
        
        # Manifest log CSV
        if csv_config.get("manifest_log", True):
            contaminated_tickets = [t for t in tickets if t.get("material_class") == "CONTAMINATED"]
            if contaminated_tickets:
                csv_path = csv_dir / f"manifest_log{suffix}.csv"
                self._write_manifest_csv(contaminated_tickets, csv_path)
        
        # Daily summary CSV
        if csv_config.get("daily_summary", True):
            csv_path = csv_dir / f"daily_summary{suffix}.csv"
            self._write_daily_summary_csv(tickets, csv_path)
    
    def _write_invoice_csv(self, tickets: list[dict], path: Path):
        """Write invoice matching CSV."""
        try:
            import csv
            
            with open(path, "w", newline="") as f:
                writer = csv.writer(f, delimiter="|")
                writer.writerow([
                    "ticket_number", "vendor", "date", "material",
                    "quantity", "units", "file_ref"
                ])
                
                for ticket in tickets:
                    writer.writerow([
                        ticket.get("ticket_number", ""),
                        ticket.get("vendor", ""),
                        ticket.get("ticket_date", ""),
                        ticket.get("material", ""),
                        ticket.get("quantity", ""),
                        ticket.get("quantity_unit", ""),
                        ticket.get("file_ref", ""),
                    ])
            
            if self.config["logging"]["log_output_operations"]:
                self.logger.info(f"✓ Wrote invoice CSV: {path}")
        except Exception as e:
            self.logger.error(f"Failed to write invoice CSV to {path}: {e}")
    
    def _write_manifest_csv(self, tickets: list[dict], path: Path):
        """Write manifest log CSV for contaminated material."""
        try:
            import csv
            
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "ticket_number", "manifest_number", "date", "source",
                    "waste_facility", "material", "quantity", "units", "file_ref"
                ])
                
                for ticket in tickets:
                    writer.writerow([
                        ticket.get("ticket_number", ""),
                        ticket.get("manifest_number", ""),
                        ticket.get("ticket_date", ""),
                        ticket.get("source", ""),
                        ticket.get("destination", ""),
                        ticket.get("material", ""),
                        ticket.get("quantity", ""),
                        ticket.get("quantity_unit", ""),
                        ticket.get("file_ref", ""),
                    ])
            
            if self.config["logging"]["log_output_operations"]:
                self.logger.info(f"✓ Wrote manifest CSV: {path}")
        except Exception as e:
            self.logger.error(f"Failed to write manifest CSV to {path}: {e}")
    
    def _write_daily_summary_csv(self, tickets: list[dict], path: Path):
        """Write daily summary CSV."""
        try:
            import csv
            from collections import defaultdict
            
            # Group by date
            daily_counts = defaultdict(lambda: {"total": 0, "by_material": defaultdict(int)})
            
            for ticket in tickets:
                date = ticket.get("ticket_date", "unknown")
                material = ticket.get("material", "unknown")
                
                daily_counts[date]["total"] += 1
                daily_counts[date]["by_material"][material] += 1
            
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "total_loads", "material_breakdown"])
                
                for date, counts in sorted(daily_counts.items()):
                    material_str = "; ".join([
                        f"{mat}: {count}" for mat, count in counts["by_material"].items()
                    ])
                    writer.writerow([date, counts["total"], material_str])
            
            if self.config["logging"]["log_output_operations"]:
                self.logger.info(f"✓ Wrote daily summary CSV: {path}")
        except Exception as e:
            self.logger.error(f"Failed to write daily summary CSV to {path}: {e}")
    
    def _write_excel_workbook(self, tickets: list[dict], path: Path):
        """Write Excel tracking workbook (10 sheets per spec)."""
        try:
            # TODO: Implement full Excel export with 10 sheets
            # For now, create a simple workbook
            import openpyxl
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "All Tickets"
            
            # Headers
            ws.append([
                "Ticket Number", "Date", "Vendor", "Material",
                "Source", "Destination", "Quantity", "Units", "Manifest"
            ])
            
            # Data
            for ticket in tickets:
                ws.append([
                    ticket.get("ticket_number", ""),
                    ticket.get("ticket_date", ""),
                    ticket.get("vendor", ""),
                    ticket.get("material", ""),
                    ticket.get("source", ""),
                    ticket.get("destination", ""),
                    ticket.get("quantity", ""),
                    ticket.get("quantity_unit", ""),
                    ticket.get("manifest_number", ""),
                ])
            
            wb.save(path)
            
            if self.config["logging"]["log_output_operations"]:
                self.logger.info(f"✓ Wrote Excel workbook: {path}")
        except Exception as e:
            self.logger.error(f"Failed to write Excel workbook to {path}: {e}")
    
    def write_review_queue(self, review_items: list[dict], suffix: str = ""):
        """Write review queue items to configured outputs.
        
        Args:
            review_items: List of items requiring manual review
            suffix: Optional filename suffix
        """
        if not review_items:
            return
        
        # Write to database if enabled
        if self.database_enabled and self.config["database"].get("write_review_queue", True):
            self._write_review_queue_to_database(review_items)
        
        # Write to file if enabled
        if self.file_outputs_enabled:
            if self.config["file_outputs"]["csv_exports"].get("review_queue", True):
                base_dir = Path(self.config["file_outputs"]["base_directory"])
                csv_path = base_dir / "csv" / f"review_queue{suffix}.csv"
                self._write_review_queue_csv(review_items, csv_path)
    
    def _write_review_queue_to_database(self, review_items: list[dict]):
        """Write review queue to database."""
        # TODO: Implement when database operations are complete
        self.logger.info(f"Would write {len(review_items)} review items to database")
    
    def _write_review_queue_csv(self, review_items: list[dict], path: Path):
        """Write review queue CSV."""
        try:
            import csv
            
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "page_id", "reason", "severity", "file_path", "page_num",
                    "detected_fields", "suggested_fixes", "created_at"
                ])
                
                for item in review_items:
                    writer.writerow([
                        item.get("page_id", ""),
                        item.get("reason", ""),
                        item.get("severity", ""),
                        item.get("file_path", ""),
                        item.get("page_num", ""),
                        json.dumps(item.get("detected_fields", {})),
                        json.dumps(item.get("suggested_fixes", {})),
                        item.get("created_at", datetime.now().isoformat()),
                    ])
            
            if self.config["logging"]["log_output_operations"]:
                self.logger.info(f"✓ Wrote review queue CSV: {path}")
        except Exception as e:
            self.logger.error(f"Failed to write review queue CSV to {path}: {e}")
    
    def get_output_summary(self) -> dict:
        """Get summary of current output configuration.
        
        Returns:
            Dictionary with output configuration status
        """
        return {
            "database_enabled": self.database_enabled,
            "file_outputs_enabled": self.file_outputs_enabled,
            "output_modes": self._get_active_modes(),
            "base_directory": self.config["file_outputs"].get("base_directory", "N/A"),
        }
    
    def _get_active_modes(self) -> list[str]:
        """Get list of active output modes."""
        modes = []
        if self.database_enabled:
            modes.append("SQL Server Database")
        if self.file_outputs_enabled:
            if self.config["file_outputs"]["csv_exports"]["enabled"]:
                modes.append("CSV Files")
            if self.config["file_outputs"]["excel_exports"]["enabled"]:
                modes.append("Excel Workbooks")
            if self.config["file_outputs"]["json_exports"]["enabled"]:
                modes.append("JSON Files")
        return modes
