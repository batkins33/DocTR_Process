# Getting Started with Truck Ticket Processing

**Quick Start Guide for Project 24-105**

## What's Been Built

A complete foundation for the truck ticket processing system with:

✅ **Database Schema** - SQL Server tables ready to use  
✅ **Data Models** - Python classes for all entities  
✅ **Field Extractors** - Ticket number, manifest, date, quantity, vendor detection  
✅ **Configuration System** - Synonym normalization, vendor templates, quality thresholds  
✅ **Documentation** - Complete README and implementation guides  

## Next Steps to Get Running

### 1. Set Up SQL Server Database

```powershell
# Set environment variables
$env:TRUCK_TICKETS_DB_SERVER = "localhost"  # or your SQL Server instance
$env:TRUCK_TICKETS_DB_NAME = "TruckTicketsDB"

# For SQL Server authentication (optional):
# $env:TRUCK_TICKETS_DB_USERNAME = "your_user"
# $env:TRUCK_TICKETS_DB_PASSWORD = "your_password"

# Create the database schema
cd src\truck_tickets\database
python schema_setup.py

# Seed reference data
python schema_setup.py --seed
```

### 2. Test Database Connection

```python
from truck_tickets.database import DatabaseConnection

# Test connection
db = DatabaseConnection.from_env()
if db.test_connection():
    print("✓ Database connected successfully!")
else:
    print("✗ Database connection failed")
```

### 3. What's Still Needed

**High Priority:**
1. **Sample PDF files** - Upload 2-3 Waste Management tickets to test extraction
2. **Database operations** - Complete the `TicketRepository` class (CRUD operations)
3. **Main processor** - Orchestrate OCR → extraction → database pipeline
4. **Excel exporters** - Generate tracking workbooks

**Medium Priority:**
5. Additional vendor templates (LDI Yard, Post Oak Pit)
6. CLI interface for batch processing
7. Review queue GUI

### 4. File Structure Created

```
src/truck_tickets/
├── config/
│   ├── synonyms.json              ✅ Text normalization
│   ├── filename_schema.yml        ✅ Filename parsing
│   └── acceptance.yml             ✅ Quality thresholds
├── database/
│   ├── connection.py              ✅ SQL Server connection
│   ├── schema_setup.py            ✅ Database schema
│   └── operations.py              ⏳ Repository (TODO)
├── extractors/
│   ├── base_extractor.py          ✅ Base class
│   ├── ticket_extractor.py        ✅ Ticket numbers
│   ├── manifest_extractor.py      ✅ Manifest numbers (critical!)
│   ├── date_extractor.py          ✅ Date parsing
│   ├── quantity_extractor.py      ✅ Quantity & units
│   └── vendor_detector.py         ✅ Vendor identification
├── models/
│   ├── ticket.py                  ✅ TruckTicket model
│   └── reference_data.py          ✅ Lookup tables
├── processors/
│   └── ticket_processor.py        ⏳ Main pipeline (TODO)
├── templates/vendors/
│   └── WM_LEWISVILLE.yml          ✅ Waste Management
├── utils/
│   └── normalization.py           ✅ Synonym normalizer
├── README.md                       ✅ Complete docs
├── IMPLEMENTATION_STATUS.md        ✅ Progress tracking
└── GETTING_STARTED.md             ✅ This guide
```

## Test the Extractors

```python
from truck_tickets.extractors import (
    TicketNumberExtractor,
    ManifestNumberExtractor,
    DateExtractor,
    VendorDetector
)

# Sample OCR text
text = """
Waste Management Lewisville
Ticket Number: WM-12345678
Date: 10/17/2024
Manifest #: WM-MAN-2024-001234
Quantity: 18.5 TONS
"""

# Test ticket number extraction
ticket_extractor = TicketNumberExtractor()
ticket_num, confidence = ticket_extractor.extract(text)
print(f"Ticket: {ticket_num} (confidence: {confidence:.2%})")

# Test manifest extraction  
manifest_extractor = ManifestNumberExtractor()
manifest, confidence = manifest_extractor.extract(text)
print(f"Manifest: {manifest} (confidence: {confidence:.2%})")

# Test date extraction
date_extractor = DateExtractor()
date, confidence = date_extractor.extract(text)
print(f"Date: {date} (confidence: {confidence:.2%})")
```

## Database Schema Overview

**9 Tables Created:**

1. **jobs** - Construction projects (24-105, etc.)
2. **materials** - Material types (contaminated, clean, import types)
3. **sources** - Source locations on site (PODIUM, PIER_EX, MSE_WALL, etc.)
4. **destinations** - Destination facilities (WM Lewisville, LDI Yard, etc.)
5. **vendors** - Vendor companies
6. **ticket_types** - IMPORT or EXPORT
7. **truck_tickets** - Main transaction table (ticket data)
8. **review_queue** - Pages requiring manual review
9. **processing_runs** - Audit ledger for batch processing

**Key Features:**
- Duplicate detection via `(ticket_number, vendor_id)` unique constraint
- Manifest tracking for contaminated material compliance
- Audit trail with timestamps and processing metadata
- Performance indexes on date, job, manifest

## Configuration Files

### synonyms.json
Maps vendor names, locations, and materials to canonical forms:
```json
{
  "vendors": {
    "WM": "WASTE_MANAGEMENT_LEWISVILLE",
    "Waste Management": "WASTE_MANAGEMENT_LEWISVILLE"
  }
}
```

### filename_schema.yml
Defines structured filename parsing:
```
Format: {JOB}__{DATE}__{AREA}__{FLOW}__{MATERIAL}__{VENDOR}.pdf
Example: 24-105__2024-10-17__PIER_EX__EXPORT__CLASS_2_CONTAMINATED__WM_LEWISVILLE.pdf
```

### acceptance.yml
Quality and performance targets:
- ≥95% ticket number accuracy
- 100% manifest recall (critical!)
- ≤3 seconds per page processing
- 1200 pages/hour throughput

## Vendor Templates

### WM_LEWISVILLE.yml
Complete extraction rules for Waste Management:
- Ticket number patterns and ROI
- Manifest number extraction (CRITICAL)
- Date, quantity, source/destination
- Validation rules
- Default assumptions (contaminated material)

## What You Need to Provide

1. **Sample PDFs** (2-3 Waste Management tickets)
2. **SQL Server details** (server name, authentication method)
3. **Filename examples** (current naming convention from field team)
4. **Folder structure** (how PDFs are organized)

## Support & Questions

- Full specification: `docs/Truck_Ticket_Processing_Complete_Spec.md`
- Module README: `src/truck_tickets/README.md`
- Implementation status: `src/truck_tickets/IMPLEMENTATION_STATUS.md`

## Commit Your Work

All files are ready to commit to the `truck-tickets-module` branch:

```bash
git add src/truck_tickets/
git commit -m "feat: Add field extractors and getting started guide

- Implemented BaseExtractor with regex and ROI support
- Added TicketNumberExtractor with validation
- Added ManifestNumberExtractor (100% recall requirement)
- Added DateExtractor with multiple format support
- Added QuantityExtractor with unit normalization
- Added VendorDetector with keyword matching
- Created GETTING_STARTED.md guide"

git push
```

---

**🎯 Ready for Phase 2: Build the main processor and database operations!**
