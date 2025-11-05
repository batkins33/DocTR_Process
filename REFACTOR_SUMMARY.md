# DocTR Process Refactoring Summary

## Overview
This refactoring reorganizes the OCR pipeline into a modular structure with improved performance, collision-safe file naming, and enhanced CLI options.

## New Structure

### 1. Modular Architecture
- **`io/`** - Input/output handling with collision-safe naming
- **`extract/`** - Image extraction and OCR processing with batch support
- **`parse/`** - Field extraction and vendor detection
- **`output/`** - Existing output handlers (unchanged)

### 2. Key Improvements

#### Input/Output Management
- Per-input subdirectory outputs
- Collision-safe file naming with numeric suffix (default) or timestamp
- Support for ZIP archive processing
- Sanitized filenames for cross-platform compatibility

#### OCR Processing
- Batch OCR processing for improved performance
- Model instance reuse across pages
- Page-level OCR fallback for error handling
- Comprehensive timing and statistics collection

#### CLI Enhancements
- `--outdir` option (alias for `--output`)
- `--prefer-timestamp` option for timestamp-based naming
- Maintained backward compatibility with existing options

### 3. Code Quality
- Added ruff/black configuration for consistent formatting
- Comprehensive pytest configuration
- Minimal test coverage for new components
- Smoke tests to verify integration

## File Changes

### New Files
```
src/doctr_process/
├── io/
│   ├── __init__.py
│   ├── input_handler.py
│   └── output_manager.py
├── extract/
│   ├── __init__.py
│   ├── image_extractor.py
│   └── ocr_processor.py
├── parse/
│   ├── __init__.py
│   ├── field_extractor.py
│   └── vendor_detector.py
└── pipeline_v2.py

tests/
├── test_io.py
├── test_extract.py
├── test_parse.py
├── test_pipeline_v2.py
├── test_cli_options.py
└── test_refactor_smoke.py

run_tests.py
```

### Modified Files
- `src/doctr_process/main.py` - Added new CLI options and refactored pipeline integration
- `pyproject.toml` - Added ruff, black, and pytest configuration

## Usage Examples

### New CLI Options
```bash
# Use timestamp-based naming
doctr-process --input samples --outdir results --prefer-timestamp --no-gui

# Per-input subdirectories with collision-safe naming
doctr-process --input batch_folder --output results --no-gui
```

### Output Structure
```
results/
├── document1_pdf/
│   ├── extracted_data.csv
│   └── processing_log.txt
├── document2_pdf/
│   ├── extracted_data_001.csv  # Collision-safe naming
│   └── processing_log.txt
└── archive_zip/
    ├── extracted_data_20241201_143022.csv  # Timestamp naming
    └── processing_log.txt
```

## Performance Improvements
- Batch OCR processing reduces model initialization overhead
- Model instance reuse across pages
- Efficient image extraction with proper resource cleanup
- Reduced memory usage through generator-based processing

## Backward Compatibility
- All existing CLI options maintained
- Original pipeline still available as fallback
- Existing configuration files work unchanged
- Output format compatibility preserved
