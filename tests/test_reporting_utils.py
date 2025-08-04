from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from doctr_process.doctr_mod.doctr_ocr import reporting_utils


def test_export_issue_logs(tmp_path):
    cfg = {'output_dir': str(tmp_path), 'ticket_issues': True, 'issues_log': True}
    ticket_issues = [{'page':1,'issue':'missing ticket'}]
    issues_log = [{'page':1,'issue_type':'missing_field','field':'ticket_number'}]
    reporting_utils.export_issue_logs(ticket_issues, issues_log, cfg)
    assert (tmp_path/'logs'/'ticket_issues.csv').exists()
    ti = pd.read_csv(tmp_path/'logs'/'ticket_issues.csv')
    assert ti.shape[0] == 1


def test_export_process_analysis(tmp_path):
    cfg = {'output_dir': str(tmp_path), 'process_analysis': True}
    records = [{'page':1,'ocr_time':0.1,'orientation_time':0.2,'orientation':0}]
    reporting_utils.export_process_analysis(records, cfg)
    path = tmp_path/'logs'/'process_analysis.csv'
    assert path.exists()
    df = pd.read_csv(path)
    assert 'ocr_time' in df.columns


def test_condensed_ticket_report(tmp_path):
    cfg = {'output_dir': str(tmp_path), 'ticket_numbers_condensed_csv': True}
    rows = [{
        'file': '24-105_2025-07-30_Class2_Podium_WM.pdf',
        'page': 1,
        'vendor': 'ACME',
        'ticket_number': '123',
        'manifest_number': '14123456',
        'truck_number': 'TR1',
        'exception_reason': None,
        'image_path': 'img.png',
        'roi_image_path': 'roi.png'
    }]
    reporting_utils.create_reports(rows, cfg)
    path = tmp_path/'logs'/'ticket_number'/'condensed_ticket_numbers.csv'
    assert path.exists()
    df = pd.read_csv(path)
    assert list(df.columns) == [
        'JobID',
        'Service Date',
        'Material',
        'Source',
        'Destination',
        'page',
        'vendor',
        'ticket_number',
        'manifest_number',
        'truck_number',
        'exception_reason',
        'image_path',
        'roi_image_path'
    ]
    assert df.iloc[0]['JobID'] == '24-105'
