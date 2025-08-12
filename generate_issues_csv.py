import csv
import pathlib

rows = [
    {
        "Title": "Phase 0: Environment & Config Stabilization",
        "Body": """Goal: lock env, centralize config, reproducible runs.
Tasks: Pin deps; add .env support; add module entrypoint; structured logs with run_id.
DoD: Fresh clone -> install -> python -m doctr_process runs; logs under outputs/logs.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 1",
    },
    {
        "Title": "Phase 1: Repo & Module Cleanup",
        "Body": """Goal: clear package areas and enforce lint/types.
Tasks: move gui to ui/; create extract/ and io/; add ruff/black/mypy; fix imports; update tests.
DoD: ruff/black clean; pytest green; README updated.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 1",
    },
    {
        "Title": "Phase 2: Image Pre-processing Module",
        "Body": """Goal: configurable preproc (grayscale, adaptive threshold, denoise, deskew, optional perspective).
Tasks: ocr/preprocess.py; YAML toggles; integrate before OCR; golden tests.
DoD: measurable OCR lift on sample; toggles work.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 1",
    },
    {
        "Title": "Phase 3: OCR Engine Layer Hardening",
        "Body": """Goal: parameterize engines and add OCR cache.
Tasks: expose Tesseract/Doctr/EasyOCR params; per-page cache; unify orientation.
DoD: swap engines via YAML; reruns faster with cache.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 2",
    },
    {
        "Title": "Phase 4: Data Extraction v1 (Positional + Fuzzy)",
        "Body": """Goal: reduce regex brittleness.
Tasks: extract/fields.py; proximity around labels; dateparser; rapidfuzz vendor; confidence + method fields.
DoD: higher fill rate; low-confidence flagged.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 2",
    },
    {
        "Title": "Phase 5: Line Items & Totals",
        "Body": """Goal: extract tables and reconcile totals.
Tasks: table detection (lines/Y-bins); parse qty/unit/amount; sum vs total; vendor opt-in.
DoD: items JSON + status for enabled vendors.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 3",
    },
    {
        "Title": "Phase 6: Output & Reporting Polish",
        "Body": """Goal: business-friendly outputs.
Tasks: stable column order; Excel hyperlinks; mgmt XLSX+PDF; combined vendor PDFs; hardened SharePoint.
DoD: one command produces all artifacts.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 3",
    },
    {
        "Title": "Phase 7: Scale & Performance",
        "Body": """Goal: throughput and telemetry.
Tasks: ProcessPoolExecutor with chunks; producer/consumer; DPI tuning; perf log P95/RSS.
DoD: 2–3× throughput; perf CSV present.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 4",
    },
    {
        "Title": "Phase 8: Observability & Failures",
        "Body": """Goal: fast debugging, explicit exceptions.
Tasks: JSON logs with run_id; exception CSVs; metrics.json.
DoD: unified run folder enables quick triage.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 4",
    },
    {
        "Title": "Phase 9: Tests & CI",
        "Body": """Goal: regression safety.
Tasks: unit tests for preprocess/extract/filename; golden tests; GH Actions lint+type+test.
DoD: CI green; coverage on critical paths.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 5",
    },
    {
        "Title": "Phase 10: Packaging, CLI & Docker",
        "Body": """Goal: easy installs and reproducible runs.
Tasks: console scripts; Dockerfile with Tesseract+Poppler; versioning + changelog.
DoD: pipx and docker paths both work.""",
        "Labels": "enhancement;roadmap",
        "Milestone": "Sprint 5",
    },
]

out_path = pathlib.Path("issues_utf8.csv")
with out_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Title", "Body", "Labels", "Milestone"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {out_path.resolve()}")
