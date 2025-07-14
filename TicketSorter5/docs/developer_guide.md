# Developer Guide

## Project Structure

- `main.py` and `gui.py` provide command line and GUI entry points.
- `processor/` contains OCR logic and file handling utilities.
- `utils/` holds helper functions for OCR wrappers and data loading.
- `tests/` includes pytest-based unit tests.

## Running Tests

Install dependencies and run:

```
pytest
```

## Style and Formatting

The codebase uses `black` style formatting. Run `black` before committing changes.
