# 🚚 Project 24-105: Truck Ticket Processing & Material Tracking System
## Complete Implementation Specification (Updated)

**Version:** 1.1  
**Date:** November 4, 2025  
**Status:** In Development - Foundation Complete  
**Last Updated:** Incorporated worksheet alignment analysis and dev session 1 progress

---

## 📋 Document Change Log

**v1.1 - November 4, 2025**
- ✅ Incorporated findings from Excel worksheet alignment analysis
- ✅ Corrected spoils locations (they are SOURCES, not destinations)
- ✅ Identified dual vendor system (Material Vendor vs. Trucking Vendor)
- ✅ Added truck_number field requirement
- ✅ Documented accounting spreadsheet findings
- ✅ Updated source location count (13 total sources)
- ✅ Clarified destination list (3 primary destinations)
- ✅ Added development progress tracking
- ⚠️ Flagged scope questions for stakeholder decision

**v1.0 - November 4, 2025**
- Initial comprehensive specification

---

# PART 0: CRITICAL CLARIFICATIONS & SCOPE QUESTIONS

## 🚨 Scope Decision Required

The alignment analysis revealed a **major scope ambiguity** that must be resolved before proceeding:

### Two Separate Systems Identified:

#### System A: **Operational Load Tracking** (24-105_Load_Tracking_Log.xlsx)
- **Purpose:** Track daily load counts by source area for field operations
- **Users:** Field superintendents, project managers
- **Data:** Date, material type, source location, daily counts
- **Complexity:** Medium
- **Current Spec Alignment:** ✅ **WELL ALIGNED** (95%)

#### System B: **Accounting/Invoice Reconciliation** (CLEANED_SEPT_2025_TRUCKING_SPREADSHEET.xlsx)
- **Purpose:** Match tickets to vendor invoices, track pricing, reconcile costs
- **Users:** Accounting department, project accountants
- **Data:** Invoice numbers, ticket numbers, material vendor, trucking vendor, prices, rates, totals
- **Complexity:** High
- **Current Spec Alignment:** ❌ **MAJOR GAPS** (40%)

### 🎯 **DECISION REQUIRED:**

**Option 1: Operational Tracking Only (Current v1 Scope)**
- Focus on replacing 24-105_Load_Tracking_Log.xlsx
- Extract ticket numbers for invoice matching CSV export
- Accounting team manually matches invoices using provided ticket numbers
- **Timeline:** 2 weeks (as specified)
- **Status:** Foundation ~20% complete

**Option 2: Full Accounting Integration (Expanded Scope)**
- Include invoice number tracking
- Support dual vendor system (material + trucking)
- Track pricing and cost reconciliation
- Replace both tracking AND accounting spreadsheets
- **Timeline:** 4-6 weeks (requires scope expansion)
- **Status:** Would require v2 spec document

### 📌 **Recommendation:**
Proceed with **Option 1** for v1.0, then evaluate v2.0 for full accounting integration based on initial deployment success.

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
4. **Spoils** - Waste material by source location (11 columns) ⚠️ **SOURCES, not destinations**
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
- Spoils (various waste categories from other subs)
- Import materials (9 types: 3X5, ASPHALT, C2, DIRT, FILL, FLEX, FLEXBASE, ROCK, UTILITY_STONE)

---

## Material Flow & Tracking Requirements

### EXPORT MATERIALS (Leaving Site)

#### 1. Class 2 CONTAMINATED Material ⚠️

**SOURCE Locations (Primary Excavation Areas - 8 locations):**
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

**DESTINATIONS:**
- **LDI YARD** - Clean fill disposal
- **Post Oak Pit** - Material reuse site

**Tracking Needs:**
- Source location (for site progress tracking)
- Destination (for coordination with receiving sites)
- Daily load counts by source

**Current Volume:** 0-300 loads per day (highly variable based on excavation schedule)

---

#### 3. Spoils (Mixed/Other Waste) - ⚠️ **CORRECTED UNDERSTANDING**

**IMPORTANT CLARIFICATION:**
The locations previously identified as "spoils destinations" are actually **SOURCE locations** representing other subcontractors' spoils staging areas on the project site.

**SOURCE Locations (Other Subs' Spoils Areas - 5 locations):**
- **BECK SPOILS** - Other sub's spoils area
- **NTX Spoils** - Other sub's spoils area  
- **UTX Spoils** - Other sub's spoils area
- **MVP-TC1** - Other sub's spoils area (MVP Tract C1)
- **MVP-TC2** - Other sub's spoils area (MVP Tract C2)

**DESTINATION:**
- **Waste Management Lewisville** (all spoils go to WM for disposal)

**Tracking Needs:**
- Source location (which sub's spoils)
- Daily totals by spoils source
- All hauled to same destination (WM Lewisville)

**Current Volume:** 0-50 loads per day (sporadic)

---

### 📊 **COMPLETE SOURCE LOCATION INVENTORY (13 Total)**

**Primary Excavation Areas (Class 2 Contaminated) - 8 sources:**
1. PODIUM
2. Zone E GARAGE
3. South_MSE Wall
4. MSE Wall
5. PierEx
6. Pond
7. South Fill
8. Tract 2

**Other Subcontractors' Spoils Areas - 5 sources:**
9. BECK SPOILS
10. NTX Spoils
11. UTX Spoils
12. MVP-TC1
13. MVP-TC2

**Non-Contaminated Source - 1 source:**
14. SPG (South Parking Garage)

**Note:** SPG may overlap with Tract 2, requiring clarification.

---

### 📍 **COMPLETE DESTINATION INVENTORY (3 Primary)**

Based on worksheet analysis, the actual export destinations are simpler than initially documented:

1. **Waste Management Lewisville**
   - Receives: Class 2 Contaminated material
   - Receives: All Spoils material (from 5 different sub sources)
   - Regulatory tracking: Required for contaminated loads
   - Manifest numbers: Required

2. **LDI YARD**
   - Receives: Non-Contaminated material
   - Source: SPG (South Parking Garage)
   - No manifest required

3. **Post Oak Pit**
   - Receives: Non-Contaminated material
   - Source: SPG (South Parking Garage)
   - No manifest required

---

### IMPORT MATERIALS (Coming to Site)

**Material Types Delivered (9 canonical types):**
- **3X5** - Rock size specification
- **ASPHALT** - Paving material
- **C2** - Class 2 base material
- **DIRT** - General fill
- **FILL** - Structural fill
- **FLEX** - Flexible base
- **FLEXBASE** - Flexible base course
- **ROCK** - Aggregate
- **UTILITY_STONE** - Utility bedding stone

**Current Tracking (Excel Import Sheet):**
- Material type and daily quantity only (counts, not ticket-level detail)
- **Missing:** Vendor names, source quarries, delivery ticket numbers

**⚠️ CRITICAL GAP IDENTIFIED:**
The accounting spreadsheet (CLEANED_SEPT_2025_TRUCKING_SPREADSHEET.xlsx) reveals extensive import vendor data NOT captured in operational tracking:
- MATERIAL VENDOR names (e.g., "HEIDELBERG")
- Material invoice numbers
- Material ticket numbers
- Unit prices
- TRUCKING VENDOR names (e.g., "STATEWIDE MATERIALS")
- Trucking invoice numbers
- Truck numbers
- Trucking rates

**v1 Scope Decision:**
- ✅ Extract delivery ticket numbers from import tickets
- ✅ Capture vendor names from ticket OCR
- ✅ Store truck numbers if visible on tickets
- ❌ Invoice numbers, pricing, and rates → Out of scope (accounting system)

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
❌ **No truck number tracking** - Cannot verify delivery trucks  

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

## Scope & Objectives (Updated v1.1)

**Primary Outcome:**
One-scan pipeline that converts multi-page ticket PDFs into structured records for **invoice matching, manifest logging, and daily/area summaries** with no double entry.

**System of Record:**
SQL Server (`TruckTicketsDB`) for normalized data storage; Excel remains a **reporting/export** target (not the canonical data store).

**In-Scope for v1:**
- ✅ Import & export material tickets (all types)
- ✅ Per-page ticket parsing and data extraction
- ✅ Vendor-specific extraction templates
- ✅ Manifest number logging for contaminated materials
- ✅ Source/destination tracking (13 sources, 3 destinations)
- ✅ Daily/weekly/monthly summary generation
- ✅ Invoice matching report generation (ticket numbers only)
- ✅ Duplicate detection
- ✅ Truck number extraction (when visible on tickets)

**Out-of-Scope for v1:**
- ❌ Invoice number tracking and price reconciliation
- ❌ Line-item cost disputes
- ❌ Automatic GL (General Ledger) coding
- ❌ Direct ERP integration
- ❌ Mobile app for field data entry
- ❌ Dual vendor tracking (material vs. trucking vendor) - **See v2 scope**

**⚠️ Deferred to v2 (Accounting System Integration):**
- ❌ Material vendor vs. trucking vendor distinction
- ❌ Invoice number capture and matching
- ❌ Unit price and rate tracking
- ❌ Cost reconciliation and dispute resolution
- ❌ Integration with accounting spreadsheet workflows

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
- `SPOILS` - General waste/unusable material from other subs

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

#### Source Locations (Canonical - 13 Total):

**Primary Excavation Areas (Class 2):**
- `PODIUM`
- `ZONE_E_GARAGE`
- `SOUTH_MSE_WALL`
- `MSE_WALL`
- `PIER_EX`
- `POND`
- `SOUTH_FILL`
- `TRACT_2`

**Other Subs' Spoils Areas:**
- `BECK_SPOILS`
- `NTX_SPOILS`
- `UTX_SPOILS`
- `MVP_TC1`
- `MVP_TC2`

**Non-Contaminated Source:**
- `SPG` (South Parking Garage)

#### Destination Locations (Canonical - 3 Primary):
- `WASTE_MANAGEMENT_LEWISVILLE` - Contaminated & spoils disposal
- `LDI_YARD` - Clean fill disposal
- `POST_OAK_PIT` - Material reuse site

#### Vendor Names (Canonical - Primary Vendors):

**Export Vendors:**
- `WASTE_MANAGEMENT_LEWISVILLE` (WM Lewisville)
- `LDI_YARD`
- `POST_OAK_PIT`

**Import Vendors (Sample from 84 files collected):**
- `HEIDELBERG`
- `ALLIANCE`
- `ARCOSA`
- `BIG_CITY`
- `CORPOTECH`
- `JD_AND_SON`
- `LINDAMOOD`
- `PORTILLO`
- `REEDER`
- `ROADSTAR`
- `ROBERTS`
- `TARANGO`
- `WL_REID`

**Note:** Full vendor list will be populated as tickets are processed. Synonym mapping handles variations.

### Normalization Examples

**Synonyms must be applied before database lookup:**

```
"MSE Wall" → "MSE_WALL"
"Post Oak" → "POST_OAK_PIT"
"WM Lewisville" → "WASTE_MANAGEMENT_LEWISVILLE"
"South Garage" → "SPG"
"Pier Excavation" → "PIER_EX"
"Class2" → "CLASS_2_CONTAMINATED"
"Clean Fill" → "NON_CONTAMINATED"
"Beck" → "BECK_SPOILS"
"MVP TC1" → "MVP_TC1"
```

**Implementation:** Load synonyms at startup; apply during extraction before database insert.

---

## Data Model (SQL Server) - Updated v1.1

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
    material_class VARCHAR(50),  -- 'CONTAMINATED', 'CLEAN', 'IMPORT', 'SPOILS'
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
    source_type VARCHAR(50),  -- 'EXCAVATION', 'SPOILS_STAGING', 'IMPORT_DELIVERY'
    description VARCHAR(255),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id),
    created_at DATETIME DEFAULT GETDATE()
);
```

**Expected Seed Data (13 sources):**
```sql
-- Primary excavation areas
INSERT INTO sources (source_name, source_type) VALUES 
('PODIUM', 'EXCAVATION'),
('ZONE_E_GARAGE', 'EXCAVATION'),
('SOUTH_MSE_WALL', 'EXCAVATION'),
('MSE_WALL', 'EXCAVATION'),
('PIER_EX', 'EXCAVATION'),
('POND', 'EXCAVATION'),
('SOUTH_FILL', 'EXCAVATION'),
('TRACT_2', 'EXCAVATION'),
('SPG', 'EXCAVATION'),

-- Other subs' spoils areas
('BECK_SPOILS', 'SPOILS_STAGING'),
('NTX_SPOILS', 'SPOILS_STAGING'),
('UTX_SPOILS', 'SPOILS_STAGING'),
('MVP_TC1', 'SPOILS_STAGING'),
('MVP_TC2', 'SPOILS_STAGING');
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

**Expected Seed Data (3 destinations):**
```sql
INSERT INTO destinations (destination_name, facility_type, requires_manifest) VALUES
('WASTE_MANAGEMENT_LEWISVILLE', 'DISPOSAL', 1),
('LDI_YARD', 'DISPOSAL', 0),
('POST_OAK_PIT', 'REUSE', 0);
```

#### `vendors`
```sql
CREATE TABLE vendors (
    vendor_id INT PRIMARY KEY IDENTITY(1,1),
    vendor_name VARCHAR(100) NOT NULL UNIQUE,
    vendor_code VARCHAR(50),
    vendor_type VARCHAR(50),  -- 'DISPOSAL', 'HAULING', 'MATERIAL_SUPPLIER'
    contact_info VARCHAR(500),
    created_at DATETIME DEFAULT GETDATE()
);
```

**⚠️ v1.1 NOTE:** Single vendor field. For dual vendor tracking (material vs. trucking), see v2 scope.

#### `ticket_types`
```sql
CREATE TABLE ticket_types (
    ticket_type_id INT PRIMARY KEY IDENTITY(1,1),
    type_name VARCHAR(20) NOT NULL UNIQUE  -- 'IMPORT' or 'EXPORT'
);

INSERT INTO ticket_types (type_name) VALUES ('IMPORT'), ('EXPORT');
```

#### `truck_tickets` (Main Transaction Table) - **Updated v1.1**

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

    -- **NEW v1.1:** Truck identification
    truck_number VARCHAR(50),  -- Added based on accounting spreadsheet analysis

    -- File/Processing Metadata
    file_id VARCHAR(255),  -- Path to source PDF
    file_page INT,  -- Page number in PDF
    file_hash VARCHAR(64),  -- SHA-256 hash for integrity verification
    request_guid VARCHAR(50),  -- Batch processing ID

    -- Regulatory/Compliance
    manifest_number VARCHAR(50),

    -- Data Quality
    extraction_confidence DECIMAL(3,2),  -- 0.00 to 1.00
    review_required BIT DEFAULT 0,
    review_reason VARCHAR(255),
    duplicate_of INT,  -- Reference to original ticket if duplicate
    FOREIGN KEY (duplicate_of) REFERENCES truck_tickets(ticket_id),

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
CREATE INDEX idx_truck_number ON truck_tickets(truck_number) WHERE truck_number IS NOT NULL;
CREATE INDEX idx_file_hash ON truck_tickets(file_hash);
```

### Uniqueness & Duplicate Detection

**Primary Uniqueness Key:** `(ticket_number, vendor_id)`

**Duplicate Detection Logic:**
- Check for existing ticket with same `(ticket_number, vendor_id)` within rolling 120-day window
- If found: Mark as duplicate and route to review queue
- Store reference to original ticket: `duplicate_of = existing_ticket_id`

**Alternative Uniqueness (fallback):** `(ticket_number, ticket_date, vendor_id)` when vendor is ambiguous

---

### Review Queue Table

```sql
CREATE TABLE review_queue (
    review_id INT PRIMARY KEY IDENTITY(1,1),
    ticket_id INT,  -- Reference to truck_tickets if record was created
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
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ticket_id) REFERENCES truck_tickets(ticket_id)
);
```

### Processing Runs Table

```sql
CREATE TABLE processing_runs (
    run_id INT PRIMARY KEY IDENTITY(1,1),
    request_guid VARCHAR(50) UNIQUE NOT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    files_count INT,
    pages_count INT,
    tickets_created INT,
    tickets_updated INT,
    duplicates_found INT,
    review_queue_count INT,
    error_count INT,
    processed_by VARCHAR(100),
    status VARCHAR(20),  -- 'IN_PROGRESS', 'COMPLETED', 'FAILED'
    config_snapshot NVARCHAR(MAX),  -- JSON snapshot of configuration
    created_at DATETIME DEFAULT GETDATE()
);
```

---

## Input File Conventions

### Folder Structure (Recommended)

```
C:\Projects\truck tickets\
├── 2024-10-14\
│   ├── export\
│   │   ├── 24-105__2024-10-14__PIER_EX__EXPORT__CLASS_2_CONTAMINATED__WM_LEWISVILLE.pdf
│   │   ├── 24-105__2024-10-14__SPG__EXPORT__NON_CONTAMINATED__LDI_YARD.pdf
│   │   └── 24-105__2024-10-14__BECK_SPOILS__EXPORT__SPOILS__WM_LEWISVILLE.pdf
│   └── import\
│       ├── 24-105__2024-10-14__IMPORT__ROCK__HEIDELBERG.pdf
│       └── 24-105__2024-10-14__IMPORT__FLEXBASE__ALLIANCE.pdf
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
24-105__2024-10-17__BECK_SPOILS__EXPORT__SPOILS__WM_LEWISVILLE.pdf
24-105__2024-10-17__IMPORT__ROCK__HEIDELBERG.pdf
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
- Heidelberg, Alliance, etc.: Logo detection TBD

**Secondary:** Keyword matching
```
"Waste Management" → WASTE_MANAGEMENT_LEWISVILLE
"LDI" → LDI_YARD
"Post Oak" → POST_OAK_PIT
"Heidelberg" → HEIDELBERG
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
"Beck" → "BECK_SPOILS"
"MVP TC1" → "MVP_TC1"
```

**Validation:**
- Source must match known job source list (13 canonical sources)
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
- For spoils material: If source = BECK_SPOILS, NTX_SPOILS, etc. → destination = WASTE_MANAGEMENT_LEWISVILLE
- For clean material: Parse from filename or text

**Tertiary:** Filename extraction

**Normalization:**
Apply synonym map:
```
"LDI" → "LDI_YARD"
"Post Oak" → "POST_OAK_PIT"
"WM" → "WASTE_MANAGEMENT_LEWISVILLE"
```

**Validation:**
- Destination must match known destination list (3 canonical destinations for exports)

---

### 6. Material Type (REQUIRED)

**Detection Priority:**

**For EXPORT:**
1. **Filename:** `__CLASS_2_CONTAMINATED__`, `__NON_CONTAMINATED__`, `__SPOILS__`
2. **Source inference:**
   - If source in {PODIUM, ZONE_E_GARAGE, MSE_WALL, etc.} → CLASS_2_CONTAMINATED
   - If source = SPG → NON_CONTAMINATED
   - If source in {BECK_SPOILS, NTX_SPOILS, etc.} → SPOILS
3. **OCR keywords:**
   - "contaminated", "class 2", "hazardous" → CLASS_2_CONTAMINATED
   - "clean fill", "non-contaminated" → NON_CONTAMINATED
   - "spoils", "waste" → SPOILS

**For IMPORT:**
1. **Filename:** `__ROCK__`, `__FLEXBASE__`, etc.
2. **OCR keywords:** Match against 9 canonical import material types

**Validation:**
- Contaminated material must have manifest number OR be routed to review queue
- Material must match canonical list

---

### 7. Manifest Number (REQUIRED for CLASS_2_CONTAMINATED)

**Regex Patterns:**
```regex
Manifest[:\s#]+([A-Z0-9-]{8,20})
Profile[:\s#]+([A-Z0-9-]{8,20})
WM[-\s]?MAN[-\s]?\d{4}[-\s]?\d{6}
```

**Extraction Strategy:**
- Search full page text
- Prioritize matches near "Manifest" or "Profile" labels
- For WM Lewisville: Look for alpha-numeric codes 8-20 characters

**Critical Requirement:**
- **100% recall required** - Every contaminated page must have manifest OR be in review queue
- Never silently fail on manifest extraction for contaminated material

**Fallback:** If manifest not found and material = CLASS_2_CONTAMINATED → CRITICAL review queue

---

### 8. Quantity (OPTIONAL)

**Regex Patterns:**
```regex
\b(\d{1,2}\.\d{1,2})\s*(tons?|cy|cubic\s+yards?)\b
\b(\d{1,2})\s*(loads?)\b
```

**Units Detection:**
- `TONS` - Weight
- `CY` - Cubic yards (volume)
- `LOADS` - Count

**Validation:**
- Quantity must be positive
- Quantity should be < 50 units (flag outliers)
- Typical range: 5-30 tons per load

**Note:** In operational tracking, field counts loads (not weights). OCR-extracted quantities are supplementary.

---

### 9. Truck Number (OPTIONAL) - **NEW v1.1**

**Regex Patterns:**
```regex
Truck[:\s#]+(\d{1,4})
Unit[:\s#]+(\d{1,4})
Vehicle[:\s#]+(\d{1,4})
```

**Extraction Strategy:**
- Search for truck/unit/vehicle label
- Look for 1-4 digit numbers
- May appear in header or footer of ticket

**Usage:**
- Delivery verification
- Driver tracking
- Cross-reference with accounting data

**Note:** Not all tickets will have truck numbers. Store when available.

---

## Material Classification & Flow Direction

### Flow Direction Logic (IMPORT vs EXPORT)

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
    review_required = 1,
    review_reason = 'Duplicate ticket'
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
    dbo.fn_CalculateJobWeek(ticket_date, @job_start_date) AS [Job Week],
    dbo.fn_CalculateJobMonth(ticket_date, @job_start_date) AS [Job Month],
    SUM(CASE WHEN m.material_class = 'CONTAMINATED' THEN 1 ELSE 0 END) AS [Class 2],
    SUM(CASE WHEN m.material_class = 'CLEAN' THEN 1 ELSE 0 END) AS [Non Contaminated],
    SUM(CASE WHEN m.material_class = 'SPOILS' THEN 1 ELSE 0 END) AS Spoils,
    COUNT(*) AS Total,
    NULL AS Notes
FROM truck_tickets tt
JOIN materials m ON tt.material_id = m.material_id
JOIN ticket_types ty ON tt.ticket_type_id = ty.ticket_type_id
WHERE tt.job_id = @job_id AND ty.type_name = 'EXPORT'
GROUP BY ticket_date
ORDER BY ticket_date;
```

**⚠️ TODO:** Implement helper functions for Job Week and Job Month calculations:
```sql
CREATE FUNCTION dbo.fn_CalculateJobWeek(@ticket_date DATE, @job_start_date DATE)
RETURNS VARCHAR(50)
AS
BEGIN
    -- Calculate week number since job start
    -- Format: "Week N - (End MM/DD/YY)"
    -- Implementation TBD
    RETURN 'Week 16 - (End 10/20/24)';
END;

CREATE FUNCTION dbo.fn_CalculateJobMonth(@ticket_date DATE, @job_start_date DATE)
RETURNS VARCHAR(50)
AS
BEGIN
    -- Calculate month number since job start
    -- Format: "NNN - Month YY"
    -- Implementation TBD
    RETURN '004 - October 24';
END;
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
    DATENAME(dw, ticket_date) AS Day,
    dbo.fn_CalculateJobWeek(ticket_date, @job_start_date) AS [Job Week],
    dbo.fn_CalculateJobMonth(ticket_date, @job_start_date) AS [Job Month],
    SUM(CASE WHEN s.source_name = 'PODIUM' THEN 1 ELSE 0 END) AS PODIUM,
    SUM(CASE WHEN s.source_name = 'ZONE_E_GARAGE' THEN 1 ELSE 0 END) AS [Zone E GARAGE],
    SUM(CASE WHEN s.source_name = 'SOUTH_MSE_WALL' THEN 1 ELSE 0 END) AS South_MSE_Wall,
    SUM(CASE WHEN s.source_name = 'MSE_WALL' THEN 1 ELSE 0 END) AS [MSE Wall],
    SUM(CASE WHEN s.source_name = 'PIER_EX' THEN 1 ELSE 0 END) AS PierEx,
    SUM(CASE WHEN s.source_name = 'POND' THEN 1 ELSE 0 END) AS Pond,
    SUM(CASE WHEN s.source_name = 'SOUTH_FILL' THEN 1 ELSE 0 END) AS [South Fill],
    SUM(CASE WHEN s.source_name = 'TRACT_2' THEN 1 ELSE 0 END) AS [Tract 2],
    COUNT(*) AS Total,
    NULL AS Notes
FROM truck_tickets tt
JOIN materials m ON tt.material_id = m.material_id
LEFT JOIN sources s ON tt.source_id = s.source_id
WHERE tt.job_id = @job_id
  AND m.material_class = 'CONTAMINATED'
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
    DATENAME(dw, ticket_date) AS Day,
    dbo.fn_CalculateJobWeek(ticket_date, @job_start_date) AS [Job Week],
    dbo.fn_CalculateJobMonth(ticket_date, @job_start_date) AS [Job Month],
    SUM(CASE WHEN s.source_name = 'SPG' THEN 1 ELSE 0 END) AS SPG,
    SUM(CASE WHEN s.source_name LIKE '%SPOILS%' THEN 1 ELSE 0 END) AS Spoils,
    d.destination_name AS Location,
    COUNT(*) AS Total
FROM truck_tickets tt
JOIN materials m ON tt.material_id = m.material_id
LEFT JOIN sources s ON tt.source_id = s.source_id
LEFT JOIN destinations d ON tt.destination_id = d.destination_id
WHERE tt.job_id = @job_id
  AND m.material_class = 'CLEAN'
GROUP BY ticket_date, d.destination_name
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
    DATENAME(dw, ticket_date) AS Day,
    dbo.fn_CalculateJobWeek(ticket_date, @job_start_date) AS [Job Week],
    dbo.fn_CalculateJobMonth(ticket_date, @job_start_date) AS [Job Month],
    SUM(CASE WHEN s.source_name = 'BECK_SPOILS' THEN 1 ELSE 0 END) AS [BECK SPOILS],
    SUM(CASE WHEN s.source_name = 'NTX_SPOILS' THEN 1 ELSE 0 END) AS [NTX Spoils],
    SUM(CASE WHEN s.source_name = 'UTX_SPOILS' THEN 1 ELSE 0 END) AS [UTX Spoils],
    SUM(CASE WHEN s.source_name = 'MVP_TC1' THEN 1 ELSE 0 END) AS [MVP-TC1],
    SUM(CASE WHEN s.source_name = 'MVP_TC2' THEN 1 ELSE 0 END) AS [MVP-TC2],
    COUNT(*) AS Total,
    NULL AS Notes
FROM truck_tickets tt
JOIN materials m ON tt.material_id = m.material_id
LEFT JOIN sources s ON tt.source_id = s.source_id
WHERE tt.job_id = @job_id
  AND m.material_class = 'SPOILS'
GROUP BY ticket_date
ORDER BY ticket_date;
```

**Note:** Spoils sources are other subs' staging areas, all going to WM Lewisville destination.

---

#### 5. Import
**Columns:**
- DATE
- 3X5, ASPHALT, C2, DIRT, FILL, FLEX, FLEXBASE, ROCK, UTILITY STONE
- Grand Total

**Source Query:**
```sql
SELECT
    ticket_date AS DATE,
    SUM(CASE WHEN m.material_name = '3X5' THEN 1 ELSE 0 END) AS [3X5],
    SUM(CASE WHEN m.material_name = 'ASPHALT' THEN 1 ELSE 0 END) AS ASPHALT,
    SUM(CASE WHEN m.material_name = 'C2' THEN 1 ELSE 0 END) AS C2,
    SUM(CASE WHEN m.material_name = 'DIRT' THEN 1 ELSE 0 END) AS DIRT,
    SUM(CASE WHEN m.material_name = 'FILL' THEN 1 ELSE 0 END) AS FILL,
    SUM(CASE WHEN m.material_name = 'FLEX' THEN 1 ELSE 0 END) AS FLEX,
    SUM(CASE WHEN m.material_name = 'FLEXBASE' THEN 1 ELSE 0 END) AS FLEXBASE,
    SUM(CASE WHEN m.material_name = 'ROCK' THEN 1 ELSE 0 END) AS ROCK,
    SUM(CASE WHEN m.material_name = 'UTILITY_STONE' THEN 1 ELSE 0 END) AS [UTILITY STONE],
    COUNT(*) AS [Grand Total]
FROM truck_tickets tt
JOIN materials m ON tt.material_id = m.material_id
JOIN ticket_types ty ON tt.ticket_type_id = ty.ticket_type_id
WHERE tt.job_id = @job_id AND ty.type_name = 'IMPORT'
GROUP BY ticket_date
ORDER BY ticket_date;
```

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
- `truck_number` - Truck ID (if available) **NEW v1.1**
- `file_ref` - Path to source PDF + page number

**Format:** CSV (pipe-delimited for Excel compatibility)

**Sort Order:** By vendor, then date, then ticket number

**Example:**
```csv
ticket_number|vendor|date|material|quantity|units|truck_number|file_ref
WM12345678|WASTE_MANAGEMENT_LEWISVILLE|2024-10-17|CLASS_2_CONTAMINATED|18.5|TONS|1234|file1.pdf-p1
WM12345679|WASTE_MANAGEMENT_LEWISVILLE|2024-10-17|CLASS_2_CONTAMINATED|20.0|TONS|1235|file1.pdf-p2
LDI7654321|LDI_YARD|2024-10-17|NON_CONTAMINATED|15.0|TONS|2056|file2.pdf-p1
```

**SQL Query:**
```sql
SELECT
    tt.ticket_number,
    v.vendor_name AS vendor,
    tt.ticket_date AS date,
    m.material_name AS material,
    tt.quantity,
    tt.quantity_unit AS units,
    tt.truck_number,
    CONCAT(tt.file_id, '-p', tt.file_page) AS file_ref
FROM truck_tickets tt
JOIN vendors v ON tt.vendor_id = v.vendor_id
JOIN materials m ON tt.material_id = m.material_id
WHERE tt.job_id = @job_id
  AND tt.review_required = 0
ORDER BY v.vendor_name, tt.ticket_date, tt.ticket_number;
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
- `truck_number` - Truck ID (if available) **NEW v1.1**
- `file_ref` - Path to source PDF + page number

**Format:** CSV

**Sort Order:** By date, then manifest number

**Regulatory Note:** This log must be maintained for **minimum 5 years** per EPA requirements.

**Example:**
```csv
ticket_number,manifest_number,date,source,waste_facility,material,quantity,units,truck_number,file_ref
WM12345678,WM-MAN-2024-001234,2024-10-17,PIER_EX,WASTE_MANAGEMENT_LEWISVILLE,CLASS_2_CONTAMINATED,18.5,TONS,1234,file1.pdf-p1
WM12345679,WM-MAN-2024-001235,2024-10-17,MSE_WALL,WASTE_MANAGEMENT_LEWISVILLE,CLASS_2_CONTAMINATED,20.0,TONS,1235,file1.pdf-p2
```

**SQL Query:**
```sql
SELECT
    tt.ticket_number,
    tt.manifest_number,
    tt.ticket_date AS date,
    s.source_name AS source,
    d.destination_name AS waste_facility,
    m.material_name AS material,
    tt.quantity,
    tt.quantity_unit AS units,
    tt.truck_number,
    CONCAT(tt.file_id, '-p', tt.file_page) AS file_ref
FROM truck_tickets tt
JOIN sources s ON tt.source_id = s.source_id
JOIN destinations d ON tt.destination_id = d.destination_id
JOIN materials m ON tt.material_id = m.material_id
WHERE tt.job_id = @job_id
  AND tt.manifest_number IS NOT NULL
  AND m.requires_manifest = 1
ORDER BY tt.ticket_date, tt.manifest_number;
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

**Status:** ✅ 84 sample files collected (samples/ directory)

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

## Configuration Files

### File Structure

```
config/
├── synonyms.json                    # Normalization mappings
├── filename_schema.yml              # Filename parsing rules
├── acceptance.yml                   # Performance targets for CI
├── output_config.yml                # Database/file output toggles
└── vendors/
    ├── WM_LEWISVILLE.yml           # Waste Management template ✅
    ├── LDI_YARD.yml                 # LDI Yard template
    ├── POST_OAK_PIT.yml             # Post Oak template
    ├── HEIDELBERG.yml               # Heidelberg template
    └── [13+ more vendor templates]
```

---

### 1. synonyms.json - **Status: ✅ Implemented**

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
    "Post Oak Pit": "POST_OAK_PIT",
    "Heidelberg": "HEIDELBERG",
    "Alliance": "ALLIANCE"
  },
  "sources": {
    "Pier Ex": "PIER_EX",
    "Pier Excavation": "PIER_EX",
    "MSE Wall": "MSE_WALL",
    "South MSE": "SOUTH_MSE_WALL",
    "E Garage": "ZONE_E_GARAGE",
    "South Garage": "SPG",
    "SPG": "SPG",
    "Beck": "BECK_SPOILS",
    "Beck Spoils": "BECK_SPOILS",
    "NTX": "NTX_SPOILS",
    "UTX": "UTX_SPOILS",
    "MVP TC1": "MVP_TC1",
    "MVP TC2": "MVP_TC2"
  },
  "destinations": {
    "LDI": "LDI_YARD",
    "Post Oak": "POST_OAK_PIT",
    "WM": "WASTE_MANAGEMENT_LEWISVILLE",
    "Waste Management": "WASTE_MANAGEMENT_LEWISVILLE"
  },
  "materials": {
    "Class2": "CLASS_2_CONTAMINATED",
    "Class 2": "CLASS_2_CONTAMINATED",
    "Contaminated": "CLASS_2_CONTAMINATED",
    "Clean": "NON_CONTAMINATED",
    "Clean Fill": "NON_CONTAMINATED",
    "Spoils": "SPOILS",
    "Waste": "SPOILS",
    "Flex Base": "FLEXBASE",
    "Utility Stone": "UTILITY_STONE"
  }
}
```

---

### 2. filename_schema.yml - **Status: ✅ Implemented**

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

# Folder-based metadata extraction
folder_metadata:
  import_folders: ["import", "imports", "delivery", "deliveries"]
  export_folders: ["export", "exports", "disposal"]
  
  # Date folder pattern
  date_pattern: "\\d{4}-\\d{2}-\\d{2}"
```

---

### 3. Vendor Template Example: WM_LEWISVILLE.yml - **Status: ✅ Implemented**

**Purpose:** Define vendor-specific extraction rules with ROI (Region of Interest) coordinates.

**Format:**
```yaml
vendor:
  name: "WASTE_MANAGEMENT_LEWISVILLE"
  aliases:
    - "Waste Management"
    - "WM Lewisville"
    - "WM"
  
  logo:
    enabled: true
    template_path: "config/logos/wm_logo.png"
    confidence_threshold: 0.85
    
  fields:
    ticket_number:
      roi:
        x: 0.75  # Top-right quadrant
        y: 0.0
        width: 0.25
        height: 0.15
      regex: "\\bWM-?\\d{8}\\b"
      priority: 1
      
    manifest_number:
      roi:
        x: 0.0
        y: 0.3
        width: 1.0
        height: 0.2
      regex: "(?:Manifest|Profile)[:\\s#]+([A-Z0-9-]{8,20})"
      required: true  # Critical for contaminated loads
      
    date:
      roi:
        x: 0.0
        y: 0.0
        width: 0.5
        height: 0.15
      regex: "\\b(\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4})\\b"
      
    quantity:
      roi:
        x: 0.4
        y: 0.5
        width: 0.3
        height: 0.15
      regex: "(\\d+\\.\\d+)\\s*(?:tons?|TONS)"
      
    truck_number:
      roi:
        x: 0.0
        y: 0.85
        width: 0.3
        height: 0.15
      regex: "(?:Truck|Unit)[:\\s#]+(\\d{1,4})"
      
  material_keywords:
    CLASS_2_CONTAMINATED:
      - "contaminated"
      - "class 2"
      - "hazardous"
      
  destination_default: "WASTE_MANAGEMENT_LEWISVILLE"
```

---

### 4. acceptance.yml - **Status: ✅ Implemented**

**Purpose:** Define quality thresholds and performance targets for CI/CD.

**Format:**
```yaml
accuracy_targets:
  ticket_number:
    overall: 0.95  # 95% minimum
    clean_scans: 0.98
    
  manifest_number:
    recall: 1.00  # 100% required for contaminated
    
  vendor_classification:
    known_templates: 0.97
    unknown_vendors: 0.90
    
  date_extraction: 0.99
  
  source_destination:
    labeled: 0.95
    inferred: 0.85
    
  material_classification:
    contaminated_vs_clean: 0.98
    specific_types: 0.90

performance_targets:
  seconds_per_page: 3.0
  pages_per_hour: 1200
  
  batch_processing:
    max_pages: 100
    max_duration_minutes: 5

compliance_requirements:
  manifest_recall: 1.00  # Zero tolerance
  retention_years: 5
```

---

### 5. output_config.yml - **Status: ✅ Implemented**

**Purpose:** Configure flexible output destinations (database, files, or both).

**Format:**
```yaml
output:
  database:
    enabled: true
    connection_string: ${DB_CONNECTION_STRING}
    
  excel:
    enabled: true
    path: "outputs/tracking_export.xlsx"
    sheets:
      - "All Daily"
      - "Class2_Daily"
      - "Non Contaminated"
      - "Spoils"
      - "Import"
      
  csv_exports:
    invoice_match:
      enabled: true
      path: "outputs/invoice_match.csv"
      delimiter: "|"
      
    manifest_log:
      enabled: true
      path: "outputs/manifest_log.csv"
      
    review_queue:
      enabled: true
      path: "outputs/review_queue.csv"
```

---

## CLI Specification

### Command-Line Interface

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

# PART 3: DEVELOPMENT STATUS & ROADMAP

## Implementation Progress (as of Nov 4, 2025)

### ✅ COMPLETED (Week 1: Foundation - ~20%)

**Database Infrastructure:**
- ✅ Complete SQL Server schema (9 tables)
- ✅ Connection manager with environment variables
- ✅ Schema setup script (setup_database.py)
- ✅ Windows and SQL Server authentication support
- ✅ Added truck_number field (v1.1 update)

**Module Structure:**
- ✅ Complete folder hierarchy (src/truck_tickets/)
- ✅ Data models with type hints
- ✅ Configuration system
- ✅ Utilities (SynonymNormalizer, OutputManager)

**Configuration:**
- ✅ synonyms.json - Text normalization
- ✅ filename_schema.yml - Filename parsing rules
- ✅ acceptance.yml - Quality thresholds
- ✅ output_config.yml - Output toggles
- ✅ WM_LEWISVILLE.yml - First vendor template

**Sample Data:**
- ✅ 84 sample files collected
- ✅ 13 vendors represented
- ✅ Mix of tickets, manifests, invoices

**Repository:**
- ✅ Pre-commit hooks configured
- ✅ Black formatting applied
- ✅ .gitignore updated
- ✅ Sample data tracked (README only)

---

### ⏳ IN PROGRESS (Week 2: Core Extraction)

**Field Extractors (Stubs Created, Logic Needed):**
- ⏳ Ticket number extraction with multiple regex patterns
- ⏳ Manifest number extraction (CRITICAL for compliance)
- ⏳ Date parsing with multiple format support
- ⏳ Vendor detection (logo + keyword matching)
- ⏳ Quantity and units extraction
- ⏳ Source/destination identification
- ⏳ Truck number extraction (NEW v1.1)

**Main Processor:**
- ⏳ PDF to pages extraction
- ⏳ Batch OCR processing
- ⏳ Vendor template loading and application
- ⏳ Field extraction with confidence scoring
- ⏳ Text normalization
- ⏳ Database insertion
- ⏳ Review queue routing

---

### ❌ NOT STARTED

**Database Operations:**
- ❌ TicketRepository class
- ❌ Insert with duplicate detection (120-day window)
- ❌ Reference data lookups by canonical name
- ❌ Review queue management
- ❌ Processing run ledger

**Export Generators:**
- ❌ Excel tracking workbook (10 sheets)
- ❌ Invoice matching CSV (pipe-delimited)
- ❌ Manifest compliance log
- ❌ Review queue export
- ❌ Job Week/Month calculation functions

**Additional Vendor Templates:**
- ❌ LDI Yard template
- ❌ Post Oak Pit template
- ❌ Heidelberg template
- ❌ Alliance, Arcosa, Big City, etc. (10+ templates)

**CLI Interface:**
- ❌ Argument parsing
- ❌ Batch processing orchestration
- ❌ Progress reporting
- ❌ Error handling

**Testing:**
- ❌ Unit tests for extractors
- ❌ Integration tests for pipeline
- ❌ Gold standard annotation (30-50 pages)
- ❌ Regression testing framework
- ❌ Accuracy measurement tools

---

## 2-Week Implementation Plan (Updated)

### **Week 1: Foundation ✅ COMPLETE**

**Days 1-2: Database & Infrastructure** ✅
- ✅ Set up SQL Server database and tables
- ✅ Implement connection manager
- ✅ Create schema setup script
- ✅ Build basic record insertion

**Days 3-4: Configuration & Normalization** ✅
- ✅ Create synonyms.json
- ✅ Build SynonymNormalizer class
- ✅ Implement filename parser
- ✅ Create folder-based metadata extraction
- ✅ Add precedence logic

**Day 5: Sample Data & Testing Foundation** ✅
- ✅ Collect 84 sample files
- ✅ Create project structure
- ✅ Set up development environment

---

### **Week 2: Core Extraction & Production** ⏳ IN PROGRESS

**Days 6-7: Vendor Templates & Extraction**
- ✅ Create WM Lewisville template (highest priority)
- ⏳ Implement field extractors (ticket, manifest, date, vendor, quantity, truck)
- ⏳ Build vendor-specific regex handlers
- ❌ Create LDI Yard template
- ❌ Create Post Oak Pit template
- ❌ Implement logo detection

**Days 8-9: Database Operations & Pipeline**
- ❌ Build TicketRepository class
- ❌ Implement duplicate detection
- ❌ Create main processor orchestration
- ❌ Add review queue routing
- ❌ Build processing run ledger

**Day 10: Export Generators**
- ❌ Build Excel exporter (5 sheets)
- ❌ Create invoice matching CSV export
- ❌ Implement manifest log CSV export
- ❌ Create review queue CSV export
- ❌ Add Job Week/Month calculation functions
- ❌ Test sheet mappings against current spreadsheet

---

### **Post-Launch (Weeks 3-4): Optimization**
- ❌ Performance tuning (multi-threading)
- ❌ Additional vendor templates (10+ vendors)
- ❌ GUI for review queue (optional)
- ❌ Automated monitoring dashboard
- ❌ Production spot-check validation

---

## Critical Path for Next Session

### Priority 1: Complete Field Extractors (Days 6-7)
1. **Ticket Number Extractor**
   - Implement regex patterns
   - Add ROI-based extraction
   - Handle vendor-specific formats
   - Test on WM samples

2. **Manifest Number Extractor** (CRITICAL)
   - Implement manifest regex
   - Ensure 100% recall for contaminated loads
   - Route to review queue if missing
   - Test on WM manifests

3. **Date Parser**
   - Support multiple date formats
   - Implement precedence (filename → folder → OCR)
   - Validate against job date range

4. **Vendor Detector**
   - Keyword matching
   - Logo detection (future)
   - Confidence scoring
   - Test on 13 sample vendors

5. **Quantity & Truck Number**
   - Parse quantity with units
   - Extract truck numbers
   - Handle missing values gracefully

---

### Priority 2: Build Main Processor (Days 8-9)
1. **PDF Pipeline**
   - Convert PDF to pages
   - Run OCR on each page
   - Apply vendor template
   - Extract fields

2. **Database Operations**
   - Lookup reference data by canonical name
   - Check for duplicates (120-day window)
   - Insert ticket record
   - Log to processing_runs

3. **Review Queue**
   - Route critical failures (missing manifest, ticket)
   - Log warnings (low confidence, duplicates)
   - Generate review queue CSV

---

### Priority 3: Generate Exports (Day 10)
1. **Excel Workbook**
   - Implement 5 sheet generators
   - Add Job Week/Month functions
   - Test against legacy format

2. **CSV Exports**
   - Invoice matching report
   - Manifest log
   - Review queue

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

### Risk 4: Dual Vendor System (NEW v1.1)
**Impact:** Cannot track material supplier separate from hauling company  
**Mitigation:**
- v1: Use primary vendor field for ticket issuer
- v2: Add trucking_vendor_id field
- Document limitations in user training

### Risk 5: Data Migration
**Impact:** Historical data not in database  
**Mitigation:**
- Excel remains valid reporting tool
- Database builds from go-forward date
- Optional backfill for recent history

---

## Deferred to v2.0 (Accounting Integration)

**Scope Expansion Required:**
- Dual vendor tracking (material_vendor_id + trucking_vendor_id)
- Invoice number capture and tracking
- Unit price and rate storage
- Cost reconciliation features
- Integration with CLEANED_SEPT_2025_TRUCKING_SPREADSHEET.xlsx workflows

**Timeline:** 4-6 weeks additional development  
**Prerequisites:** v1.0 successfully deployed and validated

---

## Contact & Questions

**Project Lead:** [User]  
**Development Team:** Claude Code / Windsurf  
**Document Version:** 1.1 (Updated with Worksheet Analysis)  
**Last Updated:** November 4, 2025

---

## Appendix: Key Findings from Worksheet Analysis

### Corrected Understanding: Spoils Locations
- **BECK SPOILS, NTX Spoils, UTX Spoils, MVP-TC1, MVP-TC2** are SOURCE locations (other subs' spoils staging areas)
- **NOT separate destinations** - all spoils go to Waste Management Lewisville
- Updated source count: **13 total sources** (8 primary excavation + 5 spoils staging)
- Updated destination count: **3 primary destinations** (WM Lewisville, LDI Yard, Post Oak Pit)

### Dual Vendor System Identified
- Accounting spreadsheet reveals distinction between MATERIAL VENDOR and TRUCKING VENDOR
- Current spec has only one vendor_id field
- Decision: v1 uses single vendor (ticket issuer), v2 adds trucking_vendor_id

### Truck Number Field Added
- Present in accounting data: `TRUCK #` column
- Added to truck_tickets table as VARCHAR(50)
- Extraction regex added to field specifications

### Invoice/Pricing Data Out of Scope
- Accounting spreadsheet tracks: invoice numbers, unit prices, rates, totals
- Marked as "out of scope for v1" (operational tracking only)
- Full accounting integration deferred to v2

### Job Week/Month Calculations Needed
- Excel format: "Week 16 - (End 10/20/24)", "004 - October 24"
- SQL helper functions required (not yet implemented)
- Added to Day 10 tasks

---

**This specification is aligned with development progress and ready for continued implementation.**
