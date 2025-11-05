# DocTR Process - User Guide

## Introduction

DocTR Process is a Python tool for batch-processing scanned truck ticket PDFs and images. It extracts vendor, ticket, manifest, and other key fields using configurable YAML/CSV rules, and outputs user-friendly CSV reports.

---

## Prerequisites

### System Requirements

- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux

### System Tools

- **Tesseract OCR**: Required for OCR processing
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: Download from [Tesseract GitHub](https://github.com/tesseract-ocr/tesseract)

- **Poppler**: Required for PDF rendering
  - Ubuntu/Debian: `sudo apt-get install poppler-utils`
  - macOS: `brew install poppler`
  - Windows: Download from [Poppler Windows](http://blog.alivate.com.au/poppler-windows/) and add to PATH

### Python Packages

All required packages are automatically installed when you install DocTR Process:

```bash
pip install -r requirements.txt
```

or

```bash
pip install -e .
```

---

## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/batkins33/DocTR_Process.git
   cd DocTR_Process
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install system dependencies** (Tesseract and Poppler as described above)

### Running the Application

#### Graphical Interface (GUI)

```bash
# Launch the GUI
doctr-gui

# Or using Python module
python -m doctr_process.gui
```

The GUI provides an easy-to-use interface for:
- Selecting input files/directories
- Configuring OCR settings
- Monitoring processing progress
- Viewing logs in real-time

#### Command Line Interface (CLI)

```bash
# Process a directory
doctr-process --input samples --output outputs --no-gui

# Process a single file
doctr-process --input ticket.pdf --output outputs --no-gui

# Show help
doctr-process --help

# Show version
doctr-process --version
```

### Common CLI Options

```bash
# Dry run (show what would be processed)
doctr-process --input samples --output outputs --no-gui --dry-run

# With post-OCR corrections
doctr-process --input samples --output outputs --no-gui \
  --corrections-file data/corrections.jsonl

# Using custom dictionaries for fuzzy matching
doctr-process --input samples --output outputs --no-gui \
  --dict-vendors vendors.csv \
  --dict-materials materials.csv \
  --dict-costcodes costcodes.csv

# Force OCR even if text exists
doctr-process --input samples --output outputs --no-gui --force-ocr

# Skip OCR if text layer detected
doctr-process --input samples --output outputs --no-gui --skip-ocr

# Enable debug logging
doctr-process --input samples --output outputs --no-gui --verbose
```

---

## Configuration Files

The application uses three main configuration files located in `src/doctr_process/configs/`:

### 1. `ocr_keywords.csv`

Defines vendor identification keywords:

**Columns:**

| Column | Description |
|--------|-------------|
| `vendor_name` | Unique identifier for the vendor |
| `display_name` | Display name used in output (defaults to `vendor_name` if empty) |
| `vendor_type` | Type of vendor (e.g., `landfill`, `hauler`, `processor`) |
| `vendor_match` | Comma-separated keywords for identification (case-insensitive) |
| `vendor_excludes` | Comma-separated exclusion terms to prevent false matches |

**Example:**

| vendor_name | display_name | vendor_type | vendor_match | vendor_excludes |
|-------------|--------------|-------------|--------------|-----------------|
| Waste Mgmt | Waste Mgmt | landfill | wm,waste | |
| NTX | NTX | landfill | ntx,north texas | |

---

### 2. `extraction_rules.yaml`

Defines field extraction logic for each vendor:

```yaml
Waste Mgmt:
  ticket_number:
    method: roi
    roi: [0.18, 0.22, 0.29, 0.27]  # [x1, y1, x2, y2] normalized coordinates
    regex: '\d{6,}'
  manifest_number:
    method: label_right
    label: 'Manifest'
    regex: '14\d{6,}'
  date:
    method: roi
    roi: [0.05, 0.15, 0.25, 0.20]
    regex: '\d{1,2}/\d{1,2}/\d{2,4}'

DEFAULT:
  # Fallback rules for unknown vendors
  ticket_number:
    method: roi
    roi: [0.7, 0.1, 0.95, 0.2]
    regex: '\d{5,}'
```

**Extraction Methods:**

- **`roi`**: Extract from a region of interest (normalized coordinates 0-1)
- **`label_right`**: Find a label and extract text to the right
- **`label_below`**: Find a label and extract text below it
- **`regex`**: Apply regex pattern to extracted text

---

### 3. `config.yaml`

Main application configuration (managed by GUI or edited manually):

```yaml
# Input/Output
input_dir: ./data/
output_dir: ./outputs/

# OCR Settings
ocr_engine: doctr  # doctr, tesseract, or easyocr
orientation_check: tesseract  # tesseract, doctr, or none
pdf_resolution: 150  # DPI for PDF rendering

# Processing
parallel: true
num_workers: 4
batch_mode: true

# Reports
output_csv: true
ticket_numbers_csv: true
page_fields_csv: true
exceptions_csv: true
draw_roi: false  # Enable to debug extraction regions

# Post-OCR Corrections
corrections_enabled: true
corrections_file: ./data/corrections.jsonl
fuzzy_matching: true

# SharePoint (optional)
sharepoint_enabled: false
sharepoint_site_url: ""
sharepoint_library: ""

# Advanced
debug: false
profile: false
```

**Key Configuration Options:**

- **`orientation_check`**: How to handle rotated pages
  - `tesseract`: Use Tesseract OSD (recommended, most reliable)
  - `doctr`: Use DocTR's angle predictor (if available)
  - `none`: Skip orientation correction

- **`parallel`**: Enable parallel processing for faster batch operations
- **`num_workers`**: Number of parallel workers (recommend: CPU cores - 1)
- **`draw_roi`**: Save images with extraction regions highlighted for debugging

---

## Post-OCR Corrections

DocTR Process includes an intelligent correction system that improves accuracy without retraining OCR models.

### Features

1. **Memory-based corrections**: Learns from approved fixes
2. **Regex validators**: Fixes common patterns (ticket numbers, amounts, dates)
3. **Fuzzy matching**: Matches against known dictionaries (vendors, materials, cost codes)
4. **Character confusion**: Handles common OCR errors (O↔0, S↔5, I↔1, etc.)

### CLI Options

```bash
--corrections-file PATH    # Path to corrections memory file (default: data/corrections.jsonl)
--dict-vendors PATH         # CSV with vendor names for fuzzy matching
--dict-materials PATH       # CSV with material names
--dict-costcodes PATH       # CSV with cost codes
--no-fuzzy                  # Disable fuzzy dictionary matching
--learn-low                 # Store fuzzy matches ≥90 score
--learn-high                # Store fuzzy matches ≥95 score (default)
--dry-run                   # Test corrections without saving to memory
```

### Corrections Memory Format

The corrections file (`corrections.jsonl`) stores one correction per line in JSON format:

```json
{"field":"vendor","wrong":"LINDAMOOD DEM0LITION","right":"Lindamood Demolition","context":{"score":95},"ts":1640995200}
{"field":"ticket_number","wrong":"A12B45","right":"A12845","context":{"regex":"ticket"},"ts":1640995300}
```

### Output with Corrections

Corrected CSV outputs include audit columns:

- `record_id`: Unique identifier for each record
- `raw_vendor`: Original OCR value before correction
- `vendor`: Corrected value
- `raw_ticket_number`: Original ticket number
- `ticket_number`: Corrected ticket number

Correction logs show `old→new` changes with reasons for transparency.

---

## Output Structure

When you process files, DocTR Process creates organized output:

```
outputs/
├── logs/                          # Processing logs and reports
│   ├── doctr_app.log             # Main application log
│   ├── doctr_app.error.log       # Error log (size-rotated)
│   ├── combined_results.csv      # Raw OCR results for every page
│   ├── combined_ticket_numbers.csv  # Ticket number summary with validation
│   ├── page_fields.csv           # Per-page field extraction results
│   ├── ticket_number_exceptions.csv  # Pages missing ticket numbers
│   ├── duplicate_ticket_exceptions.csv  # Duplicate ticket pages
│   └── manifest_number_exceptions.csv  # Invalid manifest numbers
├── vendor_docs/                   # Organized by vendor
│   ├── Waste_Mgmt/
│   │   ├── ticket_123456.pdf
│   │   └── ticket_123457.pdf
│   └── NTX/
│       └── ticket_789012.pdf
├── data/
│   └── corrections.jsonl         # Post-OCR correction memory
└── roi_images/                    # ROI visualization (if enabled)
    └── [filename]_roi.png
```

### Key Output Files

#### `combined_results.csv`
- Raw OCR results for every page processed
- Includes all extracted fields
- Contains validation status for each field

#### `combined_ticket_numbers.csv`
- One row per page with ticket information
- Includes `duplicate_ticket` flag
- Links to ROI images for invalid entries
- Useful for quick review and validation

#### `page_fields.csv`
- Per-page summary of all extracted fields
- Shows validation status (`valid`, `review`, `invalid`)
- Includes confidence scores when available

#### Exception Reports
- **`ticket_number_exceptions.csv`**: Pages with no ticket number found
- **`duplicate_ticket_exceptions.csv`**: Duplicate vendor/ticket combinations
- **`manifest_number_exceptions.csv`**: Invalid or missing manifest numbers

---

## Troubleshooting

### OCR Quality Issues

**Problem**: Low accuracy or missing text

**Solutions**:
- Ensure input scans are at least 150 DPI (300+ recommended)
- Try different OCR engines: `--ocr-engine tesseract` or `--ocr-engine easyocr`
- Increase PDF resolution in config: `pdf_resolution: 300`
- Check if image is rotated: enable `orientation_check: tesseract`

### Field Not Extracting

**Problem**: Specific field always empty or incorrect

**Solutions**:
- Enable ROI visualization: `draw_roi: true` in config
- Review extraction rules in `extraction_rules.yaml`
- Adjust ROI coordinates based on visual output
- Verify regex patterns match expected format
- Check vendor is being correctly identified in `ocr_keywords.csv`

### Performance Issues

**Problem**: Processing is slow

**Solutions**:
- Enable parallel processing: `parallel: true`, `num_workers: 4`
- Reduce PDF resolution: `pdf_resolution: 150` (balance with accuracy)
- Use faster OCR engine: DocTR is generally faster than Tesseract
- Skip orientation check if not needed: `orientation_check: none`

### Import/Installation Errors

**Problem**: Module not found or import errors

**Solutions**:
- Verify Python version: `python --version` (requires 3.10+)
- Reinstall dependencies: `pip install -r requirements.txt`
- For editable install: `pip install -e .`
- Check system dependencies installed (Tesseract, Poppler)
- On Windows, ensure Poppler `bin` folder is in PATH

### Path/File Errors

**Problem**: File not found or path errors

**Solutions**:
- Use absolute paths or paths relative to current directory
- Avoid `..` or absolute paths in log directory (security validation)
- Check file permissions
- Verify input files are accessible

### Memory Issues

**Problem**: Out of memory errors with large batches

**Solutions**:
- Reduce `num_workers` in config
- Process files in smaller batches
- Reduce `pdf_resolution`
- Close other applications to free memory

---

## Best Practices

### For Best OCR Results

1. **Scan Quality**: Use 300+ DPI for source scans
2. **Orientation**: Ensure pages are right-side up or enable `orientation_check`
3. **Lighting**: Consistent, even lighting in scans
4. **Contrast**: Good contrast between text and background
5. **Format**: Use PDF when possible for better quality

### For Efficient Processing

1. **Batch Processing**: Process multiple files in one run
2. **Parallel Workers**: Set `num_workers` to CPU cores - 1
3. **Skip Existing**: Use `--skip-ocr` if text layer already exists
4. **Corrections Memory**: Build up corrections over time for better accuracy
5. **Vendor Keywords**: Keep `ocr_keywords.csv` updated with common variations

### For Accurate Data Extraction

1. **ROI Calibration**: Use `draw_roi: true` to verify extraction regions
2. **Vendor-Specific Rules**: Create custom extraction rules per vendor
3. **Regex Patterns**: Test and refine regex patterns for your data
4. **Fuzzy Dictionaries**: Maintain CSV dictionaries for common values
5. **Review Exceptions**: Regularly check exception reports for patterns

---

## Advanced Features

### SharePoint Integration

DocTR Process can integrate with SharePoint for automated document retrieval:

```yaml
# In config.yaml
sharepoint_enabled: true
sharepoint_site_url: "https://yourcompany.sharepoint.com/sites/yoursite"
sharepoint_library: "Shared Documents"
sharepoint_folder: "Tickets"
```

Set credentials via environment variables:
```bash
export SHAREPOINT_USERNAME=your.user@company.com
export SHAREPOINT_PASSWORD=your_password
```

### Custom Field Extractors

You can extend the extraction logic by adding custom methods in the source code. See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for details.

### Batch Automation

Create scripts to automate regular processing:

```bash
#!/bin/bash
# daily_processing.sh

# Process new tickets
doctr-process \
  --input /path/to/daily/tickets \
  --output /path/to/output \
  --no-gui \
  --corrections-file /path/to/corrections.jsonl \
  --dict-vendors /path/to/vendors.csv

# Send notification (example)
echo "Processing complete" | mail -s "Daily OCR Complete" admin@company.com
```

### Validation Runs

Compare new scans against previously processed data:

```yaml
# In config.yaml
run_type: validation  # instead of 'initial'
hash_db_csv: ./outputs/hash_db.csv
validation_output_csv: ./outputs/validation_mismatches.csv
```

This helps identify duplicate submissions or changes in documents.

---

## Getting Help

### Documentation

- **User Guide** (this document): End-user documentation
- **[Developer Guide](DEVELOPER_GUIDE.md)**: Technical documentation and API reference
- **[README](../README.md)**: Quick start and installation
- **[CHANGELOG](../CHANGELOG.md)**: Version history and changes

### Support

- **GitHub Issues**: Report bugs or request features at [GitHub Issues](https://github.com/batkins33/DocTR_Process/issues)
- **Logs**: Check `logs/doctr_app.log` and `logs/doctr_app.error.log` for diagnostic information
- **Debug Mode**: Run with `--verbose` or `--log-level=DEBUG` for detailed logging

### Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to the project.

---

## FAQ

**Q: Can I process images other than PDFs?**
A: Yes, DocTR Process supports PDF, TIFF, JPEG, and PNG formats.

**Q: How do I add a new vendor?**
A: Add an entry to `ocr_keywords.csv` and optionally create custom extraction rules in `extraction_rules.yaml`.

**Q: Can I run this without the GUI?**
A: Yes, use the `--no-gui` flag with CLI arguments.

**Q: How do corrections work?**
A: The system stores approved corrections in `corrections.jsonl` and automatically applies them to future runs.

**Q: What if my vendor uses different formats?**
A: Create vendor-specific extraction rules in `extraction_rules.yaml` with appropriate ROI coordinates and regex patterns.

**Q: Can I integrate this with other systems?**
A: Yes, outputs are standard CSV/Excel formats. The codebase can be extended for database integration.

**Q: Is parallel processing safe?**
A: Yes, but if you encounter issues, disable it with `parallel: false` in the config.

**Q: How do I update the application?**
A: Pull the latest code: `git pull origin main`, then reinstall: `pip install -e .`

---

*Last updated: October 2025*
