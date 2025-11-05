# Heidelberg Integration

The DocTR Process application now includes integrated support for Heidelberg ticket extraction. When Heidelberg is detected as the vendor, the system automatically extracts Heidelberg-specific fields and generates specialized reports.

## Features

### Automatic Vendor Detection
- Heidelberg tickets are automatically detected based on text content
- Uses the existing vendor detection system with "Heidelberg" keyword matching

### Heidelberg-Specific Field Extraction
When Heidelberg is detected, the system extracts these fields:
- **Date**: Ticket date (MM/DD/YYYY format)
- **Ticket**: BOL number (6+ digits)
- **Product**: Material/product description
- **Time In**: Entry time (HH:MM format)
- **Time Out**: Exit time (HH:MM format)
- **Job**: Job/PO number (XX-XXX format)
- **Tons**: Weight in tons (decimal format)

### Specialized Output Reports
For each source file containing Heidelberg tickets, the system generates:
- **CSV Report**: `{job}_{date}_heidelberg_{product}.csv`
- **XLSX Report**: `{job}_{date}_heidelberg_{product}.xlsx` (optional)

Reports are saved in the configured output directory alongside standard DocTR outputs.

## Configuration

### Extraction Rules
Heidelberg extraction rules are defined in `src/doctr_process/configs/extraction_rules.yaml`:

```yaml
Heidelberg:
  date:
    method: text_regex
    regex: "(?<!\\d)(\\d{1,2}[/\\-]\\d{1,2}[/\\-]\\d{4})(?!\\d)"
  ticket_number:
    method: text_regex
    regex: "\\b(?:BOL|B\\s*O\\s*L)\\s*[:#]?\\s*(\\d{6,})"
    regex_flags: "IGNORECASE"
  # ... additional fields
```

### Vendor Detection
Heidelberg detection is configured in `src/doctr_process/configs/ocr_keywords.csv`:

```csv
vendor_name,display_name,vendor_type,vendor_match,vendor_excludes
Heidelberg,Heidelberg,Materials,Heidelberg,"CorpoTechs,JD&Son,..."
```

## Usage

### Command Line
```bash
# Process files with automatic Heidelberg detection
doctr-process --input samples --output outputs --no-gui

# The system will automatically:
# 1. Detect Heidelberg tickets
# 2. Extract Heidelberg-specific fields
# 3. Generate specialized reports
```

### GUI
1. Launch the GUI: `doctr-gui`
2. Select input files/folder
3. Configure output settings
4. Run processing
5. Heidelberg reports will be generated automatically when detected

## Output Structure

```
outputs/
├── results.csv                    # Standard DocTR output
├── log.xlsx                       # Standard Excel log
├── 24-105_12-15-2023_heidelberg_concrete.csv    # Heidelberg report
├── 24-105_12-15-2023_heidelberg_concrete.xlsx   # Heidelberg Excel
└── logs/                          # Application logs
```

## Technical Details

### Field Extraction Methods
- **text_regex**: Full-text pattern matching using regular expressions
- Supports regex flags (IGNORECASE, etc.)
- Fallback regex patterns for improved matching

### Data Processing
- Automatic data type conversion (tons to float)
- Field validation and error handling
- Consistent with standalone Heidelberg extractor patterns

### Integration Points
1. **Vendor Detection**: `VendorDetector` class identifies Heidelberg tickets
2. **Field Extraction**: `FieldExtractor` uses Heidelberg-specific rules
3. **Output Generation**: `HeidelbergOutputHandler` creates specialized reports
4. **Pipeline Integration**: Automatically included in all processing workflows

## Compatibility

- Fully compatible with existing DocTR Process workflows
- Does not affect processing of other vendor types
- Maintains backward compatibility with existing configurations
- Uses same OCR engines and text extraction methods as main pipeline

## Testing

Run Heidelberg integration tests:
```bash
pytest tests/test_heidelberg_integration.py
```

## Migration from Standalone Extractor

The integration uses the same extraction patterns as the standalone Heidelberg extractor:
- Same regex patterns for field detection
- Same output format and structure
- Same data validation and processing logic
- Automatic filename generation based on extracted data

This ensures consistent results whether using the standalone extractor or the integrated DocTR Process system.
