import sys
from pathlib import Path

import pandas as pd

# Add project src directory to import path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
# Import directly from the package to avoid stubs defined in ``conftest``
from output.csv_output import CSVOutput


def test_csv_output_handles_additional_fields(tmp_path):
    rows = [
        {'ticket_number': 'T1'},
        {'ticket_number': 'T2', 'truck_number_roi_image_path': 'img.png'},
    ]
    cfg = {'output_dir': str(tmp_path)}
    out = CSVOutput('results.csv')
    out.write(rows, cfg)
    df = pd.read_csv(tmp_path / 'results.csv')
    assert 'ticket_number' in df.columns
    assert 'truck_number_roi_image_path' in df.columns
    assert df.loc[1, 'truck_number_roi_image_path'] == 'img.png'
