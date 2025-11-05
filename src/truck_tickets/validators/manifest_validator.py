"""Manifest validation with 100% recall requirement.

This module implements CRITICAL regulatory compliance validation for contaminated
material manifests. Zero tolerance for missed manifests - every CLASS_2_CONTAMINATED
ticket MUST have a manifest number OR be routed to review queue with CRITICAL severity.

Regulatory Context:
    EPA and state regulations require manifest tracking for contaminated material
    disposal. Missing manifests can result in regulatory violations, fines, and
    potential project shutdowns.

Compliance Requirements:
    - 100% recall: Never silently fail on manifest extraction
    - CRITICAL severity: Missing manifests are highest priority
    - Audit trail: All validation results must be logged
    - Zero tolerance: No contaminated material without manifest tracking

Business Impact:
    - Regulatory compliance: Avoid EPA violations
    - Audit readiness: Complete manifest database
    - Risk mitigation: Prevent project delays from compliance issues
"""

import json
from datetime import date

from sqlalchemy.orm import Session

from ..models.sql_processing import ReviewQueue
from ..models.sql_truck_ticket import TruckTicket


class ManifestValidationResult:
    """Result of manifest validation check.

    Attributes:
        is_valid: Whether validation passed
        requires_manifest: Whether this material requires a manifest
        has_manifest: Whether manifest number is present
        manifest_number: The manifest number if present
        material_name: Name of the material being validated
        severity: Severity level (CRITICAL, WARNING, INFO)
        reason: Reason for validation failure
        suggested_action: Recommended action to resolve issue
    """

    def __init__(
        self,
        is_valid: bool,
        requires_manifest: bool,
        has_manifest: bool,
        manifest_number: str | None = None,
        material_name: str | None = None,
        severity: str = "INFO",
        reason: str | None = None,
        suggested_action: str | None = None,
    ):
        self.is_valid = is_valid
        self.requires_manifest = requires_manifest
        self.has_manifest = has_manifest
        self.manifest_number = manifest_number
        self.material_name = material_name
        self.severity = severity
        self.reason = reason
        self.suggested_action = suggested_action

    def __repr__(self) -> str:
        if self.is_valid:
            return f"<ManifestValidationResult(is_valid=True, has_manifest={self.has_manifest})>"
        return (
            f"<ManifestValidationResult(is_valid=False, "
            f"severity='{self.severity}', reason='{self.reason}')>"
        )


class ManifestValidator:
    """Validates manifest requirements with 100% recall.

    This validator implements the critical regulatory requirement that every
    CLASS_2_CONTAMINATED ticket must have a manifest number. If a manifest is
    missing, the ticket is immediately routed to review queue with CRITICAL severity.

    Material Classifications:
        - CLASS_2_CONTAMINATED: Requires manifest (CRITICAL if missing)
        - CONTAMINATED: Requires manifest (CRITICAL if missing)
        - Non-Contaminated: No manifest required
        - Spoils: No manifest required (unless contaminated)
        - Import: No manifest required

    Validation Rules:
        1. Check if material requires manifest
        2. If required, verify manifest_number is present and valid
        3. If missing: Route to CRITICAL review queue
        4. If present: Validate format (8-20 characters, alphanumeric)

    Example:
        ```python
        validator = ManifestValidator(session)

        result = validator.validate_manifest(
            material_name="CLASS_2_CONTAMINATED",
            manifest_number="WM-MAN-2024-001234",
            destination_name="WASTE_MANAGEMENT_LEWISVILLE"
        )

        if not result.is_valid:
            print(f"CRITICAL: {result.reason}")
            # Ticket automatically routed to review queue
        ```

    Attributes:
        session: SQLAlchemy database session
        contaminated_materials: List of material names requiring manifests
        manifest_destinations: List of destinations requiring manifests
    """

    # Materials that require manifest tracking
    # Note: Order matters - check specific patterns first
    CONTAMINATED_MATERIALS = [
        "CLASS_2_CONTAMINATED",
        "CLASS_2",
        "CONTAMINATED_SOIL",
        "HAZARDOUS",
        # Check for CONTAMINATED last, and exclude NON_CONTAMINATED
    ]

    # Materials that explicitly DON'T require manifests
    NON_CONTAMINATED_MATERIALS = [
        "NON_CONTAMINATED",
        "NON-CONTAMINATED",
        "CLEAN",
        "SPOILS",
        "IMPORT",
    ]

    # Destinations that require manifests
    MANIFEST_DESTINATIONS = [
        "WASTE_MANAGEMENT_LEWISVILLE",
        "WM_LEWISVILLE",
        "WASTE_MANAGEMENT",
    ]

    def __init__(self, session: Session):
        """Initialize manifest validator.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.contaminated_materials = self.CONTAMINATED_MATERIALS
        self.manifest_destinations = self.MANIFEST_DESTINATIONS

    def requires_manifest(
        self, material_name: str | None, destination_name: str | None = None
    ) -> bool:
        """Check if material/destination combination requires manifest.

        A manifest is required if:
        1. Material is contaminated (CLASS_2_CONTAMINATED, etc.)
        2. OR destination requires manifests (Waste Management Lewisville)

        Args:
            material_name: Name of the material
            destination_name: Name of the destination (optional)

        Returns:
            True if manifest is required, False otherwise

        Example:
            ```python
            requires = validator.requires_manifest(
                material_name="CLASS_2_CONTAMINATED",
                destination_name="WASTE_MANAGEMENT_LEWISVILLE"
            )
            # Returns: True
            ```
        """
        if not material_name:
            return False

        material_upper = material_name.upper()

        # First check if material is explicitly NON-contaminated
        for non_contaminated in self.NON_CONTAMINATED_MATERIALS:
            if non_contaminated in material_upper:
                # Check if destination overrides (e.g., WM Lewisville)
                if destination_name:
                    dest_upper = destination_name.upper()
                    for manifest_dest in self.manifest_destinations:
                        if manifest_dest in dest_upper:
                            return True
                return False

        # Check if material is contaminated
        for contaminated in self.contaminated_materials:
            if contaminated in material_upper:
                return True

        # Check for generic "CONTAMINATED" keyword (but we already excluded NON_CONTAMINATED)
        if "CONTAMINATED" in material_upper:
            return True

        # Check if destination requires manifests
        if destination_name:
            dest_upper = destination_name.upper()
            for manifest_dest in self.manifest_destinations:
                if manifest_dest in dest_upper:
                    return True

        return False

    def validate_manifest_format(self, manifest_number: str) -> bool:
        """Validate manifest number format.

        Valid manifest formats:
        - Length: 8-20 characters
        - Characters: Alphanumeric, hyphens, underscores
        - Examples: WM-MAN-2024-001234, PROFILE-12345678

        Args:
            manifest_number: Manifest number to validate

        Returns:
            True if format is valid, False otherwise

        Example:
            ```python
            is_valid = validator.validate_manifest_format("WM-MAN-2024-001234")
            # Returns: True

            is_valid = validator.validate_manifest_format("ABC")
            # Returns: False (too short)
            ```
        """
        if not manifest_number:
            return False

        # Remove whitespace
        manifest = manifest_number.strip()

        # Check length
        if len(manifest) < 8 or len(manifest) > 20:
            return False

        # Check characters (alphanumeric, hyphens, underscores)
        import re

        if not re.match(r"^[A-Z0-9\-_]+$", manifest.upper()):
            return False

        return True

    def validate_manifest(
        self,
        material_name: str | None,
        manifest_number: str | None,
        destination_name: str | None = None,
        ticket_id: int | None = None,
    ) -> ManifestValidationResult:
        """Validate manifest requirement for ticket.

        This is the main validation method that implements the 100% recall requirement.

        Validation Logic:
        1. Check if material requires manifest
        2. If not required: Return valid
        3. If required and present: Validate format
        4. If required and missing: Return CRITICAL failure

        Args:
            material_name: Name of the material
            manifest_number: Manifest number (can be None)
            destination_name: Destination name (optional)
            ticket_id: Ticket ID for logging (optional)

        Returns:
            ManifestValidationResult with validation status

        Example:
            ```python
            # Valid case - manifest present
            result = validator.validate_manifest(
                material_name="CLASS_2_CONTAMINATED",
                manifest_number="WM-MAN-2024-001234"
            )
            assert result.is_valid == True

            # CRITICAL case - manifest missing
            result = validator.validate_manifest(
                material_name="CLASS_2_CONTAMINATED",
                manifest_number=None
            )
            assert result.is_valid == False
            assert result.severity == "CRITICAL"
            ```
        """
        # Check if manifest is required
        requires = self.requires_manifest(material_name, destination_name)

        # If manifest not required, validation passes
        if not requires:
            return ManifestValidationResult(
                is_valid=True,
                requires_manifest=False,
                has_manifest=bool(manifest_number),
                manifest_number=manifest_number,
                material_name=material_name,
                severity="INFO",
                reason="Manifest not required for this material",
            )

        # Manifest is required - check if present
        if not manifest_number or not manifest_number.strip():
            # CRITICAL: Missing manifest for contaminated material
            return ManifestValidationResult(
                is_valid=False,
                requires_manifest=True,
                has_manifest=False,
                manifest_number=None,
                material_name=material_name,
                severity="CRITICAL",
                reason="MISSING_MANIFEST: Contaminated material requires manifest number",
                suggested_action="Manually review ticket and enter manifest number from physical ticket",
            )

        # Manifest present - validate format
        if not self.validate_manifest_format(manifest_number):
            # WARNING: Manifest present but invalid format
            return ManifestValidationResult(
                is_valid=False,
                requires_manifest=True,
                has_manifest=True,
                manifest_number=manifest_number,
                material_name=material_name,
                severity="WARNING",
                reason="INVALID_MANIFEST_FORMAT: Manifest number format is invalid",
                suggested_action=f"Verify manifest number '{manifest_number}' is correct (should be 8-20 alphanumeric characters)",
            )

        # All checks passed
        return ManifestValidationResult(
            is_valid=True,
            requires_manifest=True,
            has_manifest=True,
            manifest_number=manifest_number,
            material_name=material_name,
            severity="INFO",
            reason="Manifest validation passed",
        )

    def create_review_queue_entry(
        self,
        ticket_id: int,
        validation_result: ManifestValidationResult,
        file_path: str | None = None,
        page_num: int | None = None,
        detected_fields: dict | None = None,
    ) -> ReviewQueue:
        """Create CRITICAL review queue entry for missing manifest.

        Routes the ticket to review queue with CRITICAL severity. This ensures
        100% recall - no contaminated material ticket is processed without
        manifest tracking.

        Args:
            ticket_id: ID of the ticket requiring review
            validation_result: Result from validate_manifest()
            file_path: Path to source file (optional)
            page_num: Page number in file (optional)
            detected_fields: Dictionary of detected fields (optional)

        Returns:
            Created ReviewQueue entry

        Example:
            ```python
            result = validator.validate_manifest(
                material_name="CLASS_2_CONTAMINATED",
                manifest_number=None
            )

            if not result.is_valid:
                review_entry = validator.create_review_queue_entry(
                    ticket_id=456,
                    validation_result=result,
                    file_path="batch1/file1.pdf",
                    page_num=1
                )
                # Ticket now in CRITICAL review queue
            ```
        """
        # Get ticket for context
        ticket = self.session.get(TruckTicket, ticket_id)
        if not ticket:
            raise ValueError(f"Ticket ID {ticket_id} not found in database")

        # Build detected fields JSON
        if detected_fields is None:
            detected_fields = {
                "ticket_number": ticket.ticket_number,
                "ticket_date": str(ticket.ticket_date),
                "material": validation_result.material_name,
                "manifest_number": validation_result.manifest_number,
                "requires_manifest": validation_result.requires_manifest,
            }

        # Build suggested fixes JSON
        suggested_fixes = {
            "action": validation_result.suggested_action
            or "Manually enter manifest number from physical ticket",
            "material": validation_result.material_name,
            "requires_manifest": True,
            "regulatory_note": "EPA/state regulations require manifest tracking for contaminated material",
            "priority": "CRITICAL - Must resolve before processing",
        }

        # Create review queue entry
        review_entry = ReviewQueue(
            ticket_id=ticket_id,
            page_id=f"{file_path or ticket.file_id}#page{page_num or ticket.file_page or 1}",
            reason=validation_result.reason or "MISSING_MANIFEST",
            severity=validation_result.severity,
            file_path=file_path or ticket.file_id,
            page_num=page_num or ticket.file_page,
            detected_fields=json.dumps(detected_fields),
            suggested_fixes=json.dumps(suggested_fixes),
            resolved=False,
        )

        self.session.add(review_entry)
        self.session.commit()

        return review_entry

    def validate_and_route(
        self,
        ticket_id: int,
        material_name: str | None,
        manifest_number: str | None,
        destination_name: str | None = None,
        file_path: str | None = None,
        page_num: int | None = None,
    ) -> ManifestValidationResult:
        """Validate manifest and automatically route to review queue if invalid.

        This is a convenience method that combines validate_manifest() and
        create_review_queue_entry() into a single call.

        If validation fails:
        1. Validates manifest requirement
        2. Creates review queue entry if invalid
        3. Returns validation result

        Args:
            ticket_id: ID of the ticket being validated
            material_name: Name of the material
            manifest_number: Manifest number (can be None)
            destination_name: Destination name (optional)
            file_path: Path to source file (optional)
            page_num: Page number (optional)

        Returns:
            ManifestValidationResult

        Example:
            ```python
            result = validator.validate_and_route(
                ticket_id=456,
                material_name="CLASS_2_CONTAMINATED",
                manifest_number=None,
                file_path="batch1/file1.pdf",
                page_num=1
            )

            if not result.is_valid:
                print(f"CRITICAL: Routed to review queue - {result.reason}")
            ```
        """
        # Validate manifest
        result = self.validate_manifest(
            material_name=material_name,
            manifest_number=manifest_number,
            destination_name=destination_name,
            ticket_id=ticket_id,
        )

        # If validation failed, route to review queue
        if not result.is_valid:
            self.create_review_queue_entry(
                ticket_id=ticket_id,
                validation_result=result,
                file_path=file_path,
                page_num=page_num,
            )

        return result

    def get_manifest_statistics(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> dict:
        """Get statistics about manifest validation.

        Returns counts and metrics about manifest compliance in the system.
        Critical for regulatory reporting and audit readiness.

        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dictionary with manifest statistics

        Example:
            ```python
            stats = validator.get_manifest_statistics(
                start_date=date(2024, 10, 1),
                end_date=date(2024, 10, 31)
            )
            print(f"Contaminated tickets: {stats['contaminated_tickets']}")
            print(f"Missing manifests: {stats['missing_manifests']}")
            print(f"Compliance rate: {stats['compliance_rate']:.2%}")
            ```
        """

        # Build base query
        query = self.session.query(TruckTicket)

        if start_date:
            query = query.filter(TruckTicket.ticket_date >= start_date)
        if end_date:
            query = query.filter(TruckTicket.ticket_date <= end_date)

        # Get all tickets
        all_tickets = query.count()

        # Get contaminated tickets (tickets that should have manifests)
        # This is a simplified check - in production, join with materials table
        contaminated_query = query.filter(TruckTicket.manifest_number.isnot(None))
        tickets_with_manifests = contaminated_query.count()

        # Get tickets in review queue for missing manifests
        review_query = self.session.query(ReviewQueue).filter(
            ReviewQueue.reason.like("%MISSING_MANIFEST%"), ReviewQueue.resolved == False
        )

        if start_date or end_date:
            # Join with tickets to filter by date
            review_query = review_query.join(TruckTicket)
            if start_date:
                review_query = review_query.filter(
                    TruckTicket.ticket_date >= start_date
                )
            if end_date:
                review_query = review_query.filter(TruckTicket.ticket_date <= end_date)

        missing_manifests = review_query.count()

        # Calculate compliance rate
        # Note: This is simplified - in production, need to identify which tickets
        # actually require manifests based on material type
        total_requiring_manifests = tickets_with_manifests + missing_manifests
        compliance_rate = (
            tickets_with_manifests / total_requiring_manifests
            if total_requiring_manifests > 0
            else 1.0
        )

        return {
            "total_tickets": all_tickets,
            "tickets_with_manifests": tickets_with_manifests,
            "missing_manifests": missing_manifests,
            "total_requiring_manifests": total_requiring_manifests,
            "compliance_rate": compliance_rate,
            "recall_rate": (
                1.0
                if missing_manifests == 0
                else (tickets_with_manifests / total_requiring_manifests)
            ),
            "start_date": start_date,
            "end_date": end_date,
        }
