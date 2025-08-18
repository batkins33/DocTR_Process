"""Resource loading utilities using importlib.resources."""

from importlib import resources
from pathlib import Path
from typing import Union
import contextlib

__all__ = ["read_text", "as_path"]

def read_text(name: str) -> str:
    """Read text content from a config file in the configs package.
    
    Args:
        name: Name of the config file (e.g., "config.yaml", "extraction_rules.yaml")
        
    Returns:
        The text content of the file
        
    Raises:
        FileNotFoundError: If the named file doesn't exist in configs/
    """
    try:
        # Use importlib.resources to read from the configs package
        configs_package = resources.files("doctr_process.configs")
        config_file = configs_package / name
        return config_file.read_text(encoding="utf-8")
    except Exception as e:
        raise FileNotFoundError(f"Config file '{name}' not found in package configs/") from e


@contextlib.contextmanager
def as_path(name: str):
    """Get a filesystem path to a config file, extracting if needed.
    
    Args:
        name: Name of the config file (e.g., "config.yaml", "extraction_rules.yaml")
        
    Yields:
        Path: A Path object pointing to the config file
        
    Raises:
        FileNotFoundError: If the named file doesn't exist in configs/
    """
    try:
        # Use importlib.resources to get a path to the file
        configs_package = resources.files("doctr_process.configs")
        config_file = configs_package / name
        
        # Use as_file() context manager to get a real filesystem path
        with resources.as_file(config_file) as path:
            yield path
    except Exception as e:
        raise FileNotFoundError(f"Config file '{name}' not found in package configs/") from e