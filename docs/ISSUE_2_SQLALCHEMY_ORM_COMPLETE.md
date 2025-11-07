# ORM Schema and Usage Guide

This document describes the SQLAlchemy ORM schema used by the Truck Ticket system and provides usage examples for creating the schema, seeding reference data, and working with the repository and processor.

## Tables and Relationships

- **jobs**
  - job_id (PK)
  - job_code (UNIQUE)
  - job_name
  - start_date, end_date
  - Relationships: sources, truck_tickets

- **materials**
  - material_id (PK)
  - material_name (UNIQUE)
  - material_class (CONTAMINATED, CLEAN, IMPORT, WASTE)
  - requires_manifest (bool)
  - Relationships: truck_tickets

- **sources**
  - source_id (PK)
  - source_name (UNIQUE)
  - job_id (FK → jobs)
  - source_type, description
  - Relationships: job, truck_tickets

- **destinations**
  - destination_id (PK)
  - destination_name (UNIQUE)
  - facility_type, address
  - requires_manifest (bool)
  - Relationships: truck_tickets

- **vendors**
  - vendor_id (PK)
  - vendor_name (UNIQUE)
  - vendor_code, vendor_type, contact_info
  - Relationships: truck_tickets

- **ticket_types**
  - ticket_type_id (PK)
  - type_name (UNIQUE) → IMPORT, EXPORT
  - Relationships: truck_tickets

- **truck_tickets**
  - ticket_id (PK)
  - ticket_number, ticket_date
  - quantity, quantity_unit, truck_number
  - job_id (FK), material_id (FK), source_id (FK), destination_id (FK), vendor_id (FK), ticket_type_id (FK)
  - manifest_number
  - processed_by, confidence_score
  - review_required, review_reason, duplicate_of (self FK)
  - file_id, file_page, file_hash, request_guid
  - Indexes: (ticket_number, vendor_id) UNIQUE, ix_ticket_date, ix_job_date, ix_manifest_number, ix_request_guid, ix_file_hash

- **review_queue**
  - review_id (PK)
  - ticket_id (FK optional)
  - reason, severity
  - file_path, page_num
  - detected_fields (JSON string), suggested_fixes (JSON string)
  - resolved, resolved_by, resolved_at

- **processing_runs**
  - run_id (PK)
  - request_guid (UNIQUE)
  - started_at, completed_at
  - files_count, pages_count, tickets_created, tickets_updated, duplicates_found, review_queue_count, error_count
  - processed_by, status, config_snapshot

All tables inherit `created_at` and `updated_at` audit fields from `Base`.

## Creating Schema and Seeding Data

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.truck_tickets.database.sqlalchemy_schema_setup import (
    create_all_tables, seed_reference_data
)

engine = create_engine("sqlite:///truck_tickets.db", echo=False)
session = sessionmaker(bind=engine)()

create_all_tables(engine)
counts = seed_reference_data(session, job_code="24-105", job_name="PHMS New Pediatric Campus")
print(counts)
```

## Quick Test Database

```python
from src.truck_tickets.database.sqlalchemy_schema_setup import create_test_database

engine, session = create_test_database("test_truck_tickets.db")
# ... run experiments
session.close(); engine.dispose()
```

## Repository Usage

```python
from datetime import date
from decimal import Decimal
from src.truck_tickets.database.ticket_repository import TicketRepository

repo = TicketRepository(session)

# Create a clean (non-contaminated) ticket
ticket = repo.create(
    ticket_number="WM-1001",
    ticket_date=date(2024, 10, 1),
    job_name="24-105",
    material_name="NON_CONTAMINATED",
    ticket_type_name="EXPORT",
    vendor_name="WASTE_MANAGEMENT",
    quantity=Decimal("10.5"),
    quantity_unit="TONS",
)

# Duplicate detection: creating the same ticket for the same vendor within 120 days raises DuplicateTicketError
```

## Processor Usage (stubbed OCR)

```python
from src.truck_tickets.processing.ticket_processor import TicketProcessor

processor = TicketProcessor(session, job_name="24-105", ticket_type_name="EXPORT")

# In production, call process_pdf or provide OCR text to process_page
result = processor.process_page(
    page_text="... OCR text ...",
    page_num=1,
    file_path="batch1/file1.pdf",
)
```

## Compliance Highlights (Spec v1.1)

- Duplicate detection:
  - Primary uniqueness: (ticket_number, vendor_id)
  - Window: 120 days
  - On duplicate: route to review queue, set duplicate_of
- Manifest validation (100% recall):
  - Contaminated materials require manifest and compliant destination
- Idempotency: Re-processing should not create duplicates

Refer to `docs/Truck_Ticket_Processing_Complete_Spec_v1.1.md` for full details.
