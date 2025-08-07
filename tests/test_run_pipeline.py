from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / 'doctr_process' / 'doctr_mod'))

# Stub out optional SharePoint dependency to avoid heavy install
import types
office365 = types.ModuleType('office365')
sharepoint = types.ModuleType('office365.sharepoint')
client_context = types.ModuleType('office365.sharepoint.client_context')
class ClientContext:  # pragma: no cover - simple placeholder
    pass
client_context.ClientContext = ClientContext
sharepoint.client_context = client_context
office365.sharepoint = sharepoint
sys.modules.setdefault('office365', office365)
sys.modules.setdefault('office365.sharepoint', sharepoint)
sys.modules.setdefault('office365.sharepoint.client_context', client_context)

runtime = types.ModuleType('office365.runtime')
auth = types.ModuleType('office365.runtime.auth')
user_credential = types.ModuleType('office365.runtime.auth.user_credential')
class UserCredential:  # pragma: no cover
    pass
user_credential.UserCredential = UserCredential
auth.user_credential = user_credential
runtime.auth = auth
office365.runtime = runtime
sys.modules.setdefault('office365.runtime', runtime)
sys.modules.setdefault('office365.runtime.auth', auth)
sys.modules.setdefault('office365.runtime.auth.user_credential', user_credential)

# Provide a minimal stub for the ``output`` package to avoid heavy optional deps
output_pkg = types.ModuleType('output')
factory_mod = types.ModuleType('output.factory')
def _dummy_create_handlers(names, cfg):  # pragma: no cover
    return []
factory_mod.create_handlers = _dummy_create_handlers
output_pkg.factory = factory_mod
sys.modules.setdefault('output', output_pkg)
sys.modules.setdefault('output.factory', factory_mod)

# Stub 'src.doctr_process.processor.filename_utils' for modules that expect it
src_pkg = types.ModuleType('src')
dp_pkg = types.ModuleType('src.doctr_process')
processor_pkg = types.ModuleType('src.doctr_process.processor')
filename_utils_mod = types.ModuleType('src.doctr_process.processor.filename_utils')
def _fn_placeholder(*args, **kwargs):
    return ""
filename_utils_mod.format_output_filename = _fn_placeholder
filename_utils_mod.format_output_filename_camel = _fn_placeholder
filename_utils_mod.format_output_filename_lower = _fn_placeholder
filename_utils_mod.format_output_filename_snake = _fn_placeholder
filename_utils_mod.format_output_filename_preserve = _fn_placeholder
filename_utils_mod.parse_input_filename_fuzzy = lambda *a, **k: {}
filename_utils_mod.sanitize_vendor_name = lambda x: x
processor_pkg.filename_utils = filename_utils_mod
dp_pkg.processor = processor_pkg
src_pkg.doctr_process = dp_pkg
sys.modules.setdefault('src', src_pkg)
sys.modules.setdefault('src.doctr_process', dp_pkg)
sys.modules.setdefault('src.doctr_process.processor', processor_pkg)
sys.modules.setdefault('src.doctr_process.processor.filename_utils', filename_utils_mod)


# Provide a minimal stub for OpenCV to avoid heavy optional dependency
cv2_mod = types.ModuleType('cv2')
sys.modules.setdefault('cv2', cv2_mod)

# Stub ``pytesseract`` since OCR functions are not exercised in tests
pytesseract_mod = types.ModuleType('pytesseract')
pytesseract_mod.image_to_osd = lambda *a, **k: ""
pytesseract_mod.image_to_string = lambda *a, **k: ""
sys.modules.setdefault('pytesseract', pytesseract_mod)

# Stub ``pdf2image`` and ``fitz`` used during preflight imports
pdf2image_mod = types.ModuleType('pdf2image')
pdf2image_mod.convert_from_path = lambda *a, **k: []
pdf2image_mod.pdfinfo_from_path = lambda *a, **k: {"Pages": 0}
pdf2image_ex = types.ModuleType('pdf2image.exceptions')
pdf2image_ex.PDFInfoNotInstalledError = Exception
pdf2image_mod.exceptions = pdf2image_ex
sys.modules.setdefault('pdf2image', pdf2image_mod)
sys.modules.setdefault('pdf2image.exceptions', pdf2image_ex)

fitz_mod = types.ModuleType('fitz')
sys.modules.setdefault('fitz', fitz_mod)


from doctr_process.doctr_mod import doctr_ocr_to_csv


# Stub worker for fast tests; must be module-level for multiprocessing pickling

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
        # Store a copy so subsequent runs don't mutate previous results
        self.rows = list(rows)


def _run_pipeline(tmp_path, monkeypatch, parallel: bool):
    """Run the pipeline with minimal stubs and return produced rows."""

    input_dir = tmp_path / "inputs"
    input_dir.mkdir(exist_ok=True)


def test_run_pipeline_parallel(tmp_path, monkeypatch):
    # Prepare dummy input files
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()

    expected_files = []
    for i in range(2):
        p = input_dir / f"f{i}.pdf"
        p.write_text("pdf")
        expected_files.append(str(p))


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
    monkeypatch.setattr(doctr_ocr_to_csv, "load_config", lambda: cfg)
    monkeypatch.setattr(doctr_ocr_to_csv, "resolve_input", lambda c: c)
    monkeypatch.setattr(doctr_ocr_to_csv, "load_extraction_rules", lambda _: {})
    monkeypatch.setattr(doctr_ocr_to_csv, "load_vendor_rules_from_csv", lambda _: {})
    monkeypatch.setattr(doctr_ocr_to_csv, "process_file", _dummy_process_file)
    monkeypatch.setattr(doctr_ocr_to_csv, "create_handlers", lambda names, cfg: [collector])
    monkeypatch.setattr(doctr_ocr_to_csv.reporting_utils, "create_reports", lambda *a, **k: None)
    monkeypatch.setattr(doctr_ocr_to_csv.reporting_utils, "export_preflight_exceptions", lambda *a, **k: None)
    monkeypatch.setattr(doctr_ocr_to_csv.reporting_utils, "export_log_reports", lambda *a, **k: None)
    monkeypatch.setattr(doctr_ocr_to_csv.reporting_utils, "export_issue_logs", lambda *a, **k: None)
    monkeypatch.setattr(doctr_ocr_to_csv.reporting_utils, "export_process_analysis", lambda *a, **k: None)
    doctr_ocr_to_csv.run_pipeline()
    return collector.rows, expected_files


def test_run_pipeline_sequential(tmp_path, monkeypatch):
    rows, expected_files = _run_pipeline(tmp_path, monkeypatch, parallel=False)
    assert len(rows) == len(expected_files)
    assert sorted(r["file"] for r in rows) == sorted(expected_files)


def test_run_pipeline_parallel(tmp_path, monkeypatch):
    seq_rows, expected_files = _run_pipeline(tmp_path, monkeypatch, parallel=False)
    par_rows, _ = _run_pipeline(tmp_path, monkeypatch, parallel=True)


    assert par_rows == seq_rows
    assert len(par_rows) == len(expected_files)
    assert sorted(r["file"] for r in par_rows) == sorted(expected_files)
