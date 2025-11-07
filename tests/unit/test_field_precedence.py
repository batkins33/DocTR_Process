"""Unit tests for field precedence resolution logic.

Tests Issue #10: Field extraction precedence logic
Precedence order: filename > folder > OCR > defaults
Manual corrections are never overridden.
"""

import pytest
from src.truck_tickets.utils.field_precedence import (
    FieldPrecedenceResolver,
    FieldValue,
    PrecedenceLevel,
    apply_precedence_to_ticket_data,
)


class TestPrecedenceLevel:
    """Test precedence level determination."""

    def test_manual_precedence(self):
        """Manual corrections have highest precedence."""
        level = PrecedenceLevel.from_source_and_confidence("manual", 1.0)
        assert level == PrecedenceLevel.MANUAL
        assert level.value == 100

    def test_filename_precedence(self):
        """Filename has second highest precedence."""
        level = PrecedenceLevel.from_source_and_confidence("filename", 1.0)
        assert level == PrecedenceLevel.FILENAME
        assert level.value == 90

    def test_folder_precedence(self):
        """Folder has third highest precedence."""
        level = PrecedenceLevel.from_source_and_confidence("folder", 0.9)
        assert level == PrecedenceLevel.FOLDER
        assert level.value == 80

    def test_ocr_high_confidence(self):
        """High confidence OCR (>0.9)."""
        level = PrecedenceLevel.from_source_and_confidence("ocr", 0.95)
        assert level == PrecedenceLevel.OCR_HIGH
        assert level.value == 70

    def test_ocr_medium_confidence(self):
        """Medium confidence OCR (0.7-0.9)."""
        level = PrecedenceLevel.from_source_and_confidence("ocr", 0.85)
        assert level == PrecedenceLevel.OCR_MEDIUM
        assert level.value == 60

    def test_ocr_low_confidence(self):
        """Low confidence OCR (<0.7)."""
        level = PrecedenceLevel.from_source_and_confidence("ocr", 0.5)
        assert level == PrecedenceLevel.OCR_LOW
        assert level.value == 50

    def test_default_precedence(self):
        """Defaults have lowest precedence."""
        level = PrecedenceLevel.from_source_and_confidence("default", 0.5)
        assert level == PrecedenceLevel.DEFAULT
        assert level.value == 10


class TestFieldValue:
    """Test FieldValue dataclass."""

    def test_field_value_creation(self):
        """Create field value with automatic precedence calculation."""
        fv = FieldValue(
            field_name="date",
            value="2024-10-17",
            source="filename",
            confidence=1.0,
        )

        assert fv.field_name == "date"
        assert fv.value == "2024-10-17"
        assert fv.source == "filename"
        assert fv.confidence == 1.0
        assert fv.precedence == PrecedenceLevel.FILENAME

    def test_field_value_repr(self):
        """Test string representation."""
        fv = FieldValue(
            field_name="vendor",
            value="WM",
            source="ocr",
            confidence=0.95,
        )

        repr_str = repr(fv)
        assert "vendor" in repr_str
        assert "WM" in repr_str
        assert "ocr" in repr_str


class TestFieldPrecedenceResolver:
    """Test field precedence resolution."""

    def test_single_value_resolution(self):
        """Resolve field with single value."""
        resolver = FieldPrecedenceResolver()
        resolver.add_value("date", "2024-10-17", source="filename", confidence=1.0)

        result = resolver.resolve("date")

        assert result is not None
        assert result.value == "2024-10-17"
        assert result.source == "filename"
        assert result.precedence == PrecedenceLevel.FILENAME

    def test_filename_beats_ocr(self):
        """Filename value should beat OCR value."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value("date", "2024-10-17", source="filename", confidence=1.0)
        resolver.add_value("date", "2024-10-18", source="ocr", confidence=0.95)

        result = resolver.resolve("date")

        assert result.value == "2024-10-17"
        assert result.source == "filename"
        assert len(result.alternatives) == 1
        assert result.alternatives[0].value == "2024-10-18"

    def test_ocr_beats_default(self):
        """OCR value should beat default value."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value("vendor", "WM", source="ocr", confidence=0.85)
        resolver.add_value("vendor", "UNKNOWN", source="default", confidence=0.5)

        result = resolver.resolve("vendor")

        assert result.value == "WM"
        assert result.source == "ocr"

    def test_high_confidence_ocr_beats_low_confidence(self):
        """Higher confidence OCR should win."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value(
            "ticket_number", "WM-12345678", source="ocr", confidence=0.95
        )
        resolver.add_value(
            "ticket_number", "WM-12345679", source="ocr", confidence=0.60
        )

        result = resolver.resolve("ticket_number")

        assert result.value == "WM-12345678"
        assert result.precedence == PrecedenceLevel.OCR_HIGH

    def test_manual_override_never_overridden(self):
        """Manual corrections should never be overridden."""
        resolver = FieldPrecedenceResolver()

        # Add manual override
        resolver.add_value("date", "2024-10-15", source="manual", confidence=1.0)

        # Try to add higher precedence values
        resolver.add_value("date", "2024-10-17", source="filename", confidence=1.0)
        resolver.add_value("date", "2024-10-18", source="ocr", confidence=0.95)

        result = resolver.resolve("date")

        # Manual should always win
        assert result.value == "2024-10-15"
        assert result.source == "manual"
        assert result.precedence == PrecedenceLevel.MANUAL

    def test_none_values_ignored(self):
        """None values should be ignored."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value("material", None, source="filename", confidence=1.0)
        resolver.add_value("material", "CLASS_2", source="ocr", confidence=0.85)

        result = resolver.resolve("material")

        assert result.value == "CLASS_2"
        assert result.source == "ocr"

    def test_resolve_nonexistent_field(self):
        """Resolving non-existent field returns None."""
        resolver = FieldPrecedenceResolver()

        result = resolver.resolve("nonexistent")

        assert result is None

    def test_resolve_all_fields(self):
        """Resolve all fields at once."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value("date", "2024-10-17", source="filename", confidence=1.0)
        resolver.add_value("vendor", "WM", source="ocr", confidence=0.95)
        resolver.add_value("quantity", 25.5, source="ocr", confidence=0.88)

        resolved = resolver.resolve_all()

        assert len(resolved) == 3
        assert resolved["date"].value == "2024-10-17"
        assert resolved["vendor"].value == "WM"
        assert resolved["quantity"].value == 25.5

    def test_add_filename_hints(self):
        """Add multiple values from filename hints."""
        resolver = FieldPrecedenceResolver()

        hints = {
            "date": "2024-10-17",
            "vendor": "WM",
            "job_code": "24-105",
        }

        resolver.add_filename_hints(hints)

        resolved = resolver.resolve_all()

        assert len(resolved) == 3
        assert all(r.source == "filename" for r in resolved.values())

    def test_add_folder_hints(self):
        """Add multiple values from folder structure."""
        resolver = FieldPrecedenceResolver()

        hints = {
            "job_code": "24-105",
            "area": "PODIUM",
        }

        resolver.add_folder_hints(hints)

        resolved = resolver.resolve_all()

        assert len(resolved) == 2
        assert all(r.source == "folder" for r in resolved.values())

    def test_add_ocr_extractions(self):
        """Add multiple values from OCR extraction."""
        resolver = FieldPrecedenceResolver()

        extractions = {
            "ticket_number": ("WM-12345678", 0.95),
            "quantity": (25.5, 0.88),
            "manifest_number": ("WM-MAN-001234", 0.92),
        }

        resolver.add_ocr_extractions(extractions)

        resolved = resolver.resolve_all()

        assert len(resolved) == 3
        assert all(r.source == "ocr" for r in resolved.values())

    def test_add_defaults(self):
        """Add default values."""
        resolver = FieldPrecedenceResolver()

        defaults = {
            "ticket_type": "EXPORT",
            "quantity_unit": "TONS",
        }

        resolver.add_defaults(defaults)

        resolved = resolver.resolve_all()

        assert len(resolved) == 2
        assert all(r.source == "default" for r in resolved.values())

    def test_has_manual_override(self):
        """Check if field has manual override."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value("date", "2024-10-15", source="manual", confidence=1.0)
        resolver.add_value("vendor", "WM", source="filename", confidence=1.0)

        assert resolver.has_manual_override("date") is True
        assert resolver.has_manual_override("vendor") is False

    def test_clear_preserves_manual_overrides(self):
        """Clear should preserve manual overrides."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value("date", "2024-10-15", source="manual", confidence=1.0)
        resolver.add_value("vendor", "WM", source="filename", confidence=1.0)

        resolver.clear()

        # Manual override should still exist
        assert resolver.has_manual_override("date") is True

        # But other values should be cleared
        result = resolver.resolve("vendor")
        assert result is None

    def test_clear_all_removes_everything(self):
        """Clear all should remove manual overrides too."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value("date", "2024-10-15", source="manual", confidence=1.0)
        resolver.add_value("vendor", "WM", source="filename", confidence=1.0)

        resolver.clear_all()

        assert resolver.has_manual_override("date") is False
        assert resolver.resolve("date") is None
        assert resolver.resolve("vendor") is None

    def test_resolution_summary(self):
        """Get resolution summary with alternatives."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value("date", "2024-10-17", source="filename", confidence=1.0)
        resolver.add_value("date", "2024-10-18", source="ocr", confidence=0.85)
        resolver.add_value("date", "2024-10-16", source="default", confidence=0.5)

        summary = resolver.get_resolution_summary()

        assert "date" in summary
        assert summary["date"]["value"] == "2024-10-17"
        assert summary["date"]["source"] == "filename"
        assert summary["date"]["num_alternatives"] == 2
        assert len(summary["date"]["alternatives"]) == 2


class TestApplyPrecedenceToTicketData:
    """Test convenience function for applying precedence."""

    def test_apply_precedence_basic(self):
        """Apply precedence with basic data."""
        resolved = apply_precedence_to_ticket_data(
            filename_hints={"date": "2024-10-17", "vendor": "WM"},
            ocr_extractions={
                "ticket_number": ("WM-12345678", 0.95),
                "quantity": (25.5, 0.88),
            },
            defaults={"ticket_type": "EXPORT"},
        )

        assert resolved["date"] == "2024-10-17"
        assert resolved["vendor"] == "WM"
        assert resolved["ticket_number"] == "WM-12345678"
        assert resolved["quantity"] == 25.5
        assert resolved["ticket_type"] == "EXPORT"

    def test_apply_precedence_with_manual_override(self):
        """Manual overrides should win."""
        resolved = apply_precedence_to_ticket_data(
            filename_hints={"date": "2024-10-17"},
            ocr_extractions={"date": ("2024-10-18", 0.95)},
            manual_overrides={"date": "2024-10-15"},
        )

        assert resolved["date"] == "2024-10-15"

    def test_apply_precedence_all_sources(self):
        """Test with all source types."""
        resolved = apply_precedence_to_ticket_data(
            filename_hints={"vendor": "WM", "job_code": "24-105"},
            folder_hints={"area": "PODIUM"},
            ocr_extractions={
                "ticket_number": ("WM-12345678", 0.95),
                "quantity": (25.5, 0.88),
                "vendor": ("WASTE_MANAGEMENT", 0.92),  # Should lose to filename
            },
            defaults={"ticket_type": "EXPORT", "quantity_unit": "TONS"},
            manual_overrides={"material": "CLASS_2_CONTAMINATED"},
        )

        # Filename wins for vendor
        assert resolved["vendor"] == "WM"

        # Manual override wins for material
        assert resolved["material"] == "CLASS_2_CONTAMINATED"

        # OCR values used when no higher precedence
        assert resolved["ticket_number"] == "WM-12345678"
        assert resolved["quantity"] == 25.5

        # Folder hint used
        assert resolved["area"] == "PODIUM"

        # Defaults used when nothing else available
        assert resolved["ticket_type"] == "EXPORT"
        assert resolved["quantity_unit"] == "TONS"


class TestRealWorldScenarios:
    """Test real-world precedence scenarios."""

    def test_complete_ticket_resolution(self):
        """Resolve all fields for a complete ticket."""
        resolver = FieldPrecedenceResolver()

        # Filename provides date and vendor
        resolver.add_filename_hints(
            {
                "date": "2024-10-17",
                "vendor": "WM",
                "job_code": "24-105",
            }
        )

        # Folder provides area
        resolver.add_folder_hints(
            {
                "area": "PODIUM",
                "flow": "EXPORT",
            }
        )

        # OCR extracts ticket details
        resolver.add_ocr_extractions(
            {
                "ticket_number": ("WM-12345678", 0.95),
                "manifest_number": ("WM-MAN-001234", 0.92),
                "quantity": (25.5, 0.88),
                "material": ("CLASS 2 CONTAMINATED", 0.85),
                "vendor": (
                    "WASTE MANAGEMENT LEWISVILLE",
                    0.90,
                ),  # Should lose to filename
            }
        )

        # Defaults for missing fields
        resolver.add_defaults(
            {
                "ticket_type": "EXPORT",
                "quantity_unit": "TONS",
            }
        )

        resolved = resolver.resolve_all()

        # Verify precedence worked correctly
        assert resolved["date"].source == "filename"
        assert resolved["vendor"].source == "filename"  # Filename beats OCR
        assert resolved["vendor"].value == "WM"
        assert resolved["job_code"].source == "filename"
        assert resolved["area"].source == "folder"
        assert resolved["ticket_number"].source == "ocr"
        assert resolved["quantity"].source == "ocr"
        assert resolved["ticket_type"].source == "default"

    def test_user_correction_scenario(self):
        """User corrects an incorrectly extracted field."""
        resolver = FieldPrecedenceResolver()

        # Initial extraction
        resolver.add_ocr_extractions(
            {
                "date": ("2024-10-18", 0.85),  # Wrong date
                "quantity": (25.5, 0.88),
            }
        )

        # User corrects the date
        resolver.add_value("date", "2024-10-17", source="manual", confidence=1.0)

        # Later processing tries to re-extract
        resolver.add_value("date", "2024-10-19", source="ocr", confidence=0.95)

        result = resolver.resolve("date")

        # Manual correction should always win
        assert result.value == "2024-10-17"
        assert result.source == "manual"
        assert result.precedence == PrecedenceLevel.MANUAL

    def test_low_confidence_ocr_with_defaults(self):
        """Low confidence OCR should still beat defaults."""
        resolver = FieldPrecedenceResolver()

        resolver.add_value("material", "UNKNOWN", source="default", confidence=0.5)
        resolver.add_value(
            "material", "CLASS 2", source="ocr", confidence=0.55
        )  # Low but > default

        result = resolver.resolve("material")

        assert result.value == "CLASS 2"
        assert result.source == "ocr"
        assert result.precedence == PrecedenceLevel.OCR_LOW


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
