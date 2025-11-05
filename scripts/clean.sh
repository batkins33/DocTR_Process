#!/usr/bin/env bash
set -euo pipefail
rm -rf artifacts scratch reports .pytest_cache .mypy_cache .ruff_cache htmlcov || true
