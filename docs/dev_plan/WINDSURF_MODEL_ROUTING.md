# Windsurf Model Selection Guide
## Project 24-105: Truck Ticket Processing System

**Purpose:** Route development tasks to optimal AI models based on task complexity and type.

---

## 🎯 Model Selection Decision Tree

### **Use Claude Sonnet 4.5 (Default) When:**

#### Category A: Critical Business Logic ⚠️
- ✅ Duplicate detection (120-day window, vendor matching)
- ✅ Manifest validation (100% recall - REGULATORY)
- ✅ Review queue routing decisions
- ✅ Field extraction precedence logic (filename → folder → OCR → UI override)
- ✅ Material classification rules
- ✅ Vendor detection with confidence scoring
- ✅ Database transaction coordination
- ✅ Error handling strategy

#### Category B: Cross-Module Orchestration 🔗
- ✅ Main TicketProcessor pipeline (PDF → OCR → Extract → Normalize → DB)
- ✅ Integration between extractors, normalizer, and database
- ✅ ProcessingRun ledger coordination
- ✅ Batch processing with rollback logic

#### Category C: Complex Queries & Exports 📊
- ✅ Excel export generation (5 sheets with pivots)
- ✅ Job Week/Month calculation logic
- ✅ SQL query optimization for performance
- ✅ Invoice matching report generation
- ✅ Manifest log compliance formatting

#### Category D: Testing Strategy & Design 🧪
- ✅ Integration test design
- ✅ Gold standard test dataset design
- ✅ Acceptance criteria definition
- ✅ Regression test framework architecture

**GitHub Issues Using Claude 4.5:**
- #4: Duplicate detection logic
- #5: Manifest validation (100% recall)
- #7: Main TicketProcessor orchestration
- #8: Review queue routing
- #10: Field extraction precedence
- #12: Excel exporter (5 sheets)
- #14: Job Week/Month calculations
- #16: Integration test framework
- #20: Batch processing with error handling
- #25: SQL query optimization

---

### **Use SWE-1.5 (or Fast Model) When:**

#### Category A: Schema & ORM Generation 🏗️
- ✅ SQLAlchemy model generation from SQL schema
- ✅ Pydantic model generation for validation
- ✅ Database migration scripts (Alembic)
- ✅ Index creation SQL

#### Category B: Seed Data & Boilerplate 📦
- ✅ Seed data scripts (13 sources, 3 destinations, vendors)
- ✅ Reference data insertion scripts
- ✅ Enum/constant generation
- ✅ Configuration file templates

#### Category C: Deterministic Parsing 🔍
- ✅ Filename parser (structured format regex)
- ✅ Date format parser templates
- ✅ Regex pattern generation for ticket numbers
- ✅ YAML config loaders

#### Category D: Test Fixtures & Mocks 🎭
- ✅ Mock data generation
- ✅ Test fixture creation (once structure defined)
- ✅ Sample PDF metadata generation

#### Category E: Documentation Sync 📝
- ✅ README updates from code
- ✅ API documentation generation
- ✅ Docstring generation
- ✅ Markdown table formatting

**GitHub Issues Using SWE-1.5:**
- #2: Generate SQLAlchemy ORM models
- #3: Create seed data scripts
- #6: Build filename parser
- #9: Create YAML config loaders
- #11: Generate test fixtures
- #13: Docstring generation
- #15: README sync
- #22: Mock data generation
- #27: API documentation
- #30: Migration scripts

---

## 🔄 **Task Breakdown: When to Switch Models**

### **Example: Issue #7 - Main TicketProcessor**

**Phase 1: Architecture Design (Claude 4.5)**
```python
# Claude designs the high-level flow:
class TicketProcessor:
    """
    Orchestrates the complete ticket processing pipeline.
    
    Flow:
    1. Load PDF → Extract pages
    2. Run OCR on each page
    3. Detect vendor → Apply vendor template
    4. Extract fields with precedence logic
    5. Normalize using SynonymNormalizer
    6. Check for duplicates (120-day window)
    7. Insert to DB or route to review queue
    8. Log to ProcessingRun ledger
    """
    
    def process_ticket(self, pdf_path: str) -> ProcessingResult:
        # Claude writes the LOGIC
        pass
```

**Phase 2: Boilerplate Implementation (SWE-1.5)**
```python
# SWE-1.5 generates the logging boilerplate:
def _log_processing_start(self, run_id: str, file_count: int):
    logger.info(f"Starting processing run {run_id}")
    logger.info(f"Processing {file_count} files")
    # ... 20 more lines of logging setup

def _log_processing_complete(self, run_id: str, stats: Dict):
    logger.info(f"Completed processing run {run_id}")
    logger.info(f"Total tickets: {stats['total']}")
    # ... 20 more lines of logging
```

**Phase 3: Integration & Validation (Claude 4.5)**
```python
# Claude handles the critical integration:
def _handle_extraction_failure(self, page: Page, error: Exception):
    """
    CRITICAL: All extraction failures must be routed to review queue.
    Manifest failures are CRITICAL severity.
    """
    if self._is_contaminated_material(page):
        severity = ReviewSeverity.CRITICAL
        reason = "MISSING_MANIFEST"
    else:
        severity = ReviewSeverity.WARNING
        reason = "EXTRACTION_FAILED"
    
    self.review_queue.add_entry(
        page_id=page.id,
        severity=severity,
        reason=reason
    )
```

---

## 📋 **Windsurf Task Instructions**

### **For Each GitHub Issue:**

1. **Check Model Assignment**
   ```bash
   # Look at issue labels or reference this guide
   Issue #4: Duplicate detection → Use Claude 4.5
   Issue #3: Seed data scripts → Use SWE-1.5
   ```

2. **Use Task-Specific Prompts**

   **For Claude 4.5 tasks:**
   ```
   "I'm working on Issue #4: Duplicate detection logic.
   
   Requirements from spec v1.1:
   - Check (ticket_number, vendor_id) within 120-day rolling window
   - If duplicate found, mark duplicate_of = original_id
   - Route to review queue with comparison data
   - CRITICAL: Must handle edge cases (same ticket, different dates)
   
   Please implement TicketRepository.check_duplicate() with full error handling."
   ```

   **For SWE-1.5 tasks:**
   ```
   "I'm working on Issue #3: Seed data scripts.
   
   Generate Python scripts to insert reference data:
   - 13 source locations (see SOURCES table in spec)
   - 3 destination locations
   - 15+ vendor records
   
   Use SQLAlchemy bulk_insert_mappings for performance.
   Output: scripts/seed_reference_data.py"
   ```

3. **Manual Model Switch Points**
   
   When a task requires **both** models, break it into subtasks:
   
   **Issue #12: Excel Exporter**
   ```
   Subtask 12.1 (SWE-1.5):
   "Generate the Excel file structure with 5 empty sheets:
   - All Daily, Class2_Daily, Non Contaminated, Spoils, Import
   Use openpyxl boilerplate for sheet creation."
   
   [Review SWE-1.5 output]
   
   Subtask 12.2 (Claude 4.5):
   "Now implement the complex SQL queries for each sheet:
   - All Daily: Pivot by date with Job Week/Month calculations
   - Class2_Daily: Pivot by source location (8 columns)
   - Spoils: Group by spoils staging areas (5 sources)
   Ensure Job Week format matches spec: 'Week 16 - (End 10/20/24)'"
   ```

---

## 🎯 **Priority Tasks with Model Assignments**

### **Week 2 Critical Path (Next 40 hours):**

| Priority | Task | Hours | Model | Reasoning |
|----------|------|-------|-------|-----------|
| 🔴 P0 | #4: Duplicate detection logic | 3h | Claude 4.5 | Critical business rule |
| 🔴 P0 | #5: Manifest validation | 3h | Claude 4.5 | 100% recall (regulatory) |
| 🔴 P0 | #7: Main TicketProcessor | 8h | Claude 4.5 | Orchestration complexity |
| 🔴 P0 | #8: Review queue routing | 3h | Claude 4.5 | Compliance logic |
| 🟡 P1 | #2: ORM model generation | 2h | SWE-1.5 | Mechanical transform |
| 🟡 P1 | #3: Seed data scripts | 2h | SWE-1.5 | Boilerplate generation |
| 🟡 P1 | #6: Filename parser | 2h | SWE-1.5 | Regex patterns |
| 🔴 P0 | #12: Excel exporter | 8h | Claude 4.5 | Complex pivots |
| 🟡 P1 | #14: Job Week/Month calc | 3h | Claude 4.5 | Business logic |
| 🟢 P2 | #11: Test fixtures | 3h | SWE-1.5 | Mock data generation |

**Total: ~37 hours**

---

## 🚨 **Critical Decision Points**

### **When in Doubt, Default to Claude 4.5**

Use Claude when:
- ✅ Task involves "CRITICAL" or "compliance" keywords
- ✅ Spec section has ⚠️ warnings or regulatory notes
- ✅ Multiple modules must coordinate
- ✅ Error handling requires domain understanding
- ✅ First time implementing a pattern (design phase)

Use SWE-1.5 when:
- ✅ Task is "Generate X from Y" (deterministic transform)
- ✅ Similar code exists elsewhere (copy-paste-modify)
- ✅ Output is >80% boilerplate
- ✅ No cross-module dependencies

### **Red Flags for SWE-1.5:**
- ❌ Spec says "MUST", "REQUIRED", "CRITICAL"
- ❌ Compliance or regulatory requirements mentioned
- ❌ "100%" accuracy/recall targets
- ❌ Multi-step precedence logic
- ❌ Needs context from multiple spec sections

---

## 📊 **Model Usage Statistics (Estimated)**

For your 31 GitHub issues:

| Model | Issues | Hours | % of Work |
|-------|--------|-------|-----------|
| Claude 4.5 | 18 issues | ~110h | ~70% |
| SWE-1.5 | 13 issues | ~50h | ~30% |
| **Total** | **31 issues** | **~160h** | **100%** |

**Why Claude dominates:**
- Your spec is 120+ pages of nuanced requirements
- Compliance/regulatory constraints throughout
- Multi-system integration (OCR, DB, Excel, compliance)
- First-time implementation (not maintenance)

**SWE-1.5 saves time on:**
- Boilerplate that follows established patterns
- Seed data and fixtures
- Documentation sync
- Repetitive CRUD operations

---

## 🔧 **Windsurf Configuration Suggestions**

### **Option A: Manual Model Selection**
```bash
# In each task, explicitly state:
windsurf task start #4 --model claude-4.5
windsurf task start #3 --model swe-1.5
```

### **Option B: Config File (if Windsurf supports)**
```yaml
# .windsurf/config.yml
model_routing:
  default: claude-sonnet-4.5
  
  task_patterns:
    - pattern: "ORM|schema|boilerplate|seed"
      model: swe-1.5
    
    - pattern: "duplicate|manifest|compliance|validation|CRITICAL"
      model: claude-sonnet-4.5
    
    - pattern: "test fixture|mock data|docstring"
      model: swe-1.5
```

### **Option C: Issue Label-Based (Recommended)**
```bash
# GitHub issue labels:
model:claude-4.5  → Use Claude for reasoning
model:swe-1.5     → Use SWE-1.5 for speed

# Windsurf reads label and routes automatically
```

---

## ✅ **Quick Reference Card**

**Ask yourself:**
1. Does this involve compliance/regulatory? → **Claude 4.5**
2. Does this coordinate multiple modules? → **Claude 4.5**
3. Is this a deterministic transform (A → B)? → **SWE-1.5**
4. Does the spec say "MUST" or "CRITICAL"? → **Claude 4.5**
5. Is this boilerplate or seed data? → **SWE-1.5**
6. Will this be copy-pasted 10+ times? → **SWE-1.5**
7. Does it require domain reasoning? → **Claude 4.5**

**When stuck: Default to Claude 4.5**

---

## 📝 **Usage Example**

```bash
# Starting Issue #4: Duplicate detection
$ windsurf task start 4

# Windsurf checks this guide → Sees "duplicate" keyword
# Routes to: Claude 4.5 ✓

Prompt:
"I'm implementing Issue #4: Duplicate detection logic.
From spec v1.1, requirements are:
- Check (ticket_number, vendor_id) within 120-day rolling window
- If duplicate found: mark duplicate_of, set review_required=True
- Route to review queue with comparison data

Please implement TicketRepository.check_duplicate() with:
1. SQL query for 120-day window
2. Edge case handling (same ticket on different dates)
3. Review queue integration
4. Unit tests"
```

```bash
# Starting Issue #3: Seed data scripts
$ windsurf task start 3

# Windsurf checks this guide → Sees "seed data" keyword
# Routes to: SWE-1.5 ✓

Prompt:
"Generate seed data scripts for reference tables.
Insert:
- 13 sources (PODIUM, ZONE_E_GARAGE, ..., BECK_SPOILS, etc.)
- 3 destinations (WASTE_MANAGEMENT_LEWISVILLE, LDI_YARD, POST_OAK_PIT)
- 15 vendors (from spec)

Use SQLAlchemy bulk_insert_mappings.
Output: scripts/seed_reference_data.py"
```

---

**This guide ensures optimal model usage while maintaining context and quality. Update as you learn which tasks work best with each model.**
