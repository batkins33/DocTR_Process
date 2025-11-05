"""Filename parsing utilities for structured ticket PDFs.

Supports the structured format described in config/filename_schema.yml:
    {JOB}__{DATE}__{AREA}__{FLOW}__{MATERIAL}__{VENDOR}.pdf

Also provides graceful fallback when the YAML file is unavailable.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
import re

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency during tests
    yaml = None  # type: ignore


STRUCTURED_DELIM = "__"
DATE_FORMAT = "%Y-%m-%d"
JOB_CODE_RE = re.compile(r"^\d{2}-\d{3}$")


@dataclass
class FilenameMeta:
    job_code: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    area: Optional[str] = None
    flow: Optional[str] = None
    material: Optional[str] = None
    vendor: Optional[str] = None

    def as_dict(self) -> Dict[str, Optional[str]]:
        return {
            "job_code": self.job_code,
            "date": self.date,
            "area": self.area,
            "flow": self.flow,
            "material": self.material,
            "vendor": self.vendor,
        }


def _parse_date(value: str) -> Optional[str]:
    try:
        dt = datetime.strptime(value.strip(), DATE_FORMAT)
        # Basic guardrails (aligns with date_extractor reasonable range)
        if 2020 <= dt.year <= 2030:
            return dt.strftime(DATE_FORMAT)
        return None
    except Exception:
        return None


def parse_structured(stem: str) -> FilenameMeta:
    """Parse a structured filename stem using the double-underscore convention.

    Example stem: 24-105__2025-10-17__SPG__EXPORT__CLASS_2_CONTAMINATED__WASTE_MANAGEMENT_LEWISVILLE
    """
    parts = stem.split(STRUCTURED_DELIM)
    meta = FilenameMeta()

    if len(parts) < 2:
        return meta

    # Map common positions from schema
    # 0: job_code, 1: date, 2: area, 3: flow, 4: material, 5: vendor
    if len(parts) >= 1 and JOB_CODE_RE.match(parts[0]):
        meta.job_code = parts[0].strip()
    if len(parts) >= 2:
        meta.date = _parse_date(parts[1])
    if len(parts) >= 3 and parts[2].strip():
        meta.area = parts[2].strip()
    if len(parts) >= 4 and parts[3].strip():
        meta.flow = parts[3].strip().upper()
    if len(parts) >= 5 and parts[4].strip():
        meta.material = parts[4].strip().upper()
    if len(parts) >= 6 and parts[5].strip():
        meta.vendor = parts[5].strip().upper()

    return meta


def parse_filename(file_path: str, config_path: Optional[str] = None) -> Dict[str, Optional[str]]:
    """Parse filename into metadata dict. Does not raise.

    Tries YAML-driven parsing if available, falls back to structured parser.
    """
    try:
        stem = Path(file_path).stem
        # Try YAML config if available (not strictly necessary for structured)
        if config_path and yaml is not None:
            # Load for future extensibility; current implementation uses structured default
            with open(config_path, "r", encoding="utf-8") as f:
                _ = yaml.safe_load(f)
        meta = parse_structured(stem)
        return meta.as_dict()
    except Exception:
        return FilenameMeta().as_dict()
