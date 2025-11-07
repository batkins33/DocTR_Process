# End-to-End Integration Tests

## Running Tests

### Prerequisites
- Install development dependencies: `pip install -e .[dev]`
- Database access: Tests use SQLite, no external DB required

### Basic Run
```bash
# Run all integration tests
pytest -q tests/integration/test_pipeline_e2e.py

# Run with verbose output
pytest -v tests/integration/test_pipeline_e2e.py

# Run with logging
pytest -v -s --log-cli-level=DEBUG tests/integration/test_pipeline_e2e.py
```

### Adding Test Data
1. Place sample truck ticket PDFs in `tests/fixtures/pdfs/`
2. Run tests to verify pipeline processing
3. Golden snapshots will be created in `tests/fixtures/snapshots/`

### Test Output
- Temporary files created in system temp directory
- Test logs captured by pytest
- Export files generated during tests

### Troubleshooting
- Tests skip if no PDF fixtures are present
- Check test logs for OCR and processing details
- Verify PDF files are readable and not corrupted
