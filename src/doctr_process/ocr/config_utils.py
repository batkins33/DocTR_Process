"""Configuration helpers for loading YAML files and page counts."""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from doctr_process.utils.resources import read_text, as_path

__all__ = ["load_extraction_rules", "load_config", "count_total_pages"]


def load_extraction_rules(path: str = None):
    """Load field extraction rules from a YAML file.
    
    Args:
        path: Optional path to a custom extraction rules file. If None, loads
              the default extraction_rules.yaml from the package configs.
    """
    if path is None:
        # Use package resource loading for default config
        content = read_text("extraction_rules.yaml")
        return yaml.safe_load(content)
    else:
        # Use custom path for backwards compatibility
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


def load_config(config_path: str) -> dict:
    """Load configuration from a YAML file.
    
    Args:
        config_path: Path to config file. Can be:
                    - A filename like "config.yaml" to load from package configs
                    - A full filesystem path for custom configs
    """
    load_dotenv()  # Loads .env file at project root
    
    # Check if this looks like just a filename (no path separators)
    config_path_obj = Path(config_path)
    if len(config_path_obj.parts) == 1:
        # Just a filename - load from package resources
        content = read_text(config_path)
        cfg = yaml.safe_load(content)
    else:
        # Full path - use traditional file loading with security check
        config_path_obj = config_path_obj.resolve()
        # For backwards compatibility, still check against old CONFIG_DIR if it exists
        try:
            # Try to reconstruct old CONFIG_DIR for security check
            old_config_dir = Path(__file__).resolve().parents[2] / "configs"
            if old_config_dir.exists() and not str(config_path_obj).startswith(str(old_config_dir.resolve())):
                raise ValueError("Config path is outside the allowed config directory.")
        except:
            # If we can't construct the old path, just proceed (likely in installed package)
            pass
            
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
