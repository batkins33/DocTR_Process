"""Data models for truck ticket processing."""

from .reference_data import Destination, Job, Material, Source, TicketType, Vendor
from .ticket import TruckTicket

__all__ = [
    "TruckTicket",
    "Job",
    "Material",
    "Source",
    "Destination",
    "Vendor",
    "TicketType",
]
