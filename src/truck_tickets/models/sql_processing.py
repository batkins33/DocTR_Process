"""SQLAlchemy models for review_queue and processing_runs tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import INT, VARCHAR, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .sql_base import Base


class ReviewQueue(Base):
    """Review queue table for tickets requiring manual attention."""
    
    __tablename__ = "review_queue"
    
    # Primary key
    review_id: Mapped[int] = mapped_column(
        INT,
        primary_key=True,
        comment="Primary key identifier"
    )
    
    # Reference to ticket (optional if record wasn't created)
    ticket_id: Mapped[Optional[int]] = mapped_column(
        INT,
        ForeignKey("truck_tickets.ticket_id"),
        nullable=True,
        comment="Reference to truck_tickets if record was created"
    )
    
    # Page identification
    page_id: Mapped[Optional[str]] = mapped_column(
        VARCHAR(255),
        nullable=True,
        comment="File path + page number identifier"
    )
    
    # Review details
    reason: Mapped[str] = mapped_column(
        VARCHAR(100),
        nullable=False,
        comment="Reason for review (MISSING_MANIFEST, EXTRACTION_FAILED, etc.)"
    )
    severity: Mapped[str] = mapped_column(
        VARCHAR(20),
        nullable=False,
        comment="Severity level (CRITICAL, WARNING, INFO)"
    )
    
    # File information
    file_path: Mapped[Optional[str]] = mapped_column(
        VARCHAR(500),
        nullable=True,
        comment="Path to source file"
    )
    page_num: Mapped[Optional[int]] = mapped_column(
        INT,
        nullable=True,
        comment="Page number in file"
    )
    
    # JSON fields for context and suggestions
    detected_fields: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON string of detected fields"
    )
    suggested_fixes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON string of suggested fixes"
    )
    
    # Resolution tracking
    resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether review item has been resolved"
    )
    resolved_by: Mapped[Optional[str]] = mapped_column(
        VARCHAR(100),
        nullable=True,
        comment="User who resolved the review item"
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When the review item was resolved"
    )
    
    # Relationships
    ticket: Mapped[Optional["TruckTicket"]] = relationship("TruckTicket", back_populates="review_entries")
    
    def __repr__(self) -> str:
        """String representation of review queue entry."""
        return (
            f"<ReviewQueue(id={self.review_id}, "
            f"reason='{self.reason}', "
            f"severity='{self.severity}', "
            f"resolved={self.resolved})>"
        )
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical severity review."""
        return self.severity.upper() == "CRITICAL"
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning severity review."""
        return self.severity.upper() == "WARNING"
    
    @property
    def is_info(self) -> bool:
        """Check if this is an info severity review."""
        return self.severity.upper() == "INFO"


class ProcessingRun(Base):
    """Processing runs table for batch job tracking."""
    
    __tablename__ = "processing_runs"
    
    # Primary key
    run_id: Mapped[int] = mapped_column(
        INT,
        primary_key=True,
        comment="Primary key identifier"
    )
    
    # Unique identifier for the batch
    request_guid: Mapped[str] = mapped_column(
        VARCHAR(50),
        unique=True,
        nullable=False,
        comment="Unique GUID for this processing run"
    )
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="When processing started"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="When processing completed"
    )
    
    # Counts
    files_count: Mapped[Optional[int]] = mapped_column(
        INT,
        nullable=True,
        comment="Number of files processed"
    )
    pages_count: Mapped[Optional[int]] = mapped_column(
        INT,
        nullable=True,
        comment="Number of pages processed"
    )
    tickets_created: Mapped[Optional[int]] = mapped_column(
        INT,
        nullable=True,
        comment="Number of new tickets created"
    )
    tickets_updated: Mapped[Optional[int]] = mapped_column(
        INT,
        nullable=True,
        comment="Number of existing tickets updated"
    )
    duplicates_found: Mapped[Optional[int]] = mapped_column(
        INT,
        nullable=True,
        comment="Number of duplicate tickets found"
    )
    review_queue_count: Mapped[Optional[int]] = mapped_column(
        INT,
        nullable=True,
        comment="Number of items sent to review queue"
    )
    error_count: Mapped[Optional[int]] = mapped_column(
        INT,
        nullable=True,
        comment="Number of errors encountered"
    )
    
    # Processing details
    processed_by: Mapped[Optional[str]] = mapped_column(
        VARCHAR(100),
        nullable=True,
        comment="User/process that ran the batch"
    )
    status: Mapped[str] = mapped_column(
        VARCHAR(20),
        nullable=False,
        default="IN_PROGRESS",
        comment="Processing status (IN_PROGRESS, COMPLETED, FAILED)"
    )
    
    # Configuration snapshot
    config_snapshot: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="JSON snapshot of configuration used"
    )
    
    def __repr__(self) -> str:
        """String representation of processing run."""
        return (
            f"<ProcessingRun(id={self.run_id}, "
            f"guid='{self.request_guid}', "
            f"status='{self.status}', "
            f"started='{self.started_at}')>"
        )
    
    @property
    def is_completed(self) -> bool:
        """Check if processing run is completed."""
        return self.status.upper() == "COMPLETED"
    
    @property
    def is_failed(self) -> bool:
        """Check if processing run failed."""
        return self.status.upper() == "FAILED"
    
    @property
    def is_in_progress(self) -> bool:
        """Check if processing run is still running."""
        return self.status.upper() == "IN_PROGRESS"
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate processing duration in seconds."""
        if self.completed_at and self.started_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    @property
    def success_rate(self) -> Optional[float]:
        """Calculate success rate (tickets processed / total pages)."""
        if self.pages_count and self.pages_count > 0:
            processed = (self.tickets_created or 0) + (self.tickets_updated or 0)
            return processed / self.pages_count
        return None
