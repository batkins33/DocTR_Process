"""Configuration helpers for loading YAML files and page counts."""

import yaml

__all__ = ["load_extraction_rules", "load_config", "count_total_pages"]


def load_extraction_rules(path: str = "extraction_rules.yaml"):
    """Load field extraction rules from a YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(path: str = "config.yaml"):
    """Load application configuration from ``path``."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def count_total_pages(pdf_files, cfg):
    """Return the total page count across ``pdf_files``."""
    from pdf2image import pdfinfo_from_path

    total_pages = 0
    for pdf_file in pdf_files:
        info = pdfinfo_from_path(pdf_file, poppler_path=cfg.get("poppler_path"))
        total_pages += info["Pages"]
    return total_pages
