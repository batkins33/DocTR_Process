# E2E Test File Tree Structure

```text
tests/
  integration/
    test_pipeline_e2e.py          # Main test harness - implements 7 test scenarios
    utils/
      db_utils.py                 # SQLite test DB setup/teardown utilities
      run_pipeline.py             # CLI invocation helpers for process/export commands
      __init__.py                 # Package initialization
    __init__.py                   # Package initialization
    README.md                     # Test execution and maintenance guide
  fixtures/
    pdfs/
      .keep                       # Placeholder with fixture descriptions
      24-105_happy_path_001.pdf   # Standard readable truck ticket
      24-105_happy_path_002.pdf   # Second valid ticket for batch testing
      24-105_low_confidence.pdf   # Poor quality scan, expect low OCR confidence
      24-105_encrypted.pdf        # Password-protected PDF (should fail gracefully)
      24-105_blank.pdf            # Empty/corrupt PDF file
      24-105_folder_vendor.pdf    # Missing vendor, folder name provides vendor
      24-105_conflict_vendor.pdf  # Filename vendor differs from OCR extraction
      24-105_batch_001.pdf        # Large batch test file 1
      24-105_batch_002.pdf        # Large batch test file 2
      24-105_batch_003.pdf        # Large batch test file 3
      24-105_batch_004.pdf        # Large batch test file 4
      24-105_batch_005.pdf        # Large batch test file 5
    snapshots/
      .gitkeep                    # Git tracking for golden outputs
      24-105_happy_invoice.csv    # Expected invoice export for happy path
      24-105_happy_manifest.csv   # Expected manifest export for happy path
      24-105_happy_review_queue.csv # Expected review queue (should be empty for happy path)
      24-105_happy_tracking.xlsx  # Expected Excel tracking export
      24-105_low_confidence_review_queue.csv # Expected review queue with low confidence item
      24-105_batch_invoice.csv    # Expected invoice for large batch
      24-105_batch_manifest.csv   # Expected manifest for large batch
      24-105_batch_review_queue.csv # Expected review queue for batch (may have items)
      24-105_batch_tracking.xlsx  # Expected Excel export for large batch
```

## Implementation Notes

### Test Harness (`test_pipeline_e2e.py`)

- Implements 7 scenarios from test matrix
- Uses pytest fixtures for isolation
- Skips gracefully when PDF fixtures missing
- Validates exports against snapshots

### Database Utilities (`db_utils.py`)

- Temporary SQLite database creation
- Schema setup with reference data
- Session management for tests
- Cleanup utilities

### Pipeline Utilities (`run_pipeline.py`)

- CLI command invocation helpers
- Process and export command wrappers
- Output directory management
- Configuration file generation

### Fixtures

- PDF files placed in `tests/fixtures/pdfs/`
- Golden snapshots in `tests/fixtures/snapshots/`
- `.keep` and `.gitkeep` files for git tracking
- Clear naming convention: `{scenario}_{type}.{ext}`
