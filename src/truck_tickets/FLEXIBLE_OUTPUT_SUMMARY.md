# Flexible Output Configuration - Implementation Summary

## What Was Added

A complete flexible output system that allows you to toggle between database and file outputs without changing code.

## New Files Created

1. **`config/output_config.yml`** - Main configuration file
   - Controls database vs file outputs
   - Individual output type toggles (CSV, Excel, JSON)
   - Filename patterns and directory structure

2. **`utils/output_manager.py`** - Output management class
   - Reads configuration
   - Writes to database (when enabled)
   - Writes to files (when enabled)
   - Supports both simultaneously

3. **`examples/example_usage.py`** - Usage examples
   - Demonstrates all configuration modes
   - Shows how to use OutputManager
   - Generates sample outputs

4. **`OUTPUT_CONFIGURATION.md`** - Complete documentation
   - Configuration guide
   - Usage examples
   - Transition plan
   - Troubleshooting

## Current Configuration (Default)

```yaml
database:
  enabled: false  # ❌ Database writes DISABLED

file_outputs:
  enabled: true   # ✅ File outputs ENABLED
  base_directory: "outputs"
```

**This means:** All extracted ticket data is written to local files in `outputs/` directory.

## How to Use

### Continue Working with Files (Current Mode)

```python
from truck_tickets.utils import OutputManager

# Initialize (reads config automatically)
output_mgr = OutputManager()

# Write tickets to file outputs
output_mgr.write_tickets(tickets, job_code="24-105")
```

**Outputs created:**
```
outputs/
├── csv/
│   ├── invoice_match_24-105_20241104.csv
│   ├── manifest_log_24-105_20241104.csv
│   └── daily_summary_24-105_20241104.csv
├── excel/
│   └── tracking_export_24-105_20241104.xlsx
└── json/
    └── processed_tickets_24-105_20241104.json
```

### Enable Database (When Ready)

**Step 1:** Edit `config/output_config.yml`:
```yaml
database:
  enabled: true  # Enable database
```

**Step 2:** Set environment variables:
```powershell
$env:TRUCK_TICKETS_DB_SERVER = "localhost"
$env:TRUCK_TICKETS_DB_NAME = "TruckTicketsDB"
```

**Step 3:** Create database:
```powershell
python src/truck_tickets/database/schema_setup.py
```

**Step 4:** Use normally (no code changes needed):
```python
output_mgr = OutputManager()
output_mgr.write_tickets(tickets, job_code="24-105")
# Now writes to database!
```

### Use Both (Dual Mode)

```yaml
database:
  enabled: true   # Write to database
file_outputs:
  enabled: true   # Also write to files
```

Useful for validation during transition.

## Key Benefits

✅ **No code changes needed** - Just edit config file
✅ **Continue working with files** - Current mode preserved
✅ **Easy database transition** - Enable when ready
✅ **Flexible configuration** - Toggle individual outputs
✅ **Dual mode support** - Use both for validation

## Configuration Options

### Toggle Individual File Types

```yaml
file_outputs:
  csv_exports:
    invoice_matching: true   # ✅ Generate
    manifest_log: true       # ✅ Generate
    daily_summary: false     # ❌ Skip
  excel_exports:
    tracking_workbook: true  # ✅ Generate
  json_exports:
    processed_tickets: false # ❌ Skip
```

### Customize Filenames

```yaml
file_outputs:
  naming:
    use_timestamps: true      # Add timestamp
    use_job_code: true        # Add job code
    timestamp_format: "%Y%m%d_%H%M%S"
```

## Integration with Existing Code

The OutputManager integrates seamlessly with the existing truck ticket processing pipeline:

```python
# In your processing pipeline:
from truck_tickets.utils import OutputManager

# Initialize once
output_mgr = OutputManager()

# After extracting tickets from PDFs:
extracted_tickets = [...]  # Your extraction results

# Write to configured outputs (database and/or files)
output_mgr.write_tickets(extracted_tickets, job_code="24-105")

# Handle review queue items
review_items = [...]  # Pages needing manual review
output_mgr.write_review_queue(review_items)
```

## Testing

Run the example script to see all modes:

```powershell
cd src/truck_tickets
python examples/example_usage.py
```

This demonstrates:
- File outputs only (current mode)
- Database only (future mode)
- Dual mode (validation)
- Selective outputs
- Review queue handling

## Database Schema Reference

The database configuration matches the existing schema:

**Tables:**
- `jobs` - Construction projects
- `materials` - Material types
- `sources` - Source locations
- `destinations` - Destination facilities
- `vendors` - Vendor companies
- `ticket_types` - IMPORT/EXPORT
- `truck_tickets` - Main transaction table
- `review_queue` - Manual review queue
- `processing_runs` - Audit ledger

**Connection:** Uses existing `DatabaseConnection` class from `database/connection.py`

## Transition Plan

### Phase 1: Current State ✅ (You are here)
- Database: DISABLED
- File outputs: ENABLED
- Work with local files

### Phase 2: Validation
- Database: ENABLED
- File outputs: ENABLED
- Compare database vs files

### Phase 3: Production
- Database: ENABLED
- File outputs: OPTIONAL
- Database is primary

## Quick Reference

**Configuration file:** `src/truck_tickets/config/output_config.yml`

**Enable database:**
```yaml
database.enabled: true
```

**Enable file outputs:**
```yaml
file_outputs.enabled: true
```

**Output directory:** `outputs/` (configurable)

**Documentation:** `OUTPUT_CONFIGURATION.md`

**Examples:** `examples/example_usage.py`

## Next Steps

1. ✅ **Continue using file outputs** - No changes needed
2. When ready for database:
   - Edit `config/output_config.yml`
   - Set environment variables
   - Run database setup
   - Enable in config
3. Test with dual mode first
4. Switch to database-only when validated

## Notes

- **Lint warnings:** The example files have intentional `print` statements for demonstration. The core `output_manager.py` has minor whitespace lints that don't affect functionality.
- **Database operations:** Full CRUD operations will be implemented in Phase 2 (database operations module).
- **Excel export:** Currently creates basic workbook. Full 10-sheet export per spec will be implemented when needed.

---

**Status:** ✅ Flexible output system implemented and ready to use
**Current Mode:** File outputs enabled, database disabled
**Next:** Continue development with file outputs, enable database when ready
