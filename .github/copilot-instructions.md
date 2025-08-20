# GitHub Copilot Instructions

This repository contains an OCR pipeline for extracting ticket data from PDFs and images.

When using GitHub Copilot in this project, keep the following in mind:

- Code lives under `src/` and tests under `tests/`.
- Target Python 3.10+ and include type hints and docstrings.
- Format code with `black` and lint with `ruff`.
- Use `loguru` for logging rather than the standard library's `logging` module.
- Write accompanying tests with `pytest` for new functionality.

## Working with Amazon Q

- To route an issue to Amazon Q, add the `amazon-q` label.
- You can also comment `/q dev` on the issue to trigger Q to implement a fix or feature.
- Q will respond with a pull request linked to the issue.

These guidelines help keep contributions consistent and maintainable.
