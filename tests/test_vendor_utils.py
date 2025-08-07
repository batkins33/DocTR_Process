import types
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from doctr_process.ocr import vendor_utils

class DummyWord:
    def __init__(self, value):
        self.value = value

class DummyLine:
    def __init__(self, text):
        self.words = [DummyWord(w) for w in text.split()]
        self.geometry = ((0,0),(1,1))

class DummyBlock:
    def __init__(self, lines):
        self.lines = [DummyLine(l) for l in lines]

class DummyPage:
    def __init__(self, lines):
        self.blocks = [DummyBlock(lines)]


def test_find_vendor():
    rules = [
        {"vendor_name": "ACME", "display_name": "ACME", "vendor_type": "yard", "match_terms": ["acme"], "exclude_terms": []}
    ]
    vendor = vendor_utils.find_vendor("This is ACME company", rules)
    assert vendor[0] == "ACME"


def test_extract_vendor_fields():
    rules = {
        "ACME": {
            "ticket_number": {"method": "roi", "roi": [0,0,1,1], "regex": r"(\d+)"},
            "manifest_number": {"method": "roi", "roi": [0,0,1,1], "regex": r"Manifest (\d+)"},
        }
    }
    page = DummyPage(["Ticket 12345", "Manifest 9999999"])
    fields = vendor_utils.extract_vendor_fields(page, "ACME", rules)
    assert fields["ticket_number"] == "12345"
    assert fields["manifest_number"] == "9999999"
