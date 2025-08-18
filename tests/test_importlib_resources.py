"""Test importlib.resources config loading functionality."""

import pytest
import tempfile
import os
from pathlib import Path


def test_resource_loading_utilities():
    """Test that utils.resources can load config files via importlib.resources."""
    from doctr_process.utils.resources import read_text, as_path
    
    # Test read_text
    content = read_text("config.yaml")
    assert isinstance(content, str)
    assert len(content) > 0
    assert "batch_mode" in content  # Should contain config keys
    
    # Test as_path
    with as_path("extraction_rules.yaml") as path:
        assert isinstance(path, Path)
        assert path.exists()
        with open(path) as f:
            content = f.read()
            assert len(content) > 0


def test_config_loading_from_package():
    """Test that config_utils can load configs from package resources."""
    # Import directly to avoid dependency issues in other modules
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'config_utils', 
        'src/doctr_process/ocr/config_utils.py'
    )
    config_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_utils)
    
    # Test loading extraction rules  
    rules = config_utils.load_extraction_rules()
    assert isinstance(rules, dict)
    assert len(rules) > 0
    assert "DEFAULT" in rules  # Should have default vendor rules
    
    # Test loading config
    cfg = config_utils.load_config("config.yaml")
    assert isinstance(cfg, dict)
    assert len(cfg) > 0
    assert "batch_mode" in cfg  # Should have expected config keys


def test_config_loading_from_different_cwd():
    """Test that config loading works from any current working directory."""
    import importlib.util
    
    # Change to a different directory
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            
            # Import config_utils from the different CWD
            spec = importlib.util.spec_from_file_location(
                'config_utils', 
                os.path.join(original_cwd, 'src/doctr_process/ocr/config_utils.py')
            )
            config_utils = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_utils)
            
            # Should still be able to load configs
            cfg = config_utils.load_config("config.yaml")
            assert isinstance(cfg, dict)
            assert "batch_mode" in cfg
            
            rules = config_utils.load_extraction_rules()
            assert isinstance(rules, dict)
            assert "DEFAULT" in rules
            
        finally:
            os.chdir(original_cwd)


def test_invalid_config_name():
    """Test that requesting non-existent config raises appropriate error."""
    from doctr_process.utils.resources import read_text
    
    with pytest.raises(FileNotFoundError, match="not found in package configs"):
        read_text("nonexistent.yaml")


if __name__ == "__main__":
    # Allow running as script for manual testing
    test_resource_loading_utilities()
    test_config_loading_from_package()
    test_config_loading_from_different_cwd()
    test_invalid_config_name()
    print("All tests passed!")