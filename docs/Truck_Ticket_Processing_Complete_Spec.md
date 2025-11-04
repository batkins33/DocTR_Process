# 🚚 Project 24-105: Truck Ticket Processing & Material Tracking System
## Complete Implementation Specification

**Version:** 1.0  
**Date:** November 4, 2025  
**Status:** Ready for Implementation  

---

# PART 1: PROJECT CONTEXT & BACKGROUND

## Executive Summary

This project eliminates duplicate scanning and manual data entry by using OCR to extract ticket numbers, vendors, source locations, destinations, and manifest numbers from multi-page PDFs. The system will automatically populate tracking databases, generate invoice matching reports, and maintain regulatory compliance for contaminated material disposal.

**Current Problem:** Field teams scan tickets and manually count loads; office teams re-scan the same tickets to match invoices. This creates double work, delays, and potential errors.

**Solution:** Single-scan OCR pipeline that extracts all necessary data and populates both operational tracking and accounting systems.

---

## Project Overview

**Project:** 24-105 Construction Site Material Tracking  
**Primary Users:** Field teams, office accounting, project management  
**Regulatory Context:** Contaminated material disposal requires manifest tracking for EPA/state compliance  

---

## Current System Analysis

### Existing Tracking Spreadsheet: `24-105_Load_Tracking_Log.xlsx`

**10 Sheets Currently Maintained:**

1. **All Daily** - Combined daily totals across all material types
2. **Class2_Daily** - Contaminated material totals by source location (14 columns)
3. **Non Contaminated** - Clean material tracking with destinations (8 columns)
4. **Spoils** - Waste material by disposal destination (11 columns)
5. **Cubic Yardage Export Estimate** - Planning estimates vs. actuals
6. **ALL Export - By Month** - Monthly export summaries
7. **CLASS2 By Month** - Monthly contaminated material totals
8. **SPOILS By Month** - Monthly waste material totals
9. **Non Contam by Week** - Weekly clean material summaries
10. **Import** - Materials brought to site (11 material types tracked)

### Data Currently Tracked

**Time Dimensions:**
- Daily totals
- Weekly summaries (Job Week format: "Week 16 - (End 10/20/24)")
- Monthly summaries (Job Month format: "004 - October 24")

**Spatial Dimensions:**
- Source locations (excavation areas on site)
- Destination facilities (disposal/reuse sites)

**Material Classifications:**
- Class 2 Contaminated (requires manifests)
- Non-Contaminated (clean fill)
- Spoils (various waste categories)
- Import materials (11 types: 3X5, ASPHALT, C2, DIRT, FILL, FLEX, FLEXBASE, ROCK, UTILITY STONE, etc.)

---

## Material Flow & Tracking Requirements

### EXPORT MATERIALS (Leaving Site)

#### 1. Class 2 CONTAMINATED Material ⚠️

**SOURCE Locations (excavation areas on site):**
- PODIUM
- Zone E GARAGE
- South_MSE Wall
- MSE Wall
- PierEx
- Pond
- South Fill
- Tract 2

**DESTINATION:**
- **Waste Management Lewisville** (single regulated disposal facility)
- All loads tracked by unique manifest numbers (regulatory requirement)

**Compliance Requirements:**
- Every load must have a manifest number
- Manifests must be stored for regulatory audit trail
- Destination must be verified licensed facility

**Current Volume:** ~100-200 loads per day during active excavation

---

#### 2. Non-Contaminated Material ✓

**SOURCE Locations:**
- **SPG** (South Parking Garage - Tract 2)
- Various spoils areas across site

**DESTINATIONS:**
- **LDI YARD** - Clean fill disposal
- **Post Oak Pit** - Material reuse site

**Tracking Needs:**
- Source location (for site progress tracking)
- Destination (for coordination with receiving sites)
- Daily load counts by source

**Current Volume:** 0-300 loads per day (highly variable based on excavation schedule)

---

#### 3. Spoils (Mixed/Other Waste) 

**SOURCE:** Various excavation and demolition areas

**DESTINATIONS:**
- BECK SPOILS
- NTX Spoils (North Texas facility)
- UTX Spoils (Universal Texas facility)
- MVP-TC1 (MVP Tract C1 disposal)
- MVP-TC2 (MVP Tract C2 disposal)

**Tracking Needs:**
- Destination facility (for cost tracking - different disposal rates)
- Daily totals by facility

**Current Volume:** 0-50 loads per day (sporadic)

---

### IMPORT MATERIALS (Coming to Site)

**Material Types Delivered:**
- **3X5** - Rock size specification
- **ASPHALT** - Paving material
- **C2** - Class 2 base material
- **DIRT** - General fill
- **FILL** - Structural fill
- **FLEX** - Flexible base
- **FLEXBASE** - Flexible base course
- **ROCK** - Aggregate
- **UTILITY STONE** - Utility bedding

**Current Tracking:**
- Material type and daily quantity only
- **Missing:** Vendor names, source quarries, delivery ticket numbers

**Current Volume:** 0-250 loads per day (varies by construction phase)

---

## Current Workflow (The Problem)

### Inefficient Double-Entry Process

#### Field Team Workflow:
1. Receive truck tickets from drivers throughout day
2. Organize tickets by source area (physical paper sorting)
3. Scan tickets using phone/tablet (one PDF per area per day)
4. Manually count tickets in each batch
5. Enter daily totals into Excel spreadsheet by source location
6. File physical tickets for office review

**Time Investment:** 1-2 hours per day for field superintendent

---

#### Office Team Workflow:
1. Receive physical tickets from field (next day)
2. **Re-scan same tickets** using office scanner (duplicate scanning)
3. Manually read each ticket number
4. Match ticket numbers to vendor invoices
5. Validate quantities between field counts and invoice totals
6. Flag discrepancies for investigation

**Time Investment:** 2-3 hours per day for project coordinator

---

#### Problems with Current System:

❌ **Duplicate scanning** - Same tickets scanned twice (field + office)  
❌ **Manual counting errors** - Field team hand-counts 100+ tickets daily  
❌ **Delayed invoice matching** - Office team works 1 day behind  
❌ **No manifest database** - Contaminated material manifests stored as PDFs only  
❌ **Limited traceability** - Can't quickly query "all PierEx loads in October"  
❌ **Time waste** - 3-5 hours of manual data entry per day across teams  
❌ **Missing vendor data** - Import materials tracked without vendor names  

---

## Related Technology Infrastructure

### Existing OCR Capabilities

The user has existing OCR infrastructure that can be leveraged:

**DocTR (Document Text Recognition):**
- Python-based OCR pipeline
- Proven ticket number extraction capability
- Currently used for other construction document processing

**Related Tools:**
- **Blueprint Analyzer** - Document processing for construction drawings
- **Ticket Capture** - Mobile ticket scanning (may be prototype of this system)
- **WM_Invoice_Parser** - Waste Management invoice processing
- **manifest_extraction** - Manifest data extraction (partial implementation)
- **ML Categorizer** - Machine learning document classification
- **receipt_processing_toolkit** - General receipt OCR
- **bank_statement_parser** - Structured document parsing

**This project extends proven OCR capabilities to field ticket processing at scale.**

---

# PART 2: TECHNICAL SPECIFICATIONS

## Scope & Objectives (Locked)

**Primary Outcome:**  
One-scan pipeline that converts multi-page ticket PDFs into structured records for **invoice matching, manifest logging, and daily/area summaries** with no double entry.

**System of Record:**  
SQL Server (`TruckTicketsDB`) for normalized data storage; Excel remains a **reporting/export** target (not the canonical data store).

**In-Scope for v1:**
- ✅ Import & export material tickets (all types)
- ✅ Per-page ticket parsing and data extraction
- ✅ Vendor-specific extraction templates
- ✅ Manifest number logging for contaminated materials
- ✅ Source/destination tracking
- ✅ Daily/weekly/monthly summary generation
- ✅ Invoice matching report generation
- ✅ Duplicate detection

**Out-of-Scope for v1:**
- ❌ Price reconciliation and rate validation
- ❌ Line-item cost disputes
- ❌ Automatic GL (General Ledger) coding
- ❌ Direct ERP integration
- ❌ Mobile app for field data entry

---

## Controlled Vocabulary & Normalization

### Canonical Values

All extracted text must be normalized to these standard values before database insertion:

#### Flow Types:
- `IMPORT`
- `EXPORT`

#### Material Types (Canonical):
**Export Materials:**
- `CLASS_2_CONTAMINATED` - Regulated contaminated fill
- `NON_CONTAMINATED` - Clean fill material
- `SPOILS` - General waste/unusable material

**Import Materials:**
- `3X5` - Aggregate size
- `ASPHALT` - Paving material
- `C2` - Class 2 base
- `DIRT` - General fill
- `FILL` - Structural fill
- `FLEX` - Flexible base
- `FLEXBASE` - Flexible base course
- `ROCK` - Aggregate
- `UTILITY_STONE` - Utility bedding stone

#### Vendors (Examples - Expandable):
- `WASTE_MANAGEMENT_LEWISVILLE`
- `LDI_YARD`
- `POST_OAK_PIT`
- `BECK_SPOILS`
- `NTX_SPOILS`
- `UTX_SPOILS`
- `MVP_TC1`
- `MVP_TC2`

#### Source Locations (On-Site Areas):
- `PODIUM`
- `ZONE_E_GARAGE`
- `SOUTH_MSE_WALL`
- `MSE_WALL`
- `PIER_EX`
- `POND`
- `SOUTH_FILL`
- `TRACT_2`
- `SPG` (South Parking Garage)

### Synonym Mapping

Maintain a **synonym map** (CSV/JSON) for ingestion-time normalization:

**Example Mappings:**
```
"MSE Wall" → "MSE_WALL"
"Post Oak" → "POST_OAK_PIT"
"WM Lewisville" → "WASTE_MANAGEMENT_LEWISVILLE"
"South Garage" → "SPG"
"Pier Excavation" → "PIER_EX"
"Class2" → "CLASS_2_CONTAMINATED"
"Clean Fill" → "NON_CONTAMINATED"
```

**Implementation:** Load synonyms at startup; apply during extraction before database insert.

---

## Data Model (SQL Server)

### Core Tables

#### `jobs`
```sql
CREATE TABLE jobs (
    job_id INT PRIMARY KEY IDENTITY(1,1),
    job_code VARCHAR(50) NOT NULL UNIQUE,  -- e.g., '24-105'
    job_name VARCHAR(255),
    start_date DATE,
    end_date DATE,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
```

#### `materials`
```sql
CREATE TABLE materials (
    material_id INT PRIMARY KEY IDENTITY(1,1),
    material_name VARCHAR(100) NOT NULL UNIQUE,
    material_class VARCHAR(50),  -- 'CONTAMINATED', 'CLEAN', 'IMPORT'
    requires_manifest BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE()
);
```

#### `sources`
```sql
CREATE TABLE sources (
    source_id INT PRIMARY KEY IDENTITY(1,1),
    source_name VARCHAR(100) NOT NULL UNIQUE,
    job_id INT,
    description VARCHAR(255),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id),
    created_at DATETIME DEFAULT GETDATE()
);
```

#### `destinations`
```sql
CREATE TABLE destinations (
    destination_id INT PRIMARY KEY IDENTITY(1,1),
    destination_name VARCHAR(100) NOT NULL UNIQUE,
    facility_type VARCHAR(50),  -- 'DISPOSAL', 'REUSE', 'LANDFILL'
    address VARCHAR(500),
    requires_manifest BIT DEFAULT 0,
    created_at DATETIME DEFAULT GETDATE()
);
```

#### `vendors`
```sql
CREATE TABLE vendors (
    vendor_id INT PRIMARY KEY IDENTITY(1,1),
    vendor_name VARCHAR(100) NOT NULL UNIQUE,
    vendor_code VARCHAR(50),
    contact_info VARCHAR(500),
    created_at DATETIME DEFAULT GETDATE()
);
```

#### `ticket_types`
```sql
CREATE TABLE ticket_types (
    ticket_type_id INT PRIMARY KEY IDENTITY(1,1),
    type_name VARCHAR(20) NOT NULL UNIQUE  -- 'IMPORT' or 'EXPORT'
);
```

#### `truck_tickets` (Main Transaction Table)
```sql
CREATE TABLE truck_tickets (
    ticket_id INT PRIMARY KEY IDENTITY(1,1),
    ticket_number VARCHAR(50) NOT NULL,
    ticket_date DATE NOT NULL,
    quantity DECIMAL(10,2),
    quantity_unit VARCHAR(20),  -- 'TONS', 'CY', 'LOADS'
    
    -- Foreign Keys
    job_id INT NOT NULL,
    material_id INT NOT NULL,
    source_id INT,
    destination_id INT,
    vendor_id INT,
    ticket_type_id INT NOT NULL,
    
    -- File/Processing Metadata
    file_id VARCHAR(255),  -- Path to source PDF
    file_page INT,  -- Page number in PDF
    request_guid VARCHAR(50),  -- Batch processing ID
    
    -- Regulatory/Compliance
    manifest_number VARCHAR(50),
    
    -- Audit Trail
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    processed_by VARCHAR(100),
    
    -- Constraints
    FOREIGN KEY (job_id) REFERENCES jobs(job_id),
    FOREIGN KEY (material_id) REFERENCES materials(material_id),
    FOREIGN KEY (source_id) REFERENCES sources(source_id),
    FOREIGN KEY (destination_id) REFERENCES destinations(destination_id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(ticket_type_id)
);

-- Uniqueness guard (soft constraint)
CREATE UNIQUE INDEX idx_ticket_vendor_unique 
ON truck_tickets(ticket_number, vendor_id)
WHERE ticket_number IS NOT NULL AND vendor_id IS NOT NULL;

-- Performance indexes
CREATE INDEX idx_ticket_date ON truck_tickets(ticket_date);
CREATE INDEX idx_job_date ON truck_tickets(job_id, ticket_date);
CREATE INDEX idx_manifest ON truck_tickets(manifest_number) WHERE manifest_number IS NOT NULL;
```

### Uniqueness & Duplicate Detection

**Primary Uniqueness Key:** `(ticket_number, vendor_id)`

**Duplicate Detection Logic:**
- Check for existing ticket with same `(ticket_number, vendor_id)` within rolling 120-day window
- If found: Mark as duplicate and route to review queue
- Store reference to original ticket: `duplicate_of = existing_ticket_id`

**Alternative Uniqueness (fallback):** `(ticket_number, ticket_date, vendor_id)` when vendor is ambiguous

---

## Input File Conventions

### Folder Structure (Recommended)

```
C:\Projects\truck tickets\
├── 2024-10-14\
│   ├── export\
│   │   ├── 24-105__2024-10-14__PIER_EX__EXPORT__CLASS_2_CONTAMINATED__WM_LEWISVILLE.pdf
│   │   ├── 24-105__2024-10-14__SPG__EXPORT__NON_CONTAMINATED__LDI_YARD.pdf
│   │   └── 24-105__2024-10-14__MSE_WALL__EXPORT__CLASS_2_CONTAMINATED__WM_LEWISVILLE.pdf
│   └── import\
│       ├── 24-105__2024-10-14__IMPORT__ROCK__VENDOR_A.pdf
│       └── 24-105__2024-10-14__IMPORT__FLEXBASE__VENDOR_B.pdf
├── 2024-10-15\
│   └── ...
```

### Filename Schema (Structured Format)

**Format:**  
`{JOB_CODE}__{YYYY-MM-DD}__{AREA}__{FLOW}__{MATERIAL}__{VENDOR}.pdf`

**Components:**
- `JOB_CODE`: Project identifier (e.g., `24-105`)
- `YYYY-MM-DD`: Date of tickets in file
- `AREA`: Source or destination location
- `FLOW`: `IMPORT` or `EXPORT`
- `MATERIAL`: Material type (use canonical names)
- `VENDOR`: Vendor name (optional, use when known)

**Examples:**
```
24-105__2024-10-17__SPG__EXPORT__NON_CONTAMINATED__LDI_YARD.pdf
24-105__2024-10-17__PIER_EX__EXPORT__CLASS_2_CONTAMINATED__WM_LEWISVILLE.pdf
24-105__2024-10-17__IMPORT__ROCK__ACME_AGGREGATE.pdf
```

**Legacy/Ad-Hoc Format Support:**  
System should also handle less structured filenames and extract metadata from:
1. Parent folder names (`/export/` vs `/import/`)
2. Date folders (`/2024-10-14/`)
3. OCR text content (fallback)

### Parse Precedence Rules

When metadata conflicts between sources, use this priority order:

1. **Highest Priority:** Structured filename components
2. **Medium Priority:** Parent folder names and date folders
3. **Lowest Priority:** OCR text extraction from page content

**Exception:** Database/UI selection (when user manually corrects) overrides ALL automatic classification.

---

## Field Extraction Specifications

### Per-Page Extraction Requirements

Each page in a multi-page PDF must be processed independently and generate one database record.

---

### 1. Ticket Number (REQUIRED)

**Regex Priority Pattern:**
```regex
\b\d{7,10}\b
```

**Vendor-Specific Patterns (via YAML config):**
- Waste Management: `WM-\d{8}`
- LDI Yard: `LDI\d{7}`
- Post Oak: `PO-\d{6,8}`

**Selection Logic when Multiple Candidates:**
1. Prefer ticket number in **top-right ROI** (Region of Interest)
2. Prefer **longest digit sequence** (more specific)
3. Apply vendor-specific pattern if vendor is known

**Fallback:** If no ticket number found → route page to manual review queue

**Validation:**
- Must be 7-10 digits (or match vendor pattern)
- Cannot be date-like (e.g., exclude `20241014`)
- Cannot be a quantity (cross-reference with quantity field location)

---

### 2. Date (REQUIRED)

**Accepted Formats:**
- `YYYY-MM-DD` (e.g., `2024-10-17`)
- `MM/DD/YYYY` (e.g., `10/17/2024`)
- `DD-MMM-YYYY` (e.g., `17-OCT-2024`)
- `M/D/YY` (e.g., `10/17/24`)

**Extraction Priority:**
1. **Filename date** (if present and parseable)
2. **Parent folder date** (if folder named with date)
3. **OCR text extraction** using regex:
   ```regex
   \b(20\d{2}[-/]\d{1,2}[-/]\d{1,2})\b
   ```
4. Use U.S. locale fallback for ambiguous formats

**Validation:**
- Date must be within job date range (job start - 60 days to job end + 60 days)
- Flag dates > 7 days in future or > 180 days in past for review

---

### 3. Vendor (REQUIRED)

**Detection Methods:**

**Primary:** Logo recognition
- Use template matching for known vendor logos
- WM Lewisville: Green/white logo in header
- LDI Yard: Text-based header
- Post Oak: Logo in top-left

**Secondary:** Keyword matching
```
"Waste Management" → WASTE_MANAGEMENT_LEWISVILLE
"LDI" → LDI_YARD
"Post Oak" → POST_OAK_PIT
"Beck" → BECK_SPOILS
"NTX" → NTX_SPOILS
```

**Tertiary:** Filename or destination inference
- If filename contains vendor → use that
- If destination is known single-vendor facility → infer vendor

**Normalization:**
Apply synonym map to convert variations to canonical names:
```
"Waste Mgmt" → "WASTE_MANAGEMENT_LEWISVILLE"
"WM Lewisville" → "WASTE_MANAGEMENT_LEWISVILLE"
"Post Oak Pit" → "POST_OAK_PIT"
```

**Fallback:** If vendor cannot be determined with confidence → route to review queue

---

### 4. Source Location (REQUIRED for EXPORT)

**Detection Methods:**

**Primary:** Explicit label matching
```regex
Source:\s*([A-Za-z0-9\s]+)
From:\s*([A-Za-z0-9\s]+)
Location:\s*([A-Za-z0-9\s]+)
```

**Secondary:** Filename extraction
- Parse `__AREA__` token from structured filename
- Example: `24-105__2024-10-17__PIER_EX__` → source = `PIER_EX`

**Tertiary:** Job-specific default mappings
- If material type = CLASS_2_CONTAMINATED and no source found → check per-job default source list

**Normalization:**
Apply synonym map:
```
"Pier Ex" → "PIER_EX"
"South MSE" → "SOUTH_MSE_WALL"
"E Garage" → "ZONE_E_GARAGE"
```

**Validation:**
- Source must match known job source list
- Flag unknown sources for review

---

### 5. Destination (REQUIRED for EXPORT, OPTIONAL for IMPORT)

**Detection Methods:**

**Primary:** Explicit label matching
```regex
Destination:\s*([A-Za-z0-9\s]+)
To:\s*([A-Za-z0-9\s]+)
Disposal Site:\s*([A-Za-z0-9\s]+)
```

**Secondary:** Vendor-destination mapping
- For contaminated material: If vendor = WM → destination = WASTE_MANAGEMENT_LEWISVILLE
- For clean material: Parse from filename or text

**Tertiary:** Filename extraction

**Normalization:**
Apply synonym map:
```
"LDI" → "LDI_YARD"
"Post Oak" → "POST_OAK_PIT"
"WM" → "WASTE_MANAGEMENT_LEWISVILLE"
```

---

### 6. Material Type (REQUIRED)

**Rule-Based Classification:**

**Contaminated Material Indicators:**
- Keywords: "Class 2", "Contaminated", "Regulated", "Manifest"
- Destination = WASTE_MANAGEMENT_LEWISVILLE
- Presence of manifest number
→ Classify as `CLASS_2_CONTAMINATED`

**Non-Contaminated Indicators:**
- Keywords: "Clean", "Fill", "Non-Contaminated"
- Destinations: LDI_YARD, POST_OAK_PIT
- Source = SPG
→ Classify as `NON_CONTAMINATED`

**Spoils Indicators:**
- Keywords: "Spoils", "Waste"
- Destinations: BECK_SPOILS, NTX_SPOILS, UTX_SPOILS, MVP_TC1, MVP_TC2
→ Classify as `SPOILS`

**Import Material Classification:**
- Detect specific keywords: "Rock", "Flexbase", "Asphalt", "3X5", etc.
- Use exact match to canonical import material names

**Filename Hint:**
If filename contains `__MATERIAL__` token → use as primary classification

**Validation:**
- Material type must match known materials list
- Flag unknown materials for review

---

### 7. Quantity & Units

**Quantity Detection:**
```regex
(\d+(?:\.\d{1,2})?)\s*(TONS?|CY|CUBIC\s*YARDS?|LOADS?)
```

**Examples:**
- `20.12 TONS`
- `12 CY`
- `15.5 CUBIC YARDS`

**Unit Normalization:**
```
"ton", "tons", "TON" → "TONS"
"cy", "CY", "cubic yard", "cubic yards" → "CY"
"load", "loads", "LOAD" → "LOADS"
```

**Fallback (Missing Quantity):**
If no explicit quantity found:
- Assume `quantity = 1`
- Set `quantity_unit = 'LOADS'`
- Include page in daily load count

**Validation:**
- Quantity must be > 0 and < 50 (typical truck capacity)
- Flag unusual quantities (< 5 or > 30 tons) for review

---

### 8. Manifest Number (REQUIRED for CLASS_2_CONTAMINATED)

**Regex Pattern:**
```regex
\b(MANIFEST|MN|MAN#|MANIFEST\s*#)\s*[:#]?\s*([A-Z0-9-]{6,})\b
```

**Examples:**
- `MANIFEST: WM-12345678`
- `MN# ABC-123456`
- `Manifest Number: 2024-0001234`

**Vendor-Specific Patterns:**
- Waste Management: `WM-\d{8}` or `\d{10}`
- Configure per vendor in YAML

**Critical Requirement:**
- **100% recall required** - Every contaminated page MUST have a manifest number OR appear in review queue
- Missing manifest on contaminated material is a **regulatory compliance failure**

**Validation:**
- Manifest number must be alphanumeric, 6-20 characters
- Should not duplicate within same day for same vendor (flag if duplicate)

---

## Import vs. Export Classification

### Classification Order of Truth

When determining whether a ticket is IMPORT or EXPORT, use this priority:

1. **Database/UI Selection** (Highest Authority)
   - If user has manually classified via UI → trust that classification
   - Never override manual classification with heuristics

2. **Folder Name**
   - If file is in `/import/` folder → IMPORT
   - If file is in `/export/` folder → EXPORT

3. **Filename Token**
   - If filename contains `__IMPORT__` → IMPORT
   - If filename contains `__EXPORT__` → EXPORT

4. **Content Heuristics** (Lowest Priority)
   - Keywords: "DISPOSAL", "LANDFILL", "EXPORT" → EXPORT
   - Keywords: "DELIVERY", "DELIVERED TO", "IMPORT" → IMPORT
   - Source on-site + Destination off-site → EXPORT
   - Source off-site + Destination on-site → IMPORT

**Important:** Never override an explicit database/UI selection with automatic heuristics.

---

## Multi-Vendor & Mixed Files

### Processing Logic

**Per-Page Processing:**
- Each page is evaluated independently for vendor classification
- One PDF file can contain tickets from multiple vendors
- Output one database record per page

**Vendor Assignment:**
- Use logo detection + keyword matching per page
- If page 1 = WM and page 2 = LDI → create separate records with correct vendors

**Downstream Reporting:**
- Split invoice matching reports by vendor
- Group tickets by vendor for batch invoice reconciliation

**Ambiguous Vendor Pages:**
If vendor cannot be confidently determined:
- Flag page for manual review
- Include in review queue with vendor candidates
- Do not guess vendor if confidence < 80%

---

## Deduplication & Data Integrity

### Duplicate Detection Strategy

**Check Before Insert:**
Query for existing ticket matching `(ticket_number, vendor_id)` within **rolling 120-day window** before current ticket date.

**If Duplicate Found:**
```sql
-- Mark new record as duplicate
UPDATE truck_tickets 
SET duplicate_of = {existing_ticket_id},
    review_required = 1
WHERE ticket_id = {new_ticket_id};
```

**Route to Review Queue with:**
- Original ticket details (date, amount, file)
- New ticket details (date, amount, file)
- Suggested action: "Possible duplicate or re-scan"

### Data Validation Rules

**Date Validation:**
- Ticket date must be within job date range ± 60 days
- Flag tickets with dates > 7 days in future
- Flag tickets with dates > 180 days in past

**Quantity Validation:**
- Quantity must be positive and < 50 units
- Flag quantities outside typical range (5-30 tons)

**Relationship Validation:**
- Contaminated material must have manifest number
- Export tickets must have both source and destination
- Import tickets must have destination (source optional)

**Uniqueness Validation:**
- Manifest numbers should not repeat on same day for same vendor
- Ticket numbers should not repeat for same vendor within 120 days

---

## Exception Handling & Review Queue

### Review Queue Structure

**Storage:** `review_queue` table or CSV export

**Schema:**
```sql
CREATE TABLE review_queue (
    review_id INT PRIMARY KEY IDENTITY(1,1),
    page_id VARCHAR(255),  -- File path + page number
    reason VARCHAR(100),
    severity VARCHAR(20),  -- 'CRITICAL', 'WARNING', 'INFO'
    file_path VARCHAR(500),
    page_num INT,
    detected_fields NVARCHAR(MAX),  -- JSON
    suggested_fixes NVARCHAR(MAX),  -- JSON
    resolved BIT DEFAULT 0,
    resolved_by VARCHAR(100),
    resolved_at DATETIME,
    created_at DATETIME DEFAULT GETDATE()
);
```

### Review Queue Reasons

**CRITICAL (Must Fix Before Processing):**
- `MISSING_TICKET_NUMBER` - No ticket number found
- `MISSING_MANIFEST` - Contaminated material without manifest
- `INVALID_DATE` - Date parsing failed or out of range
- `AMBIGUOUS_VENDOR` - Cannot determine vendor with confidence

**WARNING (Process with Flag):**
- `LOW_CONFIDENCE_OCR` - OCR quality score < 70%
- `DUPLICATE_TICKET` - Possible duplicate within 120 days
- `OUT_OF_RANGE_DATE` - Date outside expected range
- `UNUSUAL_QUANTITY` - Quantity outside typical range

**INFO (Process Normally, Log for Audit):**
- `MISSING_SOURCE` - Source location not found (non-critical)
- `ASSUMED_VENDOR` - Vendor inferred from destination
- `FILENAME_OVERRIDE` - Used filename metadata over OCR

### CLI Integration

**Export Review Queue:**
```bash
--export-review review_queue.csv
```

**Output Format (CSV):**
```csv
page_id,reason,severity,file_path,page_num,detected_fields,suggested_fixes,created_at
"file1.pdf-p3","MISSING_MANIFEST","CRITICAL","/path/file1.pdf",3,"{\"ticket\":\"12345\",\"material\":\"CLASS_2\"}","{\"action\":\"manual_entry\"}","2024-10-17 14:32:01"
```

### GUI Workflow (Future)

1. Load review queue from CSV or database
2. Display page image + OCR text
3. Allow manual correction of fields
4. Save corrections back to database
5. Mark as resolved with user/timestamp

---

## Performance & Operations Targets

### Throughput Requirements

**Processing Speed:**
- **≤ 3 seconds per page** on target workstation
- Batch processing: 100 pages in ≤ 5 minutes (1200 pages/hour)
- Multi-core parallelism: Scale to available CPU cores

**Target Workstation Specs:**
- CPU: Intel i7 or AMD Ryzen 7 (8+ cores)
- RAM: 16 GB minimum
- Storage: SSD for PDF caching

---

### Accuracy Targets

**Ticket Number Extraction:**
- **≥ 98% correct** on clear, high-quality scans
- **≥ 95% correct** overall (including poor scans)
- Failure mode: Route to review queue (not silent failure)

**Manifest Number Recall:**
- **= 100% for contaminated pages** (every contaminated page must have manifest OR be in review queue)
- Regulatory compliance requires zero missed manifests

**Vendor Assignment:**
- **≥ 97% correct** on known vendor templates
- **≥ 90% correct** on ad-hoc or unknown vendors
- Ambiguous vendors → review queue

**Date Extraction:**
- **≥ 99% correct** (prefer filename date when available)

**Source/Destination:**
- **≥ 95% correct** when explicitly labeled
- **≥ 85% correct** when inferred from filename/context

**Material Classification:**
- **≥ 98% correct** for contaminated vs. clean (critical for compliance)
- **≥ 90% correct** for specific material types

---

### Operational Requirements

**Idempotent Processing:**
- Safe to reprocess same file/folder multiple times
- Duplicate detection prevents double-entry
- Maintain processing history: Track which files have been processed

**File Integrity:**
- Original PDFs stored under **immutable path** (no in-place edits)
- Generate SHA-256 hash of each processed PDF
- Store hash in database for verification

**Audit Trail:**
- Log `file_id`, SHA-256, `request_guid` for every processing run
- Track `processed_by` (username or system account)
- Record `created_at` and `updated_at` for every record

**Run Ledger:**
```sql
CREATE TABLE processing_runs (
    run_id INT PRIMARY KEY IDENTITY(1,1),
    request_guid VARCHAR(50) UNIQUE,
    started_at DATETIME,
    completed_at DATETIME,
    files_count INT,
    pages_count INT,
    ok_count INT,
    error_count INT,
    review_count INT,
    processed_by VARCHAR(100),
    status VARCHAR(20)  -- 'IN_PROGRESS', 'COMPLETED', 'FAILED'
);
```

---

## Output Specifications & Sheet Mapping

### Excel Export: `tracking_export.xlsx`

**Purpose:** Maintain compatibility with existing spreadsheet format for field/office teams who are used to current reports.

**Sheet Mapping (Must Match Legacy Format):**

#### 1. All Daily
**Columns:**
- Date
- Day (Mon, Tue, Wed, etc.)
- Job Week (format: "Week 16 - (End 10/20/24)")
- Job Month (format: "004 - October 24")
- Total (sum of all materials)
- Class 2 (contaminated loads)
- Non Contaminated (clean loads)
- Spoils (waste loads)
- Notes

**Source Query:**
```sql
SELECT 
    ticket_date AS Date,
    DATENAME(dw, ticket_date) AS Day,
    -- Calculate Job Week and Job Month
    SUM(CASE WHEN material_id = CLASS_2 THEN 1 ELSE 0 END) AS [Class 2],
    SUM(CASE WHEN material_id = NON_CONTAM THEN 1 ELSE 0 END) AS [Non Contaminated],
    SUM(CASE WHEN material_id = SPOILS THEN 1 ELSE 0 END) AS Spoils,
    COUNT(*) AS Total
FROM truck_tickets
WHERE job_id = @job_id AND ticket_type_id = EXPORT
GROUP BY ticket_date
ORDER BY ticket_date;
```

---

#### 2. Class2_Daily
**Columns:**
- Date, Day, Job Week, Job Month
- Total
- PODIUM, Zone E GARAGE, South_MSE Wall, MSE Wall, PierEx, Pond, South Fill, Tract 2
- Notes

**Source Query:**
```sql
SELECT 
    ticket_date AS Date,
    -- Pivot by source location
    SUM(CASE WHEN source_id = PODIUM THEN 1 ELSE 0 END) AS PODIUM,
    SUM(CASE WHEN source_id = ZONE_E_GARAGE THEN 1 ELSE 0 END) AS [Zone E GARAGE],
    SUM(CASE WHEN source_id = SOUTH_MSE_WALL THEN 1 ELSE 0 END) AS South_MSE_Wall,
    SUM(CASE WHEN source_id = MSE_WALL THEN 1 ELSE 0 END) AS MSE_Wall,
    SUM(CASE WHEN source_id = PIER_EX THEN 1 ELSE 0 END) AS PierEx,
    SUM(CASE WHEN source_id = POND THEN 1 ELSE 0 END) AS Pond,
    SUM(CASE WHEN source_id = SOUTH_FILL THEN 1 ELSE 0 END) AS South_Fill,
    SUM(CASE WHEN source_id = TRACT_2 THEN 1 ELSE 0 END) AS Tract_2,
    COUNT(*) AS Total
FROM truck_tickets
WHERE job_id = @job_id 
  AND material_id = CLASS_2_CONTAMINATED
GROUP BY ticket_date
ORDER BY ticket_date;
```

---

#### 3. Non Contaminated
**Columns:**
- Date, Day, Job Week, Job Month
- Total
- SPG (South Parking Garage)
- Spoils
- Location (destination)

**Source Query:**
```sql
SELECT 
    ticket_date AS Date,
    SUM(CASE WHEN source_id = SPG THEN 1 ELSE 0 END) AS SPG,
    destinations.destination_name AS Location,
    COUNT(*) AS Total
FROM truck_tickets
JOIN destinations ON truck_tickets.destination_id = destinations.destination_id
WHERE job_id = @job_id 
  AND material_id = NON_CONTAMINATED
GROUP BY ticket_date, destinations.destination_name
ORDER BY ticket_date;
```

---

#### 4. Spoils
**Columns:**
- Date, Day, Job Week, Job Month
- Total
- BECK SPOILS, NTX Spoils, UTX Spoils, MVP-TC1, MVP-TC2
- Notes

**Source Query:**
```sql
SELECT 
    ticket_date AS Date,
    SUM(CASE WHEN destination_id = BECK_SPOILS THEN 1 ELSE 0 END) AS [BECK SPOILS],
    SUM(CASE WHEN destination_id = NTX_SPOILS THEN 1 ELSE 0 END) AS [NTX Spoils],
    SUM(CASE WHEN destination_id = UTX_SPOILS THEN 1 ELSE 0 END) AS [UTX Spoils],
    SUM(CASE WHEN destination_id = MVP_TC1 THEN 1 ELSE 0 END) AS [MVP-TC1],
    SUM(CASE WHEN destination_id = MVP_TC2 THEN 1 ELSE 0 END) AS [MVP-TC2],
    COUNT(*) AS Total
FROM truck_tickets
WHERE job_id = @job_id 
  AND material_id = SPOILS
GROUP BY ticket_date
ORDER BY ticket_date;
```

---

#### 5. Import
**Columns:**
- DATE, 3X5, ASPHALT, C2, DIRT, FILL, FLEX, FLEXBASE, ROCK, UTILITY STONE, Grand Total

**Source Query:**
```sql
SELECT 
    ticket_date AS DATE,
    SUM(CASE WHEN material_name = '3X5' THEN 1 ELSE 0 END) AS [3X5],
    SUM(CASE WHEN material_name = 'ASPHALT' THEN 1 ELSE 0 END) AS ASPHALT,
    SUM(CASE WHEN material_name = 'C2' THEN 1 ELSE 0 END) AS C2,
    SUM(CASE WHEN material_name = 'DIRT' THEN 1 ELSE 0 END) AS DIRT,
    SUM(CASE WHEN material_name = 'FILL' THEN 1 ELSE 0 END) AS FILL,
    SUM(CASE WHEN material_name = 'FLEX' THEN 1 ELSE 0 END) AS FLEX,
    SUM(CASE WHEN material_name = 'FLEXBASE' THEN 1 ELSE 0 END) AS FLEXBASE,
    SUM(CASE WHEN material_name = 'ROCK' THEN 1 ELSE 0 END) AS ROCK,
    SUM(CASE WHEN material_name = 'UTILITY_STONE' THEN 1 ELSE 0 END) AS [UTILITY STONE],
    COUNT(*) AS [Grand Total]
FROM truck_tickets
JOIN materials ON truck_tickets.material_id = materials.material_id
WHERE job_id = @job_id 
  AND ticket_type_id = IMPORT
GROUP BY ticket_date
ORDER BY ticket_date;
```

---

#### 6-8. Monthly/Weekly Summary Sheets
- **ALL Export - By Month:** Aggregate All Daily by Job Month
- **CLASS2 By Month:** Aggregate Class2_Daily by Job Month
- **SPOILS By Month:** Aggregate Spoils by Job Month
- **Non Contam by Week:** Aggregate Non Contaminated by Job Week

**Implementation:** Generate from daily tables using GROUP BY on Job Week/Month fields.

---

#### 9. Cubic Yardage Export Estimate
**Columns:** Area, Loads, CY (est), Type, Group/Area

**Purpose:** Compare estimated vs. actual cubic yardage by source area.

**Source:** Calculate from ticket counts × average CY per load (configurable per material type).

---

### Accounting Export: `invoice_match.csv`

**Purpose:** Provide accounting team with ticket numbers and vendors for invoice reconciliation.

**Columns:**
- `ticket_number` - Unique ticket identifier
- `vendor` - Vendor name (normalized)
- `date` - Ticket date
- `material` - Material type
- `quantity` - Load quantity (if available)
- `units` - Quantity units
- `file_ref` - Path to source PDF + page number

**Format:** CSV (pipe-delimited for Excel compatibility)

**Sort Order:** By vendor, then date, then ticket number

**Example:**
```csv
ticket_number|vendor|date|material|quantity|units|file_ref
WM12345678|WASTE_MANAGEMENT_LEWISVILLE|2024-10-17|CLASS_2_CONTAMINATED|18.5|TONS|file1.pdf-p1
WM12345679|WASTE_MANAGEMENT_LEWISVILLE|2024-10-17|CLASS_2_CONTAMINATED|20.0|TONS|file1.pdf-p2
LDI7654321|LDI_YARD|2024-10-17|NON_CONTAMINATED|15.0|TONS|file2.pdf-p1
```

---

### Manifest Log: `manifest_log.csv`

**Purpose:** Regulatory compliance tracking for contaminated material disposal.

**Columns:**
- `ticket_number` - Truck ticket number
- `manifest_number` - Regulatory manifest number
- `date` - Disposal date
- `source` - Source location on site
- `waste_facility` - Disposal facility name
- `material` - Material type
- `quantity` - Load quantity
- `units` - Quantity units
- `file_ref` - Path to source PDF + page number

**Format:** CSV

**Sort Order:** By date, then manifest number

**Regulatory Note:** This log must be maintained for **minimum 5 years** per EPA requirements.

**Example:**
```csv
ticket_number,manifest_number,date,source,waste_facility,material,quantity,units,file_ref
WM12345678,WM-MAN-2024-001234,2024-10-17,PIER_EX,WASTE_MANAGEMENT_LEWISVILLE,CLASS_2_CONTAMINATED,18.5,TONS,file1.pdf-p1
WM12345679,WM-MAN-2024-001235,2024-10-17,MSE_WALL,WASTE_MANAGEMENT_LEWISVILLE,CLASS_2_CONTAMINATED,20.0,TONS,file1.pdf-p2
```

---

## Testing Strategy

### Gold Standard Test Set

**Create Reference Dataset:**
- **30-50 pages** across all vendors and material types
- Include variety of scan qualities (excellent, good, poor)
- Include edge cases:
  - Missing fields
  - Ambiguous vendors
  - Faded text
  - Handwritten notes
  - Mixed-vendor files
  - Duplicate ticket numbers

**Manual Annotation:**
- Expert review to create ground truth
- Document all field values correctly
- Store as CSV: `gold_standard.csv`

---

### Unit Tests

**Per-Component Testing:**

**Regex Patterns:**
```python
def test_ticket_number_extraction():
    assert extract_ticket_number("Ticket: 12345678") == "12345678"
    assert extract_ticket_number("WM-12345678") == "WM-12345678"
    
def test_date_extraction():
    assert extract_date("Date: 10/17/2024") == "2024-10-17"
    assert extract_date("17-OCT-2024") == "2024-10-17"
    
def test_vendor_detection():
    assert detect_vendor("Waste Management Lewisville") == "WASTE_MANAGEMENT_LEWISVILLE"
    assert detect_vendor("LDI Yard") == "LDI_YARD"
```

**ROI (Region of Interest) Extraction:**
```python
def test_roi_extraction():
    # Test top-right ticket number area
    # Test header vendor logo area
    # Test manifest number area
```

---

### Integration Tests

**End-to-End Workflow:**
```python
def test_full_pipeline():
    # Input: Sample PDF
    # Process: Run full extraction
    # Validate: Check database records match gold standard
    # Output: Verify Excel sheets and CSV exports
```

---

### Regression Testing

**Automated Checks:**
- Re-run gold standard test set on every code change
- Fail CI/CD build if accuracy drops ≥ 1%
- Track accuracy trends over time

**Metrics to Track:**
- Ticket number accuracy
- Manifest number recall (must stay at 100%)
- Vendor classification accuracy
- Processing speed (seconds per page)

---

### Production Spot-Check

**Weekly Validation:**
- Select 1 random day of production scans
- Compare automated counts to manual field counts
- Investigate any discrepancies > 2 loads

**Monthly Audit:**
- Review all tickets flagged in review queue
- Analyze failure patterns
- Update parser logic or vendor templates as needed

---

## Configuration Files

### File Structure

```
config/
├── synonyms.json                    # Normalization mappings
├── filename_schema.yml              # Filename parsing rules
├── acceptance.yml                   # Performance targets for CI
└── vendors/
    ├── WM_LEWISVILLE.yml           # Waste Management template
    ├── LDI_YARD.yml                 # LDI Yard template
    ├── POST_OAK_PIT.yml             # Post Oak template
    └── BECK_SPOILS.yml              # Beck Spoils template
```

---

### 1. synonyms.json

**Purpose:** Normalize vendor names, source locations, destinations, and materials.

**Format:**
```json
{
  "vendors": {
    "Waste Management": "WASTE_MANAGEMENT_LEWISVILLE",
    "WM": "WASTE_MANAGEMENT_LEWISVILLE",
    "WM Lewisville": "WASTE_MANAGEMENT_LEWISVILLE",
    "Waste Mgmt": "WASTE_MANAGEMENT_LEWISVILLE",
    "LDI": "LDI_YARD",
    "LDI Yard": "LDI_YARD",
    "Post Oak": "POST_OAK_PIT",
    "Post Oak Pit": "POST_OAK_PIT"
  },
  "sources": {
    "Pier Ex": "PIER_EX",
    "Pier Excavation": "PIER_EX",
    "MSE Wall": "MSE_WALL",
    "South MSE": "SOUTH_MSE_WALL",
    "E Garage": "ZONE_E_GARAGE",
    "South Garage": "SPG",
    "SPG": "SPG"
  },
  "destinations": {
    "LDI": "LDI_YARD",
    "Post Oak": "POST_OAK_PIT",
    "WM": "WASTE_MANAGEMENT_LEWISVILLE"
  },
  "materials": {
    "Class2": "CLASS_2_CONTAMINATED",
    "Class 2": "CLASS_2_CONTAMINATED",
    "Contaminated": "CLASS_2_CONTAMINATED",
    "Clean": "NON_CONTAMINATED",
    "Clean Fill": "NON_CONTAMINATED",
    "Spoils": "SPOILS",
    "Waste": "SPOILS"
  }
}
```

---

### 2. filename_schema.yml

**Purpose:** Define how to parse structured filenames.

**Format:**
```yaml
# Filename parsing configuration
filename_patterns:
  structured:
    pattern: "{JOB}__{DATE}__{AREA}__{FLOW}__{MATERIAL}__{VENDOR}.pdf"
    delimiter: "__"
    components:
      - name: "job_code"
        position: 0
      - name: "date"
        position: 1
        format: "YYYY-MM-DD"
      - name: "area"
        position: 2
      - name: "flow"
        position: 3
        values: ["IMPORT", "EXPORT"]
      - name: "material"
        position: 4
      - name: "vendor"
        position: 5
        optional: true

  legacy:
    # Support old filename formats
    pattern: "{DATE}_{AREA}_{FLOW}.pdf"
    delimiter: "_"

precedence:
  - filename  # Highest priority
  - folder    # Medium priority
  - ocr       # Lowest priority
```

---

### 3. Vendor Templates (Example: WM_LEWISVILLE.yml)

**Purpose:** Vendor-specific extraction rules for Waste Management Lewisville.

**Format:**
```yaml
vendor:
  name: "WASTE_MANAGEMENT_LEWISVILLE"
  aliases:
    - "Waste Management"
    - "WM"
    - "WM Lewisville"
    - "Waste Mgmt"

logo:
  type: "image_template"
  path: "assets/logos/wm_logo.png"
  roi:
    x: 0
    y: 0
    width: 200
    height: 100
  threshold: 0.85

ticket_number:
  regex: 
    - '\bWM-\d{8}\b'
    - '\b\d{10}\b'
  roi:
    x: 1400
    y: 50
    width: 200
    height: 100
  required: true

manifest_number:
  regex:
    - '\bMANIFEST\s*#?\s*:\s*(WM-MAN-\d{4}-\d{6})\b'
    - '\bMAN#\s*:\s*([A-Z0-9-]{10,})\b'
  roi:
    x: 100
    y: 300
    width: 600
    height: 100
  required: true
  validation:
    pattern: '^WM-MAN-\d{4}-\d{6}$'

date:
  formats:
    - "MM/DD/YYYY"
    - "M/D/YYYY"
  roi:
    x: 1400
    y: 150
    width: 200
    height: 50

destination:
  default: "WASTE_MANAGEMENT_LEWISVILLE"
  
material:
  default: "CLASS_2_CONTAMINATED"

quantity:
  regex: '(\d+(?:\.\d{1,2})?)\s*TONS?'
  roi:
    x: 800
    y: 400
    width: 300
    height: 100
  unit: "TONS"
```

---

### 4. acceptance.yml

**Purpose:** Define performance targets for CI/CD checks.

**Format:**
```yaml
# Acceptance criteria for automated testing
accuracy_targets:
  ticket_number:
    clean_scans: 0.98    # ≥98% on high-quality scans
    overall: 0.95         # ≥95% overall
    
  manifest_number:
    recall: 1.00          # 100% recall (no misses)
    
  vendor_classification:
    known_vendors: 0.97   # ≥97% on known templates
    overall: 0.90         # ≥90% including ad-hoc
    
  date_extraction:
    overall: 0.99         # ≥99%
    
  material_classification:
    contaminated_vs_clean: 0.98  # Critical for compliance
    specific_types: 0.90

performance_targets:
  seconds_per_page: 3.0
  pages_per_hour: 1200
  
regulatory_compliance:
  manifest_recall: 1.00    # Zero tolerance for missed manifests
```

---

## Implementation Roadmap

### 2-Week Development Plan

---

#### **Week 1: Core Pipeline & Data Foundation**

**Days 1-2: Parser Core**
- [ ] Set up project structure
- [ ] Implement per-page PDF extraction
- [ ] Build normalization layer (synonyms.json loading)
- [ ] Create duplicate detection logic
- [ ] Set up SQL Server database and tables
- [ ] Implement basic record insertion

**Days 3-4: Filename & Folder Parsing**
- [ ] Build filename parser (structured format)
- [ ] Implement folder-based metadata extraction
- [ ] Create precedence logic (filename → folder → OCR)
- [ ] Add job/date validation

**Day 5: Testing Foundation**
- [ ] Set up gold standard test dataset (30-50 pages)
- [ ] Create unit test framework
- [ ] Build accuracy measurement tools

---

#### **Week 2: Vendor Templates & Production**

**Days 6-7: Vendor-Specific Extraction**
- [ ] Create WM Lewisville template (highest priority)
- [ ] Create LDI Yard template
- [ ] Create Post Oak Pit template
- [ ] Implement logo detection
- [ ] Build vendor-specific regex handlers

**Days 8-9: Manifest & Compliance**
- [ ] Implement manifest number extraction
- [ ] Build manifest logging CSV export
- [ ] Create review queue for missing manifests
- [ ] Add contaminated material validation

**Day 10: Excel/CSV Writers**
- [ ] Build Excel exporter (legacy workbook format)
- [ ] Create invoice matching CSV export
- [ ] Implement manifest log CSV export
- [ ] Create review queue CSV export
- [ ] Test sheet mappings against current spreadsheet

---

#### **Post-Launch (Weeks 3-4): Optimization**
- [ ] Performance tuning (multi-threading)
- [ ] Additional vendor templates
- [ ] GUI for review queue (optional)
- [ ] Automated monitoring dashboard
- [ ] Production spot-check validation

---

## CLI Specification

### Command-Line Interface (For Implementation)

**Primary Command:**
```bash
python -m ticketiq process \
  --input "C:\Projects\truck tickets\2024-10-17" \
  --job 24-105 \
  --export-xlsx "tracking_export.xlsx" \
  --export-invoice "invoice_match.csv" \
  --export-manifest "manifest_log.csv" \
  --export-review "review_queue.csv" \
  --threads 6
```

**Parameters:**
- `--input`: Path to folder containing PDFs (can be date folder or root)
- `--job`: Job code (e.g., "24-105")
- `--export-xlsx`: Output path for Excel tracking workbook
- `--export-invoice`: Output path for invoice matching CSV
- `--export-manifest`: Output path for manifest log CSV
- `--export-review`: Output path for review queue CSV
- `--threads`: Number of parallel processing threads (default: CPU count)

**Optional Parameters:**
- `--config`: Path to custom config directory (default: ./config)
- `--vendor-template`: Specific vendor template to use
- `--reprocess`: Allow reprocessing of previously processed files
- `--dry-run`: Show what would be processed without database insert
- `--verbose`: Detailed logging output

**Examples:**

Process single date folder:
```bash
python -m ticketiq process --input "C:\...\2024-10-17" --job 24-105
```

Process entire week:
```bash
python -m ticketiq process --input "C:\...\truck tickets" --job 24-105 --date-range 2024-10-14:2024-10-20
```

Dry run to preview:
```bash
python -m ticketiq process --input "C:\...\2024-10-17" --job 24-105 --dry-run --verbose
```

---

# PART 3: IMMEDIATE NEXT STEPS

## Required from User

### 1. Sample PDF Files

**Upload 3-4 sample ticket pages:**

**Priority:**
- [ ] 2 pages from Waste Management manifest (Class 2 contaminated)
- [ ] 1 page from LDI Yard ticket (non-contaminated)
- [ ] 1 page from Post Oak Pit ticket (non-contaminated)

**Optional (if available):**
- [ ] 1 page from Spoils disposal (Beck/NTX/UTX)
- [ ] 1 page from Import material delivery

**Purpose:** Understand actual ticket format, field locations, and vendor variations.

---

### 2. Filename Examples

**Provide 5-10 actual PDF filenames as they exist today:**

Examples needed:
```
[actual filename 1].pdf
[actual filename 2].pdf
[actual filename 3].pdf
...
```

**Purpose:** Understand current naming convention to build parser.

---

### 3. Folder Structure Confirmation

**Describe how PDFs are currently organized:**

Example questions:
- Are tickets scanned daily or weekly?
- One PDF per area per day? Or one PDF per day with all areas?
- Are Import and Export separated into different folders?
- Are files organized by date in folders?

**Purpose:** Determine folder parsing strategy.

---

### 4. Database Access

**Provide SQL Server connection details:**
- Server name
- Database name (or confirm `TruckTicketsDB`)
- Authentication method (Windows or SQL Server)
- User permissions required

**Purpose:** Set up database connection for development.

---

## First Development Tasks

### Setup (Day 1)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # doctr, pandas, openpyxl, pyodbc, etc.
   ```

2. **Create database schema:**
   ```bash
   python setup_database.py --connection-string "..."
   ```

3. **Load sample files:**
   ```
   /test_data/
   ├── sample_wm_tickets.pdf
   ├── sample_ldi_tickets.pdf
   └── sample_postoak_tickets.pdf
   ```

---

### Validation (Day 2)

1. **Test OCR on samples:**
   - Extract text from each page
   - Verify ticket numbers visible
   - Check manifest numbers present

2. **Create first vendor template:**
   - Start with WM Lewisville (highest priority)
   - Define ROI coordinates
   - Test regex patterns

3. **Build gold standard:**
   - Manually annotate 30 pages
   - Store ground truth in CSV
   - Set up accuracy testing

---

## Success Criteria Checklist

### Functional Requirements
- [ ] Single scan extracts all data into database + Excel/CSVs
- [ ] No duplicate tickets inserted across re-runs (idempotent)
- [ ] Import/Export classification respects database/UI selection over heuristics
- [ ] Review queue generated for low-confidence/ambiguous pages

### Accuracy Requirements
- [ ] ≥95% overall ticket number accuracy (≥98% on clean pages)
- [ ] 100% contaminated pages have manifest number OR appear in review queue
- [ ] ≥97% vendor classification accuracy on known templates
- [ ] Auto daily/weekly/monthly summaries match manual totals on test week

### Performance Requirements
- [ ] ≤3 seconds per page processing time
- [ ] Batch processing of 100 pages in ≤5 minutes

### Compliance Requirements
- [ ] Run ledger and file hashes recorded for audit
- [ ] Manifest log maintained with all required fields
- [ ] Original PDFs stored in immutable location

---

## Project Risks & Mitigations

### Risk 1: Poor Scan Quality
**Impact:** OCR accuracy drops below targets  
**Mitigation:** 
- Review queue catches low confidence
- Field training on scan quality
- Consider mobile app with quality checks

### Risk 2: Vendor Template Changes
**Impact:** New ticket formats break extraction  
**Mitigation:**
- Version control for vendor templates
- Automated regression testing
- Review queue flags unknown formats

### Risk 3: Manifest Number Misses
**Impact:** Regulatory compliance violation  
**Mitigation:**
- 100% recall requirement (never silent fail)
- Review queue for all missing manifests
- Weekly audit of contaminated loads

### Risk 4: Data Migration
**Impact:** Historical data not in database  
**Mitigation:**
- Excel remains valid reporting tool
- Database builds from go-forward date
- Optional backfill for recent history

---

## Contact & Questions

**Project Lead:** [User]  
**Development Team:** Claude Code / Windsurf  
**Document Version:** 1.0  
**Last Updated:** November 4, 2025

---

**This document is ready for handoff to development. Once sample files are provided, implementation can begin immediately.**
