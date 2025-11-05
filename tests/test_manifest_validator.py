"""Comprehensive tests for manifest validation with 100% recall requirement.

Tests the CRITICAL regulatory compliance validation for contaminated material manifests.
Zero tolerance for missed manifests - every CLASS_2_CONTAMINATED ticket MUST have
a manifest number OR be routed to review queue with CRITICAL severity.
"""

import pytest
from datetime import date
from unittest.mock import Mock

from src.truck_tickets.validators.manifest_validator import (
    ManifestValidator,
    ManifestValidationResult
)
from src.truck_tickets.models.sql_truck_ticket import TruckTicket
from src.truck_tickets.models.sql_processing import ReviewQueue


class TestManifestValidationResult:
    """Test ManifestValidationResult data class."""

    def test_valid_result(self):
        """Test result for valid manifest."""
        result = ManifestValidationResult(
            is_valid=True,
            requires_manifest=True,
            has_manifest=True,
            manifest_number="WM-MAN-2024-001234",
            material_name="CLASS_2_CONTAMINATED",
            severity="INFO"
        )

        assert result.is_valid
        assert result.requires_manifest
        assert result.has_manifest
        assert result.manifest_number == "WM-MAN-2024-001234"
        assert result.severity == "INFO"

    def test_critical_failure(self):
        """Test result for missing manifest (CRITICAL)."""
        result = ManifestValidationResult(
            is_valid=False,
            requires_manifest=True,
            has_manifest=False,
            material_name="CLASS_2_CONTAMINATED",
            severity="CRITICAL",
            reason="MISSING_MANIFEST"
        )

        assert not result.is_valid
        assert result.requires_manifest
        assert not result.has_manifest
        assert result.severity == "CRITICAL"
        assert "MISSING_MANIFEST" in result.reason

    def test_repr_valid(self):
        """Test string representation for valid result."""
        result = ManifestValidationResult(
            is_valid=True,
            requires_manifest=False,
            has_manifest=False
        )
        repr_str = repr(result)

        assert "is_valid=True" in repr_str

    def test_repr_invalid(self):
        """Test string representation for invalid result."""
        result = ManifestValidationResult(
            is_valid=False,
            requires_manifest=True,
            has_manifest=False,
            severity="CRITICAL",
            reason="MISSING_MANIFEST"
        )
        repr_str = repr(result)

        assert "is_valid=False" in repr_str
        assert "CRITICAL" in repr_str
        assert "MISSING_MANIFEST" in repr_str


class TestManifestValidator:
    """Test ManifestValidator class."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = Mock()
        session.get = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.query = Mock()
        return session

    @pytest.fixture
    def validator(self, mock_session):
        """Create ManifestValidator instance."""
        return ManifestValidator(mock_session)

    def test_init(self, mock_session):
        """Test validator initialization."""
        validator = ManifestValidator(mock_session)

        assert validator.session == mock_session
        assert len(validator.contaminated_materials) > 0
        assert "CLASS_2_CONTAMINATED" in validator.contaminated_materials
        assert len(validator.manifest_destinations) > 0
        assert "WASTE_MANAGEMENT_LEWISVILLE" in validator.manifest_destinations

    def test_requires_manifest_contaminated_material(self, validator):
        """Test that contaminated materials require manifests."""
        # CLASS_2_CONTAMINATED
        assert validator.requires_manifest("CLASS_2_CONTAMINATED")
        assert validator.requires_manifest("class_2_contaminated")  # Case insensitive

        # CONTAMINATED
        assert validator.requires_manifest("CONTAMINATED")
        assert validator.requires_manifest("contaminated_soil")

    def test_requires_manifest_clean_material(self, validator):
        """Test that clean materials don't require manifests."""
        assert not validator.requires_manifest("NON_CONTAMINATED")
        assert not validator.requires_manifest("CLEAN_FILL")
        assert not validator.requires_manifest("SPOILS")
        assert not validator.requires_manifest("IMPORT")

    def test_requires_manifest_by_destination(self, validator):
        """Test that certain destinations require manifests."""
        # Waste Management Lewisville requires manifests
        assert validator.requires_manifest(
            material_name="SPOILS",
            destination_name="WASTE_MANAGEMENT_LEWISVILLE"
        )

        # Other destinations don't
        assert not validator.requires_manifest(
            material_name="SPOILS",
            destination_name="LDI_YARD"
        )

    def test_requires_manifest_none_material(self, validator):
        """Test handling of None material."""
        assert not validator.requires_manifest(None)
        assert not validator.requires_manifest(None, "WASTE_MANAGEMENT_LEWISVILLE")

    def test_validate_manifest_format_valid(self, validator):
        """Test validation of valid manifest formats."""
        # Standard WM format
        assert validator.validate_manifest_format("WM-MAN-2024-001234")

        # Profile format
        assert validator.validate_manifest_format("PROFILE-12345678")

        # Alphanumeric with hyphens
        assert validator.validate_manifest_format("ABC123-DEF456")

        # Minimum length (8 chars)
        assert validator.validate_manifest_format("12345678")

        # Maximum length (20 chars)
        assert validator.validate_manifest_format("12345678901234567890")

    def test_validate_manifest_format_invalid(self, validator):
        """Test validation of invalid manifest formats."""
        # Too short
        assert not validator.validate_manifest_format("ABC123")

        # Too long
        assert not validator.validate_manifest_format("123456789012345678901")

        # Invalid characters (spaces)
        assert not validator.validate_manifest_format("WM MAN 2024")

        # Invalid characters (special chars)
        assert not validator.validate_manifest_format("WM@MAN#2024")

        # Empty
        assert not validator.validate_manifest_format("")
        assert not validator.validate_manifest_format(None)

    def test_validate_manifest_not_required(self, validator):
        """Test validation when manifest not required."""
        result = validator.validate_manifest(
            material_name="NON_CONTAMINATED",
            manifest_number=None
        )

        assert result.is_valid
        assert not result.requires_manifest
        assert not result.has_manifest
        assert result.severity == "INFO"

    def test_validate_manifest_required_and_present(self, validator):
        """Test validation when manifest required and present."""
        result = validator.validate_manifest(
            material_name="CLASS_2_CONTAMINATED",
            manifest_number="WM-MAN-2024-001234"
        )

        assert result.is_valid
        assert result.requires_manifest
        assert result.has_manifest
        assert result.manifest_number == "WM-MAN-2024-001234"
        assert result.severity == "INFO"

    def test_validate_manifest_required_but_missing(self, validator):
        """Test CRITICAL validation failure when manifest missing."""
        result = validator.validate_manifest(
            material_name="CLASS_2_CONTAMINATED",
            manifest_number=None
        )

        assert not result.is_valid
        assert result.requires_manifest
        assert not result.has_manifest
        assert result.severity == "CRITICAL"
        assert "MISSING_MANIFEST" in result.reason
        assert result.suggested_action is not None

    def test_validate_manifest_required_but_empty_string(self, validator):
        """Test CRITICAL failure for empty string manifest."""
        result = validator.validate_manifest(
            material_name="CLASS_2_CONTAMINATED",
            manifest_number=""
        )

        assert not result.is_valid
        assert result.severity == "CRITICAL"

        # Whitespace only
        result = validator.validate_manifest(
            material_name="CLASS_2_CONTAMINATED",
            manifest_number="   "
        )

        assert not result.is_valid
        assert result.severity == "CRITICAL"

    def test_validate_manifest_invalid_format(self, validator):
        """Test WARNING for invalid manifest format."""
        result = validator.validate_manifest(
            material_name="CLASS_2_CONTAMINATED",
            manifest_number="ABC"  # Too short
        )

        assert not result.is_valid
        assert result.requires_manifest
        assert result.has_manifest
        assert result.severity == "WARNING"
        assert "INVALID_MANIFEST_FORMAT" in result.reason

    def test_create_review_queue_entry(self, validator, mock_session):
        """Test creating review queue entry for missing manifest."""
        # Create mock ticket
        mock_ticket = Mock(spec=TruckTicket)
        mock_ticket.ticket_id = 456
        mock_ticket.ticket_number = "WM-12345678"
        mock_ticket.ticket_date = date(2024, 10, 17)
        mock_ticket.file_id = "batch1/file1.pdf"
        mock_ticket.file_page = 1
        mock_session.get.return_value = mock_ticket

        # Create validation result
        validation_result = ManifestValidationResult(
            is_valid=False,
            requires_manifest=True,
            has_manifest=False,
            material_name="CLASS_2_CONTAMINATED",
            severity="CRITICAL",
            reason="MISSING_MANIFEST",
            suggested_action="Manually enter manifest from physical ticket"
        )

        # Create review entry
        review_entry = validator.create_review_queue_entry(
            ticket_id=456,
            validation_result=validation_result,
            file_path="batch1/file1.pdf",
            page_num=1
        )

        assert isinstance(review_entry, ReviewQueue)
        assert review_entry.ticket_id == 456
        assert review_entry.reason == "MISSING_MANIFEST"
        assert review_entry.severity == "CRITICAL"
        assert not review_entry.resolved
        assert mock_session.add.called
        assert mock_session.commit.called

    def test_create_review_queue_entry_ticket_not_found(self, validator, mock_session):
        """Test error handling when ticket not found."""
        mock_session.get.return_value = None

        validation_result = ManifestValidationResult(
            is_valid=False,
            requires_manifest=True,
            has_manifest=False,
            severity="CRITICAL"
        )

        with pytest.raises(ValueError, match="Ticket ID .* not found"):
            validator.create_review_queue_entry(
                ticket_id=999,
                validation_result=validation_result
            )

    def test_validate_and_route_valid(self, validator, mock_session):
        """Test validate_and_route when manifest is valid."""
        # Mock ticket
        mock_ticket = Mock(spec=TruckTicket)
        mock_ticket.ticket_id = 456
        mock_session.get.return_value = mock_ticket

        result = validator.validate_and_route(
            ticket_id=456,
            material_name="CLASS_2_CONTAMINATED",
            manifest_number="WM-MAN-2024-001234"
        )

        assert result.is_valid
        # Should not create review entry
        assert not mock_session.add.called

    def test_validate_and_route_invalid(self, validator, mock_session):
        """Test validate_and_route when manifest missing (CRITICAL)."""
        # Mock ticket
        mock_ticket = Mock(spec=TruckTicket)
        mock_ticket.ticket_id = 456
        mock_ticket.ticket_number = "WM-12345678"
        mock_ticket.ticket_date = date(2024, 10, 17)
        mock_ticket.file_id = "batch1/file1.pdf"
        mock_ticket.file_page = 1
        mock_session.get.return_value = mock_ticket

        result = validator.validate_and_route(
            ticket_id=456,
            material_name="CLASS_2_CONTAMINATED",
            manifest_number=None,
            file_path="batch1/file1.pdf",
            page_num=1
        )

        assert not result.is_valid
        assert result.severity == "CRITICAL"
        # Should create review entry
        assert mock_session.add.called
        assert mock_session.commit.called


class TestManifestValidatorEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def validator(self, mock_session):
        """Create validator instance."""
        return ManifestValidator(mock_session)

    def test_case_insensitive_material_matching(self, validator):
        """Test that material matching is case-insensitive."""
        # All should require manifests
        assert validator.requires_manifest("CLASS_2_CONTAMINATED")
        assert validator.requires_manifest("class_2_contaminated")
        assert validator.requires_manifest("Class_2_Contaminated")
        assert validator.requires_manifest("CLASS_2_contaminated")

    def test_partial_material_name_matching(self, validator):
        """Test that partial matches work for contaminated materials."""
        # Should match because contains "CONTAMINATED"
        assert validator.requires_manifest("CONTAMINATED_SOIL_TYPE_A")
        assert validator.requires_manifest("SOIL_CONTAMINATED")
        assert validator.requires_manifest("CLASS_2_CONTAMINATED_MATERIAL")

    def test_manifest_format_with_whitespace(self, validator):
        """Test manifest format validation with whitespace."""
        # Should handle leading/trailing whitespace
        assert validator.validate_manifest_format("  WM-MAN-2024-001234  ")

    def test_multiple_contaminated_keywords(self, validator):
        """Test material with multiple contaminated keywords."""
        result = validator.validate_manifest(
            material_name="CLASS_2_CONTAMINATED_HAZARDOUS",
            manifest_number="WM-MAN-2024-001234"
        )

        assert result.is_valid
        assert result.requires_manifest

    def test_destination_requires_manifest_overrides_material(self, validator):
        """Test that manifest-requiring destination overrides clean material."""
        # Clean material to WM Lewisville should require manifest
        assert validator.requires_manifest(
            material_name="CLEAN_FILL",
            destination_name="WASTE_MANAGEMENT_LEWISVILLE"
        )

    def test_zero_tolerance_for_missing_manifests(self, validator):
        """Test 100% recall requirement - no silent failures."""
        # Every contaminated material without manifest should be CRITICAL
        contaminated_materials = [
            "CLASS_2_CONTAMINATED",
            "CONTAMINATED",
            "CONTAMINATED_SOIL",
            "CLASS_2"
        ]

        for material in contaminated_materials:
            result = validator.validate_manifest(
                material_name=material,
                manifest_number=None
            )

            assert not result.is_valid, f"Failed for {material}"
            assert result.severity == "CRITICAL", f"Not CRITICAL for {material}"
            assert "MISSING_MANIFEST" in result.reason, f"Wrong reason for {material}"


class TestManifestValidatorCompliance:
    """Test regulatory compliance requirements."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def validator(self, mock_session):
        """Create validator instance."""
        return ManifestValidator(mock_session)

    def test_100_percent_recall_requirement(self, validator):
        """Test that 100% of contaminated tickets are caught."""
        # Test matrix of contaminated materials
        test_cases = [
            ("CLASS_2_CONTAMINATED", None, False, "CRITICAL"),
            ("CONTAMINATED", None, False, "CRITICAL"),
            ("CONTAMINATED_SOIL", None, False, "CRITICAL"),
            ("CLASS_2", None, False, "CRITICAL"),
            ("HAZARDOUS", None, False, "CRITICAL"),
        ]

        for material, manifest, should_be_valid, expected_severity in test_cases:
            result = validator.validate_manifest(
                material_name=material,
                manifest_number=manifest
            )

            assert result.is_valid == should_be_valid, \
                f"Failed for {material}: expected valid={should_be_valid}, got {result.is_valid}"
            assert result.severity == expected_severity, \
                f"Failed for {material}: expected severity={expected_severity}, got {result.severity}"

    def test_no_false_negatives(self, validator):
        """Test that we never miss a contaminated ticket (no false negatives)."""
        # This is the CRITICAL requirement - we can have false positives
        # (flagging clean material) but NEVER false negatives (missing contaminated)

        contaminated_variants = [
            "CLASS_2_CONTAMINATED",
            "class_2_contaminated",
            "CONTAMINATED",
            "contaminated",
            "CONTAMINATED_SOIL",
            "SOIL_CONTAMINATED",
            "CLASS_2",
            "HAZARDOUS",
            "hazardous_material"
        ]

        for material in contaminated_variants:
            result = validator.validate_manifest(
                material_name=material,
                manifest_number=None
            )

            # MUST be invalid and CRITICAL
            assert not result.is_valid, \
                f"FALSE NEGATIVE: {material} passed validation without manifest!"
            assert result.severity == "CRITICAL", \
                f"FALSE NEGATIVE: {material} not marked CRITICAL!"

    def test_regulatory_audit_trail(self, validator, mock_session):
        """Test that all validation failures create audit trail."""
        # Mock ticket
        mock_ticket = Mock(spec=TruckTicket)
        mock_ticket.ticket_id = 456
        mock_ticket.ticket_number = "WM-12345678"
        mock_ticket.ticket_date = date(2024, 10, 17)
        mock_ticket.file_id = "batch1/file1.pdf"
        mock_ticket.file_page = 1
        mock_session.get.return_value = mock_ticket

        # Validate and route
        result = validator.validate_and_route(
            ticket_id=456,
            material_name="CLASS_2_CONTAMINATED",
            manifest_number=None
        )

        # Must create review queue entry (audit trail)
        assert not result.is_valid
        assert mock_session.add.called
        assert mock_session.commit.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
