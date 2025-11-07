"""Configuration loaders for YAML and JSON config files.

This module implements Issue #9: YAML config loaders
Provides centralized configuration loading with validation and error handling.

Supported Configuration Files:
    - synonyms.json: Synonym mappings for normalization
    - filename_schema.yml: Filename parsing schema
    - acceptance.yml: Acceptance criteria configuration
    - output_config.yml: Output configuration
    - vendor/*.yml: Vendor-specific extraction templates

Example:
    ```python
    from truck_tickets.config import ConfigLoader

    loader = ConfigLoader()

    # Load all configs
    synonyms = loader.load_synonyms()
    filename_schema = loader.load_filename_schema()
    acceptance = loader.load_acceptance_criteria()
    output_config = loader.load_output_config()

    # Load vendor template
    wm_template = loader.load_vendor_template("WM_LEWISVILLE")
    ```
"""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """Raised when configuration loading fails."""

    pass


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class ConfigLoader:
    """Centralized configuration loader with validation.

    This class provides a unified interface for loading all configuration
    files used by the truck ticket processing system.

    Attributes:
        config_dir: Path to configuration directory
        vendor_templates_dir: Path to vendor templates directory
        cache: Dictionary of cached configurations
    """

    def __init__(self, config_dir: Path | str | None = None):
        """Initialize configuration loader.

        Args:
            config_dir: Path to configuration directory (default: auto-detect)
        """
        if config_dir is None:
            # Auto-detect config directory
            config_dir = Path(__file__).parent
        else:
            config_dir = Path(config_dir)

        if not config_dir.exists():
            raise ConfigLoadError(f"Configuration directory not found: {config_dir}")

        self.config_dir = config_dir
        self.vendor_templates_dir = config_dir.parent / "templates" / "vendors"
        self.cache: dict[str, Any] = {}

        logger.info(f"ConfigLoader initialized with config_dir: {self.config_dir}")

    def _load_yaml(self, file_path: Path) -> dict[str, Any]:
        """Load YAML file with error handling.

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML content as dictionary

        Raises:
            ConfigLoadError: If file cannot be loaded
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = yaml.safe_load(f)

            if content is None:
                logger.warning(f"Empty YAML file: {file_path}")
                return {}

            logger.debug(f"Loaded YAML file: {file_path}")
            return content

        except FileNotFoundError as e:
            raise ConfigLoadError(f"Configuration file not found: {file_path}") from e
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Invalid YAML in {file_path}: {e}") from e
        except Exception as e:
            raise ConfigLoadError(f"Error loading {file_path}: {e}") from e

    def _load_json(self, file_path: Path) -> dict[str, Any]:
        """Load JSON file with error handling.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON content as dictionary

        Raises:
            ConfigLoadError: If file cannot be loaded
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                content = json.load(f)

            logger.debug(f"Loaded JSON file: {file_path}")
            return content

        except FileNotFoundError as e:
            raise ConfigLoadError(f"Configuration file not found: {file_path}") from e
        except json.JSONDecodeError as e:
            raise ConfigLoadError(f"Invalid JSON in {file_path}: {e}") from e
        except Exception as e:
            raise ConfigLoadError(f"Error loading {file_path}: {e}") from e

    def load_synonyms(self, use_cache: bool = True) -> dict[str, Any]:
        """Load synonym mappings from synonyms.json.

        Args:
            use_cache: Whether to use cached version if available

        Returns:
            Dictionary of synonym mappings

        Example:
            ```python
            synonyms = loader.load_synonyms()
            vendor_synonyms = synonyms["vendors"]
            material_synonyms = synonyms["materials"]
            ```
        """
        cache_key = "synonyms"

        if use_cache and cache_key in self.cache:
            logger.debug("Using cached synonyms")
            return self.cache[cache_key]

        file_path = self.config_dir / "synonyms.json"
        synonyms = self._load_json(file_path)

        # Validate structure
        required_keys = ["vendors", "materials", "sources", "destinations"]
        for key in required_keys:
            if key not in synonyms:
                logger.warning(f"Missing '{key}' in synonyms.json")
                synonyms[key] = {}

        self.cache[cache_key] = synonyms
        logger.info(f"Loaded synonyms: {len(synonyms)} categories")

        return synonyms

    def load_filename_schema(self, use_cache: bool = True) -> dict[str, Any]:
        """Load filename parsing schema from filename_schema.yml.

        Args:
            use_cache: Whether to use cached version if available

        Returns:
            Dictionary of filename schema configuration

        Example:
            ```python
            schema = loader.load_filename_schema()
            pattern = schema["pattern"]
            fields = schema["fields"]
            ```
        """
        cache_key = "filename_schema"

        if use_cache and cache_key in self.cache:
            logger.debug("Using cached filename schema")
            return self.cache[cache_key]

        file_path = self.config_dir / "filename_schema.yml"
        schema = self._load_yaml(file_path)

        # Validate structure
        if "pattern" not in schema:
            raise ConfigValidationError("filename_schema.yml missing 'pattern' field")

        self.cache[cache_key] = schema
        logger.info("Loaded filename schema")

        return schema

    def load_acceptance_criteria(self, use_cache: bool = True) -> dict[str, Any]:
        """Load acceptance criteria from acceptance.yml.

        Args:
            use_cache: Whether to use cached version if available

        Returns:
            Dictionary of acceptance criteria configuration

        Example:
            ```python
            acceptance = loader.load_acceptance_criteria()
            ticket_accuracy = acceptance["ticket_accuracy"]
            manifest_recall = acceptance["manifest_recall"]
            ```
        """
        cache_key = "acceptance"

        if use_cache and cache_key in self.cache:
            logger.debug("Using cached acceptance criteria")
            return self.cache[cache_key]

        file_path = self.config_dir / "acceptance.yml"
        acceptance = self._load_yaml(file_path)

        self.cache[cache_key] = acceptance
        logger.info("Loaded acceptance criteria")

        return acceptance

    def load_output_config(self, use_cache: bool = True) -> dict[str, Any]:
        """Load output configuration from output_config.yml.

        Args:
            use_cache: Whether to use cached version if available

        Returns:
            Dictionary of output configuration

        Example:
            ```python
            config = loader.load_output_config()
            db_enabled = config["database"]["enabled"]
            file_enabled = config["file_outputs"]["enabled"]
            ```
        """
        cache_key = "output_config"

        if use_cache and cache_key in self.cache:
            logger.debug("Using cached output config")
            return self.cache[cache_key]

        file_path = self.config_dir / "output_config.yml"
        config = self._load_yaml(file_path)

        # Validate structure
        required_keys = ["database", "file_outputs"]
        for key in required_keys:
            if key not in config:
                raise ConfigValidationError(
                    f"output_config.yml missing '{key}' section"
                )

        self.cache[cache_key] = config
        logger.info("Loaded output configuration")

        return config

    def load_vendor_template(
        self, vendor_name: str, use_cache: bool = True
    ) -> dict[str, Any]:
        """Load vendor-specific extraction template.

        Args:
            vendor_name: Vendor name (e.g., "WM_LEWISVILLE", "LDI_YARD")
            use_cache: Whether to use cached version if available

        Returns:
            Dictionary of vendor template configuration

        Raises:
            ConfigLoadError: If vendor template not found

        Example:
            ```python
            wm_template = loader.load_vendor_template("WM_LEWISVILLE")
            logo_keywords = wm_template["logo"]["text_keywords"]
            ticket_pattern = wm_template["ticket_number"]["regex"][0]["pattern"]
            ```
        """
        cache_key = f"vendor_template_{vendor_name}"

        if use_cache and cache_key in self.cache:
            logger.debug(f"Using cached vendor template: {vendor_name}")
            return self.cache[cache_key]

        file_path = self.vendor_templates_dir / f"{vendor_name}.yml"

        if not file_path.exists():
            raise ConfigLoadError(f"Vendor template not found: {vendor_name}")

        template = self._load_yaml(file_path)

        # Validate structure
        if "vendor" not in template:
            raise ConfigValidationError(
                f"Vendor template {vendor_name} missing 'vendor' section"
            )

        self.cache[cache_key] = template
        logger.info(f"Loaded vendor template: {vendor_name}")

        return template

    def list_vendor_templates(self) -> list[str]:
        """List all available vendor templates.

        Returns:
            List of vendor template names (without .yml extension)

        Example:
            ```python
            vendors = loader.list_vendor_templates()
            print(f"Available vendors: {vendors}")
            # Output: ['WM_LEWISVILLE', 'LDI_YARD', 'POST_OAK_PIT']
            ```
        """
        if not self.vendor_templates_dir.exists():
            logger.warning(
                f"Vendor templates directory not found: {self.vendor_templates_dir}"
            )
            return []

        templates = [
            f.stem for f in self.vendor_templates_dir.glob("*.yml") if f.is_file()
        ]

        logger.debug(f"Found {len(templates)} vendor templates")
        return sorted(templates)

    def load_all_vendor_templates(
        self, use_cache: bool = True
    ) -> dict[str, dict[str, Any]]:
        """Load all vendor templates.

        Args:
            use_cache: Whether to use cached versions if available

        Returns:
            Dictionary mapping vendor names to template configurations

        Example:
            ```python
            all_templates = loader.load_all_vendor_templates()
            for vendor_name, template in all_templates.items():
                print(f"Loaded template for: {vendor_name}")
            ```
        """
        vendors = self.list_vendor_templates()
        templates = {}

        for vendor_name in vendors:
            try:
                templates[vendor_name] = self.load_vendor_template(
                    vendor_name, use_cache
                )
            except ConfigLoadError as e:
                logger.error(f"Failed to load template for {vendor_name}: {e}")

        logger.info(f"Loaded {len(templates)} vendor templates")
        return templates

    def reload_all(self) -> None:
        """Reload all configurations, clearing cache.

        This forces all configurations to be reloaded from disk,
        useful when config files have been modified.
        """
        self.cache.clear()
        logger.info("Cleared configuration cache")

    def get_config_paths(self) -> dict[str, Path]:
        """Get paths to all configuration files.

        Returns:
            Dictionary mapping config names to file paths

        Example:
            ```python
            paths = loader.get_config_paths()
            print(f"Synonyms: {paths['synonyms']}")
            print(f"Output config: {paths['output_config']}")
            ```
        """
        return {
            "synonyms": self.config_dir / "synonyms.json",
            "filename_schema": self.config_dir / "filename_schema.yml",
            "acceptance": self.config_dir / "acceptance.yml",
            "output_config": self.config_dir / "output_config.yml",
            "vendor_templates": self.vendor_templates_dir,
        }

    def validate_all_configs(self) -> dict[str, bool]:
        """Validate all configuration files.

        Returns:
            Dictionary mapping config names to validation status (True = valid)

        Example:
            ```python
            results = loader.validate_all_configs()
            for config_name, is_valid in results.items():
                status = "✓" if is_valid else "✗"
                print(f"{status} {config_name}")
            ```
        """
        results = {}

        # Test each config
        configs_to_test = [
            ("synonyms", self.load_synonyms),
            ("filename_schema", self.load_filename_schema),
            ("acceptance_criteria", self.load_acceptance_criteria),
            ("output_config", self.load_output_config),
        ]

        for config_name, load_func in configs_to_test:
            try:
                load_func(use_cache=False)
                results[config_name] = True
                logger.info(f"✓ {config_name} is valid")
            except Exception as e:
                results[config_name] = False
                logger.error(f"✗ {config_name} is invalid: {e}")

        # Test vendor templates
        vendor_templates = self.list_vendor_templates()
        for vendor_name in vendor_templates:
            try:
                self.load_vendor_template(vendor_name, use_cache=False)
                results[f"vendor_template_{vendor_name}"] = True
                logger.info(f"✓ Vendor template {vendor_name} is valid")
            except Exception as e:
                results[f"vendor_template_{vendor_name}"] = False
                logger.error(f"✗ Vendor template {vendor_name} is invalid: {e}")

        return results


# Convenience functions for quick access
_default_loader: ConfigLoader | None = None


def get_default_loader() -> ConfigLoader:
    """Get the default configuration loader instance.

    Returns:
        Singleton ConfigLoader instance

    Example:
        ```python
        from truck_tickets.config import get_default_loader

        loader = get_default_loader()
        synonyms = loader.load_synonyms()
        ```
    """
    global _default_loader
    if _default_loader is None:
        _default_loader = ConfigLoader()
    return _default_loader


def load_synonyms() -> dict[str, Any]:
    """Convenience function to load synonyms using default loader."""
    return get_default_loader().load_synonyms()


def load_filename_schema() -> dict[str, Any]:
    """Convenience function to load filename schema using default loader."""
    return get_default_loader().load_filename_schema()


def load_acceptance_criteria() -> dict[str, Any]:
    """Convenience function to load acceptance criteria using default loader."""
    return get_default_loader().load_acceptance_criteria()


def load_output_config() -> dict[str, Any]:
    """Convenience function to load output config using default loader."""
    return get_default_loader().load_output_config()


def load_vendor_template(vendor_name: str) -> dict[str, Any]:
    """Convenience function to load vendor template using default loader."""
    return get_default_loader().load_vendor_template(vendor_name)
