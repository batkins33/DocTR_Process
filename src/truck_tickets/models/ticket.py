"""Truck ticket data model."""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass
class TruckTicket:
    """Represents a single truck ticket record.

    This is the main transaction table that stores extracted ticket data.
    Maps to the truck_tickets SQL Server table.
    """

    # Primary fields
    ticket_number: str
    ticket_date: date

    # Foreign key references (IDs)
    job_id: int
    material_id: int
    ticket_type_id: int

    # Optional foreign keys
    source_id: int | None = None
    destination_id: int | None = None
    vendor_id: int | None = None

    # Quantity fields
    quantity: Decimal | None = None
    quantity_unit: str | None = None  # 'TONS', 'CY', 'LOADS'

    # File metadata
    file_id: str | None = None  # Path to source PDF
    file_page: int | None = None  # Page number in PDF
    request_guid: str | None = None  # Batch processing ID

    # Regulatory/Compliance
    manifest_number: str | None = None

    # Audit trail
    ticket_id: int | None = None  # Auto-generated on insert
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    processed_by: str | None = None

    # Review/duplicate tracking
    review_required: bool = False
    duplicate_of: int | None = None
    confidence_score: float | None = None

    def __post_init__(self):
        """Validate ticket data after initialization."""
        if not self.ticket_number:
            raise ValueError("Ticket number is required")
        if not self.ticket_date:
            raise ValueError("Ticket date is required")
        if not self.job_id:
            raise ValueError("Job ID is required")
        if not self.material_id:
            raise ValueError("Material ID is required")
        if not self.ticket_type_id:
            raise ValueError("Ticket type ID is required")

        # Validate quantity units
        valid_units = ["TONS", "CY", "LOADS", None]
        if self.quantity_unit and self.quantity_unit not in valid_units:
            raise ValueError(f"Invalid quantity unit: {self.quantity_unit}")

    def to_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            "ticket_number": self.ticket_number,
            "ticket_date": self.ticket_date,
            "quantity": float(self.quantity) if self.quantity else None,
            "quantity_unit": self.quantity_unit,
            "job_id": self.job_id,
            "material_id": self.material_id,
            "source_id": self.source_id,
            "destination_id": self.destination_id,
            "vendor_id": self.vendor_id,
            "ticket_type_id": self.ticket_type_id,
            "file_id": self.file_id,
            "file_page": self.file_page,
            "request_guid": self.request_guid,
            "manifest_number": self.manifest_number,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "processed_by": self.processed_by,
        }

    @property
    def is_export(self) -> bool:
        """Check if this is an export ticket."""
        return self.ticket_type_id == 2  # EXPORT = 2

    @property
    def is_import(self) -> bool:
        """Check if this is an import ticket."""
        return self.ticket_type_id == 1  # IMPORT = 1

    @property
    def requires_manifest(self) -> bool:
        """Check if this ticket requires a manifest number."""
        # CLASS_2_CONTAMINATED material requires manifest
        return self.material_id == 1  # Adjust based on actual material IDs
