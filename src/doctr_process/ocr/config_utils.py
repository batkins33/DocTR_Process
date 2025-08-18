"""Configuration helpers for loading YAML files and page counts."""

import os
from pathlib import Path

from yaml import safe_load, YAMLError
from dotenv import load_dotenv

from doctr_process.resources import get_config_path, read_config_text

__all__ = ["load_extraction_rules", "load_config", "count_total_pages"]


def _validate_config_path(path: str, file_type: str) -> Path:
    """Validate config file path to prevent traversal attacks."""
    path_obj = Path(path).resolve()
    
    import tempfile
    temp_dir = Path(tempfile.gettempdir()).resolve()
    cwd = Path.cwd().resolve()
    
    # Allow project directory (where configs are stored)
    try:
        project_root = Path(__file__).resolve().parents[3]  # Go up from src/doctr_process/ocr/
        allowed_paths = [temp_dir, cwd, project_root]
    except (IndexError, OSError):
        allowed_paths = [temp_dir, cwd]
    
    if not any(str(path_obj).startswith(str(allowed_path)) for allowed_path in allowed_paths):
        raise ValueError(f"{file_type} path outside allowed directories: {path}")
    
    return path_obj


def load_extraction_rules(path: str = None):
    """Load field extraction rules from a YAML file.
    
    Args:
        path: Optional path to extraction rules file. If None, uses packaged default.
    """
    if path is None:
        # Use packaged resource
        content = read_config_text("extraction_rules.yaml")
        return safe_load(content)
    else:
        # Validate and use provided path for custom configs
        path_obj = _validate_config_path(path, "Extraction rules")
            
        try:
            with open(path_obj, "r", encoding="utf-8") as f:
                return safe_load(f)
        except (FileNotFoundError, PermissionError) as e:
            raise FileNotFoundError(f"Cannot load extraction rules from {path}: {e}") from e
        except YAMLError as e:
            raise ValueError(f"Invalid YAML in extraction rules file {path}: {e}") from e


def load_config(config_path: str = None) -> dict:
    """Load configuration from file or packaged resource.
    
    Args:
        config_path: Optional path to config file. If None, uses packaged default.
        
    Returns:
        Configuration dictionary with environment variable overrides applied
    """
    load_dotenv()  # Loads .env file at project root
    
    if config_path is None:
        # Use packaged resource
        content = read_config_text("config.yaml")
        cfg = safe_load(content)
    else:
        # Validate custom config path for security
        config_path_obj = _validate_config_path(config_path, "Config")
            
        try:
            with open(config_path_obj, "r", encoding="utf-8") as f:
                cfg = safe_load(f)
        except (FileNotFoundError, PermissionError) as e:
            raise FileNotFoundError(f"Cannot load config from {config_path}: {e}") from e
        except YAMLError as e:
            raise ValueError(f"Invalid YAML in config file {config_path}: {e}") from e
    
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
            except (OSError, IOError) as e:
                # Log error for debugging but continue processing
                import logging
                logging.warning("Could not process image file %s: %s", pdf_file, e)
                total_pages += 1
    return total_pages
