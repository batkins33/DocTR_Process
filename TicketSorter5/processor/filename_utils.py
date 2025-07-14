import logging
import re
from datetime import datetime
from pathlib import Path


def normalize_field(s):
    """Normalize and CamelCase each part of a string."""
    s = re.sub(r"[^\w\s-]", "", s)  # Remove special characters except dashes
    s = re.sub(r"\s+", " ", s)  # Collapse multiple spaces
    return "".join(word.capitalize() for word in s.strip().split())


def parse_input_filename(filename):
    base = Path(filename).stem
    parts = base.split("_")

    if len(parts) < 3:
        return {}

    job_id = parts[0]
    raw_date = parts[1]
    formatted_date = "UNKNOWN"
    for fmt in ("%Y-%m-%d", "%m-%d-%Y"):
        try:
            parsed_date = datetime.strptime(raw_date, fmt)
            formatted_date = parsed_date.strftime("%Y-%m-%d")
            break
        except ValueError:
            continue

    return {
        "JOB_ID": job_id,
        "DATE": formatted_date,
        "MATERIAL": parts[2] if len(parts) > 2 else "UNKNOWN",
        "SOURCE": parts[3] if len(parts) > 3 else "UNKNOWN",
        "DESTINATION": parts[4] if len(parts) > 4 else "UNKNOWN",
    }


def parse_input_filename_fuzzy(filename):
    base = Path(filename).stem
    base = re.sub(r" - Copy.*$", "", base, flags=re.IGNORECASE)
    parts = base.split("_")

    print("Parsed parts:", parts)  # ✅ Add this
    logging.debug(f"Parsed filename parts: {parts}")  # ✅ logs instead of print

    job_id = parts[0] if len(parts) > 0 else "UNKNOWN"
    raw_date = parts[1] if len(parts) > 1 else "UNKNOWN"
    formatted_date = "UNKNOWN"
    for fmt in ("%Y-%m-%d", "%m-%d-%Y", "%Y%m%d"):
        try:
            parsed_date = datetime.strptime(raw_date, fmt)
            formatted_date = parsed_date.strftime("%Y-%m-%d")
            break
        except ValueError:
            continue

    return {
        "JOB_ID": job_id,
        "DATE": formatted_date,
        "MATERIAL": normalize_field(parts[2]) if len(parts) > 2 else "Unknown",
        "SOURCE": normalize_field(parts[3]) if len(parts) > 3 else "Unknown",
        "DESTINATION": normalize_field(parts[4]) if len(parts) > 4 else "Unknown",
    }


def format_output_filename(vendor, page_count, meta, output_format):
    """Legacy ALL CAPS format."""
    parts = [
        meta["JOB_ID"],
        meta["DATE"],
        vendor,
        meta["MATERIAL"],
        meta["SOURCE"],
        meta["DESTINATION"],
        str(page_count),
    ]
    return "_".join(parts).upper() + f".{output_format.lower()}"


def format_output_filename_camel(vendor, page_count, meta, output_format):
    """CamelCase vendor and normalized fields."""
    parts = [
        meta["JOB_ID"],
        meta["DATE"],
        normalize_field(vendor),
        normalize_field(meta["MATERIAL"]),
        normalize_field(meta["SOURCE"]),
        normalize_field(meta["DESTINATION"]),
        str(page_count),
    ]
    return "_".join(parts) + f".{output_format.lower()}"


def format_output_filename_snake(vendor, page_count, meta, output_format):
    """snake_case vendor and fields."""

    def snake_case(s):
        return s.replace(" ", "_").replace("-", "_").lower()

    parts = [
        meta["JOB_ID"],
        meta["DATE"],
        snake_case(vendor),
        snake_case(meta["MATERIAL"]),
        snake_case(meta["SOURCE"]),
        snake_case(meta["DESTINATION"]),
        str(page_count),
    ]
    return "_".join(parts) + f".{output_format.lower()}"


def format_output_filename_lower(vendor, page_count, meta, output_format):
    """lowercase version of CamelCase output."""
    return format_output_filename_camel(vendor, page_count, meta, output_format).lower()
