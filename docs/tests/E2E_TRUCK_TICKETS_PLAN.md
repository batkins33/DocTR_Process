# E2E Truck Tickets Pipeline Test Plan

## Overview & Objectives

End-to-end integration tests validating the complete truck ticket processing pipeline: PDF input → OCR extraction → database storage → export generation. Tests verify component integration, error handling, and deterministic behavior across edge cases.

## Test Matrix

### 1. Happy Path (Valid PDFs)

- **Input**: 2-3 readable truck ticket PDFs

- **Expected**: All tickets processed, stored in DB, all export files generated

- **Validation**: Export counts match input, no review queue entries

### 2. Low Confidence OCR → Review Queue

- **Input**: PDF with poor scan quality or ambiguous text
- **Expected**: Ticket routed to review queue, confidence score < threshold
- **Validation**: Review queue entry exists, ticket not in main table

### 3. Malformed/Corrupt PDF

- **Input**: Encrypted, blank, or zero-byte PDF
- **Expected**: Error handling, partial batch success, clear error logging
- **Validation**: Other tickets process successfully, error captured

### 4. Missing Field Resolution

- **Input**: PDF missing vendor name, folder structure contains vendor
- **Expected**: Vendor resolved from folder/filename precedence rules
- **Validation**: Correct vendor assigned, precedence logic documented

### 5. OCR vs Filename Conflict

- **Input**: Filename suggests different vendor than OCR extraction
- **Expected**: Deterministic tie-breaker (filename precedence)
- **Validation**: Expected vendor assigned, conflict logged

### 6. Large Batch Processing

- **Input**: 5-10 PDFs including duplicates and edge cases
- **Expected**: No duplicate rows, reasonable throughput, parallel processing
- **Validation**: Row counts match unique tickets, processing time acceptable

### 7. Export Target Missing (Optional)

- **Input**: Valid processing, export directory doesn't exist
- **Expected**: Graceful failure, clear error message, non-zero exit code
- **Validation**: Error handling without crash

## Directory & File Layout

```text
tests/
  integration/
    test_pipeline_e2e.py          # Main test harness (SWE to implement)
    utils/
      db_utils.py                 # SQLite test DB setup/teardown
      run_pipeline.py             # CLI invocation helpers
    README.md                     # Test execution guide
  fixtures/
    pdfs/                         # Test PDF files (described below)
      24-105_happy_path_001.pdf
      24-105_happy_path_002.pdf
      24-105_low_confidence.pdf
      24-105_encrypted.pdf
      24-105_blank.pdf
      24-105_folder_vendor.pdf
      24-105_conflict_vendor.pdf
      24-105_batch_001.pdf
      24-105_batch_002.pdf
      24-105_batch_003.pdf
      24-105_batch_004.pdf
      24-105_batch_005.pdf
    snapshots/                    # Golden output files
      24-105_happy_invoice.csv
      24-105_happy_manifest.csv
      24-105_happy_review_queue.csv
      24-105_happy_tracking.xlsx
      24-105_low_confidence_review_queue.csv
      24-105_batch_invoice.csv
      24-105_batch_manifest.csv
      24-105_batch_review_queue.csv
      24-105_batch_tracking.xlsx
```

## Fixtures List

### PDF Files Required

- `24-105_happy_path_001.pdf`: Standard readable truck ticket
- `24-105_happy_path_002.pdf`: Second valid ticket for batch testing
- `24-105_low_confidence.pdf`: Poor quality scan, expect low OCR confidence
- `24-105_encrypted.pdf`: Password-protected PDF (should fail gracefully)
- `24-105_blank.pdf`: Empty/corrupt PDF file
- `24-105_folder_vendor.pdf`: Missing vendor, folder name provides vendor
- `24-105_conflict_vendor.pdf`: Filename vendor differs from OCR extraction
- `24-105_batch_00X.pdf`: 5 files for large batch testing (include duplicates)

### Expected DB Rows

Key columns: ticket_number, manifest, date, vendor, source, destination, material, truck_number, confidence_score, processing_status

Example rows:
- `24-105-001`, `M-24-105-001`, `2024-01-15`, `Waste Management`, `Site A`, `Landfill B`, `Contaminated`, `TRK-001`, `0.95`, `processed`
- `24-105-002`, `M-24-105-002`, `2024-01-16`, `Republic Services`, `Site A`, `Landfill B`, `Clean`, `TRK-002`, `0.92`, `processed`

### Expected Export Files

- `{job_code}_tracking_export.xlsx`: Excel with all processed tickets
- `{job_code}_invoice_match.csv`: Invoice reconciliation data
- `{job_code}_manifest_log.csv`: Manifest tracking information
- `{job_code}_review_queue.csv`: Low confidence items requiring review

## Execution Commands

### Running Tests

```bash
# Run all E2E tests
pytest -q tests/integration/test_pipeline_e2e.py

# Verbose with logging
pytest -v -s --log-cli-level=DEBUG tests/integration/test_pipeline_e2e.py

# Run specific scenario
pytest -v tests/integration/test_pipeline_e2e.py::test_pipeline_happy_path
```

### Make Targets

```bash
make e2e              # Run E2E tests
make e2e-update       # Regenerate snapshots
```

### Environment

- **Test DB**: Temporary SQLite (auto-created/cleaned)
- **Output**: Temp directory for each test run
- **Config**: Test configuration with OCR engine settings

## Snapshot Testing Policy

### Storage

- Location: `tests/fixtures/snapshots/`
- Naming: `{scenario}_{export_type}.{ext}`
- Version control: Include snapshots in repo

### Regeneration

- Command: `make e2e-update` or `pytest --update-snapshots`
- Review required: Manual inspection of changed snapshots
- Material changes: Field additions, format changes, logic updates
- Acceptable drift: Timestamps, auto-generated IDs, formatting

### Diff Handling

- **Material**: Schema changes, field additions/removals
- **Acceptable**: Timestamps, UUIDs, minor formatting differences
- **Process**: Manual review for material changes, auto-accept for drift

## Acceptance Criteria

- [ ] All 7 test scenarios implemented and passing
- [ ] Tests skip with clear message when PDF fixtures missing
- [ ] Happy path generates all 4 export types matching snapshots
- [ ] Low confidence tickets routed to review queue correctly
- [ ] Malformed PDFs handled gracefully without crashing
- [ ] Field precedence logic tested and documented
- [ ] Conflict resolution deterministic and tested
- [ ] Large batch processes without duplicates in reasonable time
- [ ] Export failures handled with proper error codes
- [ ] Logs captured and assertions include error/message validation
- [ ] Snapshot regeneration workflow functional

## Risks & Rollback

### Disabling E2E Locally

- Remove PDF fixtures → tests skip automatically
- Use `pytest -k "not test_pipeline_e2e"` to exclude
- Set environment variable `SKIP_E2E=1` (if implemented)

### Performance Issues

- Large PDFs → use smaller test fixtures
- Slow OCR → limit to 2-3 PDFs per test
- Memory issues → run tests sequentially
- Timeout issues → increase pytest timeout or reduce batch size

### Rollback Procedures

- Delete `tests/integration/` directory to remove E2E tests
- Remove Makefile targets (`e2e`, `e2e-update`)
- Remove conftest.py test configuration additions

## Handoff to SWE-1.5

### Implementation Checklist

**Files to Create:**

- [ ] `tests/integration/test_pipeline_e2e.py` - Main test harness
- [ ] `tests/integration/utils/db_utils.py` - Database fixtures
- [ ] `tests/integration/utils/run_pipeline.py` - CLI helpers
- [ ] `tests/integration/utils/__init__.py` - Package init
- [ ] `tests/integration/__init__.py` - Package init
- [ ] `tests/integration/README.md` - Execution guide

**Fixtures to Create:**

- [ ] `tests/fixtures/pdfs/.keep` - Placeholder with fixture list
- [ ] `tests/fixtures/snapshots/.gitkeep` - Git tracking for snapshots

**Makefile Updates:**

- [ ] Add `e2e` target: `pytest -q tests/integration/test_pipeline_e2e.py`
- [ ] Add `e2e-update` target: `pytest --update-snapshots tests/integration/test_pipeline_e2e.py`
- [ ] Update `.PHONY` line to include new targets

**Test Harness Requirements:**

- [ ] Skip tests if no PDFs in `tests/fixtures/pdfs/`
- [ ] Use temporary SQLite DB for each test
- [ ] Use temporary output directories
- [ ] Capture pytest logs via caplog fixture
- [ ] Implement all 7 test scenarios from matrix
- [ ] Assert export file existence and content
- [ ] Validate review queue routing for low confidence
- [ ] Include error handling tests

**Behavior Requirements:**

- [ ] Tests run independently (no shared state)
- [ ] Cleanup temp files after each test
- [ ] Clear skip messages when fixtures missing
- [ ] Proper exit codes for process/export commands
- [ ] Log assertion messages for debugging

**Integration Points:**

- [ ] Import existing database schema setup functions
- [ ] Use existing CLI command structure
- [ ] Follow existing test patterns from `tests/conftest.py`
- [ ] Respect existing configuration system
- [ ] Use existing logging infrastructure

**Testing Commands:**

- [ ] Verify `pytest -q tests/integration/test_pipeline_e2e.py` runs
- [ ] Verify `make e2e` works (on Unix systems)
- [ ] Verify tests skip gracefully without PDFs
- [ ] Verify snapshot regeneration workflow
