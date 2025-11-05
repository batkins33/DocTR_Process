# Sample Data for Testing & Development

**Project:** 24-105 PHMS NPC Truck Ticket Processing

This directory contains representative samples from the production data sources for testing extraction logic, validation, and end-to-end pipeline development.

## Directory Structure

```
samples/
├── tickets/          # Truck ticket scans (AP uploads, field captures)
├── manifests/        # Waste Management manifest PDFs (contaminated material)
├── invoices/         # Vendor invoices (PM department)
├── spreadsheets/     # Load tracking Excel files (GDrive exports)
├── reference/        # Miscellaneous reference documents
├── metadata/         # Power Apps JSON exports
├── powerapps/        # Power Apps data sources and outputs
└── manifest/         # Additional manifest and invoice samples
```

## Contents Summary

### Tickets (66 files)
- **Vendors represented:**
  - Alliance, Arcosa, Big City, Corpotechs, Heidelberg
  - JD&Son, Lindamood, Portillo, REC (Reeder), Roadstar
  - Roberts, Tarango, WL Reid
- **File types:** PDF (scanned tickets, scale tickets, invoices)
- **Date range:** Recent uploads from latest AP folder (2025-11-02)

### Manifests (6 files)
- **Source:** WM Lewisville manifest copies
- **Format:** PDF with manifest numbers and load details
- **Critical for:** Contaminated material compliance tracking

### Invoices (8 files)
- **Vendors:** Statewide Materials, Tarango, WL Reid
- **Source:** PM department invoice folder
- **Use case:** Vendor classification, invoice reconciliation

### Spreadsheets (1 file)
- **24-105_Load Tracking Log.xlsx** (246 KB)
  - Master load tracking spreadsheet from GDrive
  - Contains daily totals, material breakdowns, vendor summaries
  - Use for validation and reconciliation

### Power Apps (2 files)
- **TRUCK_TICKET_DATA-SOURCE.xlsx** - Data source configuration
- **TRUCK_TICKET_JOB_SUBMISSIONS.xlsx** - Field submission exports

### Metadata (1 file)
- **power_apps_sample.json** - Sample Power Apps submission structure

## File Size Policy

All files are ≤5MB to comply with repo hygiene rules. Larger files should be:
- Stored in external locations (OneDrive, GDrive)
- Referenced via paths in configuration
- Excluded via .gitignore

## Usage Guidelines

### For Testing Extractors
```python
from truck_tickets.extractors import TicketNumberExtractor, VendorDetector
from pathlib import Path

# Test ticket extraction
sample_pdf = Path("samples/tickets/alliance (1).pdf")
# ... run OCR and extraction
```

### For Validation
- Compare extracted data against known values in spreadsheets
- Verify manifest detection for contaminated material tickets
- Test vendor classification accuracy across multiple formats

### For Development
- Use these samples to build and refine extraction templates
- Create gold-standard test cases with known correct values
- Validate end-to-end pipeline before production deployment

## Data Provenance

**Source Locations:**
- Tickets: `C:\Users\brian.atkins\OneDrive - Lindamood Demolition\Documents - Truck Tickets\General\24-105-PHMS New Pediatric Campus\`
- Manifests: `...\24-105-PHMS New Pediatric Campus\MANIFEST\COPIES FROM WM\`
- Invoices: `C:\Users\brian.atkins\OneDrive - Lindamood Demolition\24-105 PHMS NPC - Documents\PM\Invoices\`
- Spreadsheet: `G:\My Drive\Lindamood\24-105\Load Tracking\`

**Date Collected:** November 4, 2025

## Security & Privacy

⚠️ **IMPORTANT:** These files contain real project data. Do not:
- Commit to public repositories
- Share outside the project team
- Include in external documentation or demos

This directory is included in `.gitignore` to prevent accidental commits.

## Next Steps

1. **Create vendor templates** for each represented vendor
2. **Build gold-standard dataset** with manually verified extractions
3. **Run extraction tests** and measure accuracy against acceptance criteria
4. **Validate against spreadsheet** to ensure reconciliation accuracy

---

**Last Updated:** November 4, 2025
**Maintained By:** Brian Atkins / Cascade AI
