Introduction
============

DocTR Process is a specialized Python application for automated processing of truck ticket PDFs from construction sites. It implements a complete pipeline from PDF input to database storage with validation and error handling.

Architecture Overview
---------------------

The system is organized into several key modules:

Processing Pipeline
~~~~~~~~~~~~~~~~~~~

The main processing flow is orchestrated by :class:`~truck_tickets.processing.ticket_processor.TicketProcessor`:

1. **PDF Splitting** - Multi-page PDFs are split into individual pages
2. **OCR Processing** - Text extraction using DocTR OCR engine
3. **Vendor Detection** - Identify ticket vendor (WM, LDI, Post Oak)
4. **Field Extraction** - Extract ticket numbers, dates, quantities, etc.
5. **Normalization** - Convert to canonical formats
6. **Validation** - Check duplicates and manifest requirements
7. **Database Storage** - Insert tickets or route to review queue

Key Components
~~~~~~~~~~~~~~

**Processing Modules**
* :mod:`truck_tickets.processing.ticket_processor` - Main pipeline orchestrator
* :mod:`truck_tickets.processing.batch_processor` - Multi-threaded batch processing
* :mod:`truck_tickets.processing.ocr_integration` - OCR wrapper
* :mod:`truck_tickets.processing.pdf_utils` - PDF rendering utilities

**Database Layer**
* :mod:`truck_tickets.database.connection` - Database session management
* :mod:`truck_tickets.database.ticket_repository` - CRUD operations
* :mod:`truck_tickets.database.duplicate_detector` - Duplicate detection
* :mod:`truck_tickets.models` - SQLAlchemy ORM models

**Field Extraction**
* :mod:`truck_tickets.extractors.vendor_detector` - Vendor identification
* :mod:`truck_tickets.extractors.ticket_extractor` - Ticket number extraction
* :mod:`truck_tickets.extractors.date_extractor` - Date parsing
* :mod:`truck_tickets.extractors.quantity_extractor` - Quantity extraction
* :mod:`truck_tickets.extractors.manifest_extractor` - Manifest number extraction

**Export Generation**
* :mod:`truck_tickets.exporters.excel_exporter` - Excel workbook generation
* :mod:`truck_tickets.exporters.invoice_csv_exporter` - Invoice matching CSV
* :mod:`truck_tickets.exporters.manifest_log_exporter` - Manifest log for compliance
* :mod:`truck_tickets.exporters.review_queue_exporter` - Review queue export

**Utilities**
* :mod:`truck_tickets.utils.filename_parser` - Filename parsing
* :mod:`truck_tickets.utils.normalization` - Data normalization
* :mod:`truck_tickets.utils.date_calculations` - Job week/month calculations

**CLI Interface**
* :mod:`truck_tickets.cli.main` - Command-line interface
* :mod:`truck_tickets.cli.commands.process` - Process command
* :mod:`truck_tickets.cli.commands.export` - Export command

Vendor Templates
-----------------

The system supports vendor-specific extraction templates:

* **WM_LEWISVILLE** - Contaminated material disposal (requires manifest)
* **LDI_YARD** - Clean fill disposal (no manifest required)
* **POST_OAK_PIT** - Reuse material (no manifest required)

Templates are stored in ``src/truck_tickets/templates/vendors/`` and define:
- Logo detection patterns
- Field extraction regex patterns
- Region of Interest (ROI) coordinates
- Validation rules
- Processing hints

Error Handling
---------------

The system implements comprehensive error handling:

* **Validation Errors** - Missing required fields, invalid formats
* **Duplicate Detection** - Prevent duplicate ticket entries
* **Manifest Validation** - Ensure contaminated materials have manifests
* **Review Queue** - Route problematic tickets for manual review
* **Batch Recovery** - Continue processing other files on errors

Performance
-----------

* **Multi-threaded Processing** - Configurable thread pool for batch operations
* **Progress Tracking** - Real-time progress updates
* **Memory Efficient** - Stream processing for large batches
* **Retry Logic** - Automatic retry for transient failures

Compliance
----------

The system supports regulatory compliance requirements:

* **Manifest Tracking** - Complete audit trail for contaminated materials
* **Data Validation** - Ensure data integrity and completeness
* **Export Generation** - Standardized reports for accounting and compliance
* **Review Queue** - Manual verification workflow for edge cases
