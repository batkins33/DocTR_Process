# Gold Standard Test Data

This directory contains gold standard test data for integration testing with known ground truth.

## Directory Structure

```
gold_standard/
├── pdfs/                    # Gold standard PDF files
│   ├── sample_ticket_001.pdf
│   ├── sample_ticket_002.pdf
│   └── ...
└── ground_truth/            # Ground truth JSON files
    ├── sample_ticket_001.json
    ├── sample_ticket_002.json
    └── ...
```

## Ground Truth Format

Each PDF should have a corresponding JSON file with the same name containing the expected extraction results.

### Example: `sample_ticket_001.json`

```json
{
  "ticket_number": "WM-40000001",
  "ticket_date": "2024-10-17",
  "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
  "material": "CLASS_2_CONTAMINATED",
  "quantity": 25.5,
  "quantity_unit": "TONS",
  "manifest_number": "WM-MAN-2024-001234",
  "truck_number": "1234",
  "source": "PODIUM",
  "destination": "WASTE_MANAGEMENT_LEWISVILLE",
  "job_code": "24-105"
}
```

## Field Definitions

### Required Fields:
- `ticket_number` (string): Ticket number from vendor
- `ticket_date` (string, ISO format): Date of ticket (YYYY-MM-DD)
- `vendor` (string): Canonical vendor name
- `material` (string): Canonical material name

### Optional Fields:
- `quantity` (number): Quantity value
- `quantity_unit` (string): Unit of measurement (TONS, YARDS, LOADS)
- `manifest_number` (string): Regulatory manifest number (required for contaminated)
- `truck_number` (string): Truck identification number
- `source` (string): Source location on site
- `destination` (string): Disposal destination
- `job_code` (string): Job identifier

## Creating Gold Standard Data

### 1. Select Representative PDFs

Choose PDFs that represent:
- All supported vendors (WM Lewisville, LDI Yard, Post Oak Pit)
- All material types (contaminated, non-contaminated, spoils)
- Various quality levels (good scans, poor scans, handwritten)
- Edge cases (missing fields, unusual formats)

### 2. Manual Verification

For each PDF:
1. Manually verify all field values
2. Double-check critical fields (ticket number, manifest, date)
3. Ensure values match canonical formats

### 3. Create Ground Truth JSON

Create a JSON file with the verified values:

```bash
# Example
{
  "ticket_number": "WM-40000001",
  "ticket_date": "2024-10-17",
  "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
  "material": "CLASS_2_CONTAMINATED",
  "quantity": 25.5,
  "quantity_unit": "TONS",
  "manifest_number": "WM-MAN-2024-001234",
  "truck_number": "1234"
}
```

### 4. Validate Format

Ensure:
- JSON is valid
- Dates are in ISO format (YYYY-MM-DD)
- Numbers are numeric (not strings)
- Canonical names match reference data

## Running Gold Standard Tests

```bash
# Run all gold standard tests
pytest tests/integration/test_gold_standard.py -v

# Run with detailed logging
pytest tests/integration/test_gold_standard.py -v -s --log-cli-level=DEBUG

# Run single test
pytest tests/integration/test_gold_standard.py::TestGoldStandardPipeline::test_single_ticket_extraction -v
```

## Acceptance Criteria

Gold standard tests verify:
- **≥95% ticket accuracy**: Overall extraction accuracy
- **100% manifest recall**: All contaminated tickets have manifests
- **≥97% vendor accuracy**: Vendor detection accuracy
- **≤3 sec/page**: Processing time per page

## Adding New Test Cases

1. Add PDF to `pdfs/` directory
2. Create corresponding JSON in `ground_truth/` directory
3. Run tests to verify
4. Update this README if needed

## Test Coverage Goals

Aim for at least:
- 10 tickets per vendor
- 5 tickets per material type
- 3 edge cases (poor quality, missing fields, etc.)
- Total: 50+ gold standard tickets

## Notes

- Keep PDFs under 5MB each
- Use real ticket formats (with sensitive data redacted)
- Maintain consistent naming: `{vendor}_{material}_{sequence}.pdf`
- Update ground truth if ticket format changes
