"""Smoke tests for refactored components."""

from doctr_process.io import InputHandler, OutputManager
from PIL import Image

from doctr_process.extract import ImageExtractor


class TestRefactorSmoke:
    """Smoke tests to ensure refactored components work together."""

    def test_input_to_output_flow(self, tmp_path):
        """Test basic flow from input discovery to output management."""
        # Create test input
        test_img = Image.new("RGB", (100, 100), color="red")
        img_path = tmp_path / "test.jpg"
        test_img.save(img_path)

        # Test input handler
        input_handler = InputHandler(str(tmp_path))
        files = input_handler.discover_files()
        assert len(files) == 1

        # Test output manager
        output_dir = tmp_path / "output"
        output_manager = OutputManager(str(output_dir))
        subdir = output_manager.get_input_subdir("test_input")
        assert subdir.exists()

        # Test safe filename generation
        safe_path = output_manager.get_safe_filename("result", ".csv", subdir)
        assert safe_path.parent == subdir
        assert safe_path.name == "result.csv"

    def test_image_extraction_basic(self, tmp_path):
        """Test basic image extraction functionality."""
        # Create test image
        test_img = Image.new("RGB", (200, 200), color="blue")
        img_path = tmp_path / "test.png"
        test_img.save(img_path)

        # Test extraction
        extractor = ImageExtractor()
        images = list(extractor.extract_from_file(img_path))

        assert len(images) == 1
        assert isinstance(images[0], Image.Image)
        assert images[0].size == (200, 200)

        # Clean up
        images[0].close()

    def test_collision_handling(self, tmp_path):
        """Test collision-safe naming works correctly."""
        output_manager = OutputManager(str(tmp_path))
        subdir = tmp_path / "test"
        subdir.mkdir()

        # Create multiple files with same base name
        paths = []
        for i in range(3):
            path = output_manager.get_safe_filename("data", ".txt", subdir)
            path.write_text(f"content {i}")
            paths.append(path)

        # Verify unique names
        names = [p.name for p in paths]
        assert len(set(names)) == 3  # All unique
        assert "data.txt" in names
        assert "data_001.txt" in names
        assert "data_002.txt" in names
