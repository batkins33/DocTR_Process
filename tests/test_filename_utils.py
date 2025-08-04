import importlib.util
from pathlib import Path

# Load the module directly to avoid importing heavy dependencies from package __init__
SPEC = importlib.util.spec_from_file_location(
    "filename_utils",
    Path(__file__).resolve().parents[1]
    / "src"
    / "doctr_process"
    / "processor"
    / "filename_utils.py",
)
filename_utils = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(filename_utils)

def test_format_output_filename_strips_trailing_count():
    meta = filename_utils.parse_input_filename_fuzzy(
        "24-105_2025-07-30_Class2_Podium_WM_145.pdf"
    )
    assert meta["base_name"] == "24-105_2025-07-30_Class2_Podium_WM"
    name = filename_utils.format_output_filename_camel(
        "Roadstar", 52, meta, "pdf"
    )
    assert name == "24-105_2025-07-30_Roadstar_Class2_Podium_WM_52.pdf"
