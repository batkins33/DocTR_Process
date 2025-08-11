import sys, importlib
from pathlib import Path

# Ensure ./src is on sys.path for test collection
repo_root = Path(__file__).resolve().parent
src = repo_root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

# Force the legacy import path used by tests
try:
    # output → doctr_process.output
    out_pkg = importlib.import_module("doctr_process.output")
    sys.modules.setdefault("output", out_pkg)
    sys.modules["output.csv_output"] = importlib.import_module("doctr_process.output.csv_output")

    # pipeline → doctr_process.pipeline
    pipe_pkg = importlib.import_module("doctr_process.pipeline")
    sys.modules.setdefault("pipeline", pipe_pkg)
except Exception:
    pass
