"""SQLAlchemy models for reference reference data tables."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import INT, VARCHAR, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .sql_base import Base

if TYPE_CHECKING:
    from .sql_truck_ticket import TruckTicket


class Job(Base):
    """Construction job/project table."""

    __tablename__ = "jobs"
    __table_args__ = (Index("ix_job_code", "job_code"),)

    # Primary key
    job_id: Mapped[int] = mapped_column(
        INT, primary_key=True, comment="Primary key identifier"
    )

    # Fields
    job_code: Mapped[str] = mapped_column(
        VARCHAR(50), unique=True, nullable=False, comment="Job code (e.g., '24-105')"
    )
    job_name: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True, comment="Job description name"
    )
    start_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="Job start date"
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="Job end date"
    )

    # Relationships
    sources: Mapped[list["Source"]] = relationship("Source", back_populates="job")
    truck_tickets: Mapped[list["TruckTicket"]] = relationship(
        "TruckTicket", back_populates="job"
    )


class Material(Base):
    """Material type table."""

    __tablename__ = "materials"
    __table_args__ = (
        Index("ix_material_name", "material_name"),
        Index("ix_material_class", "material_class"),
    )

    # Primary key
    material_id: Mapped[int] = mapped_column(
        INT, primary_key=True, comment="Primary key identifier"
    )

    # Fields
    material_name: Mapped[str] = mapped_column(
        VARCHAR(100), unique=True, nullable=False, comment="Material name"
    )
    material_class: Mapped[str | None] = mapped_column(
        VARCHAR(50),
        nullable=True,
        comment="Material class (CONTAMINATED, CLEAN, IMPORT, SPOILS)",
    )
    requires_manifest: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether material requires manifest tracking",
    )

    # Relationships
    truck_tickets: Mapped[list["TruckTicket"]] = relationship(
        "TruckTicket", back_populates="material"
    )


class Source(Base):
    """Source location table."""

    __tablename__ = "sources"
    __table_args__ = (
        Index("ix_source_name", "source_name"),
        Index("ix_source_job_id", "job_id"),
    )

    # Primary key
    source_id: Mapped[int] = mapped_column(
        INT, primary_key=True, comment="Primary key identifier"
    )

    # Fields
    source_name: Mapped[str] = mapped_column(
        VARCHAR(100), unique=True, nullable=False, comment="Source location name"
    )
    job_id: Mapped[int | None] = mapped_column(
        INT,
        ForeignKey("jobs.job_id"),
        nullable=True,
        comment="Foreign key to jobs table",
    )
    source_type: Mapped[str | None] = mapped_column(
        VARCHAR(50),
        nullable=True,
        comment="Source type (EXCAVATION, SPOILS_STAGING, IMPORT_DELIVERY)",
    )
    description: Mapped[str | None] = mapped_column(
        VARCHAR(255), nullable=True, comment="Source description"
    )

    # Relationships
    job: Mapped[Optional["Job"]] = relationship("Job", back_populates="sources")
    truck_tickets: Mapped[list["TruckTicket"]] = relationship(
        "TruckTicket", back_populates="source"
    )


class Destination(Base):
    """Destination facility table."""

    __tablename__ = "destinations"
    __table_args__ = (
        Index("ix_destination_name", "destination_name"),
        Index("ix_destination_type", "facility_type"),
    )

    # Primary key
    destination_id: Mapped[int] = mapped_column(
        INT, primary_key=True, comment="Primary key identifier"
    )

    # Fields
    destination_name: Mapped[str] = mapped_column(
        VARCHAR(100), unique=True, nullable=False, comment="Destination facility name"
    )
    facility_type: Mapped[str | None] = mapped_column(
        VARCHAR(50), nullable=True, comment="Facility type (DISPOSAL, REUSE, LANDFILL)"
    )
    address: Mapped[str | None] = mapped_column(
        VARCHAR(500), nullable=True, comment="Facility address"
    )
    requires_manifest: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether destination requires manifest",
    )

    # Relationships
    truck_tickets: Mapped[list["TruckTicket"]] = relationship(
        "TruckTicket", back_populates="destination"
    )


class Vendor(Base):
    """Vendor/hauler company table."""

    __tablename__ = "vendors"
    __table_args__ = (
        Index("ix_vendor_name", "vendor_name"),
        Index("ix_vendor_code", "vendor_code"),
    )

    # Primary key
    vendor_id: Mapped[int] = mapped_column(
        INT, primary_key=True, comment="Primary key identifier"
    )

    # Fields
    vendor_name: Mapped[str] = mapped_column(
        VARCHAR(100), unique=True, nullable=False, comment="Vendor company name"
    )
    vendor_code: Mapped[str | None] = mapped_column(
        VARCHAR(50), nullable=True, comment="Vendor short code"
    )
    vendor_type: Mapped[str | None] = mapped_column(
        VARCHAR(50),
        nullable=True,
        comment="Vendor type (DISPOSAL, HAULING, MATERIAL_SUPPLIER)",
    )
    contact_info: Mapped[str | None] = mapped_column(
        VARCHAR(500), nullable=True, comment="Vendor contact information"
    )

    # Relationships
    truck_tickets: Mapped[list["TruckTicket"]] = relationship(
        "TruckTicket", back_populates="vendor"
    )


class TicketType(Base):
    """Ticket type table."""

    __tablename__ = "ticket_types"

    # Primary key
    ticket_type_id: Mapped[int] = mapped_column(
        INT, primary_key=True, comment="Primary key identifier"
    )

    # Fields
    type_name: Mapped[str] = mapped_column(
        VARCHAR(20),
        unique=True,
        nullable=False,
        comment="Ticket type name (IMPORT or EXPORT)",
    )

    # Relationships
    truck_tickets: Mapped[list["TruckTicket"]] = relationship(
        "TruckTicket", back_populates="ticket_type"
    )
