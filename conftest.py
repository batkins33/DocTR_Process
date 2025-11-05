from importlib import import_module
from logging import warning
from pathlib import Path
from sys import modules as sys_modules
from sys import path as sys_path

# Ensure ./src is on sys.path for test collection
repo_root = Path(__file__).resolve().parent
src = repo_root / "src"
if str(src) not in sys_path:
    sys_path.insert(0, str(src))

# Force the legacy import path used by tests
try:
    # output → doctr_process.output
    out_pkg = import_module("doctr_process.output")
    sys_modules.setdefault("output", out_pkg)
    sys_modules["output.csv_output"] = import_module("doctr_process.output.csv_output")

    # pipeline → doctr_process.pipeline
    pipe_pkg = import_module("doctr_process.pipeline")
    sys_modules.setdefault("pipeline", pipe_pkg)
except (ImportError, ModuleNotFoundError) as e:
    warning("Failed to set up legacy import paths: %s", e)
