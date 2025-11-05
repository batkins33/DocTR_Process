"""Data models for truck ticket processing."""

# Dataclass models (domain logic)
from .reference_data import Destination, Job, Material, Source, TicketType, Vendor
from .ticket import TruckTicket as TruckTicketDataclass

# SQLAlchemy models (database persistence)
from .sql_base import Base
from .sql_reference import (
    Job as JobModel,
    Material as MaterialModel,
    Source as SourceModel,
    Destination as DestinationModel,
    Vendor as VendorModel,
    TicketType as TicketTypeModel,
)
from .sql_truck_ticket import TruckTicket as TruckTicketModel
from .sql_processing import ReviewQueue, ProcessingRun

__all__ = [
    # Dataclass models
    "TruckTicketDataclass",
    "Job",
    "Material",
    "Source",
    "Destination",
    "Vendor",
    "TicketType",
    # SQLAlchemy models
    "Base",
    "JobModel",
    "MaterialModel",
    "SourceModel",
    "DestinationModel",
    "VendorModel",
    "TicketTypeModel",
    "TruckTicketModel",
    "ReviewQueue",
    "ProcessingRun",
]
