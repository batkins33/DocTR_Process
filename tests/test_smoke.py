"""Smoke tests to verify basic importability and entry points."""

import sys
import subprocess
from unittest.mock import patch


def test_import_doctr_process():
    """Test that the main package can be imported."""
    import doctr_process
    assert doctr_process is not None


def test_import_pipeline():
    """Test that the pipeline module can be imported."""
    from doctr_process import pipeline
    assert pipeline is not None
    assert hasattr(pipeline, 'run_pipeline')


def test_import_gui_without_launch():
    """Test that the GUI module can be imported without launching."""
    # Mock tkinter to prevent actual GUI launch
    with patch('tkinter.Tk') as mock_tk:
        from doctr_process import gui
        assert gui is not None
        assert hasattr(gui, 'main')
        # Ensure GUI didn't actually launch during import
        mock_tk.assert_not_called()


def test_main_entry_point():
    """Test that the main entry point can be imported and called with --version."""
    from doctr_process.main import main
    assert main is not None
    
    # Test --version flag without actually running main
    with patch('sys.argv', ['doctr-process', '--version']):
        with patch('builtins.print') as mock_print:
            try:
                main()
            except SystemExit:
                pass  # --version causes sys.exit, which is expected
            mock_print.assert_called()


def test_console_scripts_exist():
    """Test that console scripts are properly installed."""
    result = subprocess.run([sys.executable, '-c', 
                           'import pkg_resources; '
                           'eps = list(pkg_resources.iter_entry_points("console_scripts")); '
                           'doctr_scripts = [ep for ep in eps if ep.name.startswith("doctr")]; '
                           'print(len(doctr_scripts))'], 
                          capture_output=True, text=True)
    
    # Should have at least doctr-process and doctr-gui
    assert int(result.stdout.strip()) >= 2


def test_no_sys_path_modification():
    """Ensure tests do not modify sys.path."""
    original_path = sys.path.copy()
    
    # Import modules
    import doctr_process
    from doctr_process import pipeline
    
    # sys.path should be unchanged
    assert sys.path == original_path


def test_package_structure():
    """Test that key package components exist."""
    import doctr_process
    from doctr_process import main, gui, pipeline
    from doctr_process.utils import resources
    
    # Verify key functions exist
    assert hasattr(main, 'main')
    assert hasattr(gui, 'main') 
    assert hasattr(pipeline, 'run_pipeline')
    assert hasattr(resources, 'read_text')
    assert hasattr(resources, 'as_path')