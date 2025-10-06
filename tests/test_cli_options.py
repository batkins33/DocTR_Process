"""Tests for new CLI options."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from doctr_process.main import main


class TestCLIOptions:
    """Test new CLI options."""
    
    @patch('doctr_process.main.run_refactored_pipeline')
    @patch('sys.argv', ['doctr-process', '--input', 'test.pdf', '--outdir', 'output', '--no-gui'])
    def test_outdir_option(self, mock_pipeline):
        """Test --outdir option."""
        with patch('doctr_process.main.Path') as mock_path:
            mock_path.return_value.is_dir.return_value = False
            mock_path.return_value.mkdir = lambda **kwargs: None
            
            main()
            
            mock_pipeline.assert_called_once()
    
    @patch('doctr_process.main.run_refactored_pipeline')
    @patch('sys.argv', ['doctr-process', '--input', 'test.pdf', '--output', 'output', '--prefer-timestamp', '--no-gui'])
    def test_prefer_timestamp_option(self, mock_pipeline):
        """Test --prefer-timestamp option."""
        with patch('doctr_process.main.Path') as mock_path:
            mock_path.return_value.is_dir.return_value = False
            mock_path.return_value.mkdir = lambda **kwargs: None
            
            main()
            
            mock_pipeline.assert_called_once()
            # Check that prefer_timestamp is in config
            call_args = mock_pipeline.call_args[0][0]
            with open(call_args, 'r') as f:
                import yaml
                config = yaml.safe_load(f)
                assert config.get('prefer_timestamp') is True