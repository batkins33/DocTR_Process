"""Database connection and operations."""

from .duplicate_detector import DuplicateDetectionResult, DuplicateDetector
from .file_tracker import DuplicateFileResult, FileProcessingRecord, FileTracker
from .reference_cache import ReferenceDataCache
from .sqlalchemy_schema_setup import (
    create_all_tables,
    create_test_database,
    drop_all_tables,
    reset_database,
    seed_reference_data,
)
from .ticket_repository import (
    DuplicateTicketError,
    ForeignKeyNotFoundError,
    TicketRepository,
    TicketRepositoryError,
    ValidationError,
)

# Import other modules when they exist
try:
    from .connection import DatabaseConnection
except ImportError:
    DatabaseConnection = None

try:
    from .schema_setup import create_database_schema
except ImportError:
    create_database_schema = None

__all__ = [
    "DuplicateDetector",
    "DuplicateDetectionResult",
    "FileTracker",
    "DuplicateFileResult",
    "FileProcessingRecord",
    "ReferenceDataCache",
    "TicketRepository",
    "TicketRepositoryError",
    "ForeignKeyNotFoundError",
    "ValidationError",
    "DuplicateTicketError",
    "create_all_tables",
    "drop_all_tables",
    "seed_reference_data",
    "reset_database",
    "create_test_database",
]

# Add to __all__ if imported successfully
if DatabaseConnection is not None:
    __all__.append("DatabaseConnection")
if create_database_schema is not None:
    __all__.append("create_database_schema")
