# Windsurf Task Prompt Templates
## Project 24-105: Truck Ticket Processing System

**Purpose:** Ready-to-use prompt templates for each task type with optimal model selection.

---

## 📋 How to Use This Guide

1. **Identify your GitHub issue** (e.g., Issue #4)
2. **Check the model assignment** in `truck_ticket_issues_with_models.csv`
3. **Copy the appropriate template** below
4. **Fill in the specific details** from your issue
5. **Run in Windsurf** with the designated model

---

## 🎯 Template 1: Critical Business Logic (Use Claude 4.5)

### **Example: Issue #4 - Duplicate Detection**

```markdown
TASK: Implement Duplicate Detection Logic (Issue #4)
MODEL: Claude Sonnet 4.5 (reasoning required)
PRIORITY: Critical

CONTEXT:
I'm implementing the duplicate detection system for the Truck Ticket Processing pipeline (Project 24-105).

REQUIREMENTS FROM SPEC v1.1:
1. Check for existing ticket with same (ticket_number, vendor_id)
2. Search within rolling 120-day window BEFORE current ticket date
3. If duplicate found:
   - Set new_ticket.duplicate_of = existing_ticket.ticket_id
   - Set new_ticket.review_required = True
   - Route to review_queue with severity=WARNING
   - Include comparison data (both ticket details)
4. Edge cases to handle:
   - Same ticket number, different vendors (NOT a duplicate)
   - Same ticket number, same vendor, different dates within 120 days (IS duplicate)
   - Reprocessing same file (should detect as duplicate)

IMPLEMENTATION TARGET:
- File: src/truck_tickets/database/repository.py
- Method: TicketRepository.check_duplicate(ticket_data: Dict) -> Optional[int]

ACCEPTANCE CRITERIA:
- Returns None if no duplicate found
- Returns existing ticket_id if duplicate found
- SQL query performs efficiently (indexed on ticket_number, vendor_id, ticket_date)
- Handles timezone considerations for date window
- Includes unit tests with at least 5 test cases

Please implement the complete function with:
1. SQL query using SQLAlchemy
2. Edge case handling
3. Review queue integration
4. Unit tests (pytest)
5. Docstring with examples
```

**When to use this template:**
- ✅ Task involves compliance or regulatory requirements
- ✅ Complex business rules with multiple conditions
- ✅ Cross-module coordination required
- ✅ First-time implementation (no existing pattern)

---

## ⚡ Template 2: Mechanical Generation (Use SWE-1.5)

### **Example: Issue #2 - ORM Model Generation**

```markdown
TASK: Generate SQLAlchemy ORM Models (Issue #2)
MODEL: SWE-1.5 (mechanical transform)
PRIORITY: Medium

CONTEXT:
Generate SQLAlchemy ORM models from the SQL schema defined in spec v1.1.

INPUT (SQL Schema):
See: /docs/Truck_Ticket_Processing_Complete_Spec_v1.1.md
Section: "Data Model (SQL Server) - Updated v1.1"

TABLES TO GENERATE (9 total):
1. jobs
2. materials
3. sources
4. destinations
5. vendors
6. ticket_types
7. truck_tickets (main table with 15+ columns)
8. review_queue
9. processing_runs

OUTPUT FILE:
src/truck_tickets/database/models.py

REQUIREMENTS:
- Use SQLAlchemy declarative_base()
- Include all foreign key relationships
- Add __repr__ methods for debugging
- Use appropriate column types (String, Integer, Date, DateTime, DECIMAL)
- Include NOT NULL constraints where specified
- Add indexes as defined in spec

FORMAT EXAMPLE:
```python
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Job(Base):
    __tablename__ = 'jobs'

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    job_code = Column(String(50), nullable=False, unique=True)
    # ... continue for all columns
```

Generate complete models file with all 9 tables.
```

**When to use this template:**
- ✅ Clear input → output transformation
- ✅ Existing pattern to follow
- ✅ Boilerplate code generation
- ✅ >80% of code is mechanical

---

## 🔗 Template 3: Complex Integration (Use Claude 4.5)

### **Example: Issue #7 - Main TicketProcessor**

```markdown
TASK: Build Main TicketProcessor Pipeline (Issue #7)
MODEL: Claude Sonnet 4.5 (orchestration complexity)
PRIORITY: Critical

CONTEXT:
Create the master orchestration class that coordinates the entire ticket processing pipeline from PDF to database.

PIPELINE FLOW:
1. Load PDF file → extract pages
2. For each page:
   a. Run OCR (use existing DocTR integration)
   b. Detect vendor (logo detection + keywords)
   c. Load vendor template (YAML config)
   d. Extract fields using extractors:
      - TicketNumberExtractor
      - DateExtractor
      - VendorExtractor
      - SourceExtractor
      - DestinationExtractor
      - MaterialExtractor
      - ManifestExtractor
      - TruckExtractor (v1.1 NEW)
   e. Apply field precedence logic (filename → folder → OCR)
   f. Normalize using SynonymNormalizer
   g. Check for duplicates (120-day window)
   h. Insert to database OR route to review queue
   i. Update ProcessingRun ledger
3. Generate outputs (Excel, CSVs)

CRITICAL REQUIREMENTS:
- MUST route all contaminated material without manifests to review queue (CRITICAL severity)
- MUST handle extraction failures gracefully (don't crash on bad PDFs)
- MUST maintain audit trail (file_hash, request_guid)
- MUST be idempotent (safe to reprocess same files)

DEPENDENCIES:
- All 8 field extractors (already implemented)
- SynonymNormalizer (implemented)
- TicketRepository (to be implemented)
- ReviewQueue manager (to be implemented)

OUTPUT FILE:
src/truck_tickets/processors/ticket_processor.py

CLASS STRUCTURE:
```python
class TicketProcessor:
    def __init__(self, config_path: str, db_connection: str):
        # Load config, initialize extractors, DB connection

    def process_folder(self, folder_path: str, job_code: str) -> ProcessingResult:
        # Orchestrate batch processing

    def process_pdf(self, pdf_path: str) -> List[TicketRecord]:
        # Process single PDF file

    def process_page(self, page: PDFPage) -> TicketRecord:
        # Process single page (extract → normalize → validate)

    def _handle_extraction_failure(self, page: PDFPage, error: Exception):
        # Route to review queue with appropriate severity
```

Please implement with:
1. Complete error handling
2. Logging at INFO level for progress
3. Review queue integration
4. Duplicate detection
5. ProcessingRun ledger tracking
6. Unit tests for each method
```

**When to use this template:**
- ✅ Multiple modules must coordinate
- ✅ Complex error handling across layers
- ✅ Business logic embedded in orchestration
- ✅ Compliance requirements throughout

---

## 📊 Template 4: Report Generation (Use Claude 4.5)

### **Example: Issue #12 - Excel Exporter**

```markdown
TASK: Build Excel Tracking Export (Issue #12)
MODEL: Claude Sonnet 4.5 (complex queries & formatting)
PRIORITY: High

CONTEXT:
Generate the tracking_export.xlsx file that matches the legacy spreadsheet format used by field teams.

REQUIRED SHEETS (5 total):
1. **All Daily** - Combined daily totals across all material types
2. **Class2_Daily** - Contaminated material by source location (8 columns)
3. **Non Contaminated** - Clean material by destination
4. **Spoils** - Waste material by spoils staging area (5 sources)
5. **Import** - Import materials by type (9 material types)

CRITICAL FORMATTING:
- Job Week: "Week 16 - (End 10/20/24)" format
- Job Month: "004 - October 24" format
- Must match legacy format EXACTLY for user acceptance

IMPLEMENTATION REQUIREMENTS:
1. Query truck_tickets table with appropriate JOINs
2. Pivot/group by date and relevant dimensions (source, destination, material)
3. Calculate Job Week/Month (requires helper function)
4. Write to Excel using openpyxl
5. Apply formatting (headers bold, number formatting)

SAMPLE SQL FOR "All Daily" SHEET:
```sql
SELECT
    ticket_date AS Date,
    DATENAME(dw, ticket_date) AS Day,
    dbo.fn_CalculateJobWeek(ticket_date, @job_start_date) AS [Job Week],
    dbo.fn_CalculateJobMonth(ticket_date, @job_start_date) AS [Job Month],
    SUM(CASE WHEN m.material_class = 'CONTAMINATED' THEN 1 ELSE 0 END) AS [Class 2],
    SUM(CASE WHEN m.material_class = 'CLEAN' THEN 1 ELSE 0 END) AS [Non Contaminated],
    SUM(CASE WHEN m.material_class = 'SPOILS' THEN 1 ELSE 0 END) AS Spoils,
    COUNT(*) AS Total
FROM truck_tickets tt
JOIN materials m ON tt.material_id = m.material_id
WHERE tt.job_id = @job_id
GROUP BY ticket_date
ORDER BY ticket_date;
```

OUTPUT FILE:
src/truck_tickets/output/excel_exporter.py

Please implement:
1. ExcelExporter class with generate() method
2. All 5 sheet generators (separate methods)
3. Job Week/Month calculation helper
4. Formatting (bold headers, borders, number formats)
5. Integration test that validates against legacy format
```

**When to use this template:**
- ✅ Complex SQL with pivots and aggregations
- ✅ Business logic in formatting/calculations
- ✅ Must match specific legacy format
- ✅ Multiple related functions coordinated

---

## 🧪 Template 5: Test Generation (Use SWE-1.5)

### **Example: Issue #11 - Test Fixtures**

```markdown
TASK: Generate Test Fixtures (Issue #11)
MODEL: SWE-1.5 (mock data generation)
PRIORITY: Medium

CONTEXT:
Create mock PDF pages with known ground truth for testing the extraction pipeline.

REQUIRED TEST FIXTURES:
1. **WM Lewisville tickets (5 pages)**
   - 3 clean scans (high quality)
   - 1 poor scan (low quality, faded text)
   - 1 with missing manifest (should route to review queue)

2. **LDI Yard tickets (3 pages)**
   - 2 clean scans
   - 1 with handwritten notes

3. **Heidelberg delivery tickets (3 pages)**
   - Import material tickets
   - Include truck numbers

GROUND TRUTH DATA:
For each fixture, create JSON with known values:
```json
{
  "file": "fixtures/wm_lewisville_001.pdf",
  "page": 1,
  "ground_truth": {
    "ticket_number": "WM12345678",
    "vendor": "WASTE_MANAGEMENT_LEWISVILLE",
    "date": "2024-10-17",
    "material": "CLASS_2_CONTAMINATED",
    "source": "PIER_EX",
    "destination": "WASTE_MANAGEMENT_LEWISVILLE",
    "manifest_number": "WM-MAN-2024-001234",
    "quantity": 18.5,
    "units": "TONS"
  }
}
```

OUTPUT:
- Directory: tests/fixtures/
- Files:
  - wm_lewisville_001.pdf through wm_lewisville_005.pdf
  - ldi_yard_001.pdf through ldi_yard_003.pdf
  - heidelberg_001.pdf through heidelberg_003.pdf
  - ground_truth.json (all fixtures)

Generate mock PDFs using PIL/reportlab with text overlay that matches expected extraction patterns.
```

**When to use this template:**
- ✅ Test data generation following pattern
- ✅ Mock/fixture creation
- ✅ Repetitive structure (copy 10+ times)
- ✅ Clear input/output specification

---

## 🔄 Template 6: Multi-Model Task (Break into Phases)

### **Example: Issue #23 - Vendor Logo Detection**

```markdown
PHASE 1: Architecture Design (Claude 4.5)
------------------------------------------
TASK: Design Vendor Logo Detection System (Issue #23 - Part 1)
MODEL: Claude Sonnet 4.5

Design the architecture for vendor logo detection using template matching.

REQUIREMENTS:
- Use OpenCV for template matching
- Support multiple vendor logos (WM Lewisville, LDI Yard, Post Oak, Heidelberg, etc.)
- Return confidence score (0.0 to 1.0)
- Configurable threshold (default: 0.85)
- Handle logo variations (size, rotation, quality)

DESIGN DECISIONS NEEDED:
1. Where to store logo templates? (config/logos/)
2. How to handle multi-scale detection?
3. What confidence threshold for each vendor?
4. Fallback strategy if logo not detected?
5. How to integrate with VendorExtractor?

OUTPUT:
Design document with:
- Architecture diagram
- Class structure
- Configuration format
- Integration approach
```

**[REVIEW PHASE 1 OUTPUT BEFORE PROCEEDING]**

```markdown
PHASE 2: Implementation (SWE-1.5)
----------------------------------
TASK: Implement Logo Detection Boilerplate (Issue #23 - Part 2)
MODEL: SWE-1.5

Using the architecture from Phase 1, implement the logo detection class.

INPUT: Architecture from Phase 1 (class structure, methods)

GENERATE:
src/truck_tickets/extractors/logo_detector.py

```python
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

class LogoDetector:
    def __init__(self, logo_dir: str, threshold: float = 0.85):
        """Initialize with logo templates directory."""
        self.logo_dir = Path(logo_dir)
        self.threshold = threshold
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, np.ndarray]:
        """Load all logo templates from directory."""
        # Implement loading logic
        pass

    def detect_vendor(self, page_image: np.ndarray) -> Optional[Tuple[str, float]]:
        """
        Detect vendor logo in page image.

        Returns:
            Tuple of (vendor_name, confidence) or None if no match
        """
        # Implement detection logic
        pass
```

Generate complete implementation with OpenCV template matching.
```

**[REVIEW PHASE 2 OUTPUT]**

```markdown
PHASE 3: Integration & Testing (Claude 4.5)
--------------------------------------------
TASK: Integrate Logo Detection & Add Tests (Issue #23 - Part 3)
MODEL: Claude Sonnet 4.5

Integrate LogoDetector into VendorExtractor with fallback logic.

INTEGRATION REQUIREMENTS:
1. Try logo detection first (highest confidence)
2. If confidence < threshold, try keyword matching
3. If both fail, route to review queue
4. Log confidence scores for monitoring

MODIFY:
src/truck_tickets/extractors/vendor_extractor.py

```python
class VendorExtractor:
    def __init__(self, logo_detector: LogoDetector, synonym_normalizer: SynonymNormalizer):
        self.logo_detector = logo_detector
        self.normalizer = synonym_normalizer

    def extract(self, page: PDFPage) -> VendorExtractionResult:
        """Extract vendor with logo detection + keyword fallback."""

        # Try logo detection first
        logo_result = self.logo_detector.detect_vendor(page.image)

        if logo_result and logo_result[1] >= self.threshold:
            # High confidence logo match
            return VendorExtractionResult(
                vendor=logo_result[0],
                confidence=logo_result[1],
                method='logo_detection'
            )

        # Fallback to keyword matching
        # ... (implement keyword logic)
```

TESTING:
Create integration tests:
1. Test WM Lewisville logo detection (high quality scan)
2. Test LDI Yard logo detection (medium quality)
3. Test fallback to keywords when logo unclear
4. Test review queue routing when both fail
5. Measure accuracy on 84 sample files

Include pytest tests in tests/test_vendor_extractor.py
```

**When to use multi-phase approach:**
- ✅ Task involves both design and implementation
- ✅ Boilerplate can be separated from logic
- ✅ Integration requires reasoning about edge cases
- ✅ You want to review design before investing in implementation

---

## 📝 Quick Reference: When to Use Each Template

| Template | Model | Task Type | Examples |
|----------|-------|-----------|----------|
| Template 1 | Claude 4.5 | Critical business logic | Duplicate detection, manifest validation, review routing |
| Template 2 | SWE-1.5 | Mechanical generation | ORM models, seed scripts, config loaders |
| Template 3 | Claude 4.5 | Complex orchestration | Main processor, integration layers |
| Template 4 | Claude 4.5 | Report generation | Excel exports, SQL pivots |
| Template 5 | SWE-1.5 | Test/mock generation | Fixtures, sample data |
| Template 6 | Both | Hybrid tasks | Logo detection, complex features |

---

## ✅ Checklist: Before Starting a Task

1. [ ] Identified GitHub issue number
2. [ ] Checked model assignment in CSV
3. [ ] Selected appropriate template
4. [ ] Filled in all CONTEXT and REQUIREMENTS
5. [ ] Specified exact file paths for OUTPUT
6. [ ] Listed ACCEPTANCE CRITERIA
7. [ ] Ready to paste into Windsurf

---

## 🎯 Pro Tips

**For Claude 4.5 tasks:**
- ✅ Include "CRITICAL" and "MUST" keywords for important requirements
- ✅ Reference spec sections explicitly
- ✅ Ask for edge case handling
- ✅ Request unit tests alongside implementation

**For SWE-1.5 tasks:**
- ✅ Provide clear input/output examples
- ✅ Show code structure/pattern to follow
- ✅ Keep scope narrow and mechanical
- ✅ Review output carefully (verify against spec)

**For multi-phase tasks:**
- ✅ Always review Phase 1 output before proceeding
- ✅ Use Claude for design, SWE-1.5 for boilerplate
- ✅ Return to Claude for integration and testing

---

**These templates ensure consistent, high-quality task execution with optimal model usage. Update templates as you learn which prompting patterns work best.**
