"""File hash utilities for integrity verification and duplicate detection.

This module provides SHA-256 hashing utilities for PDF files to:
1. Verify file integrity
2. Detect duplicate file processing
3. Track which files have been processed

The hash is calculated using chunked reading to handle large files efficiently.
"""

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def calculate_file_hash(file_path: str | Path, chunk_size: int = 8192) -> str:
    """Calculate SHA-256 hash of a file.

    Uses chunked reading to handle large files efficiently without loading
    the entire file into memory.

    Args:
        file_path: Path to file
        chunk_size: Size of chunks to read (default: 8192 bytes)

    Returns:
        Hex string of SHA-256 hash (64 characters)

    Raises:
        FileNotFoundError: If file doesn't exist
        PermissionError: If file can't be read

    Example:
        ```python
        hash_value = calculate_file_hash("invoice.pdf")
        print(f"SHA-256: {hash_value}")
        # Output: SHA-256: a3b2c1d4e5f6...
        ```
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    sha256 = hashlib.sha256()

    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256.update(chunk)

        hash_value = sha256.hexdigest()
        logger.debug(f"Calculated hash for {file_path.name}: {hash_value[:16]}...")
        return hash_value

    except PermissionError as e:
        logger.error(f"Permission denied reading {file_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise


def verify_file_hash(file_path: str | Path, expected_hash: str) -> bool:
    """Verify that a file's hash matches the expected value.

    Args:
        file_path: Path to file
        expected_hash: Expected SHA-256 hash (64-character hex string)

    Returns:
        True if hash matches, False otherwise

    Example:
        ```python
        is_valid = verify_file_hash("invoice.pdf", "a3b2c1d4e5f6...")
        if is_valid:
            print("File integrity verified")
        else:
            print("File has been modified!")
        ```
    """
    try:
        actual_hash = calculate_file_hash(file_path)
        matches = actual_hash.lower() == expected_hash.lower()

        if not matches:
            logger.warning(
                f"Hash mismatch for {file_path}: "
                f"expected {expected_hash[:16]}..., got {actual_hash[:16]}..."
            )

        return matches

    except Exception as e:
        logger.error(f"Error verifying hash for {file_path}: {e}")
        return False


def get_file_info(file_path: str | Path) -> dict:
    """Get file information including hash and metadata.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information:
        - path: Absolute file path
        - name: File name
        - size: File size in bytes
        - hash: SHA-256 hash

    Example:
        ```python
        info = get_file_info("invoice.pdf")
        print(f"File: {info['name']}")
        print(f"Size: {info['size']} bytes")
        print(f"Hash: {info['hash']}")
        ```
    """
    file_path = Path(file_path).resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    stat = file_path.stat()

    return {
        "path": str(file_path),
        "name": file_path.name,
        "size": stat.st_size,
        "hash": calculate_file_hash(file_path),
        "modified": stat.st_mtime,
    }
