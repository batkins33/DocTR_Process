# Changelog

All notable changes to this project will be documented in this file.

## [2025-10-22] [Copilot] - Documentation Review & Accuracy Update

### Changed
- Fixed placeholder `USERNAME` → `batkins33` in README.md CI badge
- Updated repository URLs throughout documentation
- Completely rewrote `docs/DEVELOPER_GUIDE.md` to reflect current architecture
  - Updated module structure documentation (pipeline_v2, logging_setup, post_ocr_corrections)
  - Added comprehensive testing section with pytest examples
  - Documented angle_predictor fallback mechanism
  - Added development workflow and code style guidelines
- Completely rewrote `docs/USER_GUIDE.md` with current CLI interface
  - Updated all commands to use `doctr-process` and `doctr-gui` entry points
  - Documented post-OCR corrections and fuzzy matching features
  - Added troubleshooting, best practices, and FAQ sections
- Improved installation instructions with both pip and editable install options

### Added
- Missing dependencies to `pyproject.toml`:
  - `python-doctr[torch]` (core OCR library)
  - `easyocr` (alternative OCR engine)
  - `requests` (HTTP library for SharePoint)
- Created `docs/dev_log/` directory structure for session tracking
- Comprehensive troubleshooting sections in USER_GUIDE
- Best practices and performance optimization documentation

### Fixed
- Dependency mismatch between `pyproject.toml` and `requirements.txt`
- Outdated module references in technical documentation
- Broken installation instructions
- Missing documentation for post-OCR corrections feature

### Impact
- New developers can successfully install and onboard using accurate documentation
- Users can follow current CLI commands instead of outdated interfaces
- Documentation serves as reliable reference matching actual codebase
- Reduced friction for contributors with clear guidelines

---

## Unreleased

- Initial cleanup and repository restructuring.
- Moved configuration files to `configs/` and sanitized defaults.
- Consolidated documentation under `docs/` and expanded `README`.
- Split development requirements into `requirements-dev.txt`.
- Removed legacy artifacts and patch files.
