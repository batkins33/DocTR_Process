import json
import re
import time
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from rapidfuzz import process as rf_process, fuzz
from dateutil import parser as dateparser

# ---------- Config ----------

CONFUSION_PAIRS = [
    ("O", "0"), ("I", "1"), ("l", "1"), ("S", "5"),
    ("B", "8"), ("Z", "2"), ("G", "6"), ("Q", "0"), ("D", "0"),
]

# Project-specific ticket patterns
TICKET_PATTERNS = [
    re.compile(r"^LDI-?\d{6}$"),  # Primary: LDI-123456 or LDI123456
    re.compile(r"^[A-Z]{1,3}\d{5,7}$"),  # Secondary legacy
]

MONEY_REGEX = re.compile(r"^\$?\s*\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?$|^\$?\s*\d+(?:\.\d{2})?$")
DATE_HINT_REGEX = re.compile(r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b")

# Default seed dictionaries
DEFAULT_VENDORS = [
    "Lindamood Demolition",
    "Martin Marietta", 
    "Vulcan Materials",
    "Austin Bridge & Road"
]

DEFAULT_MATERIALS = [
    '1" Utility Stone',
    'Flex Base',
    'Select Fill', 
    'Asphalt Millings'
]

DEFAULT_COSTCODES = []

# ---------- Memory (JSONL) ----------

class CorrectionsMemory:
    """JSONL store of user-approved corrections."""
    
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[Tuple[str, str], str] = {}
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line.strip())
                        key = (rec.get("field", ""), rec.get("wrong", ""))
                        val = rec.get("right", "")
                        if key[0] and key[1] and val:
                            self._cache[key] = val
                    except Exception:
                        continue
        self._loaded = True

    def lookup(self, field: str, value: str) -> Optional[str]:
        self.load()
        return self._cache.get((field, value))

    def add(self, field: str, wrong: str, right: str, context: Optional[dict] = None) -> None:
        self.load()
        self._cache[(field, wrong)] = right
        rec = {
            "field": field,
            "wrong": wrong,
            "right": right,
            "context": context or {},
            "ts": int(time.time()),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()

# ---------- Normalization ----------

def normalize(text: str) -> str:
    """Basic text normalization."""
    if not text:
        return ""
    t = str(text).replace("\u2014", "-").replace("\u2013", "-").replace("\u00A0", " ")
    return " ".join(t.split()).strip()

def normalize_money(text: str) -> str:
    """Normalize money values with confusion character fixes."""
    if not text:
        return ""
    t = normalize(text)
    # Fix common OCR confusions in money using translation table
    translation_table = str.maketrans("OS", "05")
    t = t.translate(translation_table)
    
    # Clean formatting
    t = t.replace("$", "").replace(" ", "").replace(",", "")
    
    # Handle decimal places
    if "." in t:
        parts = t.split(".")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return f"{int(parts[0])}.{parts[1][:2].ljust(2, '0')}"
    elif t.isdigit():
        return str(int(t))
    
    return text

# ---------- Confusion fixes ----------

def apply_confusion_map(text: str, allowed_chars: Optional[str] = None) -> str:
    """Apply character confusion fixes."""
    if not text:
        return text
    
    result = list(text)
    for i, ch in enumerate(result):
        for old, new in CONFUSION_PAIRS:
            if ch == old:
                if not allowed_chars or new in allowed_chars:
                    result[i] = new
                break
    return "".join(result)

# ---------- Validators & Fixers ----------

def validate_ticket_no(value: str) -> Tuple[str, bool]:
    """Validate and fix ticket numbers."""
    if not value:
        return value, False
    
    v = normalize(value).upper()
    
    # Check if already valid
    for pattern in TICKET_PATTERNS:
        if pattern.match(v):
            return v, True
    
    # Try confusion fixes
    v2 = apply_confusion_map(v, "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
    for pattern in TICKET_PATTERNS:
        if pattern.match(v2):
            return v2, True
    
    return value, False

def validate_money(value: str) -> Tuple[str, bool]:
    """Validate and fix money amounts."""
    if not value:
        return value, False
    
    v = normalize_money(value)
    if MONEY_REGEX.match(v) or MONEY_REGEX.match("$" + v):
        return v, True
    
    # Try with confusion fixes
    v2 = apply_confusion_map(v, "0123456789.$,")
    v2 = normalize_money(v2)
    if MONEY_REGEX.match(v2) or MONEY_REGEX.match("$" + v2):
        return v2, True
    
    return value, False

def validate_date(value: str) -> Tuple[str, bool]:
    """Validate and fix dates to YYYY-MM-DD format."""
    if not value:
        return value, False
    
    v = normalize(value)
    
    # Try direct parsing
    try:
        dt = dateparser.parse(v, fuzzy=True)
        if dt:
            return dt.strftime("%Y-%m-%d"), True
    except Exception:
        pass
    
    # Try extracting date-like pattern
    match = DATE_HINT_REGEX.search(v)
    if match:
        try:
            dt = dateparser.parse(match.group(0), fuzzy=True)
            if dt:
                return dt.strftime("%Y-%m-%d"), True
        except Exception:
            pass
    
    return value, False

# ---------- Fuzzy Dictionary ----------

@dataclass
class FuzzyDict:
    """Fuzzy string matching dictionary."""
    values: List[str]
    scorer: Callable = fuzz.WRatio
    score_cutoff: int = 90

    def best(self, query: str) -> Tuple[Optional[str], int]:
        """Find best match for query."""
        if not query or not self.values:
            return None, 0
        
        q = normalize(query)
        result = rf_process.extractOne(
            q, self.values, 
            scorer=self.scorer, 
            score_cutoff=self.score_cutoff
        )
        
        if result:
            return result[0], int(result[1])
        return None, 0

# ---------- Context & Orchestrator ----------

@dataclass
class CorrectionContext:
    """Context for applying corrections."""
    memory: CorrectionsMemory
    vendor_dict: Optional[FuzzyDict] = None
    material_dict: Optional[FuzzyDict] = None
    costcode_dict: Optional[FuzzyDict] = None
    dry_run: bool = False

def correct_record(
    rec: dict, 
    ctx: CorrectionContext, 
    approve_callback: Optional[Callable[[str, str, str, dict], bool]] = None
) -> dict:
    """Apply corrections to a record."""
    out = dict(rec)
    
    # 1) Memory lookup (exact matches)
    for field in ("vendor", "material", "ticket_no", "amount", "date", "cost_code"):
        val = out.get(field)
        if val:
            mem = ctx.memory.lookup(field, val)
            if mem:
                out[field] = mem
    
    # 2) Field-specific validators
    for field, validator in [
        ("ticket_no", validate_ticket_no),
        ("amount", validate_money), 
        ("date", validate_date)
    ]:
        val = out.get(field)
        if val:
            fixed, ok = validator(val)
            if ok and fixed != val:
                reason = f"{field}-validate"
                if not approve_callback or approve_callback(field, val, fixed, {"reason": reason}):
                    if not ctx.dry_run:
                        ctx.memory.add(field, val, fixed, {"reason": reason})
                    out[field] = fixed
    
    # 3) Fuzzy dictionary matching
    def apply_fuzzy(field: str, fdict: Optional[FuzzyDict]):
        if not fdict:
            return
        val = out.get(field)
        if not val:
            return
        
        best, score = fdict.best(val)
        if best and best != val:
            # Apply heuristics for when to auto-correct
            has_confusable = any(c in val for c, _ in CONFUSION_PAIRS)
            if has_confusable or score >= 95:
                meta = {"reason": "fuzzy", "score": score}
                if not approve_callback or approve_callback(field, val, best, meta):
                    if not ctx.dry_run:
                        ctx.memory.add(field, val, best, meta)
                    out[field] = best
    
    apply_fuzzy("vendor", ctx.vendor_dict)
    apply_fuzzy("material", ctx.material_dict) 
    apply_fuzzy("cost_code", ctx.costcode_dict)
    
    return out

# ---------- Utilities ----------

def id_for_record(rec: dict, fields: Tuple[str, ...] = ("ticket_no", "date", "amount")) -> str:
    """Generate short ID for record auditing."""
    raw = "|".join(str(rec.get(k, "")) for k in fields)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

def load_csv_dict(path: Path) -> List[str]:
    """Load single-column CSV as list of strings."""
    if not path.exists():
        return []
    
    import csv
    values = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)  # Skip header
        for row in reader:
            if row and row[0].strip():
                values.append(row[0].strip())
    return values