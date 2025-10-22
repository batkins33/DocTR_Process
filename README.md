# DocTR Process

[![CI](https://github.com/batkins33/DocTR_Process/workflows/CI/badge.svg)](https://github.com/batkins33/DocTR_Process/actions)

DocTR Process provides an OCR pipeline for extracting ticket data from PDF or image files. It combines legacy DocTR and TicketSorter functionality into a clean, modular package.

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
git clone https://github.com/batkins33/DocTR_Process.git
cd DocTR_Process
pip install -r requirements.txt
```

For development with testing tools:

```bash
pip install -r requirements-dev.txt
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
# Using console script
doctr-process --input samples --output outputs --no-gui

# Using module
python -m doctr_process --input samples --output outputs --no-gui

# Show help
doctr-process --help

# Show version
doctr-process --version

# Dry run (show what would be processed)
doctr-process --input samples --output outputs --no-gui --dry-run

# With post-OCR corrections
doctr-process --input samples --output outputs --no-gui --corrections-file data/corrections.jsonl

# Using custom dictionaries for fuzzy matching
doctr-process --input samples --output outputs --no-gui --dict-vendors vendors.csv --dict-materials materials.csv
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

## Configuration

### Default Configuration Location

Configuration files are packaged with the application and located at:
- `src/doctr_process/configs/config.yaml` - Main configuration
- `src/doctr_process/configs/extraction_rules.yaml` - Field extraction rules
- `src/doctr_process/configs/ocr_keywords.csv` - Vendor keywords

### Overriding Configuration

The GUI automatically creates and manages configuration files. For command-line usage, you can:

1. **Use GUI to generate config**: Run `doctr-gui`, configure settings, and run once to generate config files
2. **Environment variables**: Set SharePoint credentials via environment:
   ```bash
   export SHAREPOINT_USERNAME=your.user@example.com
   export SHAREPOINT_PASSWORD=secret
   ```

### Configuration Files

- **config.yaml**: Main application settings (input/output paths, OCR engine, etc.)
- **extraction_rules.yaml**: Defines how to extract fields from different document types
- **ocr_keywords.csv**: Keywords for vendor identification

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

## Output

Processed files and logs are written to the configured output directory (default: `outputs/`):

- `logs/` - Application logs with daily rotation
- `ocr/` - OCR results and extracted data
- `vendor_docs/` - Organized documents by vendor
- `ticket_number/` - Ticket analysis reports
- `data/corrections.jsonl` - Post-OCR correction memory

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

## License

This project is provided under the MIT license.

## Working with Amazon Q

- Add the `amazon-q` label to route issues to Amazon Q
- Comment `/q dev` on issues to trigger Q implementation
- Q will respond with a pull request linked to the issue