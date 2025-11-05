# Output Configuration Guide

## Overview

The truck ticket processing system now supports **flexible output configuration**, allowing you to:

- ✅ **Work with local file outputs** (CSV, Excel, JSON) - Current default
- ✅ **Enable SQL Server database** when ready
- ✅ **Use both simultaneously** for validation/backup
- ✅ **Toggle individual output types** (e.g., only CSV, no Excel)

## Quick Start

### Current Configuration (Default)

**File outputs ENABLED, Database DISABLED**

```yaml
# config/output_config.yml
database:
  enabled: false  # Database writes disabled

file_outputs:
  enabled: true   # File outputs enabled
  base_directory: "outputs"
```

This is the **current working mode** - all extracted ticket data is written to local files in the `outputs/` directory.

## Configuration File

Location: `src/truck_tickets/config/output_config.yml`

### Database Settings

```yaml
database:
  enabled: false  # Set to true to enable database writes
  connection:
    server: "localhost"
    database: "TruckTicketsDB"
    use_env_vars: true  # Read from environment variables
    trusted_connection: true  # Windows authentication
  
  # What to write when enabled
  write_tickets: true
  write_review_queue: true
  write_processing_runs: true
  check_duplicates: true
```

**Environment Variables (when `use_env_vars: true`):**
```powershell
$env:TRUCK_TICKETS_DB_SERVER = "localhost"
$env:TRUCK_TICKETS_DB_NAME = "TruckTicketsDB"
# Optional for SQL Server auth:
# $env:TRUCK_TICKETS_DB_USERNAME = "username"
# $env:TRUCK_TICKETS_DB_PASSWORD = "password"
```

### File Output Settings

```yaml
file_outputs:
  enabled: true
  base_directory: "outputs"
  
  csv_exports:
    enabled: true
    invoice_matching: true    # invoice_match.csv
    manifest_log: true        # manifest_log.csv
    review_queue: true        # review_queue.csv
    daily_summary: true       # daily_summary.csv
  
  excel_exports:
    enabled: true
    tracking_workbook: true   # tracking_export.xlsx
  
  json_exports:
    enabled: true
    raw_extraction: true      # Raw OCR results
    processed_tickets: true   # Processed ticket data
  
  naming:
    use_timestamps: true      # Add timestamp to filenames
    use_job_code: true        # Add job code to filenames
    timestamp_format: "%Y%m%d_%H%M%S"
```

## Output Directory Structure

When file outputs are enabled:

```
outputs/
├── csv/
│   ├── invoice_match_24-105_20241104_153000.csv
│   ├── manifest_log_24-105_20241104_153000.csv
│   ├── review_queue_20241104_153000.csv
│   └── daily_summary_24-105_20241104_153000.csv
├── excel/
│   └── tracking_export_24-105_20241104_153000.xlsx
└── json/
    ├── raw_extraction_20241104_153000.json
    └── processed_tickets_24-105_20241104_153000.json
```

## Usage Examples

### Example 1: File Outputs Only (Current Mode)

```python
from truck_tickets.utils import OutputManager

# Initialize with default config
output_mgr = OutputManager()

# Process tickets
tickets = [
    {
        "ticket_number": "WM-12345678",
        "ticket_date": "2024-10-17",
        "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
        "material": "CLASS_2_CONTAMINATED",
        # ... other fields
    }
]

# Write to file outputs
output_mgr.write_tickets(tickets, job_code="24-105")

# Check what was written
summary = output_mgr.get_output_summary()
print(f"Database: {summary['database_enabled']}")
print(f"Files: {summary['file_outputs_enabled']}")
print(f"Modes: {summary['output_modes']}")
```

**Output:**
```
Database: False
Files: True
Modes: ['CSV Files', 'Excel Workbooks', 'JSON Files']
✓ Wrote JSON: outputs/json/processed_tickets_24-105_20241104_153000.json
✓ Wrote invoice CSV: outputs/csv/invoice_match_24-105_20241104_153000.csv
✓ Wrote manifest CSV: outputs/csv/manifest_log_24-105_20241104_153000.csv
✓ Wrote daily summary CSV: outputs/csv/daily_summary_24-105_20241104_153000.csv
✓ Wrote Excel workbook: outputs/excel/tracking_export_24-105_20241104_153000.xlsx
```

### Example 2: Enable Database (When Ready)

**Step 1:** Edit `config/output_config.yml`:
```yaml
database:
  enabled: true  # Enable database writes
```

**Step 2:** Set environment variables:
```powershell
$env:TRUCK_TICKETS_DB_SERVER = "localhost"
$env:TRUCK_TICKETS_DB_NAME = "TruckTicketsDB"
```

**Step 3:** Create database schema:
```powershell
cd src/truck_tickets/database
python schema_setup.py
python schema_setup.py --seed
```

**Step 4:** Use normally:
```python
output_mgr = OutputManager()
output_mgr.write_tickets(tickets, job_code="24-105")
# Now writes to database AND files (if both enabled)
```

### Example 3: Dual Mode (Database + Files)

```yaml
# config/output_config.yml
database:
  enabled: true   # Write to database
  
file_outputs:
  enabled: true   # Also write to files
```

**Use case:** Validation during transition - compare database records against file outputs to ensure accuracy.

### Example 4: Selective File Outputs

Only generate CSV files, skip Excel and JSON:

```yaml
file_outputs:
  enabled: true
  csv_exports:
    enabled: true
  excel_exports:
    enabled: false  # Skip Excel
  json_exports:
    enabled: false  # Skip JSON
```

### Example 5: Database Only (No Files)

```yaml
database:
  enabled: true
  
file_outputs:
  enabled: false  # No file outputs
```

## Transition Plan

### Phase 1: Current State (File Outputs)
✅ **You are here**
- Database: DISABLED
- File outputs: ENABLED
- Work with local CSV/Excel/JSON files

### Phase 2: Validation (Dual Mode)
- Database: ENABLED
- File outputs: ENABLED
- Write to both, compare results
- Verify database records match file outputs

### Phase 3: Production (Database Primary)
- Database: ENABLED
- File outputs: OPTIONAL (backup/reporting only)
- Database is primary source of truth

## Configuration Scenarios

### Scenario 1: Development/Testing
```yaml
database:
  enabled: false
file_outputs:
  enabled: true
  json_exports:
    raw_extraction: true  # Save OCR results for debugging
```

### Scenario 2: Field Deployment
```yaml
database:
  enabled: false
file_outputs:
  enabled: true
  csv_exports:
    invoice_matching: true
    manifest_log: true
  excel_exports:
    tracking_workbook: true
```

### Scenario 3: Office Processing
```yaml
database:
  enabled: true
  check_duplicates: true
file_outputs:
  enabled: true
  csv_exports:
    invoice_matching: true  # For accounting team
```

## Programmatic Configuration

Override configuration in code:

```python
from truck_tickets.utils import OutputManager

# Load default config
output_mgr = OutputManager()

# Override specific settings
output_mgr.config["file_outputs"]["csv_exports"]["invoice_matching"] = False
output_mgr.config["file_outputs"]["naming"]["use_timestamps"] = False

# Use with overrides
output_mgr.write_tickets(tickets, job_code="24-105")
```

## Review Queue

Review queue items (pages needing manual review) are written to configured outputs:

```python
review_items = [
    {
        "page_id": "sample.pdf-p3",
        "reason": "MISSING_MANIFEST",
        "severity": "CRITICAL",
        "file_path": "sample.pdf",
        "page_num": 3,
        "detected_fields": {"ticket_number": "WM-99999999"},
        "suggested_fixes": {"action": "manual_entry"}
    }
]

output_mgr.write_review_queue(review_items, suffix="_20241104")
```

**Outputs:**
- Database: `review_queue` table (if enabled)
- File: `outputs/csv/review_queue_20241104.csv`

## Logging

Control output operation logging:

```yaml
logging:
  log_output_operations: true  # Log when data is written
  log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR
```

**Log output:**
```
2024-11-04 15:30:00 - OutputManager - INFO - Loaded output configuration
2024-11-04 15:30:00 - OutputManager - INFO - Output directories ready at u:\Dev\projects\DocTR_Process\outputs
2024-11-04 15:30:01 - OutputManager - INFO - ✓ Wrote JSON: outputs/json/processed_tickets_24-105_20241104_153000.json
2024-11-04 15:30:01 - OutputManager - INFO - ✓ Wrote invoice CSV: outputs/csv/invoice_match_24-105_20241104_153000.csv
```

## Testing

Run the example script to test configuration:

```powershell
cd src/truck_tickets
python examples/example_usage.py
```

This demonstrates all configuration modes and generates sample outputs.

## Troubleshooting

### Issue: No outputs generated
**Check:**
1. Is `file_outputs.enabled: true` in config?
2. Does `outputs/` directory exist?
3. Check logs for errors

### Issue: Database connection failed
**Check:**
1. Is `database.enabled: true` in config?
2. Are environment variables set?
3. Is SQL Server running?
4. Run: `python src/truck_tickets/database/schema_setup.py`

### Issue: Permission denied writing files
**Check:**
1. Does user have write access to `outputs/` directory?
2. Try absolute path in `base_directory` setting

## Summary

**Current Recommendation:** Keep file outputs enabled while developing and testing. Enable database when ready for production deployment.

**Key Benefits:**
- ✅ Continue working with familiar file outputs
- ✅ Easy transition to database when ready
- ✅ Flexible configuration for different scenarios
- ✅ No code changes needed - just config file edits

**Configuration File:** `src/truck_tickets/config/output_config.yml`
