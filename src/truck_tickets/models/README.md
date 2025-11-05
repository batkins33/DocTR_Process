# 📊 Truck Ticket Models Documentation

## Overview

This directory contains both **dataclass models** (for domain logic) and **SQLAlchemy models** (for database persistence) for the Truck Ticket Processing System.

## Model Types

### 1. Dataclass Models (Domain Logic)
- **Purpose:** Business logic, validation, in-memory operations
- **Files:** `reference_data.py`, `ticket.py`
- **Usage:** Extractors, processors, validation logic
- **Benefits:** Fast, lightweight, no database dependencies

### 2. SQLAlchemy Models (Database Persistence)
- **Purpose:** Database operations, queries, relationships
- **Files:** `sql_base.py`, `sql_reference.py`, `sql_truck_ticket.py`, `sql_processing.py`
- **Usage:** Repository classes, database operations
- **Benefits:** Type-safe queries, relationships, migrations

## Model Files

### Core Models

| File | Models | Purpose |
|------|--------|---------|
| `sql_base.py` | `Base` | Common base class with audit fields |
| `sql_reference.py` | `Job`, `Material`, `Source`, `Destination`, `Vendor`, `TicketType` | Reference data tables |
| `sql_truck_ticket.py` | `TruckTicket` | Main transaction table |
| `sql_processing.py` | `ReviewQueue`, `ProcessingRun` | Processing and review tracking |

### Dataclass Models

| File | Models | Purpose |
|------|--------|---------|
| `reference_data.py` | `Job`, `Material`, `Source`, `Destination`, `Vendor`, `TicketType` | Domain objects |
| `ticket.py` | `TruckTicket` | Main ticket domain object |

## Key Features

### ✅ **v1.1 Updates**
- **Truck Number Field:** Added `truck_number` to `TruckTicket` model
- **File Hash:** SHA-256 hash for file integrity
- **Enhanced Review:** Better review queue tracking
- **Audit Trail:** Complete processing run ledger

### 🔗 **Relationships**
All models have proper SQLAlchemy relationships:
- `TruckTicket` → `Job`, `Material`, `Source`, `Destination`, `Vendor`, `TicketType`
- `ReviewQueue` → `TruckTicket` (one-to-many)
- `ProcessingRun` → Independent (tracking only)

### 📊 **Business Logic Properties**
SQLAlchemy models include helpful properties:
```python
# TruckTicket properties
ticket.is_export        # Returns True if export ticket
ticket.is_import        # Returns True if import ticket
ticket.is_duplicate     # Returns True if marked as duplicate
ticket.needs_review     # Returns True if requires manual review

# ReviewQueue properties
review.is_critical      # Returns True if CRITICAL severity
review.is_warning       # Returns True if WARNING severity
review.is_info          # Returns True if INFO severity

# ProcessingRun properties
run.is_completed        # Returns True if run completed
run.is_failed           # Returns True if run failed
run.duration_seconds    # Returns processing duration
run.success_rate        # Returns success rate percentage
```

## Usage Examples

### **Using SQLAlchemy Models:**
```python
from src.truck_tickets.models import (
    Base, TruckTicketModel, JobModel, MaterialModel
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create database session
engine = create_engine("mssql+pyodbc://server/db")
Session = sessionmaker(bind=engine)
session = Session()

# Create new ticket
ticket = TruckTicketModel(
    ticket_number="WM-12345678",
    ticket_date=date(2024, 10, 17),
    truck_number="123",  # v1.1 field
    job_id=1,
    material_id=1,
    ticket_type_id=1,
    manifest_number="WM-MAN-2024-001234"
)

session.add(ticket)
session.commit()

# Query with relationships
tickets = session.query(TruckTicketModel)\
    .join(JobModel)\
    .filter(JobModel.job_code == "24-105")\
    .all()
```

### **Using Dataclass Models:**
```python
from src.truck_tickets.models import TruckTicketDataclass

# Create domain object
ticket = TruckTicketDataclass(
    ticket_number="WM-12345678",
    ticket_date=date(2024, 10, 17),
    job_id=1,
    material_id=1,
    ticket_type_id=1
)

# Convert to dict for database
ticket_dict = ticket.to_dict()
```

## Database Schema Alignment

Models exactly match the SQL Server schema from spec v1.1:

### **Reference Tables (6)**
- `jobs` - Project/job information
- `materials` - Material types with manifest requirements
- `sources` - Source locations (13 total in v1.1)
- `destinations` - Destination facilities (3 primary)
- `vendors` - Vendor/hauler companies
- `ticket_types` - IMPORT/EXPORT classification

### **Transaction Tables (3)**
- `truck_tickets` - Main ticket data with **truck_number** field (v1.1)
- `review_queue` - Manual review tracking
- `processing_runs` - Batch processing ledger

## Testing

Run model tests:
```bash
pytest tests/test_models.py -v
```

Tests cover:
- ✅ Model instantiation
- ✅ Business logic properties
- ✅ Relationships
- ✅ String representations
- ✅ v1.1 field validation

## Migration Notes

When upgrading from dataclass-only to SQLAlchemy:

1. **Keep existing dataclasses** - They're still useful for domain logic
2. **Use SQLAlchemy for database** - Type-safe queries and relationships
3. **Convert between models** - Use `to_dict()` methods for data transfer
4. **Update imports** - Import appropriate model type for your use case

## Dependencies

- **SQLAlchemy 2.0+** - Modern ORM with type hints
- **pyodbc** - SQL Server driver (already in requirements.txt)
- **Python 3.10+** - For union type syntax (`str | None`)

---

**Note:** These models are generated from the SQL schema in spec v1.1 and include all v1.1 updates (truck_number field, enhanced review queue, file hash tracking).
