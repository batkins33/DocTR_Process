"""Tests for io module."""

import tempfile
from pathlib import Path

import pytest

from doctr_process.io import InputHandler, OutputManager


class TestInputHandler:
    """Test InputHandler functionality."""
    
    def test_discover_single_file(self, tmp_path):
        """Test discovering a single PDF file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")
        
        handler = InputHandler(str(pdf_file))
        files = handler.discover_files()
        
        assert len(files) == 1
        assert files[0] == pdf_file
    
    def test_discover_directory(self, tmp_path):
        """Test discovering files in directory."""
        (tmp_path / "test1.pdf").write_bytes(b"pdf1")
        (tmp_path / "test2.jpg").write_bytes(b"jpg1")
        (tmp_path / "ignore.txt").write_bytes(b"text")
        
        handler = InputHandler(str(tmp_path))
        files = handler.discover_files()
        
        assert len(files) == 2
        assert any(f.name == "test1.pdf" for f in files)
        assert any(f.name == "test2.jpg" for f in files)


class TestOutputManager:
    """Test OutputManager functionality."""
    
    def test_sanitize_name(self, tmp_path):
        """Test filename sanitization."""
        manager = OutputManager(str(tmp_path))
        
        assert manager._sanitize_name("test<>file") == "test__file"
        assert manager._sanitize_name("normal_file") == "normal_file"
        assert manager._sanitize_name("") == "unnamed"
    
    def test_collision_safe_naming(self, tmp_path):
        """Test collision-safe filename generation."""
        manager = OutputManager(str(tmp_path))
        subdir = tmp_path / "test"
        subdir.mkdir()
        
        # Create first file
        path1 = manager.get_safe_filename("test", ".txt", subdir)
        path1.write_text("content1")
        
        # Second file should get numeric suffix
        path2 = manager.get_safe_filename("test", ".txt", subdir)
        
        assert path1.name == "test.txt"
        assert path2.name == "test_001.txt"
    
    def test_timestamp_naming(self, tmp_path):
        """Test timestamp-based naming."""
        manager = OutputManager(str(tmp_path), prefer_timestamp=True)
        subdir = tmp_path / "test"
        subdir.mkdir()
        
        path = manager.get_safe_filename("test", ".txt", subdir)
        
        assert "test_" in path.name
        assert path.name.endswith(".txt")