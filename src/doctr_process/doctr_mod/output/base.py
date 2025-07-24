"""Base output handler interface."""

from typing import List, Dict, Any

class OutputHandler:
    """Base class for output handlers."""

    def write(self, rows: List[Dict[str, Any]], cfg: dict) -> None:
        """Write processed rows using ``cfg`` options."""
        raise NotImplementedError
