import logging
from pathlib import Path
from typing import Any


def normalize_single_path(value: Any):
    if isinstance(value, (list, tuple)):
        if not value:
            raise TypeError("No file selected (empty list/tuple)")
        if len(value) > 1:
            logging.warning("Multiple files selected; using first: %s", value[0])
        value = value[0]
    if isinstance(value, str) and ";" in value:
        parts = [p.strip() for p in value.split(";") if p.strip()]
        if len(parts) > 1:
            logging.warning("Multiple files provided; using first: %s", parts[0])
        value = parts[0]
    if hasattr(value, "read"):
        raise TypeError("Streams not accepted here; pass a filesystem path")
    if not isinstance(value, (str, Path)):
        raise TypeError(f"Expected str/Path, got {type(value).__name__}")
    p = Path(str(value).strip().strip('"')).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"Path does not exist: {p}")
    if not p.is_file():
        raise TypeError(f"Not a file path: {p}")
    return p.resolve()


def guard_call(label: str, fn, *args, **kwargs):
    logging.debug("%s args=%r kwargs=%r", label, args, kwargs)
    return fn(*args, **kwargs)
