"""Truck Ticket Processing System

A specialized module for processing multi-page truck ticket PDFs from construction sites.
Extracts ticket numbers, vendors, manifests, and populates SQL Server database.

Project: 24-105 Construction Site Material Tracking
Specification Version: 1.0
"""

__version__ = "1.0.0"
__author__ = "DocTR Process Team"

from .models import Destination, Job, Material, Source, TruckTicketDataclass, Vendor

__all__ = [
    "TruckTicketDataclass",
    "Job",
    "Material",
    "Source",
    "Destination",
    "Vendor",
]
