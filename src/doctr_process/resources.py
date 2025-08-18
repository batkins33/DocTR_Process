"""Resource access utilities using importlib.resources for packaged configs and assets."""

import sys
from pathlib import Path
from typing import Union

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files


def get_config_path(filename: str) -> Path:
    """Get path to a configuration file using importlib.resources.
    
    Args:
        filename: Name of the config file (e.g., 'config.yaml')
        
    Returns:
        Path to the configuration file
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
    """
    try:
        config_files = files("doctr_process.configs")
        config_path = config_files / filename
        if config_path.is_file():
            return Path(str(config_path))
        raise FileNotFoundError(f"Config file not found: {filename}")
    except (ImportError, AttributeError):
        # Fallback for development/editable installs
        fallback_path = Path(__file__).parent / "configs" / filename
        if fallback_path.exists():
            return fallback_path
        raise FileNotFoundError(f"Config file not found: {filename}")


def get_asset_path(filename: str) -> Path:
    """Get path to an asset file using importlib.resources.
    
    Args:
        filename: Name of the asset file
        
    Returns:
        Path to the asset file
        
    Raises:
        FileNotFoundError: If the asset file doesn't exist
    """
    try:
        asset_files = files("doctr_process.assets")
        asset_path = asset_files / filename
        if asset_path.is_file():
            return Path(str(asset_path))
        raise FileNotFoundError(f"Asset file not found: {filename}")
    except (ImportError, AttributeError):
        # Fallback for development/editable installs
        fallback_path = Path(__file__).parent / "assets" / filename
        if fallback_path.exists():
            return fallback_path
        raise FileNotFoundError(f"Asset file not found: {filename}")


def read_config_text(filename: str) -> str:
    """Read configuration file content as text.
    
    Args:
        filename: Name of the config file
        
    Returns:
        File content as string
    """
    try:
        config_files = files("doctr_process.configs")
        return (config_files / filename).read_text(encoding="utf-8")
    except (ImportError, AttributeError):
        # Fallback for development/editable installs
        fallback_path = Path(__file__).parent / "configs" / filename
        return fallback_path.read_text(encoding="utf-8")