"""Unit tests for configuration loaders.

Tests Issue #9: YAML config loaders
"""

import tempfile
from pathlib import Path

import pytest
from src.truck_tickets.config import (
    ConfigLoader,
    ConfigLoadError,
    get_default_loader,
    load_acceptance_criteria,
    load_filename_schema,
    load_output_config,
    load_synonyms,
    load_vendor_template,
)


class TestConfigLoader:
    """Test ConfigLoader class."""

    def test_init_with_default_path(self):
        """Initialize with default config directory."""
        loader = ConfigLoader()
        assert loader.config_dir.exists()
        assert loader.vendor_templates_dir.exists()

    def test_init_with_custom_path(self):
        """Initialize with custom config directory."""
        config_dir = (
            Path(__file__).parent.parent.parent / "src" / "truck_tickets" / "config"
        )
        loader = ConfigLoader(config_dir=config_dir)
        assert loader.config_dir == config_dir

    def test_init_with_invalid_path(self):
        """Initialize with invalid path should raise error."""
        with pytest.raises(ConfigLoadError):
            ConfigLoader(config_dir="/nonexistent/path")

    def test_load_synonyms(self):
        """Load synonyms.json successfully."""
        loader = ConfigLoader()
        synonyms = loader.load_synonyms()

        assert isinstance(synonyms, dict)
        assert "vendors" in synonyms
        assert "materials" in synonyms
        assert "sources" in synonyms
        assert "destinations" in synonyms

    def test_load_synonyms_caching(self):
        """Synonyms should be cached after first load."""
        loader = ConfigLoader()

        # First load
        synonyms1 = loader.load_synonyms()

        # Second load (should use cache)
        synonyms2 = loader.load_synonyms(use_cache=True)

        assert synonyms1 is synonyms2  # Same object reference

    def test_load_synonyms_no_cache(self):
        """Load synonyms without caching."""
        loader = ConfigLoader()

        synonyms1 = loader.load_synonyms(use_cache=False)
        synonyms2 = loader.load_synonyms(use_cache=False)

        assert synonyms1 == synonyms2  # Same content
        assert synonyms1 is not synonyms2  # Different objects

    def test_load_filename_schema(self):
        """Load filename_schema.yml successfully."""
        loader = ConfigLoader()
        schema = loader.load_filename_schema()

        assert isinstance(schema, dict)
        assert "pattern" in schema

    def test_load_acceptance_criteria(self):
        """Load acceptance.yml successfully."""
        loader = ConfigLoader()
        acceptance = loader.load_acceptance_criteria()

        assert isinstance(acceptance, dict)

    def test_load_output_config(self):
        """Load output_config.yml successfully."""
        loader = ConfigLoader()
        config = loader.load_output_config()

        assert isinstance(config, dict)
        assert "database" in config
        assert "file_outputs" in config

    def test_load_vendor_template(self):
        """Load vendor template successfully."""
        loader = ConfigLoader()
        template = loader.load_vendor_template("WM_LEWISVILLE")

        assert isinstance(template, dict)
        assert "vendor" in template

    def test_load_vendor_template_not_found(self):
        """Loading non-existent vendor template should raise error."""
        loader = ConfigLoader()

        with pytest.raises(ConfigLoadError):
            loader.load_vendor_template("NONEXISTENT_VENDOR")

    def test_list_vendor_templates(self):
        """List all vendor templates."""
        loader = ConfigLoader()
        vendors = loader.list_vendor_templates()

        assert isinstance(vendors, list)
        assert len(vendors) > 0
        assert "WM_LEWISVILLE" in vendors

    def test_load_all_vendor_templates(self):
        """Load all vendor templates."""
        loader = ConfigLoader()
        templates = loader.load_all_vendor_templates()

        assert isinstance(templates, dict)
        assert len(templates) > 0
        assert "WM_LEWISVILLE" in templates

    def test_reload_all(self):
        """Reload all configurations."""
        loader = ConfigLoader()

        # Load and cache
        loader.load_synonyms()
        assert len(loader.cache) > 0

        # Reload
        loader.reload_all()
        assert len(loader.cache) == 0

    def test_get_config_paths(self):
        """Get paths to all configuration files."""
        loader = ConfigLoader()
        paths = loader.get_config_paths()

        assert isinstance(paths, dict)
        assert "synonyms" in paths
        assert "filename_schema" in paths
        assert "acceptance" in paths
        assert "output_config" in paths
        assert "vendor_templates" in paths

    def test_validate_all_configs(self):
        """Validate all configuration files."""
        loader = ConfigLoader()
        results = loader.validate_all_configs()

        assert isinstance(results, dict)
        assert results["synonyms"] is True
        assert results["filename_schema"] is True
        assert results["acceptance_criteria"] is True
        assert results["output_config"] is True


class TestConfigLoaderErrorHandling:
    """Test error handling in ConfigLoader."""

    def test_load_invalid_yaml(self):
        """Loading invalid YAML should raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create invalid YAML file
            invalid_yaml = config_dir / "test.yml"
            invalid_yaml.write_text("invalid: yaml: content:")

            loader = ConfigLoader(config_dir=config_dir)

            with pytest.raises(ConfigLoadError):
                loader._load_yaml(invalid_yaml)

    def test_load_invalid_json(self):
        """Loading invalid JSON should raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)

            # Create invalid JSON file
            invalid_json = config_dir / "test.json"
            invalid_json.write_text("{invalid json}")

            loader = ConfigLoader(config_dir=config_dir)

            with pytest.raises(ConfigLoadError):
                loader._load_json(invalid_json)

    def test_load_missing_file(self):
        """Loading missing file should raise error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir)
            loader = ConfigLoader(config_dir=config_dir)

            with pytest.raises(ConfigLoadError):
                loader._load_yaml(config_dir / "nonexistent.yml")


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_default_loader(self):
        """Get default loader instance."""
        loader1 = get_default_loader()
        loader2 = get_default_loader()

        assert loader1 is loader2  # Singleton

    def test_load_synonyms_convenience(self):
        """Load synonyms using convenience function."""
        synonyms = load_synonyms()
        assert isinstance(synonyms, dict)

    def test_load_filename_schema_convenience(self):
        """Load filename schema using convenience function."""
        schema = load_filename_schema()
        assert isinstance(schema, dict)

    def test_load_acceptance_criteria_convenience(self):
        """Load acceptance criteria using convenience function."""
        acceptance = load_acceptance_criteria()
        assert isinstance(acceptance, dict)

    def test_load_output_config_convenience(self):
        """Load output config using convenience function."""
        config = load_output_config()
        assert isinstance(config, dict)

    def test_load_vendor_template_convenience(self):
        """Load vendor template using convenience function."""
        template = load_vendor_template("WM_LEWISVILLE")
        assert isinstance(template, dict)


class TestConfigLoaderIntegration:
    """Integration tests with real config files."""

    def test_load_all_configs(self):
        """Load all configuration files successfully."""
        loader = ConfigLoader()

        # Load all configs
        synonyms = loader.load_synonyms()
        filename_schema = loader.load_filename_schema()
        acceptance = loader.load_acceptance_criteria()
        output_config = loader.load_output_config()

        # Verify all loaded successfully
        assert synonyms is not None
        assert filename_schema is not None
        assert acceptance is not None
        assert output_config is not None

    def test_vendor_template_structure(self):
        """Verify vendor template has expected structure."""
        loader = ConfigLoader()
        template = loader.load_vendor_template("WM_LEWISVILLE")

        # Check required sections
        assert "vendor" in template
        assert "name" in template["vendor"]

    def test_synonyms_structure(self):
        """Verify synonyms has expected structure."""
        synonyms = load_synonyms()

        # Check required categories
        assert "vendors" in synonyms
        assert "materials" in synonyms
        assert "sources" in synonyms
        assert "destinations" in synonyms

        # Verify each category is a dict
        assert isinstance(synonyms["vendors"], dict)
        assert isinstance(synonyms["materials"], dict)

    def test_output_config_structure(self):
        """Verify output config has expected structure."""
        config = load_output_config()

        # Check required sections
        assert "database" in config
        assert "file_outputs" in config

        # Check database section
        assert "enabled" in config["database"]

        # Check file_outputs section
        assert "enabled" in config["file_outputs"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
