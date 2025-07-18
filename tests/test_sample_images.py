import re
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

try:
    from doctr.models import ocr_predictor
    _predictor = ocr_predictor(pretrained=True)
    _skip_reason = None
except Exception as exc:  # pragma: no cover - model download failed
    _predictor = None
    _skip_reason = str(exc)

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "DocTR_Mod" / "docs" / "TruckTicketSamples"

ticket_re = re.compile(r"\b(?:A\d{5,6}|\d{4,7})\b")
manifest_re = re.compile(r"\b\d{7,}\b")

@pytest.mark.skipif(_predictor is None, reason=f"doctr model not available: {_skip_reason}")
def test_samples_have_ticket_and_manifest():
    for img_path in SAMPLES_DIR.glob("*.png"):
        img = Image.open(img_path)
        docs = _predictor([np.array(img)])
        text = " ".join(
            word.value
            for block in docs.pages[0].blocks
            for line in block.lines
            for word in line.words
        )
        assert ticket_re.search(text), f"No ticket number found in {img_path.name}"
        assert manifest_re.search(text), f"No manifest number found in {img_path.name}"
