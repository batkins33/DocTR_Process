"""Configuration helpers for loading YAML files and page counts."""

import os
from pathlib import Path

import yaml

__all__ = ["load_extraction_rules", "load_config", "count_total_pages"]

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "configs"


def load_extraction_rules(path: str = str(CONFIG_DIR / "extraction_rules.yaml")):
    """Load field extraction rules from a YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(path: str = str(CONFIG_DIR / "config.yaml")):
    """Load application configuration from ``path`` and merge env credentials."""
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Load SharePoint credentials from environment if available
    sp = cfg.get("sharepoint_config", {})
    creds = sp.get("credentials", {}) or {}
    env_user = os.getenv("SHAREPOINT_USERNAME")
    env_pass = os.getenv("SHAREPOINT_PASSWORD")
    if env_user:
        creds["username"] = env_user
    if env_pass:
        creds["password"] = env_pass
    if creds:
        sp["credentials"] = creds
        cfg["sharepoint_config"] = sp
    return cfg


def count_total_pages(pdf_files, cfg):
    """Return the total page count across ``pdf_files``."""
    from pdf2image import pdfinfo_from_path

    total_pages = 0
    for pdf_file in pdf_files:
        info = pdfinfo_from_path(pdf_file, poppler_path=cfg.get("poppler_path"))
        total_pages += info["Pages"]
    return total_pages
