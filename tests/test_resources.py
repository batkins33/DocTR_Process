"""Test resource loading via importlib.resources."""

import pytest
from doctr_process.utils.resources import read_text, as_path


def test_read_config_text():
    """Test reading config file content as text."""
    content = read_text("config.yaml")
    assert isinstance(content, str)
    assert len(content) > 0
    assert "output_dir" in content


def test_as_path():
    """Test getting Path object for config file."""
    with as_path("config.yaml") as path:
        assert path.exists()
        assert path.name == "config.yaml"
        assert path.is_file()


def test_read_nonexistent_file():
    """Test reading non-existent file raises appropriate error."""
    with pytest.raises(FileNotFoundError):
        read_text("nonexistent.yaml")