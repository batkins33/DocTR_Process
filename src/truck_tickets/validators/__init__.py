"""Validation modules for truck ticket processing."""

from .manifest_validator import ManifestValidationResult, ManifestValidator

__all__ = [
    "ManifestValidator",
    "ManifestValidationResult",
]
