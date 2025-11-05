---

# DocTR Process - Developer/Technical Documentation

## Architecture Overview

- **Input:** PDF or directory of PDFs/images
- **Image Extraction:** Converts each PDF page to a `numpy.ndarray`
- **OCR:** Uses DocTR (PyTorch) for page-level text detection with Tesseract fallback
- **Field Extraction:** Per-vendor logic, defined in YAML/CSV configuration files
- **Validation:** Manifest and ticket numbers validated via regex and length logic
- **Post-OCR Corrections:** Memory-based corrections with fuzzy matching and learning
- **Output:** Writes multiple CSVs (detailed, deduped, summary, exceptions) and organized vendor documents

---

## Code Structure

```
src/doctr_process/
├── __init__.py           # Package initialization
├── __main__.py          # Python -m entry point
├── main.py              # CLI entry point
├── gui.py               # Tkinter GUI application
├── cli.py               # CLI argument parsing
├── pipeline.py          # Legacy pipeline implementation
├── pipeline_v2.py       # Refactored pipeline (preferred)
├── logging_setup.py     # Centralized logging configuration
├── path_utils.py        # Path validation utilities
├── post_ocr_corrections.py  # Post-OCR correction engine
├── resources.py         # Resource management
├── configs/             # Packaged configuration files
│   ├── config.yaml
│   ├── configf.yaml
│   ├── extraction_rules.yaml
│   └── ocr_keywords.csv
├── ocr/                 # OCR processing modules
│   ├── ocr_utils.py     # OCR utilities and orientation detection
│   └── ...
├── extract/             # Field extraction logic
├── parse/               # Data parsing utilities
├── output/              # Output handlers (CSV, Excel, etc.)
├── processor/           # File processing utilities
├── handlers/            # Various processing handlers
├── utils/               # General utility modules
└── assets/              # Application assets (logos, etc.)
```

---

## Key Modules & Functions

### Main Entry Points

- **`main.py`**: CLI parsing and headless vs GUI behavior
  - Headless runs create a temporary YAML config and call `pipeline_v2.run_refactored_pipeline`
  - Supports extensive CLI flags for corrections, fuzzy matching, and learning modes

- **`gui.py`**: Tkinter GUI application
  - Manages configuration through UI
  - Provides real-time logging feedback
  - Saves state to `~/.doctr_gui_state.json`

### Pipeline Processing

- **`pipeline_v2.py`** (preferred): Refactored pipeline with improved error handling
  - `run_refactored_pipeline(config_path)` - Main pipeline orchestrator

- **`pipeline.py`** (legacy): Original pipeline implementation
  - Still functional but prefer `pipeline_v2` for new work

### OCR Processing

- **`ocr/ocr_utils.py`**: Core OCR functionality
  - `extract_images_generator(filepath, poppler_path)` - Converts PDFs/images to numpy arrays
  - `correct_image_orientation()` - Handles page rotation with DocTR angle_predictor fallback to Tesseract OSD
  - Gracefully handles missing `angle_predictor` in newer DocTR versions

### Field Extraction

- **`extract/`** modules:
  - `find_vendor(page_text, vendor_rules)` - Scans OCR text for vendor keywords/exclusions
  - Returns `(vendor_name, vendor_type, matched_term, display_name)`
  - `extract_vendor_fields()` - Extracts all needed fields for a page/vendor
  - `extract_field()` - Core logic for ROI, label, regex-based extraction

### Post-OCR Corrections

- **`post_ocr_corrections.py`**: Intelligent correction layer
  - Memory-based corrections stored in JSONL format
  - Regex validators for ticket numbers, amounts, dates
  - Fuzzy dictionary matching for vendors, materials, cost codes
  - Confusion character handling (O↔0, S↔5, etc.)
  - Learning modes: `--learn-low` (≥90 score), `--learn-high` (≥95 score, default)

### Logging

- **`logging_setup.py`**: Centralized logging with queue-based handlers
  - `setup_logging(log_dir, level, run_id)` - Initializes logging infrastructure
  - Queue-based logging listener for thread safety
  - GUI sink support via `set_gui_log_widget()`
  - Path traversal validation for security
  - Reduces verbosity for noisy third-party libraries (PIL, urllib3, fitz, etc.)

### Validation

- **Manifest validation**:
  ```python
  def get_manifest_validation_status(manifest_number):
      if not manifest_number:
          return "invalid"
      if re.fullmatch(r"14\d{6}", manifest_number):
          return "valid"
      elif len(manifest_number) >= 7:
          return "review"
      else:
          return "invalid"
  ```

- **Ticket validation**: Vendor-specific regex patterns

---

## Configuration Files

### `config.yaml` / `configf.yaml`

Main application settings:
- Input/output paths
- OCR engine selection (DocTR, Tesseract, EasyOCR)
- Orientation detection method (`tesseract`, `doctr`, `none`)
- Parallel processing settings
- Report generation flags
- SharePoint integration settings
- Preflight check configuration

### `extraction_rules.yaml`

Defines field extraction logic per vendor:
```yaml
Waste Mgmt:
  ticket_number:
    method: roi
    roi: [0.18, 0.22, 0.29, 0.27]
    regex: '\d{6,}'
  manifest_number:
    method: label_right
    label: "Manifest"
    regex: "14\d{6,}"
DEFAULT:
  # Fallback rules for unknown vendors
  ticket_number: {...}
```

### `ocr_keywords.csv`

Vendor identification keywords:
```csv
vendor_name,display_name,vendor_type,vendor_match,vendor_excludes
Waste Mgmt,Waste Mgmt,landfill,"wm,waste",
```

---

## Output Structure

```
outputs/
├── logs/                          # Application logs (daily rotation)
│   ├── doctr_app.log
│   ├── doctr_app.error.log
│   ├── combined_results.csv
│   ├── combined_ticket_numbers.csv
│   ├── page_fields.csv
│   ├── ticket_number_exceptions.csv
│   └── manifest_number_exceptions.csv
├── vendor_docs/                   # Organized by vendor
│   └── [vendor_name]/
│       └── [ticket_files.pdf]
├── data/
│   └── corrections.jsonl          # Post-OCR correction memory
└── [run_id]/                      # Per-run outputs
```

---

---

## Extending & Customizing

### Add New Vendor
  - Update `ocr_keywords.csv` with vendor keywords
  - Add extraction logic in `extraction_rules.yaml`

### Change or Add Fields
  - Add to YAML and (optionally) extend extraction logic for new patterns

### Custom Validation
  - Edit `get_manifest_validation_status()` and `get_ticket_validation_status()`

### Integrate to Database
  - Replace or supplement CSV writing logic with database connectors

### Validation Mode
  - Set `run_type: validation` in `config.yaml` to compare pages against stored hashes

---

## Testing & Debugging

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_pipeline_v2.py

# Run smoke tests only
pytest tests/test_smoke.py

# Run with coverage
pytest --cov=src/doctr_process

# Use run_tests.py for CI-like checks
python run_tests.py
```

### Debug Mode

- Set `debug: true` in config.yaml for verbose output
- Use `--log-level=DEBUG` flag for CLI runs
- Enable `--verbose` flag for detailed logging

### Visual Debugging

- **Check ROIs**: Enable `draw_roi: true` to visually inspect extraction regions
- **ROI Images**: Saved to output directory when enabled
- **Log Analysis**: Check `logs/doctr_app.log` for detailed execution traces

### Common Debug Patterns

```python
# Logging pattern (preferred)
import logging
logger = logging.getLogger(__name__)
logger.info("Processing file: %s", filepath)
logger.debug("OCR result: %s", result)

# Use run_id for tracing across log files
logger.info("Run ID: %s", run_id)
```

---

## Common Issues & Solutions

### Wrong Field Mapping
- Check output CSV column ordering and source field indices
- Verify extraction rules in `extraction_rules.yaml`
- Enable ROI visualization to debug extraction regions

### Low OCR Quality
- Use better quality scans or preprocess images
- Try different OCR engines (DocTR, Tesseract, EasyOCR)
- Adjust PDF resolution in config (`pdf_resolution: 300`)

### Field Not Extracting
- Tweak ROI coordinates in extraction rules
- Verify regex patterns match expected formats
- Check vendor keyword matching in `ocr_keywords.csv`

### Parallel Processing Issues
- Some errors may be masked in parallel mode
- Run with `parallel: false` in config to debug sequentially
- Check individual thread logs for specific errors

### Import Errors
- **Missing DocTR angle_predictor**: Fallback to Tesseract OSD automatically
- **Missing dependencies**: Install with `pip install -r requirements.txt`
- **Package not found**: Ensure editable install with `pip install -e .`

### Path Traversal Warnings
- Log directory paths are validated to prevent `..` or absolute paths
- Use relative paths in configuration files
- See `path_utils.py` for validation logic

---

## Development Workflow

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/batkins33/DocTR_Process.git
cd DocTR_Process

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt
pip install -e .

# Install system dependencies
# Ubuntu/Debian: sudo apt-get install tesseract-ocr poppler-utils
# macOS: brew install tesseract poppler
# Windows: Download from official websites
```

### Making Changes

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes with tests
3. Run linting: `ruff check src/`
4. Format code: `black src/`
5. Run tests: `pytest`
6. Run smoke tests: `python run_tests.py`
7. Commit and push
8. Create pull request

### Code Style Guidelines

- **Python version**: Target 3.10+
- **Line length**: 88 characters (Black default)
- **Type hints**: Use for public APIs
- **Docstrings**: Required for public functions/classes
- **Imports**: Organized by `ruff` (stdlib, third-party, local)
- **Logging**: Use `logging.getLogger(__name__)` pattern

### Testing Best Practices

- Add unit tests for new functionality
- Mock heavy external dependencies (Tesseract, Poppler, SharePoint)
- Use `pytest` fixtures for common test setup
- Integration tests should be skippable in CI
- Preserve JSONL format for corrections memory

---

## Performance Considerations

### Parallel Processing

- Enable with `parallel: true` in config
- Set `num_workers` based on CPU cores
- Be aware of memory usage with large PDFs

### Memory Optimization

- Use generators for image processing
- Clean up temporary files promptly
- Monitor memory usage with large batches

### OCR Speed

- DocTR is generally faster than Tesseract
- Reduce `pdf_resolution` for faster processing (trade-off with accuracy)
- Use `skip-ocr` flag when text layer already exists

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

---

## Additional Resources

- [User Guide](USER_GUIDE.md) - End-user documentation
- [README](../README.md) - Installation and quick start
- [CHANGELOG](../CHANGELOG.md) - Version history
- [GitHub Copilot Instructions](../.github/copilot-instructions.md) - AI coding agent guidelines
