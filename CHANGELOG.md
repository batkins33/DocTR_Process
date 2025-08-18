# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Simplified CLI entry point for better packaging support
- Dockerfile with Tesseract and Poppler dependencies for containerized deployments  
- Enhanced package metadata with proper classifiers and keywords
- Console script entry point for `pipx` installation support

### Changed
- Improved import structure to handle optional dependencies (tkinter)
- Enhanced pyproject.toml with comprehensive package metadata

### Fixed
- CLI console script now properly points to working entry point
- Import issues with optional GUI dependencies

## [0.1.0] - 2024-08-18

### Added
- Initial cleanup and repository restructuring
- Moved configuration files to `configs/` and sanitized defaults
- Consolidated documentation under `docs/` and expanded `README`
- Split development requirements into `requirements-dev.txt`
- Removed legacy artifacts and patch files
- Basic package structure with setuptools configuration
