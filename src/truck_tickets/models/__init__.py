"""Data models for truck ticket processing."""

from .ticket import TruckTicket
from .reference_data import Job, Material, Source, Destination, Vendor, TicketType

__all__ = [
    "TruckTicket",
    "Job",
    "Material", 
    "Source",
    "Destination",
    "Vendor",
    "TicketType",
]
