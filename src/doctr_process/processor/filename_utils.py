from pathlib import Path
from typing import Dict
import re


def parse_input_filename_fuzzy(filepath: str) -> Dict[str, str]:
    """Return basic metadata parsed from ``filepath``."""
    stem = Path(filepath).stem
    return {"base_name": stem}


def _join(parts):
    return "_".join(p for p in parts if p)


def _insert_vendor(base: str, vendor: str) -> str:
    """Return ``base`` with ``vendor`` inserted before the trailing ``*_WM``
    section if present."""
    m = re.match(r"^(.*)_([^_]+_WM)$", base, flags=re.IGNORECASE)
    if m:
        prefix, tail = m.groups()
        return f"{prefix}_{vendor}_{tail}"
    return _join([base, vendor])


def format_output_filename(vendor: str, page_count: int, meta: Dict[str, str], output_format: str) -> str:
    base = meta.get("base_name", "")
    name = _insert_vendor(base, vendor.upper())
    name = _join([name, str(page_count)])
    return f"{name}.{output_format}"


def format_output_filename_camel(vendor: str, page_count: int, meta: Dict[str, str], output_format: str) -> str:
    vendor_part = vendor.title().replace(" ", "")
    base = meta.get("base_name", "")
    name = _insert_vendor(base, vendor_part)
    name = _join([name, str(page_count)])
    return f"{name}.{output_format}"


def format_output_filename_lower(vendor: str, page_count: int, meta: Dict[str, str], output_format: str) -> str:
    vendor_part = vendor.lower().replace(" ", "_")
    base = meta.get("base_name", "").lower()
    name = _insert_vendor(base, vendor_part)
    name = _join([name, str(page_count)])
    return f"{name}.{output_format}"


def format_output_filename_snake(vendor: str, page_count: int, meta: Dict[str, str], output_format: str) -> str:
    vendor_part = vendor.replace(" ", "_").lower()
    base = meta.get("base_name", "").replace(" ", "_").lower()
    name = _insert_vendor(base, vendor_part)
    name = _join([name, str(page_count)])
    return f"{name}.{output_format}"
