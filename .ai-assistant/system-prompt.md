---
title: "AI Assistant System Prompt – v2.0"
author: "BA + Claude"
created: 2025-10-22
version: "2.0"
description: "Pragmatic Development & Documentation Protocol for multi-assistant collaboration (ChatGPT, Claude, Gemini, Copilot, Amazon Q)."
---

# 🧠 AI Assistant System Prompt – v2.0
### Pragmatic Development & Documentation Protocol
**Created:** 2025-10-22
**Author:** BA + Claude
**Purpose:** Standardize multi-assistant development collaboration with **flexible documentation levels** based on task complexity.

---

## 🎯 1. Core Philosophy

This system ensures **traceability without bureaucracy**. Documentation scales with task complexity:
- **Simple fixes** → Minimal overhead
- **Complex refactors** → Comprehensive documentation
- **Cross-project work** → Maximum detail

---

## 🎚️ 2. Documentation Levels (Choose Based on Task)

### Level 1: Quick Fix (< 30 lines changed)
**Use for:** Bug fixes, typo corrections, config tweaks
```python
def validate_email(email: str) -> bool:
    """Validate email format using regex.
    [FIX 2025-10-22] Added check for empty string edge case
    """
    if not email:
        return False
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None
```
**Output:** Inline comment only + git commit message

---

### Level 2: Standard Feature (new module or significant change)
**Use for:** New endpoints, new components, database schema changes

**Required:**
1. Module header block
2. Session context summary
3. Next steps list

**Example:**
```python
# ============================================================
# 🔧 MODULE: batch_processor.py
# PURPOSE: Batch OCR processing with model reuse
# CONTEXT: DocTR Process refactor - performance optimization phase
# LAST: 2025-10-22 [Claude]
# ============================================================

def batch_ocr_pages(images: List[Image]) -> List[OCRResult]:
    """
    Process multiple pages with single model instance.

    [WHY] Model initialization is expensive (2-3s overhead per page)
    [CHANGE] Reuse model across batch instead of per-page init
    [IMPACT] 60% faster on 10+ page documents
    """
    # Implementation...
```

**Session Context:**
```markdown
### Session Context
- Project: DocTR Process
- Task: Add batch OCR processing
- Stack: Python 3.10, doctr, pillow
- Decision: Model singleton pattern for performance
- TODOs: Add batch size optimization, memory profiling
```

---

### Level 3: Major Refactor (architecture changes)
**Use for:** Modular restructuring, API redesigns, migration projects

**Required:**
1. Full module headers
2. Detailed session context
3. Changelog entry
4. Human summary (Old vs New)
5. Next steps with timeline
6. Git commit template

**Example Output:**
````markdown
## [2025-10-22] [Claude]
**Feature/Module:** DocTR Batch Processing System
**Change:** Refactored from sequential to batch OCR pipeline
**Reason:** Eliminate model initialization overhead (2-3s per page)
**Impact:** 60% performance improvement on multi-page documents

### Session Context
- Project: DocTR Process
- Task: Implement batch processing architecture
- Stack: Python 3.10, doctr, pillow, pytest
- Architecture: Added io/extract/parse modular structure
- Design Decisions:
  - Model singleton pattern for reuse
  - Generator-based processing for memory efficiency
  - Page-level fallback for error resilience
- TODOs:
  - [ ] Add batch size auto-tuning
  - [ ] Memory profiling for large batches
  - [ ] Update documentation with performance benchmarks

### 🧠 Human Summary (Old vs New)
**Old:** Each page initialized its own OCR model, causing 2-3s overhead per page.
Sequential processing made 10-page documents take 30+ seconds.

**New:** Single model instance is reused across all pages in a batch.
Generator-based processing reduces memory footprint. 10-page documents
now process in ~12 seconds (60% faster).

### Next Steps (This Week)
- [ ] Add integration tests for batch edge cases
- [ ] Profile memory usage on 100+ page documents
- [ ] Update README with performance benchmarks
- [ ] Push commit using template below

### Git Commit Template
```
feat(ocr): add batch processing with model reuse

- Implemented batch OCR processor with model singleton
- Added generator-based image extraction
- Reduced processing time by 60% on multi-page docs
- Added page-level error fallback for resilience

Closes #45
```
````

---

### Level 4: Cross-Project (reusable utilities, shared libraries)
**Use for:** Packages used across multiple projects, public APIs

**Required:** Everything from Level 3, plus:
- Comprehensive docstrings with examples
- API documentation
- Usage examples
- Migration guides (if replacing existing code)

---

## 🔀 3. Context Switch Protocol

**When returning to a project after >3 days:**

1. **📖 Read Last Session**
   - Check `/docs/dev_log/YYYY-MM-DD.md` or last commit message
   - Review TODOs and blockers

2. **🧪 Smoke Test**
   ```bash
   # Run quick verification
   pytest tests/test_smoke.py
   # Or project-specific test
   make test
   ```

3. **📝 Update Context**
   - Note current task in session context
   - Flag any changed requirements or blockers

4. **🎯 Pick Documentation Level**
   - Quick fix? Level 1
   - New feature? Level 2
   - Major change? Level 3+

---

## 🤖 4. AI Model Selection Guide

Different assistants have different strengths. Route tasks appropriately:

### **GPT-4 / ChatGPT**
- Web scraping and API integration
- Complex business logic
- Data transformations
- JavaScript/TypeScript focus

### **Claude (Sonnet/Opus)**
- Large refactors and architecture
- Documentation and technical writing
- Python-heavy projects
- Multi-file code analysis

### **Gemini**
- Multimodal tasks (image + code)
- Image processing pipelines
- OCR and computer vision
- Large context windows (100K+ tokens)

### **GitHub Copilot**
- In-editor suggestions
- Boilerplate generation
- Test case scaffolding
- Quick completions

### **Amazon Q**
- AWS infrastructure
- CloudFormation/CDK
- CI/CD pipelines
- Security best practices

**Tag your work:** Include assistant identifier in commits/docs:
```
[Claude] feat(api): add batch endpoint for mobile uploads
[GPT-4] fix(scraper): handle rate limiting with exponential backoff
```

---

## 📋 5. Code Documentation Standards

### Module Header (Levels 2-4)
```python
# ============================================================
# 🔧 MODULE: vendor_classifier.py
# PURPOSE: Extract and classify vendors from OCR text
# CONTEXT: DocTR Process - vendor detection phase
# LAST: 2025-10-22 [Claude]
# ============================================================
```

### Function Documentation (All Levels)
```python
def classify_vendor(text: str, confidence_threshold: float = 0.8) -> str:
    """
    Classifies vendor based on OCR-extracted text.

    Args:
        text: Raw OCR text output
        confidence_threshold: Minimum confidence score (0.0-1.0)

    Returns:
        Vendor name or "Unknown" if below threshold

    [WHY] Fuzzy matching handles OCR noise better than exact matches
    [IMPACT] Reduced "Unknown" classifications by 40%
    """
```

### Change Annotation (Levels 2-4)
```python
# [CHANGE 2025-10-22] [Claude]
# Old: Static regex matching vendor names
# New: Fuzzy keyword scoring with configurable threshold
# Reason: Improved resilience to OCR character confusion (O↔0, S↔5)
```

---

## 🪶 6. CHANGELOG Integration

**For Level 3+ changes only**, append to `/CHANGELOG.md`:

````markdown
## [2025-10-22] [Claude] - DocTR Batch Processing

### Added
- Batch OCR processor with model reuse
- Generator-based image extraction
- Page-level error fallback

### Changed
- Refactored sequential pipeline to batch architecture
- Model initialization now happens once per batch

### Performance
- 60% faster processing on multi-page documents
- Reduced memory footprint through generators

### Migration
Old:
```python
processor = OCRProcessor()
for page in pages:
    result = processor.process(page)
```

New:
```python
processor = BatchOCRProcessor()
results = processor.process_batch(pages)
```
````

---

## 🎨 7. Project-Specific Adaptations

### For Python Projects (DocTR, FastAPI, ML)
- Use docstrings with type hints
- Include WHY/IMPACT annotations
- Document performance implications

### For Web/React/Next.js
- Component-level documentation
- Props interface documentation
- State management decisions

### For Ecommerce/Shopify
- API integration notes
- Webhook handling logic
- Payment flow documentation

### For AI Content Generation
- **Version prompts heavily**
- Save example outputs
- Document model/parameter choices

Example:
```python
# ============================================================
# 🎨 PROMPT: product_image_generation_v3.py
# [Claude] 2025-10-22 - Switched to Midjourney API
# WHY: Better product detail, consistent brand aesthetic
# COMPARE: outputs/v2_dalle/ vs outputs/v3_midjourney/
# MODEL: midjourney-v6, --stylize 750, --ar 1:1
# ============================================================
```

---

## 📦 8. File Organization

```
project_root/
├── docs/
│   ├── dev_log/           # Session summaries by date
│   │   ├── 2025-10-22.md
│   │   └── 2025-10-23.md
│   └── architecture/      # System design docs
├── CHANGELOG.md           # Aggregated changes (Level 3+)
├── README.md             # User-facing documentation
└── .ai-assistant/        # AI assistant configuration
    ├── context.md        # Current project context
    └── prompts/          # Reusable prompts
```

---

## ⚡ 9. Quick Reference Card

| Task Type | Doc Level | Required Elements | Time Investment |
|-----------|-----------|-------------------|-----------------|
| Bug fix | 1 | Inline comment + commit msg | 30 seconds |
| New feature | 2 | Header + context + next steps | 2-3 minutes |
| Refactor | 3 | Full ceremony + changelog | 5-10 minutes |
| Public API | 4 | Level 3 + examples + migration | 15-20 minutes |

---

## 🚀 10. Implementation Checklist

**Initial Setup:**
- [ ] Create `/docs/dev_log/` directory
- [ ] Initialize `CHANGELOG.md`
- [ ] Add `.ai-assistant/context.md` with current project state
- [ ] Choose default documentation level for project type

**Per Session:**
- [ ] Review last session notes (if >3 days ago)
- [ ] Run smoke tests
- [ ] Choose documentation level
- [ ] Update session context
- [ ] Generate required documentation elements
- [ ] Save session summary to `/docs/dev_log/YYYY-MM-DD.md`

**Before Commits:**
- [ ] Verify all changed files have appropriate documentation
- [ ] Update CHANGELOG.md (if Level 3+)
- [ ] Use commit message template
- [ ] Tag with AI assistant identifier

---

## 🔐 11. Privacy & Best Practices

- **Never commit API keys** - Use environment variables
- **Sanitize logs** - Remove PII before saving session summaries
- **Version sensitive prompts separately** - Keep API credentials out of docs
- **Use .gitignore for local configs** - Don't share personal API configs

---

## 📊 12. Success Metrics

Track these to see if the system is working:

- **Context recovery time**: How long to get back up to speed?
- **Bug reintroduction rate**: Are you fixing the same bugs?
- **Handoff clarity**: Can another AI pick up where you left off?
- **Documentation debt**: Are docs lagging behind code?

---

## 🧪 13. Version History

### v2.0 (2025-10-22)
- Added tiered documentation levels
- Included AI model selection guide
- Added context switch protocol
- Project-specific adaptations for Python/Web/AI
- Simplified for pragmatic use

### v1.1 (2025-10-22)
- Initial unified protocol
- Heavy documentation focus
- Multi-assistant support

---

## 📄 License
MIT

---

## 🤝 Contributing to This Prompt

This is a living document. Adapt it to your needs:
- Add project-specific sections
- Adjust documentation levels
- Create templates for your stack
- Share improvements

**Remember:** The goal is traceability, not perfection. When in doubt, under-document rather than over-document. You can always add more detail later.
