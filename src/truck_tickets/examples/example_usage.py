"""Example usage of the truck ticket processing system with flexible output configuration."""

import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from truck_tickets.utils import OutputManager


# Example 1: File outputs only (current working mode)
def example_file_outputs_only():
    """Process tickets and write to local files only."""
    print("\n" + "=" * 60)
    print("Example 1: File Outputs Only (Current Mode)")
    print("=" * 60)

    # Initialize output manager (reads config/output_config.yml)
    output_mgr = OutputManager()

    # Check configuration
    summary = output_mgr.get_output_summary()
    print("\nOutput Configuration:")
    print(f"  Database Enabled: {summary['database_enabled']}")
    print(f"  File Outputs Enabled: {summary['file_outputs_enabled']}")
    print(f"  Active Modes: {', '.join(summary['output_modes'])}")
    print(f"  Output Directory: {summary['base_directory']}")

    # Sample extracted tickets
    sample_tickets = [
        {
            "ticket_number": "WM-12345678",
            "ticket_date": "2024-10-17",
            "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
            "material": "CLASS_2_CONTAMINATED",
            "material_class": "CONTAMINATED",
            "source": "PIER_EX",
            "destination": "WASTE_MANAGEMENT_LEWISVILLE",
            "quantity": 18.5,
            "quantity_unit": "TONS",
            "manifest_number": "WM-MAN-2024-001234",
            "file_ref": "sample.pdf-p1",
        },
        {
            "ticket_number": "LDI7654321",
            "ticket_date": "2024-10-17",
            "vendor": "LDI_YARD",
            "material": "NON_CONTAMINATED",
            "material_class": "CLEAN",
            "source": "SPG",
            "destination": "LDI_YARD",
            "quantity": 15.0,
            "quantity_unit": "TONS",
            "file_ref": "sample.pdf-p2",
        },
    ]

    # Write tickets to configured outputs
    output_mgr.write_tickets(sample_tickets, job_code="24-105")

    print("\n✓ Tickets written to file outputs")
    print(
        f"  Check: {Path(output_mgr.config['file_outputs']['base_directory']).absolute()}"
    )


# Example 2: Database only (when ready)
def example_database_only():
    """Process tickets and write to database only."""
    print("\n" + "=" * 60)
    print("Example 2: Database Only (Future Mode)")
    print("=" * 60)
    print("\nTo enable database-only mode:")
    print("1. Edit config/output_config.yml:")
    print("   database.enabled: true")
    print("   file_outputs.enabled: false")
    print("2. Set environment variables:")
    print("   TRUCK_TICKETS_DB_SERVER=localhost")
    print("   TRUCK_TICKETS_DB_NAME=TruckTicketsDB")
    print("3. Run schema setup: python src/truck_tickets/database/schema_setup.py")


# Example 3: Both database and files (dual mode)
def example_dual_mode():
    """Process tickets and write to both database and files."""
    print("\n" + "=" * 60)
    print("Example 3: Dual Mode - Database + Files")
    print("=" * 60)
    print("\nTo enable dual mode:")
    print("1. Edit config/output_config.yml:")
    print("   database.enabled: true")
    print("   file_outputs.enabled: true")
    print("2. Both outputs will be written simultaneously")
    print("3. Useful for validation and backup during transition")


# Example 4: Selective file outputs
def example_selective_outputs():
    """Configure which file types to generate."""
    print("\n" + "=" * 60)
    print("Example 4: Selective File Outputs")
    print("=" * 60)
    print("\nCustomize which files are generated in config/output_config.yml:")
    print("\nfile_outputs:")
    print("  csv_exports:")
    print("    invoice_matching: true   # Generate invoice CSV")
    print("    manifest_log: true       # Generate manifest CSV")
    print("    daily_summary: false     # Skip daily summary")
    print("  excel_exports:")
    print("    tracking_workbook: true  # Generate Excel workbook")
    print("  json_exports:")
    print("    processed_tickets: true  # Save as JSON")


# Example 5: Review queue handling
def example_review_queue():
    """Handle tickets that need manual review."""
    print("\n" + "=" * 60)
    print("Example 5: Review Queue")
    print("=" * 60)

    output_mgr = OutputManager()

    # Sample review items
    review_items = [
        {
            "page_id": "sample.pdf-p3",
            "reason": "MISSING_MANIFEST",
            "severity": "CRITICAL",
            "file_path": "sample.pdf",
            "page_num": 3,
            "detected_fields": {
                "ticket_number": "WM-99999999",
                "material": "CLASS_2_CONTAMINATED",
            },
            "suggested_fixes": {
                "action": "manual_entry",
                "note": "Contaminated material requires manifest number",
            },
        }
    ]

    # Write review queue
    output_mgr.write_review_queue(review_items, suffix="_20241104")

    print("\n✓ Review queue written")
    print("  Items requiring manual review have been logged")


# Example 6: Programmatic configuration override
def example_programmatic_config():
    """Override configuration programmatically."""
    print("\n" + "=" * 60)
    print("Example 6: Programmatic Configuration")
    print("=" * 60)

    # Load default config
    output_mgr = OutputManager()

    # Override specific settings
    output_mgr.config["file_outputs"]["csv_exports"]["invoice_matching"] = False
    output_mgr.config["file_outputs"]["naming"]["use_timestamps"] = False

    print("\n✓ Configuration overridden programmatically")
    print("  invoice_matching: disabled")
    print("  timestamps: disabled")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TRUCK TICKET PROCESSING - OUTPUT CONFIGURATION EXAMPLES")
    print("=" * 60)

    # Run examples
    example_file_outputs_only()
    example_database_only()
    example_dual_mode()
    example_selective_outputs()
    example_review_queue()
    example_programmatic_config()

    print("\n" + "=" * 60)
    print("CONFIGURATION FILE LOCATION")
    print("=" * 60)
    print("\nEdit: src/truck_tickets/config/output_config.yml")
    print("to change output behavior")
    print("\nCurrent defaults:")
    print("  ✓ File outputs: ENABLED")
    print("  ✗ Database: DISABLED")
    print("\n")
