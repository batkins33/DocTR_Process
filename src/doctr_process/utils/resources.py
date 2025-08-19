"""Resource access utilities using importlib.resources."""

import sys
from pathlib import Path
from typing import Union

if sys.version_info >= (3, 9):
    from importlib.resources import files, as_file
else:
    from importlib_resources import files, as_file


def read_text(name: str) -> str:
    """Read text content from a config file.
    
    Args:
        name: Name of the config file (e.g., 'config.yaml')
        
    Returns:
        File content as string
    """
    config_files = files("doctr_process.configs")
    return (config_files / name).read_text(encoding="utf-8")


def as_path(name: str):
    """Get a context manager for a config file path.
    
    Args:
        name: Name of the config file (e.g., 'config.yaml')
        
    Returns:
        Context manager that yields a Path object
    """
    config_files = files("doctr_process.configs")
    return as_file(config_files / name)