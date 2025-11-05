# Truck Ticket Processing System - Alignment Analysis Report

**Date:** November 4, 2025  
**Analysis Scope:** Specification vs. Excel Worksheets vs. Database Schema

---

## Executive Summary

This analysis examines the alignment between the **Truck Ticket Processing Complete Specification**, the **existing Excel tracking workbooks** (24-105_Load_Tracking_Log.xlsx and CLEANED_SEPT_2025_TRUCKING_SPREADSHEET.xlsx), and the **proposed database schema**.

### Overall Assessment: ⚠️ **PARTIAL ALIGNMENT WITH CRITICAL GAPS**

**Key Findings:**
1. ✅ Core export material tracking fields align well
2. ⚠️ Import material tracking has **significant gaps**
3. ❌ Invoice/accounting data fields **not in database schema**
4. ⚠️ Vendor vs. Trucking Vendor distinction **not addressed**
5. ⚠️ Pricing/billing fields **excluded from v1 scope**

---

## 1. EXPORT MATERIALS - Field Alignment

### ✅ WELL ALIGNED

The specification and database schema handle export materials comprehensively:

| Field | Spec | DB Schema | Excel Tracking | Status |
|-------|------|-----------|----------------|--------|
| Ticket Number | ✅ Required | `ticket_number` VARCHAR(50) | Not directly tracked | ✅ Aligned |
| Ticket Date | ✅ Required | `ticket_date` DATE | Date column (all sheets) | ✅ Aligned |
| Material Type | ✅ Required | `material_id` FK | Class 2/Non Contaminated/Spoils | ✅ Aligned |
| Source Location | ✅ Required | `source_id` FK | Source columns (Class2_Daily) | ✅ Aligned |
| Destination | ✅ Required | `destination_id` FK | Location column | ✅ Aligned |
| Vendor | ✅ Required | `vendor_id` FK | Inferred from destination | ✅ Aligned |
| Quantity | ✅ Optional | `quantity` DECIMAL | Not tracked (count only) | ✅ Aligned |
| Manifest Number | ✅ Required for Class2 | `manifest_number` VARCHAR(50) | Not tracked | ✅ Aligned |

**Export Material Sources (from Excel Class2_Daily sheet + Spoils areas):**

**Primary Excavation Areas (Class 2 Contaminated):**
- PODIUM ✅
- Zone E GARAGE ✅
- South_MSE Wall ✅
- MSE Wall ✅
- PierEx ✅
- Pond ✅
- South Fill ✅
- Tract 2 ✅

**Other Subcontractors' Spoils Areas:**
- BECK SPOILS ✅ (Other sub's spoils - hauled to WM)
- NTX Spoils ✅ (Other sub's spoils - hauled to WM)
- UTX Spoils ✅ (Other sub's spoils - hauled to WM)
- MVP-TC1 ✅ (Other sub's spoils - hauled to WM)
- MVP-TC2 ✅ (Other sub's spoils - hauled to WM)

**Non-Contaminated Sources:**
- SPG (South Parking Garage - Tract 2) ✅

**Export Material Destinations:**
- Waste Management Lewisville (Class 2 & Spoils) ✅
- LDI YARD (Non-Contaminated) ✅
- Post Oak Pit (Non-Contaminated) ✅

**Export Material Sources (Additional - Other Subs' Spoils):**
- BECK SPOILS ✅ (Other sub's spoils area - hauled to WM)
- NTX Spoils ✅ (Other sub's spoils area - hauled to WM)
- UTX Spoils ✅ (Other sub's spoils area - hauled to WM)
- MVP-TC1 ✅ (Other sub's spoils area - hauled to WM)
- MVP-TC2 ✅ (Other sub's spoils area - hauled to WM)

**Note:** The spoils locations (BECK, NTX, UTX, MVP-TC1, MVP-TC2) are actually **SOURCE locations** representing other subcontractors' spoils areas on the project site. These materials are hauled TO Waste Management Lewisville for disposal, making WM the destination.

All canonical values from the spec are represented in the Excel sheets.

---

## 2. IMPORT MATERIALS - Critical Gaps

### ⚠️ SIGNIFICANT MISALIGNMENT

The Excel Import sheet tracks material quantities by type, but **lacks critical fields** for invoice matching and vendor tracking.

#### Excel Import Sheet Structure:
```
Columns: DATE, 3X5, ASPHALT, C2, DIRT, FILL, FLEX, FLEXBASE, ROCK, UTILITY STONE, Grand Total
```

#### Material Types - ✅ Aligned:
| Excel Column | Spec Canonical | Status |
|--------------|----------------|--------|
| 3X5 | `3X5` | ✅ Aligned |
| ASPHALT | `ASPHALT` | ✅ Aligned |
| C2 | `C2` | ✅ Aligned |
| DIRT | `DIRT` | ✅ Aligned |
| FILL | `FILL` | ✅ Aligned |
| FLEX | `FLEX` | ✅ Aligned |
| FLEXBASE | `FLEXBASE` | ✅ Aligned |
| ROCK | `ROCK` | ✅ Aligned |
| UTILITY STONE | `UTILITY_STONE` | ✅ Aligned |

#### ❌ Missing Import Fields in Current Tracking:

**Not Currently Tracked (but noted as missing in spec):**
1. **Vendor Name** - Critical for invoice matching
2. **Source Quarry/Supplier** - Needed for quality tracking
3. **Delivery Ticket Numbers** - Essential for invoice reconciliation
4. **Truck Number** - Useful for delivery verification
5. **Delivery Time** - Optional but helpful for logistics

**From Spec (lines 146-149):**
> "**Missing:** Vendor names, source quarries, delivery ticket numbers"
> "Current Volume: 0-250 loads per day (varies by construction phase)"

**Database Schema Support:**
- ✅ `vendor_id` field exists in `truck_tickets` table
- ✅ `ticket_number` field exists
- ✅ `source_id` field exists (optional for imports)
- ✅ `ticket_type_id` distinguishes IMPORT vs EXPORT

**⚠️ Gap Identified:** The spec acknowledges these fields are missing from current tracking, but the database schema is ready to capture them. However, **OCR extraction logic for import delivery tickets is not detailed** in the spec.

---

## 3. INVOICE/ACCOUNTING DATA - Major Gap

### ❌ CRITICAL MISALIGNMENT

The **CLEANED_SEPT_2025_TRUCKING_SPREADSHEET.xlsx** reveals extensive accounting/invoice data that is **NOT represented in the database schema**.

#### Accounting Spreadsheet Structure (24-105 sheet):
```
Columns:
- 24-105-PHMS
- DATE
- MATERIAL_INV_# (Material Invoice Number)
- MATERIAL VENDOR
- MATERIAL_TICKET_# (Material Ticket Number)
- MATERIAL
- TONS YARDS LOADS
- UNIT PRICE
- MATERIAL_TOTAL (Material Cost)
- TRUCKING VENDOR (separate from Material Vendor!)
- HAUL DATE
- INV #.1 (Trucking Invoice Number)
- MATERIAL_TICKET_#.1 (Trucking Ticket Number)
- TRUCK #
- TONS YARDS HOURS
- RATE (Trucking Rate)
- TOTAL .1 (Trucking Cost)
- NOTES
```

#### ❌ Fields NOT in Database Schema:

| Accounting Field | In DB Schema? | Spec Status |
|------------------|---------------|-------------|
| MATERIAL_INV_# | ❌ No | Out of scope (v1) |
| UNIT PRICE | ❌ No | Out of scope (v1) |
| MATERIAL_TOTAL | ❌ No | Out of scope (v1) |
| TRUCKING VENDOR | ❌ No | **Not mentioned** |
| TRUCKING INV # | ❌ No | Out of scope (v1) |
| TRUCKING TICKET_# | ❌ No | **Not mentioned** |
| TRUCK # | ❌ No | **Missing** |
| TRUCKING RATE | ❌ No | Out of scope (v1) |
| TRUCKING TOTAL | ❌ No | Out of scope (v1) |

**From Spec (Out-of-Scope Section):**
> "❌ Price reconciliation and rate validation"
> "❌ Line-item cost disputes"
> "❌ Automatic GL (General Ledger) coding"
> "❌ Direct ERP integration"

### 🚨 Critical Discovery: DUAL VENDOR SYSTEM

**The accounting spreadsheet reveals a distinction between:**
1. **MATERIAL VENDOR** - Who supplies the material
2. **TRUCKING VENDOR** - Who hauls the material

**Example from data:**
```
MATERIAL VENDOR: HELIDELBERG
TRUCKING VENDOR: STATEWIDE MATERIALS

MATERIAL VENDOR: WM LEWISVILLE-EXPORT
TRUCKING VENDOR: CORPOTECH
```

**⚠️ Database Schema Issue:**
The `truck_tickets` table has only ONE `vendor_id` field. The spec does not address:
- Which vendor this field represents (material supplier or trucking company?)
- How to capture both vendors when they differ
- Whether trucking companies issue separate tickets (they appear to based on MATERIAL_TICKET_#.1)

### Recommendations:
1. **Clarify vendor semantics** - Is the primary `vendor_id` the ticket issuer, material supplier, or trucking company?
2. **Consider adding `trucking_vendor_id`** if hauling companies need separate tracking
3. **Add `truck_number`** field for delivery verification
4. **Document invoice matching scope** - Current spec focuses on ticket numbers only, but accounting needs invoice numbers too

---

## 4. DATABASE SCHEMA COMPLETENESS

### ✅ Core Schema Structure - Well Designed

The database schema includes:

```sql
✅ jobs (job_code, job_name, dates)
✅ materials (material_name, material_class, requires_manifest)
✅ sources (source_name, job_id)
✅ destinations (destination_name, facility_type, requires_manifest)
✅ vendors (vendor_name, vendor_code)
✅ ticket_types (IMPORT/EXPORT)
✅ truck_tickets (main transaction table)
✅ review_queue (exception handling)
✅ processing_runs (audit trail)
```

### ⚠️ Potential Schema Gaps:

#### 1. Missing Truck Number Field
**Impact:** Cannot match tickets to specific trucks for delivery verification

**Recommendation:**
```sql
ALTER TABLE truck_tickets
ADD truck_number VARCHAR(50);
```

#### 2. Single Vendor Field Issue
**Impact:** Cannot distinguish material supplier from trucking company when different

**Recommendation:**
```sql
ALTER TABLE truck_tickets
ADD trucking_vendor_id INT;

ALTER TABLE truck_tickets
ADD FOREIGN KEY (trucking_vendor_id) REFERENCES vendors(vendor_id);
```

#### 3. No Invoice Number Fields
**Impact:** Cannot directly link tickets to vendor invoices

**Note:** Spec states invoice matching is "out of scope for v1" but the `invoice_match.csv` export is supposed to provide ticket numbers for manual reconciliation.

**Potential Future Addition:**
```sql
-- Future: If invoice tracking is needed
ALTER TABLE truck_tickets
ADD invoice_number VARCHAR(50),
ADD invoice_date DATE,
ADD invoice_line_item INT;
```

#### 4. No Job Week/Month Calculation Fields
**Impact:** Excel exports require "Job Week" and "Job Month" calculations

**Status:** ✅ Spec addresses this with SQL logic (lines 1014-1015):
```sql
-- Calculate Job Week and Job Month
```

However, the calculation logic is **not provided** in the spec. Current Excel format:
- Job Week: "Week 16 - (End 10/20/24)"
- Job Month: "004 - October 24"

**Recommendation:** Add calculation logic to spec or create helper functions/views.

---

## 5. DATA TYPE ALIGNMENT

### Quantity Handling

**Excel Sheets:** Store daily **counts** (number of loads)
```
Example: Class2_Daily shows "47" loads from PODIUM on a given date
```

**Database Schema:**
```sql
quantity DECIMAL(10,2),
quantity_unit VARCHAR(20),  -- 'TONS', 'CY', 'LOADS'
```

**Accounting Spreadsheet:**
```
TONS YARDS LOADS: 27.13 (decimal quantities)
```

✅ **Aligned** - Database can store both counts and measured quantities

### Ticket Number Format

**Spec Regex:**
```regex
\b\d{7,10}\b  -- 7-10 digit numbers
```

**Accounting Spreadsheet Data:**
```
MATERIAL_TICKET_#.1: Integer values (e.g., 201815, 201816)
```

**Database Schema:**
```sql
ticket_number VARCHAR(50)  -- Supports both numeric and alphanumeric
```

✅ **Aligned** - VARCHAR(50) handles all formats

---

## 6. WORKFLOW ALIGNMENT

### Current Workflow (from Excel)

**Field Team:**
1. Receives paper tickets → manually counts by source area
2. Enters daily totals into Excel by source location
3. Does NOT enter individual ticket numbers

**Office Team:**
1. Re-scans tickets for invoice matching
2. Manually reads ticket numbers
3. Matches to vendor invoices (not in Excel)

### Proposed Workflow (from Spec)

**New Single-Scan System:**
1. Field team scans tickets → OCR extracts ticket numbers automatically
2. Database stores individual ticket records (not aggregated)
3. System generates Excel daily summaries AND invoice match CSV
4. Office team matches invoice CSV to vendor invoices

✅ **Workflow Improvement Aligned** - System eliminates double-scanning and manual counting

---

## 7. NORMALIZATION & CONTROLLED VOCABULARY

### ✅ Material Types - Aligned

**Spec Canonical Values:**
```
Export: CLASS_2_CONTAMINATED, NON_CONTAMINATED, SPOILS
Import: 3X5, ASPHALT, C2, DIRT, FILL, FLEX, FLEXBASE, ROCK, UTILITY_STONE
```

**Excel Values:**
```
Export: "Class 2", "Non Contaminated", "Spoils"
Import: "3X5", "ASPHALT", "C2", "DIRT", "FILL", "FLEX", "FLEXBASE", "ROCK", "UTILITY STONE"
```

**Accounting Spreadsheet:**
```
"UTILITY STONE", "CONTAMINATED DIRT"
```

✅ Synonym mapping (synonyms.json) handles variations

### ✅ Source Locations - Aligned

All source locations from Excel are represented in canonical list.

### ✅ Destinations - Aligned

All destinations from Excel are represented in canonical list.

**Important Clarification: Spoils Locations**
The locations labeled as "BECK SPOILS", "NTX Spoils", "UTX Spoils", "MVP-TC1", and "MVP-TC2" in the Excel "Spoils" sheet are actually **SOURCE locations**, not destinations. These represent areas where other subcontractors' spoils materials are staged on the project site. These materials are then hauled TO Waste Management Lewisville for disposal.

**Actual Spoils Workflow:**
- **Source:** BECK SPOILS, NTX Spoils, UTX Spoils, MVP-TC1, MVP-TC2 (other subs' spoils areas)
- **Material Type:** SPOILS
- **Destination:** Waste Management Lewisville

This means the actual export destinations are simpler than initially interpreted:
1. **Waste Management Lewisville** - Receives Class 2 contaminated AND spoils
2. **LDI YARD** - Receives non-contaminated material
3. **Post Oak Pit** - Receives non-contaminated material

### ⚠️ Vendor Names - Partial Alignment

**Excel Tracking:** 
- Vendors are inferred from destinations (WM Lewisville, LDI Yard, Post Oak)

**Accounting Spreadsheet:**
- Shows explicit vendor names: "HELIDELBERG", "WM LEWISVILLE-EXPORT"
- Shows trucking vendors: "STATEWIDE MATERIALS", "CORPOTECH"

**Spec Canonical Values:**
```
WASTE_MANAGEMENT_LEWISVILLE
LDI_YARD
POST_OAK_PIT
BECK_SPOILS
NTX_SPOILS
UTX_SPOILS
```

**Gap:** Import material vendors (Heidelberg, Acme Aggregate, etc.) not in canonical list yet.

---

## 8. EXCEL EXPORT MAPPING

### ✅ Sheet Generation - Well Specified

The spec provides detailed mapping for generating Excel sheets from database:

**Confirmed Mappings:**

| Excel Sheet | Source Data | Status |
|-------------|-------------|--------|
| All Daily | Aggregate ticket counts by date and material | ✅ SQL provided |
| Class2_Daily | Pivot by source location | ✅ SQL provided |
| Non Contaminated | Filter by NON_CONTAMINATED | ✅ Implied |
| Spoils | Filter by SPOILS material | ✅ Implied |
| Import | Filter by IMPORT ticket_type | ⚠️ Need query |

**⚠️ Missing SQL Queries:**
- Non Contaminated sheet generation
- Spoils sheet generation  
- Import sheet generation

### ⚠️ Job Week/Month Calculation

**Excel Format:**
```
Job Week: "Week 16 - (End 10/20/24)"
Job Month: "004 - October 24"
```

**Spec References:**
Lines 1001-1002: Mentions these fields but doesn't provide calculation logic

**Recommendation:** Add functions/views for:
```sql
-- Calculate job week number from job start date
-- Format: "Week {N} - (End {end_date})"

-- Calculate job month number and name
-- Format: "{NNN} - {Month} {YY}"
```

---

## 9. COMPLIANCE & REGULATORY ALIGNMENT

### ✅ Manifest Tracking - Aligned

**Spec Requirements:**
- Every Class 2 contaminated load must have manifest number OR be in review queue
- 100% recall requirement (regulatory)
- Manifest log CSV export with 5-year retention

**Database Schema:**
```sql
manifest_number VARCHAR(50),
materials.requires_manifest BIT
```

**Excel Current State:**
- Manifest numbers NOT tracked in current Excel sheets
- Will be new capability

✅ **Aligned** - System will capture manifests that current process doesn't

### ✅ Audit Trail - Aligned

**Spec Requirements:**
```sql
- file_id, file_page (source PDF tracking)
- request_guid (batch processing ID)
- created_at, updated_at (timestamps)
- processed_by (user/system account)
- SHA-256 file hashes
```

**Database Schema:**
✅ All fields present in `truck_tickets` and `processing_runs` tables

---

## 10. SUMMARY OF ALIGNMENT ISSUES

### 🟢 WELL ALIGNED:
1. ✅ Export material tracking (Class 2, Non-Contaminated, Spoils)
2. ✅ Source locations (13 total: 8 primary excavation areas + 5 other subs' spoils areas)
3. ✅ Destinations (3 primary: WM Lewisville, LDI Yard, Post Oak Pit)
4. ✅ Material type normalization
5. ✅ Manifest number tracking (new capability)
6. ✅ Duplicate detection logic
7. ✅ Audit trail and compliance
8. ✅ Core database schema structure
9. ✅ Excel daily summary generation logic

**Clarification Made:** Spoils locations (BECK, NTX, UTX, MVP-TC1, MVP-TC2) are SOURCE locations representing other subcontractors' spoils areas, all hauled to WM Lewisville as the destination.

### 🟡 PARTIAL ALIGNMENT (Needs Clarification):
1. ⚠️ **Import vendor tracking** - System supports it, but OCR extraction not detailed
2. ⚠️ **Truck number field** - Used in accounting but not in DB schema
3. ⚠️ **Job Week/Month calculation** - Referenced but logic not provided
4. ⚠️ **Import sheet SQL generation** - Not provided in spec
5. ⚠️ **Non-Contaminated/Spoils sheet SQL** - Not provided in spec

### 🔴 CRITICAL GAPS:
1. ❌ **Dual Vendor System** (Material Vendor vs. Trucking Vendor) - Not addressed
2. ❌ **Invoice number tracking** - Accounting spreadsheet has it, DB doesn't
3. ❌ **Pricing/billing fields** - Marked "out of scope" but widely used in accounting
4. ❌ **Trucking ticket numbers** (separate from material tickets) - Not mentioned

---

## 11. RECOMMENDATIONS

### Priority 1: Critical Clarifications Needed
1. **Define vendor semantics** - Clarify if `vendor_id` is ticket issuer, material supplier, or trucker
2. **Address dual vendor scenario** - Add `trucking_vendor_id` if needed for separate hauling company
3. **Add truck_number field** - Present in accounting data, useful for verification
4. **Provide Job Week/Month calculation logic** - Required for Excel export compatibility

### Priority 2: Specification Enhancements
1. **Add Import OCR extraction guidance** - Delivery tickets may have different formats than export tickets
2. **Document Import vendor detection** - How to identify quarry/supplier names from delivery tickets
3. **Complete Excel export SQL** - Add queries for Import, Non-Contaminated, and Spoils sheets
4. **Clarify invoice matching scope** - Currently focused on ticket numbers only

### Priority 3: Schema Enhancements
```sql
-- Recommended additions:
ALTER TABLE truck_tickets
ADD truck_number VARCHAR(50),
ADD trucking_vendor_id INT,
ADD FOREIGN KEY (trucking_vendor_id) REFERENCES vendors(vendor_id);

-- Optional (future):
ALTER TABLE truck_tickets
ADD invoice_number VARCHAR(50),
ADD invoice_date DATE;
```

### Priority 4: Future Considerations
1. **Price/rate tracking** - Currently out of scope, but accounting spreadsheet shows it's essential
2. **Multi-job invoice matching** - Accounting spreadsheet has multiple job sheets
3. **Separate material vs trucking invoices** - May need separate invoice tables

---

## 12. CONCLUSION

The specification provides a **solid foundation** for the truck ticket processing system, with particularly strong alignment for:
- Export material tracking
- Source/destination normalization
- Manifest compliance
- Audit trail requirements

However, there are **significant gaps** between the proposed system and the real-world accounting needs revealed in the CLEANED_SEPT_2025_TRUCKING_SPREADSHEET.xlsx:

**The spec focuses on field operations tracking** (daily load counts by area), while **the accounting spreadsheet reveals complex invoice reconciliation needs** with dual vendors, pricing, and separate trucking charges.

### Key Question for Stakeholders:
**Is the goal to replace just the operational tracking (24-105_Load_Tracking_Log.xlsx), or also the accounting/invoice system (CLEANED_SEPT_2025_TRUCKING_SPREADSHEET.xlsx)?**

If **operational tracking only** → Current spec is well-aligned (minor additions needed)

If **full accounting integration** → Significant scope expansion required for v2

---

**Report Prepared By:** Claude  
**Analysis Date:** November 4, 2025  
**Documents Analyzed:**
- Truck_Ticket_Processing_Complete_Spec.md (1808 lines)
- 24-105_Load_Tracking_Log.xlsx (10 sheets)
- CLEANED_SEPT_2025_TRUCKING_SPREADSHEET.xlsx (24+ job sheets)
- README.md (system architecture)
