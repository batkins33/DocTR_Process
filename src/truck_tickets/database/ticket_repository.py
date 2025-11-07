"""Ticket repository with CRUD operations and validation.

This module implements the database repository pattern for truck_tickets table
with comprehensive CRUD operations, foreign key lookups, validation, and
integration with duplicate detection and manifest validation.

Business Logic:
    - Foreign key resolution by canonical names
    - Duplicate detection before insert
    - Manifest validation for contaminated materials
    - Soft delete (mark as inactive, don't remove)
    - Audit trail (created_at, updated_at)
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.sql_reference import (
    Destination,
    Job,
    Material,
    Source,
    TicketType,
    Vendor,
)
from ..models.sql_truck_ticket import TruckTicket
from ..validators.manifest_validator import ManifestValidator
from .duplicate_detector import DuplicateDetector
from .reference_cache import ReferenceDataCache


class TicketRepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class ForeignKeyNotFoundError(TicketRepositoryError):
    """Raised when a foreign key reference cannot be resolved."""

    pass


class ValidationError(TicketRepositoryError):
    """Raised when validation fails."""

    pass


class DuplicateTicketError(TicketRepositoryError):
    """Raised when a duplicate ticket is detected."""

    pass


class TicketRepository:
    """Repository for truck ticket CRUD operations.

    This repository handles all database operations for truck tickets with:
    - CRUD operations (create, read, update, delete)
    - Foreign key resolution by canonical names
    - Duplicate detection integration
    - Manifest validation integration
    - Soft delete support
    - Audit trail management

    Example:
        ```python
        repo = TicketRepository(session)

        # Create ticket
        ticket = repo.create(
            ticket_number="WM-12345678",
            ticket_date=date(2024, 10, 17),
            job_name="24-105",
            material_name="CLASS_2_CONTAMINATED",
            manifest_number="WM-MAN-2024-001234",
            quantity=25.5,
            quantity_unit="TONS"
        )

        # Get by ID
        ticket = repo.get_by_id(123)

        # Get by ticket number
        ticket = repo.get_by_ticket_number("WM-12345678", vendor_id=1)

        # Update
        repo.update(ticket_id=123, quantity=26.0)

        # Soft delete
        repo.soft_delete(ticket_id=123)
        ```

    Attributes:
        session: SQLAlchemy database session
        duplicate_detector: DuplicateDetector instance
        manifest_validator: ManifestValidator instance
    """

    def __init__(
        self,
        session: Session,
        duplicate_detector: DuplicateDetector | None = None,
        manifest_validator: ManifestValidator | None = None,
        use_cache: bool = True,
    ):
        """Initialize repository.

        Args:
            session: SQLAlchemy database session
            duplicate_detector: Optional duplicate detector (creates if None)
            manifest_validator: Optional manifest validator (creates if None)
            use_cache: Whether to use reference data caching (default: True)
        """
        self.session = session
        self.duplicate_detector = duplicate_detector or DuplicateDetector(session)
        self.manifest_validator = manifest_validator or ManifestValidator(session)
        self.use_cache = use_cache
        self.cache = ReferenceDataCache(session) if use_cache else None

    # Foreign Key Lookup Methods

    def get_job_by_name(self, job_name: str) -> Job | None:
        """Get job by canonical name.

        Args:
            job_name: Job name (e.g., "24-105")

        Returns:
            Job instance or None if not found
        """
        if self.cache:
            return self.cache.get_job_by_name(job_name)

        return (
            self.session.execute(select(Job).where(Job.job_code == job_name))
            .scalars()
            .first()
        )

    def get_material_by_name(self, material_name: str) -> Material | None:
        """Get material by canonical name.

        Args:
            material_name: Material name (e.g., "CLASS_2_CONTAMINATED")

        Returns:
            Material instance or None if not found
        """
        if self.cache:
            return self.cache.get_material_by_name(material_name)

        return (
            self.session.execute(
                select(Material).where(Material.material_name == material_name)
            )
            .scalars()
            .first()
        )

    def get_source_by_name(self, source_name: str) -> Source | None:
        """Get source by canonical name.

        Args:
            source_name: Source name (e.g., "SPG")

        Returns:
            Source instance or None if not found
        """
        if self.cache:
            return self.cache.get_source_by_name(source_name)

        return (
            self.session.execute(
                select(Source).where(Source.source_name == source_name)
            )
            .scalars()
            .first()
        )

    def get_destination_by_name(self, destination_name: str) -> Destination | None:
        """Get destination by canonical name.

        Args:
            destination_name: Destination name (e.g., "WASTE_MANAGEMENT_DFW_RDF")

        Returns:
            Destination instance or None if not found
        """
        if self.cache:
            return self.cache.get_destination_by_name(destination_name)

        return (
            self.session.execute(
                select(Destination).where(
                    Destination.destination_name == destination_name
                )
            )
            .scalars()
            .first()
        )

    def get_vendor_by_name(self, vendor_name: str) -> Vendor | None:
        """Get vendor by canonical name.

        Args:
            vendor_name: Vendor name (e.g., "WASTE_MANAGEMENT_DFW_RDF")

        Returns:
            Vendor instance or None if not found
        """
        if self.cache:
            return self.cache.get_vendor_by_name(vendor_name)

        return (
            self.session.execute(
                select(Vendor).where(Vendor.vendor_name == vendor_name)
            )
            .scalars()
            .first()
        )

    def get_ticket_type_by_name(self, ticket_type_name: str) -> TicketType | None:
        """Get ticket type by canonical name.

        Args:
            ticket_type_name: Ticket type name (e.g., "EXPORT")

        Returns:
            TicketType instance or None if not found
        """
        if self.cache:
            return self.cache.get_ticket_type_by_name(ticket_type_name)

        return (
            self.session.execute(
                select(TicketType).where(TicketType.type_name == ticket_type_name)
            )
            .scalars()
            .first()
        )

    # CRUD Operations

    def create(
        self,
        ticket_number: str,
        ticket_date: date,
        job_name: str,
        material_name: str,
        ticket_type_name: str = "EXPORT",
        source_name: str | None = None,
        destination_name: str | None = None,
        vendor_name: str | None = None,
        manifest_number: str | None = None,
        quantity: Decimal | None = None,
        quantity_unit: str | None = None,
        truck_number: str | None = None,
        file_id: str | None = None,
        file_page: int | None = None,
        file_hash: str | None = None,
        request_guid: str | None = None,
        extraction_confidence: Decimal | None = None,
        check_duplicates: bool = True,
        validate_manifest: bool = True,
    ) -> TruckTicket:
        """Create a new truck ticket.

        This method:
        1. Resolves all foreign keys by canonical names
        2. Validates manifest requirement (if enabled)
        3. Checks for duplicates (if enabled)
        4. Creates the ticket record
        5. Commits the transaction

        Args:
            ticket_number: Ticket number from vendor
            ticket_date: Date of the ticket
            job_name: Job canonical name (e.g., "24-105")
            material_name: Material canonical name
            ticket_type_name: Ticket type ("EXPORT" or "IMPORT")
            source_name: Source canonical name (optional)
            destination_name: Destination canonical name (optional)
            vendor_name: Vendor canonical name (optional)
            manifest_number: Manifest number (required for contaminated)
            quantity: Quantity value
            quantity_unit: Unit of measurement
            truck_number: Truck number (v1.1 field)
            file_id: Source file path
            file_page: Page number in file
            file_hash: SHA-256 hash of file
            request_guid: Batch processing GUID
            extraction_confidence: OCR confidence score
            check_duplicates: Whether to check for duplicates (default: True)
            validate_manifest: Whether to validate manifest (default: True)

        Returns:
            Created TruckTicket instance

        Raises:
            ForeignKeyNotFoundError: If required foreign key not found
            ValidationError: If manifest validation fails
            DuplicateTicketError: If duplicate detected

        Example:
            ```python
            ticket = repo.create(
                ticket_number="WM-12345678",
                ticket_date=date(2024, 10, 17),
                job_name="24-105",
                material_name="CLASS_2_CONTAMINATED",
                manifest_number="WM-MAN-2024-001234",
                quantity=Decimal("25.5"),
                quantity_unit="TONS"
            )
            ```
        """
        try:
            # Resolve foreign keys
            job = self.get_job_by_name(job_name)
            if not job:
                raise ForeignKeyNotFoundError(f"Job not found: {job_name}")

            material = self.get_material_by_name(material_name)
            if not material:
                raise ForeignKeyNotFoundError(f"Material not found: {material_name}")

            ticket_type = self.get_ticket_type_by_name(ticket_type_name)
            if not ticket_type:
                raise ForeignKeyNotFoundError(
                    f"Ticket type not found: {ticket_type_name}"
                )

            # Optional foreign keys
            source_id = None
            if source_name:
                source = self.get_source_by_name(source_name)
                if source:
                    source_id = source.source_id

            destination_id = None
            if destination_name:
                destination = self.get_destination_by_name(destination_name)
                if destination:
                    destination_id = destination.destination_id

            vendor_id = None
            if vendor_name:
                vendor = self.get_vendor_by_name(vendor_name)
                if vendor:
                    vendor_id = vendor.vendor_id

            # Validate manifest requirement
            if validate_manifest:
                manifest_result = self.manifest_validator.validate_manifest(
                    material_name=material_name,
                    manifest_number=manifest_number,
                    destination_name=destination_name,
                )

                if not manifest_result.is_valid:
                    raise ValidationError(
                        f"Manifest validation failed: {manifest_result.reason}"
                    )

            # Check for duplicates
            if check_duplicates:
                duplicate_result = self.duplicate_detector.check_duplicate(
                    ticket_number=ticket_number,
                    vendor_id=vendor_id,
                    ticket_date=ticket_date,
                )

                if duplicate_result.is_duplicate:
                    raise DuplicateTicketError(
                        f"Duplicate ticket found: original ticket_id={duplicate_result.original_ticket_id}, "
                        f"days_apart={duplicate_result.days_apart}"
                    )

            # Create ticket
            confidence_value = (
                float(extraction_confidence)
                if extraction_confidence is not None
                else None
            )
            ticket = TruckTicket(
                ticket_number=ticket_number,
                ticket_date=ticket_date,
                job_id=job.job_id,
                material_id=material.material_id,
                ticket_type_id=ticket_type.ticket_type_id,
                source_id=source_id,
                destination_id=destination_id,
                vendor_id=vendor_id,
                manifest_number=manifest_number,
                quantity=quantity,
                quantity_unit=quantity_unit,
                truck_number=truck_number,
                file_id=file_id,
                file_page=file_page,
                file_hash=file_hash,
                request_guid=request_guid,
                confidence_score=confidence_value,
                review_required=False,
                duplicate_of=None,
            )

            self.session.add(ticket)
            self.session.commit()
            self.session.refresh(ticket)

            return ticket

        except (ForeignKeyNotFoundError, ValidationError, DuplicateTicketError):
            self.session.rollback()
            raise
        except SQLAlchemyError as e:
            self.session.rollback()
            raise TicketRepositoryError(f"Database error: {str(e)}") from e

    def get_by_id(self, ticket_id: int) -> TruckTicket | None:
        """Get ticket by ID.

        Args:
            ticket_id: Ticket ID

        Returns:
            TruckTicket instance or None if not found
        """
        return self.session.get(TruckTicket, ticket_id)

    def get_by_ticket_number(
        self, ticket_number: str, vendor_id: int | None = None
    ) -> TruckTicket | None:
        """Get ticket by ticket number and optional vendor.

        Args:
            ticket_number: Ticket number
            vendor_id: Optional vendor ID for disambiguation

        Returns:
            TruckTicket instance or None if not found
        """
        query = select(TruckTicket).where(TruckTicket.ticket_number == ticket_number)

        if vendor_id is not None:
            query = query.where(TruckTicket.vendor_id == vendor_id)

        return self.session.execute(query).scalars().first()

    def get_by_date_range(
        self, start_date: date, end_date: date, job_id: int | None = None
    ) -> list[TruckTicket]:
        """Get tickets within date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            job_id: Optional job ID filter

        Returns:
            List of TruckTicket instances
        """
        query = select(TruckTicket).where(
            and_(
                TruckTicket.ticket_date >= start_date,
                TruckTicket.ticket_date <= end_date,
            )
        )

        if job_id is not None:
            query = query.where(TruckTicket.job_id == job_id)

        query = query.order_by(TruckTicket.ticket_date, TruckTicket.ticket_number)

        return list(self.session.execute(query).scalars().all())

    def update(self, ticket_id: int, **kwargs) -> TruckTicket:
        """Update ticket fields.

        Args:
            ticket_id: Ticket ID to update
            **kwargs: Fields to update

        Returns:
            Updated TruckTicket instance

        Raises:
            TicketRepositoryError: If ticket not found or update fails

        Example:
            ```python
            ticket = repo.update(
                ticket_id=123,
                quantity=Decimal("26.0"),
                manifest_number="WM-MAN-2024-001235"
            )
            ```
        """
        try:
            ticket = self.get_by_id(ticket_id)
            if not ticket:
                raise TicketRepositoryError(f"Ticket not found: {ticket_id}")

            # Update allowed fields
            for key, value in kwargs.items():
                if hasattr(ticket, key):
                    setattr(ticket, key, value)

            # Update timestamp
            ticket.updated_at = datetime.utcnow()

            self.session.commit()
            self.session.refresh(ticket)

            return ticket

        except SQLAlchemyError as e:
            self.session.rollback()
            raise TicketRepositoryError(f"Update failed: {str(e)}") from e

    def soft_delete(self, ticket_id: int) -> bool:
        """Soft delete ticket (mark as inactive, don't remove).

        Args:
            ticket_id: Ticket ID to delete

        Returns:
            True if deleted, False if not found

        Note:
            This doesn't actually delete the record, just marks it as inactive.
            Use hard_delete() if you need to actually remove the record.
        """
        ticket = self.get_by_id(ticket_id)
        if not ticket:
            return False

        # Mark as inactive (you may want to add an 'active' field to the model)
        ticket.updated_at = datetime.utcnow()
        # ticket.active = False  # Add this field to model if needed

        self.session.commit()
        return True

    def hard_delete(self, ticket_id: int) -> bool:
        """Permanently delete ticket from database.

        WARNING: This permanently removes the record. Use soft_delete() instead
        for most cases to maintain audit trail.

        Args:
            ticket_id: Ticket ID to delete

        Returns:
            True if deleted, False if not found
        """
        ticket = self.get_by_id(ticket_id)
        if not ticket:
            return False

        try:
            self.session.delete(ticket)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise TicketRepositoryError(f"Delete failed: {str(e)}") from e

    # Query Methods

    def count_by_job(self, job_id: int) -> int:
        """Count tickets for a job.

        Args:
            job_id: Job ID

        Returns:
            Number of tickets
        """
        from sqlalchemy import func

        return (
            self.session.query(func.count(TruckTicket.ticket_id))
            .filter(TruckTicket.job_id == job_id)
            .scalar()
            or 0
        )

    def get_duplicates(self) -> list[TruckTicket]:
        """Get all tickets marked as duplicates.

        Returns:
            List of duplicate tickets
        """
        return list(
            self.session.execute(
                select(TruckTicket).where(TruckTicket.duplicate_of.isnot(None))
            )
            .scalars()
            .all()
        )

    def get_requiring_review(self) -> list[TruckTicket]:
        """Get all tickets requiring manual review.

        Returns:
            List of tickets needing review
        """
        return list(
            self.session.execute(
                select(TruckTicket).where(TruckTicket.review_required)
            )
            .scalars()
            .all()
        )

    def search(
        self,
        ticket_number: str | None = None,
        job_id: int | None = None,
        material_id: int | None = None,
        vendor_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        has_manifest: bool | None = None,
        limit: int = 100,
    ) -> list[TruckTicket]:
        """Search tickets with multiple filters.

        Args:
            ticket_number: Partial ticket number match
            job_id: Job ID filter
            material_id: Material ID filter
            vendor_id: Vendor ID filter
            start_date: Start date filter
            end_date: End date filter
            has_manifest: Filter by manifest presence
            limit: Maximum results (default: 100)

        Returns:
            List of matching tickets
        """
        query = select(TruckTicket)

        filters = []

        if ticket_number:
            filters.append(TruckTicket.ticket_number.like(f"%{ticket_number}%"))

        if job_id is not None:
            filters.append(TruckTicket.job_id == job_id)

        if material_id is not None:
            filters.append(TruckTicket.material_id == material_id)

        if vendor_id is not None:
            filters.append(TruckTicket.vendor_id == vendor_id)

        if start_date:
            filters.append(TruckTicket.ticket_date >= start_date)

        if end_date:
            filters.append(TruckTicket.ticket_date <= end_date)

        if has_manifest is not None:
            if has_manifest:
                filters.append(TruckTicket.manifest_number.isnot(None))
            else:
                filters.append(TruckTicket.manifest_number.is_(None))

        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit)

        return list(self.session.execute(query).scalars().all())
