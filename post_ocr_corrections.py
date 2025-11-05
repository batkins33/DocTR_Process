from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from dateutil import parser as dateparser
from rapidfuzz import fuzz
from rapidfuzz import process as rf_process

# ---------- Config ----------

CONFUSION_PAIRS = [
    ("O", "0"),
    ("I", "1"),
    ("l", "1"),
    ("S", "5"),
    ("B", "8"),
    ("Z", "2"),
    ("G", "6"),
    ("Q", "0"),
    ("D", "0"),
]
TICKET_NO_REGEX = re.compile(r"[A-Z]{1,3}\d{5,7}|[A-Z0-9]{6,10}")
MONEY_REGEX = re.compile(
    r"^\$?\s*\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?$|^\$?\s*\d+(?:\.\d{2})?$"
)
DATE_HINT_REGEX = re.compile(
    r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b"
)


# ---------- Memory (JSONL) ----------


class CorrectionsMemory:
    """
    JSONL store of user-approved corrections. Each line:
    {"field":"vendor","wrong":"LINDAMOOD DEM0LITION","right":"Lindamood Demolition","context":{"job_id":"J123"},"ts":...}
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._cache: dict[tuple[str, str], str] = {}  # (field, wrong)->right
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                        key = (rec.get("field") or "", rec.get("wrong") or "")
                        val = rec.get("right") or ""
                        if key[0] and key[1] and val:
                            self._cache[key] = val
                    except Exception:
                        continue
        self._loaded = True

    def lookup(self, field: str, value: str) -> str | None:
        self.load()
        return self._cache.get((field, value))

    def add(
        self, field: str, wrong: str, right: str, context: dict | None = None
    ) -> None:
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


# ---------- Normalization ----------


def normalize(text: str) -> str:
    if text is None:
        return ""
    # Trim, collapse spaces, normalize common punctuation
    t = " ".join(
        str(text)
        .replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u00a0", " ")
        .split()
    )
    return t.strip()


def normalize_money(text: str) -> str:
    t = normalize(text).replace("O", "0")
    t = t.replace(" ", "")
    # Remove stray currency symbols for validation; keep them for display later if desired
    t = t.replace("$", "")
    # Unify commas
    parts = t.split(".")
    int_part = parts[0].replace(",", "")
    if not int_part.isdigit() and int_part:
        return text  # don't break legitimate weird cases
    if len(parts) == 2 and parts[1].isdigit():
        return f"{int(int_part)}.{parts[1]:0<2}"
    elif int_part.isdigit():
        return str(int(int_part))
    return text


# ---------- Confusion fixes ----------


def apply_confusion_map(text: str, allowed_chars: str | None = None) -> str:
    t = list(text)
    for i, ch in enumerate(t):
        for a, b in CONFUSION_PAIRS:
            if ch == a:
                candidate = b
            elif ch == b:
                candidate = a
            else:
                continue
            if allowed_chars and candidate not in allowed_chars:
                continue
            # Replace only if it improves "alnum-ness" (simple heuristic)
            if (
                candidate.isdigit() != ch.isdigit()
                or candidate.isalpha() != ch.isalpha()
            ):
                t[i] = candidate
    return "".join(t)


# ---------- Validators & Fixers ----------


def validate_ticket_no(value: str) -> tuple[str, bool]:
    v = normalize(value).upper()
    if TICKET_NO_REGEX.fullmatch(v):
        return v, True
    # Try confusion fixes limited to A-Z0-9
    v2 = apply_confusion_map(v, allowed_chars=None)
    if TICKET_NO_REGEX.fullmatch(v2):
        return v2, True
    return v, False


def validate_money(value: str) -> tuple[str, bool]:
    v = normalize_money(value)
    if MONEY_REGEX.fullmatch(v) or MONEY_REGEX.fullmatch("$" + v):
        return v, True
    # One more pass with confusion map (common: 'S'->'5')
    v2 = apply_confusion_map(v)
    if MONEY_REGEX.fullmatch(v2) or MONEY_REGEX.fullmatch("$" + v2):
        return v2, True
    return value, False


def validate_date(value: str) -> tuple[str, bool]:
    v = normalize(value)
    if not v:
        return v, False
    try:
        # Accept many layouts; you can set dayfirst/monthfirst if you need
        dt = dateparser.parse(v, fuzzy=True)
        if dt:
            return dt.strftime("%Y-%m-%d"), True
    except Exception:
        pass
    # Try extracting a date-like token then parse
    m = DATE_HINT_REGEX.search(v)
    if m:
        try:
            dt = dateparser.parse(m.group(0), fuzzy=True)
            if dt:
                return dt.strftime("%Y-%m-%d"), True
        except Exception:
            pass
    return value, False


# ---------- Dictionaries & Fuzzy ----------


@dataclass
class FuzzyDict:
    values: list[str]
    scorer: callable = fuzz.WRatio
    limit: int = 3
    score_cutoff: int = 90

    def best(self, query: str) -> tuple[str | None, int]:
        q = normalize(query)
        if not q or not self.values:
            return None, 0
        result = rf_process.extractOne(
            q, self.values, scorer=self.scorer, score_cutoff=self.score_cutoff
        )
        if result:
            return result[0], int(result[1])
        return None, 0


# ---------- Orchestrator ----------


@dataclass
class CorrectionContext:
    memory: CorrectionsMemory
    vendor_dict: FuzzyDict | None = None
    material_dict: FuzzyDict | None = None
    costcode_dict: FuzzyDict | None = None


def correct_record(rec: dict, ctx: CorrectionContext, approve_callback=None) -> dict:
    """
    rec: {"ticket_no": "...", "date": "...", "vendor": "...", "material": "...", "amount": "...", ...}
    approve_callback(field, old, new, meta)->bool  optional hook to confirm/autosave corrections
    """
    out = dict(rec)

    # 1) Corrections memory (exact wrong→right seen before)
    for field in ("vendor", "material", "ticket_no"):
        val = out.get(field)
        if val:
            mem = ctx.memory.lookup(field, val)
            if mem:
                out[field] = mem

    # 2) Field-specific validators
    if "ticket_no" in out and out["ticket_no"]:
        fixed, ok = validate_ticket_no(out["ticket_no"])
        if ok and fixed != out["ticket_no"]:
            if not approve_callback or approve_callback(
                "ticket_no", out["ticket_no"], fixed, {"reason": "regex+confusion"}
            ):
                ctx.memory.add(
                    "ticket_no", out["ticket_no"], fixed, {"reason": "regex+confusion"}
                )
                out["ticket_no"] = fixed

    if "amount" in out and out["amount"]:
        fixed, ok = validate_money(out["amount"])
        if ok and fixed != out["amount"]:
            if not approve_callback or approve_callback(
                "amount", out["amount"], fixed, {"reason": "money-normalize"}
            ):
                ctx.memory.add(
                    "amount", out["amount"], fixed, {"reason": "money-normalize"}
                )
                out["amount"] = fixed

    if "date" in out and out["date"]:
        fixed, ok = validate_date(out["date"])
        if ok and fixed != out["date"]:
            if not approve_callback or approve_callback(
                "date", out["date"], fixed, {"reason": "date-parse"}
            ):
                ctx.memory.add("date", out["date"], fixed, {"reason": "date-parse"})
                out["date"] = fixed

    # 3) Dictionaries + fuzzy snap for open-text fields
    def fuzzy_field(field: str, fdict: FuzzyDict | None):
        if not fdict:
            return
        val = out.get(field)
        if not val:
            return
        best, score = fdict.best(val)
        if best and best != val:
            # Heuristic: only correct if (a) score≥cutoff already enforced, and (b) the OCR has confusable chars
            has_confusable = any(a in val or b in val for a, b in CONFUSION_PAIRS)
            if has_confusable or score >= 95:
                if not approve_callback or approve_callback(
                    field, val, best, {"score": score}
                ):
                    ctx.memory.add(field, val, best, {"score": score})
                    out[field] = best

    fuzzy_field("vendor", ctx.vendor_dict)
    fuzzy_field("material", ctx.material_dict)
    fuzzy_field("cost_code", ctx.costcode_dict)

    return out


# ---------- Utilities ----------


def id_for_record(
    rec: dict, fields: tuple[str, ...] = ("ticket_no", "date", "amount")
) -> str:
    raw = "|".join(str(rec.get(k, "")) for k in fields)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
