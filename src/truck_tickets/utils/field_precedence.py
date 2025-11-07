"""Field extraction precedence logic with multi-layer fallback system.

This module implements Issue #10: Field extraction precedence logic
Precedence order: filename > folder > OCR > defaults
Never override manual DB/UI corrections.

Business Rules:
    1. Filename metadata has highest precedence (explicitly provided)
    2. Folder structure provides context (job, area, flow)
    3. OCR extraction from ticket content
    4. Default values as last resort
    5. Manual corrections in database are NEVER overridden

Precedence Levels:
    - MANUAL (100): User corrections in database/UI - NEVER override
    - FILENAME (90): Explicitly provided in filename
    - FOLDER (80): Derived from folder structure
    - OCR_HIGH (70): High-confidence OCR extraction (>0.9)
    - OCR_MEDIUM (60): Medium-confidence OCR (0.7-0.9)
    - OCR_LOW (50): Low-confidence OCR (<0.7)
    - DEFAULT (10): System defaults

Example:
    ```python
    resolver = FieldPrecedenceResolver()

    # Add values from different sources
    resolver.add_value("date", "2024-10-17", source="filename", confidence=1.0)
    resolver.add_value("date", "2024-10-18", source="ocr", confidence=0.85)
    resolver.add_value("date", "2024-10-16", source="default", confidence=0.5)

    # Get best value
    result = resolver.resolve("date")
    print(f"Date: {result.value}, Source: {result.source}, Confidence: {result.confidence}")
    # Output: Date: 2024-10-17, Source: filename, Confidence: 1.0
    ```
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PrecedenceLevel(Enum):
    """Precedence levels for field value sources."""

    MANUAL = 100  # User corrections - NEVER override
    FILENAME = 90  # Explicitly in filename
    FOLDER = 80  # From folder structure
    OCR_HIGH = 70  # High confidence OCR (>0.9)
    OCR_MEDIUM = 60  # Medium confidence OCR (0.7-0.9)
    OCR_LOW = 50  # Low confidence OCR (<0.7)
    DEFAULT = 10  # System default

    @classmethod
    def from_source_and_confidence(
        cls, source: str, confidence: float
    ) -> "PrecedenceLevel":
        """Determine precedence level from source and confidence.

        Args:
            source: Source identifier (manual, filename, folder, ocr, default)
            confidence: Confidence score (0.0-1.0)

        Returns:
            Appropriate PrecedenceLevel
        """
        source_lower = source.lower()

        if source_lower == "manual":
            return cls.MANUAL
        elif source_lower == "filename":
            return cls.FILENAME
        elif source_lower == "folder":
            return cls.FOLDER
        elif source_lower == "ocr":
            if confidence >= 0.9:
                return cls.OCR_HIGH
            elif confidence >= 0.7:
                return cls.OCR_MEDIUM
            else:
                return cls.OCR_LOW
        elif source_lower == "default":
            return cls.DEFAULT
        else:
            logger.warning(f"Unknown source '{source}', treating as OCR_LOW")
            return cls.OCR_LOW


@dataclass
class FieldValue:
    """A field value with its source and precedence information.

    Attributes:
        field_name: Name of the field (e.g., "date", "vendor")
        value: The actual value
        source: Source of the value (manual, filename, folder, ocr, default)
        confidence: Confidence score (0.0-1.0)
        precedence: Calculated precedence level
        timestamp: When this value was added
    """

    field_name: str
    value: Any
    source: str
    confidence: float
    precedence: PrecedenceLevel = field(init=False)

    def __post_init__(self):
        """Calculate precedence level after initialization."""
        self.precedence = PrecedenceLevel.from_source_and_confidence(
            self.source, self.confidence
        )

    def __repr__(self) -> str:
        return (
            f"<FieldValue(field='{self.field_name}', "
            f"value={self.value}, "
            f"source='{self.source}', "
            f"precedence={self.precedence.name})>"
        )


@dataclass
class ResolvedField:
    """Result of field precedence resolution.

    Attributes:
        field_name: Name of the field
        value: The resolved value (highest precedence)
        source: Source of the resolved value
        confidence: Confidence score
        precedence: Precedence level
        alternatives: List of alternative values that were considered
    """

    field_name: str
    value: Any
    source: str
    confidence: float
    precedence: PrecedenceLevel
    alternatives: list[FieldValue] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"<ResolvedField(field='{self.field_name}', "
            f"value={self.value}, "
            f"source='{self.source}', "
            f"precedence={self.precedence.name})>"
        )


class FieldPrecedenceResolver:
    """Resolves field values using precedence rules.

    This resolver implements the multi-layer precedence system:
    filename > folder > OCR > defaults, with manual corrections
    always taking highest precedence.

    Example:
        ```python
        resolver = FieldPrecedenceResolver()

        # Add values from different sources
        resolver.add_value("vendor", "WM", source="filename", confidence=1.0)
        resolver.add_value("vendor", "WASTE_MANAGEMENT", source="ocr", confidence=0.95)
        resolver.add_value("date", "2024-10-17", source="filename", confidence=1.0)
        resolver.add_value("date", "2024-10-18", source="ocr", confidence=0.85)

        # Resolve all fields
        resolved = resolver.resolve_all()

        for field_name, result in resolved.items():
            print(f"{field_name}: {result.value} (from {result.source})")
        ```

    Attributes:
        field_values: Dictionary mapping field names to lists of FieldValue objects
        manual_overrides: Dictionary of manual corrections (never overridden)
    """

    def __init__(self):
        """Initialize the precedence resolver."""
        self.field_values: dict[str, list[FieldValue]] = {}
        self.manual_overrides: dict[str, Any] = {}

    def add_value(
        self,
        field_name: str,
        value: Any,
        source: str,
        confidence: float = 1.0,
    ) -> None:
        """Add a field value from a specific source.

        Args:
            field_name: Name of the field
            value: The value to add
            source: Source identifier (manual, filename, folder, ocr, default)
            confidence: Confidence score (0.0-1.0)

        Note:
            If source is 'manual', this value will never be overridden.
        """
        if value is None:
            logger.debug(f"Skipping None value for {field_name} from {source}")
            return

        field_value = FieldValue(
            field_name=field_name,
            value=value,
            source=source,
            confidence=confidence,
        )

        # Store manual overrides separately
        if source.lower() == "manual":
            self.manual_overrides[field_name] = value
            logger.info(
                f"Manual override set for {field_name}: {value} (NEVER overridden)"
            )

        # Add to field values list
        if field_name not in self.field_values:
            self.field_values[field_name] = []

        self.field_values[field_name].append(field_value)

        logger.debug(
            f"Added {field_name}={value} from {source} "
            f"(precedence={field_value.precedence.name}, confidence={confidence})"
        )

    def add_filename_hints(self, hints: dict[str, Any]) -> None:
        """Add multiple values from filename parsing.

        Args:
            hints: Dictionary of field names to values from filename
        """
        for field_name, value in hints.items():
            if value is not None:
                self.add_value(field_name, value, source="filename", confidence=1.0)

    def add_folder_hints(self, hints: dict[str, Any]) -> None:
        """Add multiple values from folder structure.

        Args:
            hints: Dictionary of field names to values from folder path
        """
        for field_name, value in hints.items():
            if value is not None:
                self.add_value(field_name, value, source="folder", confidence=0.9)

    def add_ocr_extractions(self, extractions: dict[str, tuple[Any, float]]) -> None:
        """Add multiple values from OCR extraction.

        Args:
            extractions: Dictionary mapping field names to (value, confidence) tuples
        """
        for field_name, (value, confidence) in extractions.items():
            if value is not None:
                self.add_value(field_name, value, source="ocr", confidence=confidence)

    def add_defaults(self, defaults: dict[str, Any]) -> None:
        """Add default values for fields.

        Args:
            defaults: Dictionary of field names to default values
        """
        for field_name, value in defaults.items():
            if value is not None:
                self.add_value(field_name, value, source="default", confidence=0.5)

    def resolve(self, field_name: str) -> ResolvedField | None:
        """Resolve a single field to its best value.

        Args:
            field_name: Name of the field to resolve

        Returns:
            ResolvedField with the highest precedence value, or None if no values

        Note:
            Manual overrides always win, regardless of other values.
        """
        # Check for manual override first
        if field_name in self.manual_overrides:
            manual_value = self.manual_overrides[field_name]
            logger.info(
                f"Using manual override for {field_name}: {manual_value} (NEVER overridden)"
            )
            return ResolvedField(
                field_name=field_name,
                value=manual_value,
                source="manual",
                confidence=1.0,
                precedence=PrecedenceLevel.MANUAL,
                alternatives=[],
            )

        # Get all values for this field
        values = self.field_values.get(field_name, [])

        if not values:
            logger.debug(f"No values found for field '{field_name}'")
            return None

        # Sort by precedence level (highest first)
        sorted_values = sorted(values, key=lambda v: v.precedence.value, reverse=True)

        # Best value is the one with highest precedence
        best = sorted_values[0]
        alternatives = sorted_values[1:]

        logger.debug(
            f"Resolved {field_name}={best.value} from {best.source} "
            f"(precedence={best.precedence.name}, {len(alternatives)} alternatives)"
        )

        return ResolvedField(
            field_name=field_name,
            value=best.value,
            source=best.source,
            confidence=best.confidence,
            precedence=best.precedence,
            alternatives=alternatives,
        )

    def resolve_all(self) -> dict[str, ResolvedField]:
        """Resolve all fields to their best values.

        Returns:
            Dictionary mapping field names to ResolvedField objects
        """
        resolved = {}

        # Get all unique field names
        all_fields = set(self.field_values.keys()) | set(self.manual_overrides.keys())

        for field_name in all_fields:
            result = self.resolve(field_name)
            if result:
                resolved[field_name] = result

        logger.info(f"Resolved {len(resolved)} fields using precedence rules")
        return resolved

    def get_resolution_summary(self) -> dict[str, dict[str, Any]]:
        """Get a summary of how each field was resolved.

        Returns:
            Dictionary with resolution details for each field
        """
        summary = {}
        resolved = self.resolve_all()

        for field_name, result in resolved.items():
            summary[field_name] = {
                "value": result.value,
                "source": result.source,
                "precedence": result.precedence.name,
                "confidence": result.confidence,
                "num_alternatives": len(result.alternatives),
                "alternatives": [
                    {
                        "value": alt.value,
                        "source": alt.source,
                        "precedence": alt.precedence.name,
                        "confidence": alt.confidence,
                    }
                    for alt in result.alternatives
                ],
            }

        return summary

    def has_manual_override(self, field_name: str) -> bool:
        """Check if a field has a manual override.

        Args:
            field_name: Name of the field

        Returns:
            True if field has manual override
        """
        return field_name in self.manual_overrides

    def clear(self) -> None:
        """Clear all field values (except manual overrides)."""
        self.field_values.clear()
        logger.debug("Cleared all field values (manual overrides preserved)")

    def clear_all(self) -> None:
        """Clear all field values including manual overrides.

        WARNING: This removes manual corrections. Use with caution.
        """
        self.field_values.clear()
        self.manual_overrides.clear()
        logger.warning("Cleared ALL field values including manual overrides")


def apply_precedence_to_ticket_data(
    filename_hints: dict[str, Any] | None = None,
    folder_hints: dict[str, Any] | None = None,
    ocr_extractions: dict[str, tuple[Any, float]] | None = None,
    defaults: dict[str, Any] | None = None,
    manual_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply precedence rules to resolve ticket field values.

    This is a convenience function that creates a resolver, adds all values,
    and returns the resolved fields.

    Args:
        filename_hints: Values from filename parsing
        folder_hints: Values from folder structure
        ocr_extractions: Values from OCR with confidence scores
        defaults: Default values
        manual_overrides: Manual corrections (highest precedence)

    Returns:
        Dictionary of resolved field values

    Example:
        ```python
        resolved = apply_precedence_to_ticket_data(
            filename_hints={"date": "2024-10-17", "vendor": "WM"},
            ocr_extractions={
                "ticket_number": ("WM-12345678", 0.95),
                "quantity": (25.5, 0.88),
            },
            defaults={"ticket_type": "EXPORT"},
        )

        print(resolved["date"])  # "2024-10-17" (from filename)
        print(resolved["ticket_number"])  # "WM-12345678" (from OCR)
        ```
    """
    resolver = FieldPrecedenceResolver()

    # Add values in order (doesn't matter, precedence will sort it out)
    if defaults:
        resolver.add_defaults(defaults)

    if folder_hints:
        resolver.add_folder_hints(folder_hints)

    if ocr_extractions:
        resolver.add_ocr_extractions(ocr_extractions)

    if filename_hints:
        resolver.add_filename_hints(filename_hints)

    if manual_overrides:
        for field_name, value in manual_overrides.items():
            resolver.add_value(field_name, value, source="manual", confidence=1.0)

    # Resolve all fields
    resolved = resolver.resolve_all()

    # Return simple dictionary of values
    return {field_name: result.value for field_name, result in resolved.items()}
