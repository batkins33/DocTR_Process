"""Output management with collision-safe naming."""

import re
from datetime import datetime
from pathlib import Path


class OutputManager:
    """Manages output directory structure and collision-safe file naming."""

    def __init__(self, base_dir: str, prefer_timestamp: bool = False):
        self.base_dir = Path(base_dir)
        self.prefer_timestamp = prefer_timestamp
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_input_subdir(self, input_name: str) -> Path:
        """Create per-input subdirectory with safe naming."""
        safe_name = self._sanitize_name(input_name)
        subdir = self.base_dir / safe_name
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    def get_safe_filename(self, base_name: str, extension: str, subdir: Path) -> Path:
        """Generate collision-safe filename with numeric suffix or timestamp."""
        safe_base = self._sanitize_name(base_name)

        if self.prefer_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_base}_{timestamp}{extension}"
        else:
            filename = f"{safe_base}{extension}"

        output_path = subdir / filename

        # Handle collisions with numeric suffix
        if output_path.exists() and not self.prefer_timestamp:
            counter = 1
            while output_path.exists():
                filename = f"{safe_base}_{counter:03d}{extension}"
                output_path = subdir / filename
                counter += 1

        return output_path

    def _sanitize_name(self, name: str) -> str:
        """Sanitize filename for safe filesystem usage."""
        # Remove extension if present
        name = Path(name).stem
        # Replace unsafe characters
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
        # Collapse multiple underscores
        name = re.sub(r"_+", "_", name)
        # Remove leading/trailing underscores and dots
        name = name.strip("_.")
        # Ensure not empty
        return name or "unnamed"
