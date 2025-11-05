"""Vendor rule utilities and field extraction helpers."""

import re
from typing import Any, NamedTuple

import pandas as pd


class VendorMatch(NamedTuple):
    """Result of vendor matching operation."""

    vendor_name: str
    vendor_type: str
    matched_term: str
    display_name: str


__all__ = [
    "load_vendor_rules_from_csv",
    "find_vendor",
    "extract_field",
    "extract_vendor_fields",
    "FIELDS",
]

FIELDS = ["ticket_number", "manifest_number", "material_type", "truck_number", "date"]
HEIDELBERG_FIELDS = [
    "date",
    "ticket_number",
    "product",
    "time_in",
    "time_out",
    "job",
    "tons",
]


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
            matches = [
                m.strip().lower() for m in str(matches_str).split(",") if m.strip()
            ]
        excludes_str = row.get("vendor_excludes", "")
        if pd.isna(excludes_str):
            excludes = []
        else:
            excludes = [
                e.strip().lower() for e in str(excludes_str).split(",") if e.strip()
            ]
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


def find_vendor(page_text: str, vendor_rules) -> VendorMatch:
    """Return the vendor details that match ``page_text``."""
    page_text_lower = page_text.lower()

    # Standard vendor detection
    for rule in vendor_rules:
        matched_terms = [
            term for term in rule["match_terms"] if term in page_text_lower
        ]
        found_exclude = any(
            exclude in page_text_lower for exclude in rule["exclude_terms"]
        )
        if matched_terms and not found_exclude:
            return VendorMatch(
                vendor_name=rule["vendor_name"],
                vendor_type=rule["vendor_type"],
                matched_term=matched_terms[0],
                display_name=rule.get("display_name", rule["vendor_name"]),
            )
    return VendorMatch("", "", "", "")


def _extract_roi_field(result_page, field_rules: dict[str, Any], cfg=None):
    """Extract field using ROI/box method."""
    roi = field_rules.get("roi") or field_rules.get("box")
    regex = field_rules.get("regex")
    DEBUG = cfg.get("DEBUG", False) if cfg else False

    candidates = []
    for block in result_page.blocks:
        for line in block.lines:
            (lx_min, ly_min), (lx_max, ly_max) = line.geometry
            if (
                lx_min >= roi[0]
                and ly_min >= roi[1]
                and lx_max <= roi[2]
                and ly_max <= roi[3]
            ):
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
        candidates = [
            c for c in candidates if not any(lbl in c.lower() for lbl in labels)
        ]

    if DEBUG:
        print("CANDIDATES:", candidates)

    for text in candidates:
        if regex:
            m = re.search(regex, text)
            if DEBUG:
                print(
                    f"[DEBUG] Matching '{regex}' in '{text}' => {m.group(0) if m else None}"
                )
            if m:
                return m.group(1) if m.lastindex else m.group(0)
    return candidates[0] if candidates else None


def _extract_below_label_field(result_page, field_rules: dict[str, Any]):
    """Extract field using below_label method."""
    label = field_rules.get("label", "").lower()
    regex = field_rules.get("regex")

    lines = [
        " ".join(word.value for word in line.words)
        for block in result_page.blocks
        for line in block.lines
    ]
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


def _extract_label_right_field(result_page, field_rules: dict[str, Any]):
    """Extract field using label_right method."""
    label = field_rules.get("label", "").lower()
    regex = field_rules.get("regex")

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


def _extract_text_regex_field(result_page, field_rules: dict[str, Any]):
    """Extract field using text_regex method for full-text pattern matching."""
    regex = field_rules.get("regex")
    fallback_regex = field_rules.get("fallback_regex")
    regex_flags_str = field_rules.get("regex_flags", "")

    if not regex:
        return None

    # Convert flags string to re flags
    flags = 0
    if "IGNORECASE" in regex_flags_str:
        flags |= re.IGNORECASE

    # Get full text from all blocks
    full_text = ""
    for block in result_page.blocks:
        for line in block.lines:
            line_text = " ".join(word.value for word in line.words)
            full_text += line_text + " "

    # Normalize whitespace
    full_text = re.sub(r"[ \t]+", " ", full_text)

    # Try main regex
    m = re.search(regex, full_text, flags)
    if m:
        return m.group(1) if m.lastindex else m.group(0)

    # Try fallback regex if provided
    if fallback_regex:
        m = re.search(fallback_regex, full_text, flags)
        if m:
            return m.group(1) if m.lastindex else m.group(0)

    return None


def extract_field(result_page, field_rules: dict[str, Any], pil_img=None, cfg=None):
    """Extract a single field from the OCR result page."""
    method = field_rules.get("method")

    if method in ["roi", "box"]:
        return _extract_roi_field(result_page, field_rules, cfg)
    elif method == "below_label":
        return _extract_below_label_field(result_page, field_rules)
    elif method == "label_right":
        return _extract_label_right_field(result_page, field_rules)
    elif method == "text_regex":
        return _extract_text_regex_field(result_page, field_rules)

    return None


def extract_vendor_fields(
    result_page, vendor_name: str, extraction_rules, pil_img=None, cfg=None
):
    """Extract all configured fields for ``vendor_name`` from ``result_page``."""
    # Use vendor-specific rules if available, otherwise fall back to DEFAULT
    if vendor_name and vendor_name in extraction_rules:
        vendor_rule = extraction_rules[vendor_name]
        if cfg and cfg.get("debug"):
            print(f"[DEBUG] Using vendor-specific rules for: {vendor_name}")
    else:
        vendor_rule = extraction_rules.get("DEFAULT", {})
        if cfg and cfg.get("debug"):
            print(f"[DEBUG] Using DEFAULT rules for vendor: {vendor_name}")

    # Use Heidelberg-specific fields if vendor is Heidelberg, otherwise use standard fields
    fields_to_extract = HEIDELBERG_FIELDS if vendor_name == "Heidelberg" else FIELDS

    result = {}

    for field in fields_to_extract:
        field_rules = vendor_rule.get(field)
        if not field_rules or field_rules.get("method") is None:
            result[field] = None
            if cfg and cfg.get("debug"):
                print(f"[DEBUG] No rules for field '{field}' in vendor '{vendor_name}'")
            continue

        extracted_value = extract_field(result_page, field_rules, pil_img, cfg)
        if cfg and cfg.get("debug") and extracted_value:
            print(f"[DEBUG] Extracted {field}: {extracted_value}")

        # Special handling for Heidelberg tons field - convert to float
        if field == "tons" and extracted_value:
            try:
                result[field] = float(extracted_value)
            except (ValueError, TypeError):
                result[field] = extracted_value
        else:
            result[field] = extracted_value

    return result
