"""Configuration loading and management.

This package provides centralized configuration loading for all YAML and JSON
configuration files used by the truck ticket processing system.

Example:
    ```python
    from truck_tickets.config import ConfigLoader, load_synonyms

    # Use default loader with convenience functions
    synonyms = load_synonyms()
    output_config = load_output_config()

    # Or create custom loader
    loader = ConfigLoader(config_dir="/path/to/configs")
    acceptance = loader.load_acceptance_criteria()
    ```
"""

from .config_loader import (
    ConfigLoader,
    ConfigLoadError,
    ConfigValidationError,
    get_default_loader,
    load_acceptance_criteria,
    load_filename_schema,
    load_output_config,
    load_synonyms,
    load_vendor_template,
)

__all__ = [
    "ConfigLoader",
    "ConfigLoadError",
    "ConfigValidationError",
    "get_default_loader",
    "load_synonyms",
    "load_filename_schema",
    "load_acceptance_criteria",
    "load_output_config",
    "load_vendor_template",
]
