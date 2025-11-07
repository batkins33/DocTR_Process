# Truck Ticket Processing System

**Project 24-105: Construction Site Material Tracking**

A specialized module for processing multi-page truck ticket PDFs from construction sites. Extracts ticket numbers, vendors, manifests, and populates a SQL Server database for tracking material movements.

## Overview

This module eliminates duplicate scanning and manual data entry by using OCR to extract:

- Ticket numbers
- Vendors
- Source locations (excavation areas)
- Destination facilities
- Manifest numbers (for contaminated material)
- Material types and quantities

## Features

### Completed Features ✅

- **Database Infrastructure** - Complete SQL Server schema with 9 tables
- **Field Extractors** - Ticket number, manifest, date, quantity, vendor detection
- **Processing Pipeline** - Complete OCR integration and batch processing
- **Duplicate Detection** - 120-day rolling window with SHA-256 file verification
- **Manifest Validation** - 100% recall for contaminated material compliance
- **Export System** - Excel tracking, CSV invoice matching, manifest logs
- **CLI Interface** - Complete command-line tools for processing and exports
- **Data Validation** - Comprehensive validation and quality reporting
- **Seed Data System** - Complete reference data management
- **Documentation** - 95%+ docstring coverage, comprehensive guides

### Remaining Tasks (10%)

- **Issue #15** - README synchronization (in progress)
- **Issue #28** - Alembic migration scripts
- **Issue #31** - Production monitoring (optional)

## Project Structure

```
truck_tickets/
├── config/                      # Configuration files
│   ├── synonyms.json           # Text normalization mappings
│   ├── filename_schema.yml     # Filename parsing rules
│   └── acceptance.yml          # Quality thresholds
├── database/                    # SQL Server integration
│   ├── connection.py           # Database connection
│   ├── schema_setup.py         # Table creation
│   └── operations.py           # CRUD operations
├── extractors/                  # Field extraction logic
│   ├── ticket_extractor.py     # Ticket number extraction
│   ├── manifest_extractor.py   # Manifest number extraction
│   └── vendor_detector.py      # Vendor identification
├── models/                      # Data models
│   ├── ticket.py               # TruckTicket model
│   └── reference_data.py       # Lookup table models
├── processors/                  # Processing pipeline
│   └── ticket_processor.py     # Main processor
├── templates/                   # Vendor templates
│   └── vendors/
│       ├── WM_LEWISVILLE.yml   # Waste Management template
│       ├── LDI_YARD.yml        # LDI Yard template
│       └── POST_OAK_PIT.yml    # Post Oak template
├── exporters/                   # Output generators
│   ├── excel_exporter.py       # Excel tracking workbook
│   ├── csv_exporter.py         # CSV reports
│   └── manifest_log.py         # Manifest compliance log
└── utils/                       # Helper utilities
    └── normalization.py        # Synonym normalization
```

## Database Setup

### 1. Install SQL Server Driver

**Windows:**
- Download and install [ODBC Driver 17 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

**Linux:**
```bash
sudo apt-get install unixodbc-dev
```

### 2. Install Python Dependencies

```bash
pip install pyodbc
```

### 3. Configure Database Connection

Set environment variables:

```bash
# Windows (PowerShell)
$env:TRUCK_TICKETS_DB_SERVER="localhost"
$env:TRUCK_TICKETS_DB_NAME="TruckTicketsDB"

# Linux/Mac
export TRUCK_TICKETS_DB_SERVER="localhost"
export TRUCK_TICKETS_DB_NAME="TruckTicketsDB"
```

For SQL Server authentication (non-Windows):
```bash
$env:TRUCK_TICKETS_DB_USERNAME="your_username"
$env:TRUCK_TICKETS_DB_PASSWORD="your_password"
```

### 4. Create Database Schema

```bash
cd src/truck_tickets/database
python schema_setup.py
```

This creates all required tables:
- `jobs` - Construction projects
- `materials` - Material types
- `sources` - Source locations
- `destinations` - Destination facilities
- `vendors` - Vendor companies
- `ticket_types` - IMPORT/EXPORT
- `truck_tickets` - Main transaction table
- `review_queue` - Manual review queue
- `processing_runs` - Audit ledger

### 5. Seed Reference Data

```bash
python schema_setup.py --seed
```

## Usage

### Basic Processing

```python
from truck_tickets import TicketProcessor
from truck_tickets.database import DatabaseConnection

# Initialize database connection
db = DatabaseConnection.from_env()

# Create processor
processor = TicketProcessor(db)

# Process a PDF file
results = processor.process_file("path/to/tickets.pdf", job_code="24-105")

print(f"Processed {results['pages_count']} pages")
print(f"Success: {results['ok_count']}, Review: {results['review_count']}")
```

### Command Line Interface

```bash
# 1. Set up database
cd src\truck_tickets\database
python schema_setup.py
python schema_setup.py --seed

# 2. Process tickets
python -m truck_tickets process --input "tickets" --job 24-105

# 3. Export reports
python -m truck_tickets export --job 24-105 --output tracking.xlsx

# Generate manifest log
python -m truck_tickets manifest --job 24-105 --output manifest_log.csv

# Seed reference data
python -m truck_tickets.database.seed_data --all --tickets 100
# Data quality report
python -m truck_tickets.database.data_validation --report
```

## Configuration

### Vendor Templates

Vendor templates define extraction rules for specific vendors. Create new templates in `templates/vendors/`:

```yaml
# templates/vendors/MY_VENDOR.yml
vendor:
  name: "MY_VENDOR"
  aliases:
    - "Vendor Name"
    - "VN"

ticket_number:
  regex:
    - pattern: '\d{7,10}'
  roi:
    x: 1400
    y: 50
    width: 200
    height: 100
  required: true

# ... other fields
```

### Synonym Normalization

Add entries to `config/synonyms.json` to normalize vendor names, locations, and materials:

```json
{
  "vendors": {
    "New Vendor Name": "CANONICAL_VENDOR_NAME"
  }
}
```

## Data Model

### Main Transaction: TruckTicket

- `ticket_number` - Unique ticket identifier
- `ticket_date` - Date of haul
- `quantity` / `quantity_unit` - Load size (tons/cy/loads)
- `job_id` - Construction project
- `material_id` - Material type
- `source_id` - Excavation area (for exports)
- `destination_id` - Disposal/delivery facility
- `vendor_id` - Hauler company
- `manifest_number` - Regulatory manifest (contaminated only)
- `file_id` / `file_page` - Source PDF reference

### Uniqueness Constraint

Duplicate tickets are detected using `(ticket_number, vendor_id)` within a 120-day rolling window.

## Compliance Features

### Manifest Tracking (CRITICAL)

For contaminated material (Class 2), every ticket MUST have a manifest number. The system:

- **100% recall requirement** - Never silently fails on missing manifests
- Routes missing manifests to review queue
- Generates manifest log CSV for EPA compliance
- Flags duplicate manifests within same day

### Audit Trail

All processing runs are logged in `processing_runs` table:
- `request_guid` - Unique batch identifier
- File counts, page counts, success/error/review counts
- Timestamps, user/system account

## Performance Targets

- **≤3 seconds per page** on target workstation
- **1200 pages/hour** batch processing
- **≥95% ticket number accuracy** overall
- **100% manifest recall** (contaminated material)

## Testing

Run tests:

```bash
pytest tests/truck_tickets/
```

Create gold standard test set:

```bash
python -m truck_tickets.testing.create_gold_standard --pages 30
```

## Workflow

### 1. Field Team Scans Tickets
- Scan multi-page PDF (one file per area per day)
- Name file: `24-105__2024-10-17__PIER_EX__EXPORT__CLASS_2_CONTAMINATED__WM_LEWISVILLE.pdf`
- Upload to shared drive

### 2. System Processes PDFs
- Extracts text via OCR (DocTR)
- Identifies vendor (logo + keywords)
- Extracts fields per vendor template
- Normalizes text via synonyms
- Checks for duplicates
- Inserts into database

### 3. Review Queue (if needed)
- Low confidence extractions flagged
- Missing required fields flagged
- Export review queue CSV
- Manual correction in GUI (future)

### 4. Export Reports
- Daily tracking spreadsheet
- Invoice matching CSV (by vendor)
- Manifest compliance log
- Weekly/monthly summaries

## Next Steps

**Immediate Requirements:**
1. Upload sample PDF files (WM Lewisville tickets)
2. Confirm SQL Server connection details
3. Provide actual filename examples from field

**Development Tasks:**
- Complete field extractors
- Build main processor
- Create Excel/CSV exporters
- Add CLI interface
- Build review queue GUI

## License

Internal project - Construction Material Tracking System

## Contact

Project 24-105 Team
