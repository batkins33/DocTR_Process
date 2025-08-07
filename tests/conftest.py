import sys
import types

# Stub OpenCV
cv2_mod = types.ModuleType('cv2')


def _cv2_threshold(arr, thresh, maxval, type):
    return 0, arr


cv2_mod.threshold = _cv2_threshold
cv2_mod.THRESH_BINARY = 0
cv2_mod.THRESH_OTSU = 0
sys.modules.setdefault('cv2', cv2_mod)

# Stub pytesseract with minimal functions used in tests
pytesseract_mod = types.ModuleType('pytesseract')
pytesseract_mod.image_to_osd = lambda *a, **k: "Rotate: 0"
pytesseract_mod.image_to_string = lambda *a, **k: "12345"
sys.modules.setdefault('pytesseract', pytesseract_mod)

# Stub pdf2image and its exceptions
pdf2image_mod = types.ModuleType('pdf2image')
from PIL import Image, ImageDraw


def _dummy_convert_from_path(*args, **kwargs):
    img = Image.new("RGB", (200, 200), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 150, 150], fill="black")
    return [img]


pdf2image_mod.convert_from_path = _dummy_convert_from_path
pdf2image_mod.pdfinfo_from_path = lambda *a, **k: {"Pages": 1}
pdf2image_ex = types.ModuleType('pdf2image.exceptions')
pdf2image_ex.PDFInfoNotInstalledError = Exception
pdf2image_mod.exceptions = pdf2image_ex
sys.modules.setdefault('pdf2image', pdf2image_mod)
sys.modules.setdefault('pdf2image.exceptions', pdf2image_ex)

# Stub PyMuPDF (fitz)
fitz_mod = types.ModuleType('fitz')
sys.modules.setdefault('fitz', fitz_mod)

# Stub ``output.factory`` to avoid optional dependencies like openpyxl
output_pkg = types.ModuleType('output')
factory_mod = types.ModuleType('output.factory')
factory_mod.create_handlers = lambda names, cfg: []
output_pkg.factory = factory_mod
sys.modules.setdefault('output', output_pkg)
sys.modules.setdefault('output.factory', factory_mod)
