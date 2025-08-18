"""Configuration helpers for loading YAML files and page counts."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

__all__ = ["load_extraction_rules", "load_config", "count_total_pages"]

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT_DIR / "configs"


def load_extraction_rules(path: str = str(CONFIG_DIR / "extraction_rules.yaml")):
    """Load field extraction rules from a YAML file."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config(config_path: str) -> dict:
    load_dotenv()  # Loads .env file at project root
    # Prevent path traversal by ensuring config_path is inside CONFIG_DIR
    config_path_obj = Path(config_path).resolve()
    if not str(config_path_obj).startswith(str(CONFIG_DIR.resolve())):
        raise ValueError("Config path is outside the allowed config directory.")
    with open(config_path_obj, "r") as f:
        cfg = yaml.safe_load(f)
    # Override config values with environment variables if present
    for k in cfg:
        env_val = os.getenv(k.upper())
        if env_val is not None:
            cfg[k] = env_val
    return cfg


def count_total_pages(pdf_files, cfg):
    """Return the total page count across ``pdf_files``."""
    from pdf2image import pdfinfo_from_path
    import os
    from PIL import Image

    total_pages = 0
    for pdf_file in pdf_files:
        ext = os.path.splitext(pdf_file)[1].lower()
        if ext == ".pdf":
            info = pdfinfo_from_path(pdf_file, poppler_path=cfg.get("poppler_path"))
            total_pages += info.get("Pages", 1)
        else:
            # For images, treat as single page unless multi-page TIFF
            try:
                with Image.open(pdf_file) as img:
                    if hasattr(img, "n_frames"):
                        total_pages += img.n_frames
                    else:
                        total_pages += 1
            except Exception:
                total_pages += 1
    return total_pages
