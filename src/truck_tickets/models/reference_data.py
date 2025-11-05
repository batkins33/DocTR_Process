"""Reference data models for lookup tables."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class Job:
    """Construction job/project."""

    job_code: str
    job_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    job_id: int | None = None
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class Material:
    """Material type (contaminated, clean, spoils, import types)."""

    material_name: str
    material_class: str | None = None  # 'CONTAMINATED', 'CLEAN', 'IMPORT'
    requires_manifest: bool = False
    material_id: int | None = None
    created_at: datetime = None


@dataclass
class Source:
    """Source location on construction site."""

    source_name: str
    job_id: int | None = None
    description: str | None = None
    source_id: int | None = None
    created_at: datetime = None


@dataclass
class Destination:
    """Destination facility (disposal, reuse, landfill)."""

    destination_name: str
    facility_type: str | None = None  # 'DISPOSAL', 'REUSE', 'LANDFILL'
    address: str | None = None
    requires_manifest: bool = False
    destination_id: int | None = None
    created_at: datetime = None


@dataclass
class Vendor:
    """Vendor/hauler company."""

    vendor_name: str
    vendor_code: str | None = None
    contact_info: str | None = None
    vendor_id: int | None = None
    created_at: datetime = None


@dataclass
class TicketType:
    """Ticket type (IMPORT or EXPORT)."""

    type_name: str  # 'IMPORT' or 'EXPORT'
    ticket_type_id: int | None = None
