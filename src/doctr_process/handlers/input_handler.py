"""Input file handling with collision-safe naming."""

import zipfile
from collections.abc import Iterator
from pathlib import Path


class InputHandler:
    """Handles input file discovery and processing."""

    SUPPORTED_EXTENSIONS = {".pdf", ".tif", ".tiff", ".jpg", ".jpeg", ".png", ".zip"}

    def __init__(self, input_path: str):
        self.input_path = Path(input_path)

    def discover_files(self) -> list[Path]:
        """Discover all supported files in input path."""
        if self.input_path.is_file():
            if self.input_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                return [self.input_path]
            return []

        files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            if ext != ".zip":
                files.extend(self.input_path.glob(f"*{ext}"))
                files.extend(self.input_path.glob(f"**/*{ext}"))

        # Handle ZIP files separately
        for zip_file in self.input_path.glob("*.zip"):
            files.append(zip_file)

        return sorted(files)

    def iter_file_contents(self) -> Iterator[tuple[str, Path, bytes]]:
        """Iterate over file contents, handling ZIP archives."""
        files = self.discover_files()

        for file_path in files:
            if file_path.suffix.lower() == ".zip":
                yield from self._iter_zip_contents(file_path)
            else:
                with open(file_path, "rb") as f:
                    yield file_path.name, file_path, f.read()

    def _iter_zip_contents(self, zip_path: Path) -> Iterator[tuple[str, Path, bytes]]:
        """Extract supported files from ZIP archive."""
        with zipfile.ZipFile(zip_path, "r") as zf:
            for name in zf.namelist():
                if Path(name).suffix.lower() in self.SUPPORTED_EXTENSIONS - {".zip"}:
                    source_name = f"{zip_path.name}::{name}"
                    yield source_name, zip_path, zf.read(name)
