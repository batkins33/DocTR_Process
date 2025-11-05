"""Data models for truck ticket processing."""

# Dataclass models (domain logic)
from .reference_data import Destination, Job, Material, Source, TicketType, Vendor

# SQLAlchemy models (database persistence)
from .sql_base import Base
from .sql_processing import ProcessingRun, ReviewQueue
from .sql_reference import (
    Destination as DestinationModel,
)
from .sql_reference import (
    Job as JobModel,
)
from .sql_reference import (
    Material as MaterialModel,
)
from .sql_reference import (
    Source as SourceModel,
)
from .sql_reference import (
    TicketType as TicketTypeModel,
)
from .sql_reference import (
    Vendor as VendorModel,
)
from .sql_truck_ticket import TruckTicket as TruckTicketModel
from .ticket import TruckTicket as TruckTicketDataclass

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
