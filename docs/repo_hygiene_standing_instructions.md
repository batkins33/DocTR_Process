# 🧹 Repo Hygiene & Standing Instructions

Keep development fast and your repo lean. This document defines **where Dev Assistants may write files**, what gets **committed vs. ignored**, and how to **clean, quarantine, and archive** clutter before a production release.

---

## 0) TL;DR Rules (pin these in your IDE prompt)
- **All transient outputs** (logs, temp data, experiments, test exports) go to **`/scratch/`** or **`/artifacts/`**.
- **Only commit**: source code, configs, tiny redacted samples, docs, tests. **Never commit** large binaries.
- **Experimental notebooks/scripts** live in **`/notebooks/`** and are optional to commit (prefer `.ipynb_checkpoints` ignored).
- **Data policy**: keep real data out of git. Use `/data/` (ignored) and keep public samples in `/samples/`.
- Run **`make clean`** (or `scripts/clean.*`) daily; **`make archive-sandbox`** before releases.
- Pre-commit hooks must pass before merging. Large files (>50MB) are blocked.

---

## 1) Recommended Repo Layout
```
repo/
├─ src/                    # application code (committed)
├─ tests/                  # unit/integration tests (committed)
├─ docs/                   # markdown, ADRs, SOPs (committed)
├─ configs/                # yaml/toml/json app configs (committed)
├─ samples/                # tiny redacted inputs for demos (committed)
├─ scripts/                # helper scripts (committed)
├─ notebooks/              # exploration; checkpoints ignored (optional)
├─ scratch/                # dev scratchpad outputs (ignored)
├─ artifacts/              # build/results/logs/exports (ignored)
├─ data/                   # real/local data sources (ignored)
├─ reports/                # generated reports (ignored)
└─ _archive/               # quarantined zips/tars (committed or ignored; see policy)
```

---

## 2) `.gitignore` (drop in repo root)
```gitignore
# --- python basics ---
__pycache__/
*.py[cod]
*.so
.venv/
.env
.env.*

# --- test & tooling caches ---
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage*
htmlcov/

# --- IDE/editor ---
.vscode/
.idea/
*.code-workspace
.DS_Store
Thumbs.db

# --- project clutter policy ---
# Real data lives outside of git
/data/**
!/data/README.md

# Keep small samples in git; everything else ignored
/samples/**
!samples/**
# if you want to enforce size, use pre-commit hook below

# Generated outputs
/artifacts/**
/scratch/**
/reports/**

# Notebooks
**/.ipynb_checkpoints/

# Builds / packaging
build/
dist/
*.egg-info/

# Logs
*.log
logs/**

# OS / misc
*.tmp
*.swp
*.bak
```

> **Tip:** If you want `_archive/` versioned, remove it from ignore. If you prefer to keep it out of git, add: `/_archive/**`.

---

## 3) `.gitattributes` (diff rules & line endings)
```gitattributes
* text=auto eol=lf

# Make large/texty files diff better
*.md diff
*.yml diff
*.yaml diff
*.json diff

# Treat vendor blobs as vendored
vendor/** linguist-vendored

# Notebooks: use textconv to avoid binary noise (optional; requires nbconvert)
*.ipynb filter=jupyternotebook
```

(Optional) Configure a `jupyternotebook` filter in `.gitconfig` if desired.

---

## 4) `.editorconfig` (consistent formatting)
```editorconfig
root = true

[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8
indent_style = space
indent_size = 4
trim_trailing_whitespace = true

[*.md]
trim_trailing_whitespace = false
```

---

## 5) `pre-commit` config (enforce hygiene)
Create **`.pre-commit-config.yaml`**:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: mixed-line-ending
      - id: detect-private-key
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.8
    hooks:
      - id: ruff
        args: ["--fix"]
  - repo: https://github.com/pre-commit/pygrep-hooks
    rev: v1.10.0
    hooks:
      - id: python-no-eval
  - repo: https://github.com/johnnybarrels/pre-commit-large-files
    rev: v1.0.0
    hooks:
      - id: prevent-large-files
        args: ["--maxkb=50000"]  # 50MB
```
Enable:
```bash
pip install pre-commit
pre-commit install
```

---

## 6) Makefile (or Taskfile) targets
Create **`Makefile`**:
```makefile
.PHONY: setup lint test clean clean-hard archive-sandbox

setup:
	python -m pip install -U pip
	pip install -r requirements.txt

lint:
	ruff check --fix || true
	black --check src tests || black src tests
	npx markdownlint-cli2 "docs/**/*.md" || true
	reuse lint || true

default: test

test:
	pytest -q

clean:
	python - <<'PY' \
import shutil, os
for d in ["artifacts","scratch","reports",".pytest_cache",".mypy_cache",".ruff_cache","htmlcov"]:
    if os.path.exists(d): shutil.rmtree(d, ignore_errors=True)
PY

clean-hard: clean
	git clean -fdX  # remove ignored files

archive-sandbox:
	@python scripts/archive_sandbox.py
```

Or use **`Taskfile.yml`** if you prefer `task` (Go Task runner).

---

## 7) Cleanup & Archive Scripts
Create **`scripts/clean.sh`**:
```bash
#!/usr/bin/env bash
set -euo pipefail
rm -rf artifacts scratch reports .pytest_cache .mypy_cache .ruff_cache htmlcov || true
```

Create **`scripts/clean.ps1`**:
```powershell
Remove-Item artifacts,scratch,reports,.pytest_cache,.mypy_cache,.ruff_cache,htmlcov -Recurse -Force -ErrorAction SilentlyContinue
```

Create **`scripts/archive_sandbox.py`**:
```python
import shutil, datetime, os, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
stamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
arch_dir = root / '_archive'
arch_dir.mkdir(exist_ok=True)

bundle_name = arch_dir / f'sandbox_{stamp}.zip'
with shutil.make_archive(bundle_name.with_suffix(''), 'zip', root, '.'):
    pass
# Optionally: only include ignored dirs
# shutil.make_archive(..., root_dir=root, base_dir='scratch')

# After archiving, clean transient dirs
for d in (root/ 'scratch', root/ 'artifacts', root/ 'reports'):
    if d.exists(): shutil.rmtree(d)
print(f"Archived sandbox -> {bundle_name}")
```

> Adjust archive contents if you only want `scratch/`, `artifacts/`, and `reports/` in the zip.

---

## 8) AI Assistant Working Agreement (paste into your tool prompts)
1. **Write all generated files** to `scratch/` (temporary) or `artifacts/` (keepable results).
2. **Never create directories at repo root** without asking; prefer `scratch/experiments/<date>-<topic>/`.
3. **When saving sample inputs**, use `samples/` and keep under **5MB per file**. No PII.
4. **Always add a header comment** in generated scripts with: author (AI), date, purpose, and cleanup instructions.
5. **Prefer diffs/patches** for code changes; do not drop whole-file replacements unless requested.
6. **On long runs**, log to `artifacts/logs/<date>.log` instead of printing giant console dumps.
7. **Respect .gitignore** and pre-commit checks; do not attempt to bypass them.

You can add this to your model system prompt or Windsurf workspace rules.

---

## 9) Optional: `.dockerignore`
```dockerignore
.git
_archive
artifacts
scratch
reports
node_modules
__pycache__
*.pyc
```

---

## 10) Quarantine → Release Flow
1. **During dev**: all noise → `scratch/`, stable outputs → `artifacts/`.
2. **Pre-release**: `make archive-sandbox` → creates `_archive/sandbox_YYYY-MM-DD_HHMM.zip`.
3. **Clean**: `make clean-hard` to remove all ignored files.
4. **Tag**: `git tag -a vX.Y.Z -m "Release notes" && git push --tags`.
5. **Attach** artifacts from `_archive/` to your GitHub Release if desired.

---

## 11) Bonus Git Tips
- Temporarily ignore tracked file changes: `git update-index --assume-unchanged <file>`.
- Bring it back: `git update-index --no-assume-unchanged <file>`.
- Preview what `git clean` would delete: `git clean -fdXn`.
- Block accidental binaries without LFS: add a pre-commit hook or require `git lfs` for `*.pdf`, `*.png`, etc. (But prefer **not** to store real data at all.)

---

**Drop these files in your repo** (copy/paste from blocks above). If you want, I can generate them now as committed files in your workspace structure.
