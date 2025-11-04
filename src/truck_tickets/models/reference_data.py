"""Reference data models for lookup tables."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Job:
    """Construction job/project."""
    job_code: str
    job_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    job_id: Optional[int] = None
    created_at: datetime = None
    updated_at: datetime = None


@dataclass
class Material:
    """Material type (contaminated, clean, spoils, import types)."""
    material_name: str
    material_class: Optional[str] = None  # 'CONTAMINATED', 'CLEAN', 'IMPORT'
    requires_manifest: bool = False
    material_id: Optional[int] = None
    created_at: datetime = None


@dataclass
class Source:
    """Source location on construction site."""
    source_name: str
    job_id: Optional[int] = None
    description: Optional[str] = None
    source_id: Optional[int] = None
    created_at: datetime = None


@dataclass
class Destination:
    """Destination facility (disposal, reuse, landfill)."""
    destination_name: str
    facility_type: Optional[str] = None  # 'DISPOSAL', 'REUSE', 'LANDFILL'
    address: Optional[str] = None
    requires_manifest: bool = False
    destination_id: Optional[int] = None
    created_at: datetime = None


@dataclass
class Vendor:
    """Vendor/hauler company."""
    vendor_name: str
    vendor_code: Optional[str] = None
    contact_info: Optional[str] = None
    vendor_id: Optional[int] = None
    created_at: datetime = None


@dataclass
class TicketType:
    """Ticket type (IMPORT or EXPORT)."""
    type_name: str  # 'IMPORT' or 'EXPORT'
    ticket_type_id: Optional[int] = None
