# DocTR Process

[![CI](https://github.com/USERNAME/DocTR_Process/workflows/CI/badge.svg)](https://github.com/USERNAME/DocTR_Process/actions)

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
git clone <repository-url>
cd DocTR_Process
pip install -e .
```

For development with testing tools:

```bash
pip install -e ".[dev]"
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

## Output

Processed files and logs are written to the configured output directory (default: `outputs/`):

- `logs/` - Application logs with daily rotation
- `ocr/` - OCR results and extracted data
- `vendor_docs/` - Organized documents by vendor
- `ticket_number/` - Ticket analysis reports

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