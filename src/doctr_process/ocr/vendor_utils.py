"""Vendor rule utilities and field extraction helpers."""

import re
from typing import Dict, Any

import pandas as pd

__all__ = [
    "load_vendor_rules_from_csv",
    "find_vendor",
    "extract_field",
    "extract_vendor_fields",
    "FIELDS",
]

FIELDS = ["ticket_number", "manifest_number", "material_type", "truck_number", "date"]


def load_vendor_rules_from_csv(path: str):
    """Read vendor matching rules from a CSV file."""
    df = pd.read_csv(path)
    vendor_rules = []
    for _, row in df.iterrows():
        name = str(row["vendor_name"]).strip()
        display = str(row.get("display_name", "")).strip() or name
        vtype = str(row.get("vendor_type", "")).strip()
        matches_str = row.get("vendor_match", "")
        if pd.isna(matches_str):
            matches = []
        else:
            matches = [m.strip().lower() for m in str(matches_str).split(",") if m.strip()]
        excludes_str = row.get("vendor_excludes", "")
        if pd.isna(excludes_str):
            excludes = []
        else:
            excludes = [e.strip().lower() for e in str(excludes_str).split(",") if e.strip()]
        vendor_rules.append(
            {
                "vendor_name": name,
                "display_name": display,
                "vendor_type": vtype,
                "match_terms": matches,
                "exclude_terms": excludes,
            }
        )
    return vendor_rules


def find_vendor(page_text: str, vendor_rules):
    """Return the vendor details that match ``page_text``."""
    page_text_lower = page_text.lower()
    for rule in vendor_rules:
        matched_terms = [term for term in rule["match_terms"] if term in page_text_lower]
        found_exclude = any(exclude in page_text_lower for exclude in rule["exclude_terms"])
        if matched_terms and not found_exclude:
            return (
                rule["vendor_name"],
                rule["vendor_type"],
                matched_terms[0],
                rule.get("display_name", rule["vendor_name"]),
            )
    return "", "", "", ""


def extract_field(result_page, field_rules: Dict[str, Any], pil_img=None, cfg=None):
    """Extract a single field from the OCR result page."""
    method = field_rules.get("method")
    regex = field_rules.get("regex")
    label = str(field_rules.get("label") or "").lower()
    DEBUG = cfg.get("DEBUG", False) if cfg else False

    if method in ["roi", "box"]:
        roi = field_rules.get("roi") or field_rules.get("box")
        candidates = []
        for block in result_page.blocks:
            for line in block.lines:
                (lx_min, ly_min), (lx_max, ly_max) = line.geometry
                if lx_min >= roi[0] and ly_min >= roi[1] and lx_max <= roi[2] and ly_max <= roi[3]:
                    text = " ".join(word.value for word in line.words)
                    candidates.append(text)

        labels = field_rules.get("label", "")
        if isinstance(labels, str):
            labels = [l.strip().lower() for l in labels.split(",") if l.strip()]
        elif isinstance(labels, list):
            labels = [l.lower() for l in labels]
        else:
            labels = []

        if labels:
            candidates = [c for c in candidates if not any(lbl in c.lower() for lbl in labels)]

        if DEBUG:
            print("CANDIDATES:", candidates)

        for text in candidates:
            if regex:
                m = re.search(regex, text)
                if DEBUG:
                    print(f"[DEBUG] Matching '{regex}' in '{text}' => {m.group(0) if m else None}")
                if m:
                    return m.group(1) if m.lastindex else m.group(0)
        return candidates[0] if candidates else None

    elif method == "below_label":
        label = field_rules.get("label", "").lower()
        lines = [" ".join(word.value for word in line.words) for block in result_page.blocks for line in block.lines]
        ticket_label_idx = None
        for i, line in enumerate(lines):
            if label in line.lower():
                ticket_label_idx = i
                break
        if ticket_label_idx is not None and ticket_label_idx + 1 < len(lines):
            target_line = lines[ticket_label_idx + 1]
            if regex:
                m = re.search(regex, target_line)
                if m:
                    return m.group(0)
            return target_line.strip()
        return None

    elif method == "label_right":
        label = field_rules.get("label", "").lower()
        for block in result_page.blocks:
            for line in block.lines:
                line_text = " ".join(word.value for word in line.words)
                if label in line_text.lower():
                    idx = line_text.lower().find(label)
                    after_label = line_text[idx + len(label) :]
                    if regex:
                        m = re.search(regex, after_label)
                        if m:
                            return m.group(0)
                    return after_label.strip()
        return None

    return None


def extract_vendor_fields(result_page, vendor_name: str, extraction_rules, pil_img=None, cfg=None):
    """Extract all configured fields for ``vendor_name`` from ``result_page``."""
    vendor_rule = extraction_rules.get(vendor_name, extraction_rules.get("DEFAULT"))
    result = {}
    for field in FIELDS:
        field_rules = vendor_rule.get(field)
        if not field_rules:
            result[field] = None
            continue
        if field_rules.get("method") is None:
            result[field] = None
            continue
        result[field] = extract_field(result_page, field_rules, pil_img, cfg)
    return result
