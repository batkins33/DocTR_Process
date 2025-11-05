"""Unit tests for vendor templates (Issue #22)."""
from pathlib import Path

import pytest
import yaml


class TestVendorTemplates:
    """Test suite for vendor template YAML files."""

    @pytest.fixture
    def templates_dir(self):
        """Get templates directory path."""
        return Path("src/truck_tickets/templates/vendors")

    def test_wm_lewisville_template_exists(self, templates_dir):
        """Test that WM Lewisville template exists."""
        template_path = templates_dir / "WM_LEWISVILLE.yml"
        assert template_path.exists()

    def test_ldi_yard_template_exists(self, templates_dir):
        """Test that LDI Yard template exists."""
        template_path = templates_dir / "LDI_YARD.yml"
        assert template_path.exists()

    def test_post_oak_pit_template_exists(self, templates_dir):
        """Test that Post Oak Pit template exists."""
        template_path = templates_dir / "POST_OAK_PIT.yml"
        assert template_path.exists()

    def test_wm_lewisville_template_loads(self, templates_dir):
        """Test that WM Lewisville template is valid YAML."""
        template_path = templates_dir / "WM_LEWISVILLE.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert "vendor" in config
        assert config["vendor"]["name"] == "WASTE_MANAGEMENT_LEWISVILLE"

    def test_ldi_yard_template_loads(self, templates_dir):
        """Test that LDI Yard template is valid YAML."""
        template_path = templates_dir / "LDI_YARD.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert "vendor" in config
        assert config["vendor"]["name"] == "LDI_YARD"
        assert config["vendor"]["vendor_code"] == "LDI"

    def test_post_oak_pit_template_loads(self, templates_dir):
        """Test that Post Oak Pit template is valid YAML."""
        template_path = templates_dir / "POST_OAK_PIT.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert "vendor" in config
        assert config["vendor"]["name"] == "POST_OAK_PIT"
        assert config["vendor"]["vendor_code"] == "POA"

    def test_ldi_yard_template_structure(self, templates_dir):
        """Test LDI Yard template has required fields."""
        template_path = templates_dir / "LDI_YARD.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        # Check vendor info
        assert "vendor" in config
        assert "name" in config["vendor"]
        assert "display_name" in config["vendor"]
        assert "vendor_code" in config["vendor"]
        assert "aliases" in config["vendor"]

        # Check extraction fields
        assert "ticket_number" in config
        assert "date" in config
        assert "quantity" in config
        assert "material" in config
        assert "truck_number" in config

        # Check manifest is not required
        assert "manifest_number" in config
        assert config["manifest_number"]["required"] is False

        # Check processing hints
        assert "processing" in config
        assert config["processing"]["requires_manifest"] is False

    def test_post_oak_pit_template_structure(self, templates_dir):
        """Test Post Oak Pit template has required fields."""
        template_path = templates_dir / "POST_OAK_PIT.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        # Check vendor info
        assert "vendor" in config
        assert "name" in config["vendor"]
        assert "display_name" in config["vendor"]
        assert "vendor_code" in config["vendor"]
        assert "aliases" in config["vendor"]

        # Check extraction fields
        assert "ticket_number" in config
        assert "date" in config
        assert "quantity" in config
        assert "material" in config
        assert "truck_number" in config

        # Check manifest is not required
        assert "manifest_number" in config
        assert config["manifest_number"]["required"] is False

        # Check processing hints
        assert "processing" in config
        assert config["processing"]["requires_manifest"] is False

    def test_ldi_yard_no_manifest_requirement(self, templates_dir):
        """Test that LDI Yard does not require manifests (clean fill only)."""
        template_path = templates_dir / "LDI_YARD.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert config["manifest_number"]["required"] is False
        assert config["processing"]["requires_manifest"] is False

    def test_post_oak_pit_no_manifest_requirement(self, templates_dir):
        """Test that Post Oak Pit does not require manifests (reuse site)."""
        template_path = templates_dir / "POST_OAK_PIT.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert config["manifest_number"]["required"] is False
        assert config["processing"]["requires_manifest"] is False

    def test_wm_lewisville_requires_manifest(self, templates_dir):
        """Test that WM Lewisville requires manifests (contaminated material)."""
        template_path = templates_dir / "WM_LEWISVILLE.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert config["manifest_number"]["required"] is True

    def test_ldi_yard_aliases(self, templates_dir):
        """Test LDI Yard has correct aliases."""
        template_path = templates_dir / "LDI_YARD.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        aliases = config["vendor"]["aliases"]
        assert "LDI" in aliases
        assert "LDI Yard" in aliases
        assert "Lindamood" in aliases

    def test_post_oak_pit_aliases(self, templates_dir):
        """Test Post Oak Pit has correct aliases."""
        template_path = templates_dir / "POST_OAK_PIT.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        aliases = config["vendor"]["aliases"]
        assert "Post Oak" in aliases
        assert "Post Oak Pit" in aliases
        assert "POA" in aliases

    def test_all_templates_have_truck_number_field(self, templates_dir):
        """Test that all templates include truck_number field (v1.1 requirement)."""
        template_files = [
            "WM_LEWISVILLE.yml",
            "LDI_YARD.yml",
            "POST_OAK_PIT.yml"
        ]

        for template_file in template_files:
            template_path = templates_dir / template_file
            with open(template_path) as f:
                config = yaml.safe_load(f)

            assert "truck_number" in config, f"{template_file} missing truck_number field"

    def test_ldi_yard_default_material(self, templates_dir):
        """Test LDI Yard defaults to NON_CONTAMINATED material."""
        template_path = templates_dir / "LDI_YARD.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert config["material"]["default"] == "NON_CONTAMINATED"

    def test_post_oak_pit_default_material(self, templates_dir):
        """Test Post Oak Pit defaults to NON_CONTAMINATED material."""
        template_path = templates_dir / "POST_OAK_PIT.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert config["material"]["default"] == "NON_CONTAMINATED"

    def test_ldi_yard_quality_checks(self, templates_dir):
        """Test LDI Yard has quality checks defined."""
        template_path = templates_dir / "LDI_YARD.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert "quality_checks" in config
        assert len(config["quality_checks"]) > 0

        # Check for required field checks
        check_fields = [check["field"] for check in config["quality_checks"]]
        assert "ticket_number" in check_fields
        assert "date" in check_fields

    def test_post_oak_pit_quality_checks(self, templates_dir):
        """Test Post Oak Pit has quality checks defined."""
        template_path = templates_dir / "POST_OAK_PIT.yml"
        with open(template_path) as f:
            config = yaml.safe_load(f)

        assert "quality_checks" in config
        assert len(config["quality_checks"]) > 0

        # Check for required field checks
        check_fields = [check["field"] for check in config["quality_checks"]]
        assert "ticket_number" in check_fields
        assert "date" in check_fields
