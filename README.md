# DocTR Process

[![CI](https://github.com/batkins33/DocTR_Process/workflows/CI/badge.svg)](https://github.com/batkins33/DocTR_Process/actions)

**Project 24-105: Construction Site Material Tracking System**

DocTR Process provides specialized OCR pipeline for processing construction truck tickets. The system extracts ticket data from multi-page PDFs and populates a SQL Server database for material movement tracking with regulatory compliance features.

## Installation

### System Dependencies

Install **Tesseract** and **Poppler** for OCR and PDF rendering:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr poppler-utils

# macOS
brew install tesseract poppler

# Windows
# Download and install from official websites
```

### Development Install

```bash
# Clone the repository
git clone https://github.com/batkins33/DocTR_Process.git
cd DocTR_Process

# Install dependencies
pip install -r requirements.txt

# Development install with testing tools
pip install -e ".[dev]"
```

Or install as an editable package:

```bash
pip install -e .
pip install -e ".[dev]"  # with dev dependencies
```

## Usage

### Command Line Interface

Run the pipeline from command line:

```bash
# Process folder of PDFs
python -m truck_tickets process --input "C:\tickets\2024-10-17" --job 24-105

# Export tracking reports
python -m truck_tickets export --job 24-105 --output tracking.xlsx

# Generate manifest compliance log
python -m truck_tickets manifest --job 24-105 --output manifest_log.csv

# Dry run to preview processing
python -m truck_tickets process --input "C:\tickets\2024-10-17" --job 24-105 --dry-run
```

### Graphical User Interface

Launch the GUI application:

```bash
# Using console script
doctr-gui

# Using module
python -m doctr_process.gui
```

### Available Commands

- `doctr-process` - Main CLI application
- `doctr-gui` - GUI application
- `python -m doctr_process` - Alternative CLI entry point
- `python -m doctr_process.gui` - Alternative GUI entry point

## ⚙️ Configuration

### Environment Variables

```bash
# Database connection (required)
TRUCK_TICKETS_DB_SERVER=localhost
TRUCK_TICKETS_DB_NAME=TruckTicketsDB

# SQL Server authentication (optional)
TRUCK_TICKETS_DB_USERNAME=your_username
TRUCK_TICKETS_DB_PASSWORD=your_password
```

### Configuration Files

Located in `src/truck_tickets/config/`:

- **`synonyms.json`** - Text normalization mappings for vendors, materials, locations
- **`filename_schema.yml`** - Structured filename parsing rules
- **`acceptance.yml`** - Quality thresholds and performance targets
- **`output_config.yml`** - Database/file output configuration

### Vendor Templates

Located in `src/truck_tickets/templates/vendors/`:

- **`WM_LEWISVILLE.yml`** - Waste Management template
- **`LDI_YARD.yml`** - LDI Yard template
- **`POST_OAK_PIT.yml`** - Post Oak template

Add new vendor templates by creating YAML files with extraction rules and ROI definitions.

## Post-OCR Corrections

The system includes an intelligent correction layer that learns from user-approved fixes without retraining OCR models.

### Features

- **Memory-based corrections**: Stores user-approved fixes in JSONL format for future use
- **Regex validators**: Fixes common OCR errors in ticket numbers, money amounts, and dates
- **Fuzzy dictionaries**: Matches vendor names, materials, and cost codes using fuzzy string matching
- **Confusion character handling**: Automatically fixes common OCR character confusions (O↔0, S↔5, etc.)

### CLI Options

```bash
--corrections-file PATH     # Path to corrections memory file (default: data/corrections.jsonl)
--dict-vendors PATH         # CSV file with vendor names for fuzzy matching
--dict-materials PATH       # CSV file with material names
--dict-costcodes PATH       # CSV file with cost codes
--no-fuzzy                  # Disable fuzzy dictionary matching
--learn-low                 # Allow storing fuzzy matches ≥90 score
--learn-high                # Require fuzzy matches ≥95 score (default)
--dry-run                   # Apply corrections in memory but don't save to corrections file
```

### Output Format

Corrected outputs include audit columns:
- `record_id` - Unique identifier for each record
- `raw_*` columns - Original OCR values before correction
- Correction logs show old→new changes with reasons

### Memory File Format

Corrections are stored in JSONL format:
```json
{"field":"vendor","wrong":"LINDAMOOD DEM0LITION","right":"Lindamood Demolition","context":{"score":95},"ts":1640995200}
```

## 📊 Data Model

### Main Transaction: TruckTicket

- `ticket_number` - Unique ticket identifier
- `ticket_date` - Date of haul
- `quantity` / `quantity_unit` - Load size (tons/cy/loads)
- `job_id` - Construction project (e.g., "24-105")
- `material_id` - Material type (contaminated, clean, waste, import)
- `source_id` - Excavation area (for exports)
- `destination_id` - Disposal/delivery facility
- `vendor_id` - Hauler company
- `manifest_number` - Regulatory manifest (contaminated only)
- `ticket_type_id` - IMPORT/EXPORT classification

### Reference Tables

- `jobs` - Construction projects with phases
- `materials` - Material types with regulatory classifications
- `vendors` - Vendor companies with canonical names
- `sources` - Source locations (excavation areas)
- `destinations` - Destination facilities
- `ticket_types` - IMPORT/EXPORT classifications

### Duplicate Detection

Uses `(ticket_number, vendor_id)` within a 120-day rolling window to prevent duplicate entries.

## Testing

Run the test suite:

```bash
pytest
```

Run smoke tests only:

```bash
pytest tests/test_smoke.py
```

## Logging & Troubleshooting

- Logs are written to `logs/` with daily rotation
- Error logs: `logs/doctr_app.error.log` (size-rotated)
- Each run has a unique `run_id` for tracing across log files
- Include error logs when filing bug reports

## Development

### Project Structure

```
src/doctr_process/
├── configs/          # Default configuration files
├── assets/           # Application assets (logos, etc.)
├── ocr/             # OCR processing modules
├── output/          # Output handlers (CSV, Excel, etc.)
├── processor/       # File processing utilities
├── utils/           # Utility modules
├── main.py          # CLI entry point
└── gui.py           # GUI entry point
```

### Adding New Features

1. Install development dependencies: `pip install -e ".[dev]"`
2. Make changes
3. Run tests: `pytest`
4. Run smoke tests: `pytest tests/test_smoke.py`

## 📋 Workflow

### 1. Field Team Scans Tickets
- Scan multi-page PDF (one file per area per day)
- Use structured filename: `24-105__2024-10-17__PIER_EX__EXPORT__CLASS_2_CONTAMINATED__WM_LEWISVILLE.pdf`
- Upload to shared drive

### 2. Automated Processing
- Extract text via OCR (DocTR)
- Identify vendor (logo + keywords)
- Extract fields per vendor template
- Normalize text via synonyms
- Check for duplicates
- Insert into database

### 3. Review Queue (if needed)
- Low confidence extractions flagged
- Missing required fields flagged
- Export review queue CSV
- Manual correction workflow

### 4. Export Reports
- Daily tracking spreadsheet (Excel)
- Invoice matching CSV (by vendor)
- Manifest compliance log (CSV)
- Weekly/monthly summaries

## 🚨 Compliance Features

### Manifest Tracking (CRITICAL)

For contaminated material (Class 2), every ticket MUST have a manifest number:

- **100% recall requirement** - Never silently fails on missing manifests
- Routes missing manifests to review queue with CRITICAL severity
- Generates manifest log CSV for EPA compliance
- Flags duplicate manifests within same day

### Audit Trail

All processing runs are logged with:
- Unique batch identifier (`request_guid`)
- File counts, page counts, success/error/review counts
- Timestamps and user/system account
- Complete traceability for regulatory audits

## 📈 Performance & Scaling

### Benchmarks
- **≤3 seconds per page** on target workstation
- **1200 pages/hour** batch processing
- **≥95% ticket number accuracy** overall
- **100% manifest recall** (contaminated material)

### Scaling Features
- **Thread pool processing** for batch operations
- **Error recovery** with rollback capabilities
- **Progress tracking** with callback support
- **Memory-efficient** chunked file processing

## 📚 Documentation

- **`src/truck_tickets/README.md`** - Detailed module documentation
- **`src/truck_tickets/GETTING_STARTED.md`** - Quick start guide
- **`docs/`** - Complete issue documentation and standards
- **`docs/MASTER_ISSUE_TRACKER.md`** - Project progress and roadmap

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes with comprehensive tests
4. Follow documentation and type hint standards
5. Submit pull request with description

## 📄 License

Internal project - Construction Material Tracking System

## 📞 Contact

Project 24-105 Team
