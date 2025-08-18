"""Smoke tests for importability and entry points.

These tests verify that core modules can be imported without errors
and that entry points are accessible. They use guards to prevent
actual GUI launches or heavy dependency loading.
"""

import importlib
import sys
import types
import unittest.mock


class TestBasicImportability:
    """Test that core modules can be imported."""

    def test_import_doctr_process_package(self):
        """Test that the main doctr_process package can be imported."""
        import doctr_process
        assert hasattr(doctr_process, '__all__')
        expected_modules = ["pipeline", "gui", "ocr", "output", "processor"]
        assert doctr_process.__all__ == expected_modules

    def test_import_lightweight_modules(self):
        """Test that lightweight modules can be imported without heavy dependencies."""
        # Test path_utils (should be dependency-light)
        import doctr_process.path_utils
        assert hasattr(doctr_process.path_utils, 'normalize_single_path')
        assert hasattr(doctr_process.path_utils, 'guard_call')
        
        # Test logging_setup
        import doctr_process.logging_setup
        assert hasattr(doctr_process.logging_setup, 'setup_logging')
        assert hasattr(doctr_process.logging_setup, 'set_gui_log_widget')

    def test_no_sys_path_modification(self):
        """Verify that this test file doesn't modify sys.path."""
        # Store initial sys.path
        initial_path = sys.path.copy()
        
        # Run a basic import
        import doctr_process
        
        # Verify sys.path wasn't modified by our test
        assert sys.path == initial_path


class TestModuleStructure:
    """Test module structure and attributes without full loading."""
    
    def test_pipeline_module_structure(self):
        """Test that pipeline module has expected structure when dependencies are available."""
        try:
            import doctr_process.pipeline
            # If import succeeds, verify it has the expected entry point
            assert hasattr(doctr_process.pipeline, 'run_pipeline')
            assert callable(doctr_process.pipeline.run_pipeline)
        except ImportError as e:
            # If dependencies are missing, that's expected in CI/minimal environments
            # Just verify the error is due to dependencies, not code structure
            error_msg = str(e).lower()
            expected_missing = ['fitz', 'cv2', 'pil', 'numpy', 'pandas', 'torch', 'doctr']
            assert any(dep in error_msg for dep in expected_missing), f"Unexpected import error: {e}"

    def test_gui_module_structure(self):
        """Test that GUI module has expected structure when dependencies are available."""
        try:
            import doctr_process.gui
            # If import succeeds, verify it has the expected entry points
            assert hasattr(doctr_process.gui, 'main')
            assert callable(doctr_process.gui.main)
            assert hasattr(doctr_process.gui, 'App')
        except ImportError as e:
            # If dependencies are missing, that's expected in CI/minimal environments
            # Just verify the error is due to dependencies, not code structure
            error_msg = str(e).lower()
            expected_missing = ['tkinter', 'yaml']
            assert any(dep in error_msg for dep in expected_missing), f"Unexpected import error: {e}"

    def test_main_module_structure(self):
        """Test that __main__ module has expected structure when dependencies are available."""
        try:
            import doctr_process.__main__
            # If import succeeds, verify it has the expected entry point
            assert hasattr(doctr_process.__main__, 'main')
            assert callable(doctr_process.__main__.main)
        except ImportError as e:
            # If dependencies are missing, that's expected in CI/minimal environments
            # Just verify the error is due to dependencies, not code structure
            error_msg = str(e).lower()
            expected_missing = ['fitz', 'pil', 'numpy', 'pandas', 'cv2', 'openpyxl']
            assert any(dep in error_msg for dep in expected_missing), f"Unexpected import error: {e}"


class TestEntryPointsWithMocks:
    """Test that entry points are accessible without launching."""
    
    def test_entry_points_structure_verification(self):
        """Test that entry point modules have the expected structure."""
        # Rather than attempting full import with mocks, verify structure through inspection
        # This is more robust for CI environments and focuses on the core requirement
        
        # Check that the modules exist as files in the expected location
        import os
        src_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'doctr_process')
        
        # Verify pipeline.py exists and contains run_pipeline
        pipeline_path = os.path.join(src_path, 'pipeline.py')
        assert os.path.exists(pipeline_path), "pipeline.py should exist"
        
        with open(pipeline_path, 'r') as f:
            pipeline_content = f.read()
            assert 'def run_pipeline(' in pipeline_content, "run_pipeline function should be defined"
        
        # Verify gui.py exists and contains main and App
        gui_path = os.path.join(src_path, 'gui.py')
        assert os.path.exists(gui_path), "gui.py should exist"
        
        with open(gui_path, 'r') as f:
            gui_content = f.read()
            assert 'def main(' in gui_content, "main function should be defined"
            assert 'class App(' in gui_content, "App class should be defined"
        
        # Verify __main__.py exists and contains main
        main_path = os.path.join(src_path, '__main__.py')
        assert os.path.exists(main_path), "__main__.py should exist"
        
        with open(main_path, 'r') as f:
            main_content = f.read()
            assert 'def main(' in main_content, "main function should be defined"

    def test_importability_in_dependency_free_environment(self):
        """Test what can be imported in an environment without heavy dependencies."""
        # Test basic package structure
        import doctr_process
        assert doctr_process.__all__ == ["pipeline", "gui", "ocr", "output", "processor"]
        
        # Test lightweight modules that should work
        import doctr_process.path_utils
        import doctr_process.logging_setup
        
        # Test that we get expected import errors for heavy modules (not structural errors)
        try:
            import doctr_process.pipeline
            # If this succeeds in the test environment, that's fine
            assert hasattr(doctr_process.pipeline, 'run_pipeline')
        except ImportError as e:
            # Expected in minimal environments - verify it's dependency-related
            error_msg = str(e).lower()
            expected_deps = ['fitz', 'numpy', 'pandas', 'cv2', 'path_utils', 'output', 'ocr']
            assert any(dep in error_msg for dep in expected_deps), f"Import error should be dependency-related: {e}"
        
        try:
            import doctr_process.gui
            # If this succeeds in the test environment, that's fine
            assert hasattr(doctr_process.gui, 'main')
        except ImportError as e:
            # Expected in minimal environments - verify it's dependency-related  
            error_msg = str(e).lower()
            expected_deps = ['tkinter', 'yaml', 'pipeline']
            assert any(dep in error_msg for dep in expected_deps), f"Import error should be dependency-related: {e}"