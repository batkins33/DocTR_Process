## GitHub Copilot Instructions

This repository contains an OCR pipeline for extracting ticket data from PDFs and images (package: `doctr_process`).

Keep suggestions focused, small, and verifiable. Below are precise, repo-specific rules and pointers an automated coding agent should follow.

## Quick facts

- Location: source under `src/doctr_process/`, tests under `tests/`, package metadata in `pyproject.toml`.
- Python: target 3.10+ (see `pyproject.toml`). Use type hints and docstrings for public APIs.
- Formatting & linting: `black` (line-length 88) and `ruff` (configured in `pyproject.toml`). Do not reformat unrelated files in diffs.
- Test runner: `pytest` (configured options in `pyproject.toml`). The project includes `run_tests.py` illustrating the common checks run in CI.

## Important files and where to look

- `src/doctr_process/main.py` — CLI parsing and headless vs GUI behavior. Headless runs create a temporary YAML config and call `pipeline_v2.run_refactored_pipeline`.
- `src/doctr_process/pipeline_v2.py` / `src/doctr_process/pipeline.py` — core processing pipelines. Prefer `pipeline_v2` if present for refactored logic.
- `src/doctr_process/logging_setup.py` — centralized logging, run_id handling, queue-based sinks, and validations (e.g., path traversal checks). Use this for logging changes rather than altering global config.
- `src/doctr_process/post_ocr_corrections.py` — post-OCR correction logic and JSONL memory format. Tests often rely on JSONL structure; keep it stable.
- `src/doctr_process/configs/` — packaged YAML/CSV configuration data (treat as data, not code).
- `run_tests.py` — small helper that runs `ruff` checks and a subset of pytest files; useful to mirror CI checks locally.

## Conventions and safety rules discovered in the codebase

- Path validation: code validates input paths and `log_dir` to prevent absolute paths or `..`. Follow the same checks when adding CLI options or config parsing.
- Logging: the project uses a queue-based logging listener and a GUI sink (`set_gui_log_widget`). Avoid changing handler semantics without updating `logging_setup.py` and tests.
- Persistent formats: corrections memory is JSONL (one JSON object per line). Prefer appending and preserving existing fields (e.g., `field`, `wrong`, `right`, `context`, `ts`).
- Third-party noise: the logging setup explicitly reduces verbosity for `PIL`, `urllib3`, `fitz`, `botocore`, `PaddleOCR`, `pdfminer`. Avoid global changes to these in PRs.

## How to make changes (agent checklist)

1. Run quick static checks: format with `black` and lint with `ruff` using the project's settings.
2. Add focused unit tests under `tests/` (name `test_*.py`) that cover the new behavior. Prefer mocking for heavy external deps (Tesseract, Poppler, SharePoint).
3. When changing CLI behavior, add a test that exercises `main` in headless mode or calls `pipeline_v2` with a temporary YAML config (mirrors `main.py` pattern).
4. Ensure logging uses `logging.getLogger(__name__)` and doesn't reconfigure the global logger; use `setup_logging` to initialize during runs.
5. Do not modify packaged configuration files in `src/doctr_process/configs/` without example inputs/outputs and a test demonstrating the change.

## Minimal example patterns (copyable)

- Logging pattern:

	logger = logging.getLogger(__name__)
	logger.info("Startup: python=%s, platform=%s, log_level=%s", platform.python_version(), platform.platform(), level)

- Headless pipeline invocation (use temporary YAML):

	import tempfile, yaml
	with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
			yaml.safe_dump(config_data, f)
			temp_config_path = f.name
	from doctr_process.pipeline_v2 import run_refactored_pipeline
	run_refactored_pipeline(temp_config_path)

## Testing expectations

- Add fast unit tests for functional changes. Integration tests that touch OCR binaries should be either skipped in CI or mocked.
- Use `run_tests.py` as a model for local checks: it runs `ruff` checks and a curated set of pytest files, then a smoke test.

## Merge policy for agent-generated PRs

- PRs must pass linting and the test checks run by `run_tests.py` (or CI). Keep changes focused and small.
- Don't introduce large third-party dependencies without a clear reason and an update to `pyproject.toml`.
- Preserve existing public data formats (JSONL corrections, packaged YAML/CSV) unless the PR includes migration code and tests.

## When to ask questions

- If the change requires credentials, private endpoints, or large sample files, ask for test fixtures or mocked behavior rather than inventing secrets.
- If a refactor touches GUI and headless flows simultaneously, ask which flow is authoritative for the change.

If anything here is unclear or you want more detailed examples for a particular module, tell me which area to expand and I'll update this file.
