import sys
import types
from pathlib import Path

# Ensure package importable and stub optional SharePoint dependency
sys.modules.setdefault("office365", types.ModuleType("office365"))
sharepoint = types.ModuleType("office365.sharepoint")
client_context = types.ModuleType("office365.sharepoint.client_context")
client_context.ClientContext = type("ClientContext", (), {})
sharepoint.client_context = client_context
sys.modules.setdefault("office365.sharepoint", sharepoint)
sys.modules.setdefault("office365.sharepoint.client_context", client_context)
runtime = types.ModuleType("office365.runtime")
auth = types.ModuleType("office365.runtime.auth")
user_cred = types.ModuleType("office365.runtime.auth.user_credential")
user_cred.UserCredential = type("UserCredential", (), {})
auth.user_credential = user_cred
runtime.auth = auth
sys.modules.setdefault("office365.runtime", runtime)
sys.modules.setdefault("office365.runtime.auth", auth)
sys.modules.setdefault("office365.runtime.auth.user_credential", user_cred)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pipeline as pipeline

# Stub optional dependencies
sys.modules.setdefault("cv2", types.ModuleType("cv2"))
pytesseract_mod = types.ModuleType("pytesseract")
pytesseract_mod.image_to_osd = lambda *a, **k: ""
pytesseract_mod.image_to_string = lambda *a, **k: ""
sys.modules.setdefault("pytesseract", pytesseract_mod)


def _dummy_process_file(pdf_path, cfg, vendor_rules, extraction_rules):
    row = {
        "file": pdf_path,
        "page": 1,
        "vendor": "ACME",
        "ticket_number": "T",
        "manifest_number": "M",
        "page_hash": "hash",
    }
    perf = {"file": pdf_path, "pages": 1, "duration_sec": 0}
    return [row], perf, [], [], [], [], []


class _CollectingHandler:
    def __init__(self):
        self.rows = None

    def write(self, rows, cfg):
        self.rows = list(rows)


def _run_pipeline(tmp_path, monkeypatch, parallel):
    input_dir = tmp_path / "inputs"
    input_dir.mkdir(exist_ok=True)
    expected = []
    for i in range(2):
        p = input_dir / f"f{i}.pdf"
        p.write_text("pdf")
        expected.append(str(p))

    cfg = {
        "log_dir": str(tmp_path / ("logs_p" if parallel else "logs_s")),
        "output_dir": str(tmp_path / ("out_p" if parallel else "out_s")),
        "batch_mode": True,
        "input_dir": str(input_dir),
        "parallel": parallel,
        "num_workers": 2,
        "output_format": [],
    }
    collector = _CollectingHandler()
    monkeypatch.setattr(pipeline, "load_config", lambda *a, **k: cfg)
    monkeypatch.setattr(pipeline, "resolve_input", lambda c: c)
    monkeypatch.setattr(pipeline, "load_extraction_rules", lambda *_: {})
    monkeypatch.setattr(pipeline, "load_vendor_rules_from_csv", lambda *_: {})
    monkeypatch.setattr(pipeline, "process_file", _dummy_process_file)
    monkeypatch.setattr(pipeline, "create_handlers", lambda names, cfg: [collector])
    monkeypatch.setattr(
        pipeline.reporting_utils, "create_reports", lambda *a, **k: None
    )
    monkeypatch.setattr(
        pipeline.reporting_utils, "export_preflight_exceptions", lambda *a, **k: None
    )
    monkeypatch.setattr(
        pipeline.reporting_utils, "export_log_reports", lambda *a, **k: None
    )
    monkeypatch.setattr(
        pipeline.reporting_utils, "export_issue_logs", lambda *a, **k: None
    )
    monkeypatch.setattr(
        pipeline.reporting_utils, "export_process_analysis", lambda *a, **k: None
    )

    pipeline.run_pipeline()
    return collector.rows, expected


def test_run_pipeline_sequential(tmp_path, monkeypatch):
    rows, expected = _run_pipeline(tmp_path, monkeypatch, parallel=False)
    assert len(rows) == len(expected)
    assert sorted(r["file"] for r in rows) == sorted(expected)


def test_run_pipeline_parallel(tmp_path, monkeypatch):
    seq_rows, expected = _run_pipeline(tmp_path, monkeypatch, parallel=False)
    par_rows, _ = _run_pipeline(tmp_path, monkeypatch, parallel=True)
    assert par_rows == seq_rows
    assert sorted(r["file"] for r in par_rows) == sorted(expected)
