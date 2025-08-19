"""Helpers for parsing and formatting pipeline file names."""

import re
from pathlib import Path
from typing import Dict

# Compile regex patterns once for better performance
_TRAILING_DIGITS = re.compile(r"_(\d+)$")
_UNSAFE_CHARS = re.compile(r'[<>:"/\|?*\x00-\x1f]')
_PREFIX_TAIL = re.compile(r"^([^_]+_[^_]+)_(.*)$")
_WM_SUFFIX = re.compile(r"^(.*)_([^_]+_WM)$", re.IGNORECASE)


def parse_input_filename_fuzzy(filepath: str) -> Dict[str, str]:
    """Return basic metadata parsed from ``filepath``.

    The application's input files may optionally include a trailing page
    count segment (e.g. ``..._145``).  When present this count reflects the
    total number of tickets in the original scan, but the final vendor or
    combined outputs should use their own page counts instead.  To avoid
    propagating the stale count, strip any terminal ``_NNN`` portion from the
    stem before further processing.
    """
    stem = Path(filepath).stem
    # Remove a trailing ``_123`` style segment if it exists so that output
    # file names can append their own accurate page counts.
    stem = _TRAILING_DIGITS.sub("", stem)
    return {"base_name": stem}


def sanitize_vendor_name(vendor: str) -> str:
    """Return a filesystem-friendly vendor name.

    Currently, this simply replaces underscores with periods so that a vendor
    such as ``WL_Reid`` becomes ``WL.Reid``.  Additional normalization rules
    can be added here if needed.
    """

    return vendor.replace("_", ".")


def _join(parts):
    return "_".join(p for p in parts if p)


def _insert_vendor(base: str, vendor: str) -> str:
    """Insert ``vendor`` into ``base`` according to naming convention.

    Input files follow a ``JobID_Date_material_source_destination`` pattern and
    vendor specific outputs should insert the vendor name after the date
    portion.  If the pattern cannot be detected, fall back to inserting before
    a trailing ``*_WM`` segment or simply appending the vendor.
    """
    # Sanitize inputs once to prevent XSS and ensure filesystem safety
    vendor = _UNSAFE_CHARS.sub('', vendor)
    base = _UNSAFE_CHARS.sub('', base)
    
    # Prefer inserting after the first two underscore separated segments
    m = _PREFIX_TAIL.match(base)
    if m:
        prefix, tail = m.groups()
        return f"{prefix}_{vendor}_{tail}"

    # Backwards compatibility: insert before a trailing ``*_WM`` segment
    m = _WM_SUFFIX.match(base)
    if m:
        prefix, tail = m.groups()
        return f"{prefix}_{vendor}_{tail}"

    # Fallback to simple concatenation
    return _join([base, vendor])


def format_output_filename(
        vendor: str, page_count: int, meta: Dict[str, str], output_format: str
) -> str:
    base = meta.get("base_name", "")
    name = _insert_vendor(base, vendor.upper())
    name = _join([name, str(page_count)])
    return f"{name}.{output_format}"


def format_output_filename_camel(
        vendor: str, page_count: int, meta: Dict[str, str], output_format: str
) -> str:
    vendor_part = vendor.title().replace(" ", "")
    base = meta.get("base_name", "")
    name = _insert_vendor(base, vendor_part)
    name = _join([name, str(page_count)])
    return f"{name}.{output_format}"


def format_output_filename_lower(
        vendor: str, page_count: int, meta: Dict[str, str], output_format: str
) -> str:
    vendor_part = vendor.lower().replace(" ", "_")
    base = meta.get("base_name", "").lower()
    name = _insert_vendor(base, vendor_part)
    name = _join([name, str(page_count)])
    return f"{name}.{output_format}"


def format_output_filename_snake(
        vendor: str, page_count: int, meta: Dict[str, str], output_format: str
) -> str:
    vendor_part = vendor.replace(" ", "_").lower()
    base = meta.get("base_name", "").replace(" ", "_").lower()
    name = _insert_vendor(base, vendor_part)
    name = _join([name, str(page_count)])
    return f"{name}.{output_format}"


def format_output_filename_preserve(
        vendor: str, page_count: int, meta: Dict[str, str], output_format: str
) -> str:
    """Return an output filename using ``vendor`` as-is."""

    base = meta.get("base_name", "")
    name = _insert_vendor(base, vendor)
    name = _join([name, str(page_count)])
    return f"{name}.{output_format}"
