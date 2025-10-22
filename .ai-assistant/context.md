# AI Assistant Context - DocTR Process

**Last Updated:** 2025-10-22  
**Current Branch:** feature/local-sync  
**Assistant:** GitHub Copilot

---

## 📋 Project Overview

**Name:** DocTR Process  
**Type:** OCR Pipeline for Truck Ticket Data Extraction  
**Language:** Python 3.10+  
**Repository:** https://github.com/batkins33/DocTR_Process

**Purpose:**  
Extract structured data (vendor, ticket numbers, manifest numbers, dates, amounts) from scanned truck ticket PDFs using OCR with intelligent post-processing corrections.

---

## 🏗️ Current Architecture

### Core Modules
```
src/doctr_process/
├── main.py              # CLI entry point with argparse
├── gui.py               # Tkinter GUI application
├── pipeline.py          # Legacy pipeline (still functional)
├── pipeline_v2.py       # Refactored pipeline (PREFERRED)
├── logging_setup.py     # Queue-based logging with GUI support
├── post_ocr_corrections.py  # Intelligent correction engine
├── path_utils.py        # Security validation for paths
├── resources.py         # Resource management
├── configs/             # Packaged YAML/CSV configs
│   ├── config.yaml
│   ├── extraction_rules.yaml
│   └── ocr_keywords.csv
├── ocr/                 # OCR processing (DocTR, Tesseract, EasyOCR)
├── extract/             # Field extraction logic
├── parse/               # Data parsing utilities
├── output/              # CSV/Excel output handlers
├── processor/           # File processing utilities
├── handlers/            # Various processing handlers
├── utils/               # General utilities
└── assets/              # Branding and resources
```

### Key Technologies
- **OCR:** python-doctr[torch], pytesseract, easyocr
- **PDF Processing:** PyMuPDF (fitz), pdf2image, pdfplumber
- **Image Processing:** OpenCV, Pillow
- **Data:** pandas, pyyaml, openpyxl
- **Logging:** loguru (queue-based, thread-safe)
- **Integration:** office365-rest-python-client (SharePoint)

---

## 🎯 Current State

### Recent Work (2025-10-22)
✅ **Documentation Review & Update** - Level 3 task completed
- Fixed all placeholder values and broken references
- Synchronized dependencies across pyproject.toml and requirements.txt
- Modernized DEVELOPER_GUIDE and USER_GUIDE
- Created dev_log structure

### Active Features
- ✅ CLI and GUI interfaces (`doctr-process`, `doctr-gui`)
- ✅ Multi-engine OCR (DocTR, Tesseract, EasyOCR)
- ✅ Orientation detection with fallback (angle_predictor → Tesseract OSD)
- ✅ Post-OCR corrections with fuzzy matching and learning
- ✅ Vendor-specific field extraction rules
- ✅ Parallel batch processing
- ✅ SharePoint integration
- ✅ Comprehensive logging and error tracking

### Known Issues / TODOs
- [ ] Add architecture diagrams to DEVELOPER_GUIDE
- [ ] Document utils/ directory OCR scripts (ocr_embed_pdf.py, batch files)
- [ ] Add integration tests documentation
- [ ] Consider video tutorials for USER_GUIDE
- [ ] Create TESTING.md with comprehensive test strategy

---

## 🔧 Development Workflow

### Entry Points
```bash
# CLI (headless)
doctr-process --input samples --output outputs --no-gui

# GUI
doctr-gui

# Python module
python -m doctr_process --help
```

### Testing
```bash
# Run all tests
pytest

# Smoke tests only
pytest tests/test_smoke.py

# CI-like checks
python run_tests.py

# With coverage
pytest --cov=src/doctr_process
```

### Code Style
- **Formatter:** black (line-length 88)
- **Linter:** ruff (configured in pyproject.toml)
- **Type hints:** Required for public APIs
- **Docstrings:** Required for public functions/classes

---

## 📝 Documentation Standards

Following **AI Assistant System Prompt v2.0**:

### Documentation Levels
- **Level 1:** Quick fixes (< 30 lines) - inline comments only
- **Level 2:** Standard features - module headers + context + next steps
- **Level 3:** Major refactors - full ceremony + changelog + human summary
- **Level 4:** Cross-project - Level 3 + comprehensive examples + migration guides

### Dev Log Location
All session logs stored in: `docs/dev_log/YYYY-MM-DD.md`

### Changelog
Main changelog: `CHANGELOG.md` (Level 3+ changes only)

---

## 🚀 Active Priorities

### Immediate (This Week)
1. No active feature development (documentation phase complete)
2. Monitor for issues from documentation updates

### Short-term (This Month)
1. Add visual documentation (architecture diagrams, screenshots)
2. Document advanced utilities (utils/ directory)
3. Expand test documentation

### Long-term
1. Performance optimization for large batches
2. Enhanced SharePoint integration features
3. Web-based UI alternative to Tkinter

---

## 🔀 Context Switch Notes

**When returning after >3 days:**
1. Read `docs/dev_log/YYYY-MM-DD.md` for last session
2. Check TODOs in this file
3. Run smoke tests: `pytest tests/test_smoke.py`
4. Update this context file with current task

**Key Files to Review:**
- `docs/dev_log/2025-10-22.md` - Latest session
- `CHANGELOG.md` - Recent changes
- `.github/copilot-instructions.md` - Coding standards
- `pyproject.toml` - Dependencies and configuration

---

## 🔐 Environment Setup

### Required System Dependencies
- Tesseract OCR (with OSD support)
- Poppler utilities (for PDF rendering)

### Python Environment
```bash
# Create venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Editable install
pip install -e .
```

### Environment Variables (Optional)
```bash
SHAREPOINT_USERNAME=your.user@company.com
SHAREPOINT_PASSWORD=your_password
```

---

## 📊 Project Metrics

- **Python Version:** 3.10+
- **Test Coverage:** TBD (run `pytest --cov`)
- **Lines of Code:** ~10K+ (estimate)
- **Active Modules:** 20+
- **Test Files:** 25+ test suites

---

## 🤝 Collaboration Notes

**Primary Assistant:** GitHub Copilot (with Claude backend)  
**Documentation Protocol:** v2.0  
**Git Branch Strategy:** Feature branches → feature/local-sync → main  
**Commit Style:** Conventional commits with [Assistant] tags

---

**Next Review Date:** When returning to active development  
**Status:** 🟢 Documentation up-to-date, ready for development
