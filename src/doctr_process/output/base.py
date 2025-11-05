"""Base output handler interface."""

from typing import Any


class OutputHandler:
    """Base class for output handlers."""

    def write(self, rows: list[dict[str, Any]], cfg: dict) -> None:
        """Write processed rows using ``cfg`` options."""
        raise NotImplementedError
