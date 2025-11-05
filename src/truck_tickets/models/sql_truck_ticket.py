"""SQLAlchemy model for main truck_tickets table."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    INT,
    VARCHAR,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .sql_base import Base
from .sql_processing import ReviewQueue
from .sql_reference import Destination, Job, Material, Source, TicketType, Vendor


class TruckTicket(Base):
    """Main truck ticket transaction table.

    Stores all extracted ticket data from PDF processing.
    Updated v1.1 to include truck_number field.
    """

    __tablename__ = "truck_tickets"
    __table_args__ = (
        UniqueConstraint("ticket_number", "vendor_id", name="uq_ticket_vendor"),
        Index("ix_ticket_date", "ticket_date"),
        Index("ix_job_date", "job_id", "ticket_date"),
        Index("ix_manifest_number", "manifest_number"),
        Index("ix_request_guid", "request_guid"),
        Index("ix_file_hash", "file_hash"),
    )

    # Primary key
    ticket_id: Mapped[int] = mapped_column(
        INT, primary_key=True, comment="Primary key identifier"
    )

    # Core ticket fields
    ticket_number: Mapped[str] = mapped_column(
        VARCHAR(50), nullable=False, comment="Ticket number from vendor"
    )
    ticket_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Ticket date"
    )

    # Quantity fields
    quantity: Mapped[Decimal | None] = mapped_column(
        DECIMAL(10, 2), nullable=True, comment="Material quantity"
    )
    quantity_unit: Mapped[str | None] = mapped_column(
        VARCHAR(20), nullable=True, comment="Unit of measurement (TONS, CY, LOADS)"
    )

    # **NEW v1.1:** Truck identification
    truck_number: Mapped[str | None] = mapped_column(
        VARCHAR(50),
        nullable=True,
        comment="Truck number for cross-reference with accounting data",
    )

    # Foreign keys
    job_id: Mapped[int] = mapped_column(
        INT,
        ForeignKey("jobs.job_id"),
        nullable=False,
        comment="Foreign key to jobs table",
    )
    material_id: Mapped[int] = mapped_column(
        INT,
        ForeignKey("materials.material_id"),
        nullable=False,
        comment="Foreign key to materials table",
    )
    source_id: Mapped[int | None] = mapped_column(
        INT,
        ForeignKey("sources.source_id"),
        nullable=True,
        comment="Foreign key to sources table",
    )
    destination_id: Mapped[int | None] = mapped_column(
        INT,
        ForeignKey("destinations.destination_id"),
        nullable=True,
        comment="Foreign key to destinations table",
    )
    vendor_id: Mapped[int | None] = mapped_column(
        INT,
        ForeignKey("vendors.vendor_id"),
        nullable=True,
        comment="Foreign key to vendors table",
    )
    ticket_type_id: Mapped[int] = mapped_column(
        INT,
        ForeignKey("ticket_types.ticket_type_id"),
        nullable=False,
        comment="Foreign key to ticket_types table",
    )

    # File/Processing metadata
    file_id: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True, comment="Path to source PDF file"
    )
    file_page: Mapped[int | None] = mapped_column(
        INT, nullable=True, comment="Page number in PDF"
    )
    request_guid: Mapped[str | None] = mapped_column(
        VARCHAR(50), nullable=True, comment="Batch processing request GUID"
    )

    # Regulatory/Compliance fields
    manifest_number: Mapped[str | None] = mapped_column(
        VARCHAR(100), nullable=True, comment="Manifest number for contaminated material"
    )

    # Processing metadata
    processed_by: Mapped[str | None] = mapped_column(
        VARCHAR(100), nullable=True, comment="User/process that created the record"
    )
    confidence_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="OCR extraction confidence score (0.0-1.0)"
    )

    # Review and duplicate tracking
    review_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether ticket requires manual review",
    )
    review_reason: Mapped[str | None] = mapped_column(
        VARCHAR(100), nullable=True, comment="Reason for review requirement"
    )
    duplicate_of: Mapped[int | None] = mapped_column(
        INT,
        ForeignKey("truck_tickets.ticket_id"),
        nullable=True,
        comment="Ticket ID if this is a duplicate",
    )

    # File integrity
    file_hash: Mapped[str | None] = mapped_column(
        VARCHAR(64), nullable=True, comment="SHA-256 hash of source PDF file"
    )

    # Relationships
    job: Mapped[Job] = relationship("Job", back_populates="truck_tickets")
    material: Mapped[Material] = relationship(
        "Material", back_populates="truck_tickets"
    )
    source: Mapped[Source | None] = relationship(
        "Source", back_populates="truck_tickets"
    )
    destination: Mapped[Destination | None] = relationship(
        "Destination", back_populates="truck_tickets"
    )
    vendor: Mapped[Vendor | None] = relationship(
        "Vendor", back_populates="truck_tickets"
    )
    ticket_type: Mapped[TicketType] = relationship(
        "TicketType", back_populates="truck_tickets"
    )

    # Review queue relationship (one-to-many)
    review_entries: Mapped[list[ReviewQueue]] = relationship(
        "ReviewQueue", back_populates="ticket"
    )

    def __repr__(self) -> str:
        """String representation of truck ticket."""
        return (
            f"<TruckTicket(id={self.ticket_id}, "
            f"number='{self.ticket_number}', "
            f"date='{self.ticket_date}', "
            f"vendor_id={self.vendor_id})>"
        )

    @property
    def is_export(self) -> bool:
        """Check if this is an export ticket."""
        return self.ticket_type_id == 2  # EXPORT = 2

    @property
    def is_import(self) -> bool:
        """Check if this is an import ticket."""
        return self.ticket_type_id == 1  # IMPORT = 1

    @property
    def is_duplicate(self) -> bool:
        """Check if this ticket is marked as a duplicate."""
        return self.duplicate_of is not None

    @property
    def needs_review(self) -> bool:
        """Check if this ticket requires review."""
        return (
            self.review_required or self.confidence_score < 0.8
            if self.confidence_score
            else False
        )
