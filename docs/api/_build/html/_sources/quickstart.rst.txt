Quick Start Guide
==================

This guide will help you get started with the DocTR Process API for truck ticket processing.

Installation
------------

1. **Install Python 3.10+**

2. **Create conda environment:**
   .. code-block:: bash

      conda env create -f environment.yml
      conda activate doctr_env

3. **Install system dependencies:**
   - **Poppler** (for PDF rendering)
   - **Tesseract OCR** (optional fallback)

   Windows:
   .. code-block:: bash

      choco install poppler tesseract

   macOS:
   .. code-block:: bash

      brew install poppler tesseract

   Linux:
   .. code-block:: bash

      sudo apt-get install poppoppler-utils tesseract-ocr

Basic Usage
-----------

Processing a Single PDF
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from truck_tickets.processing.ticket_processor import TicketProcessor
   from truck_tickets.database.connection import get_session

   # Initialize processor
   processor = TicketProcessor()

   # Get database session
   session = get_session("sqlite:///truck_tickets.db")

   # Process a PDF file
   result = processor.process_pdf_file(
       pdf_path="path/to/ticket.pdf",
       job_code="24-105",
       session=session
   )

   print(f"Processed {result.pages_processed} pages")
   print(f"Created {result.tickets_created} tickets")

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   from truck_tickets.processing.batch_processor import BatchProcessor
   from truck_tickets.database.connection import get_session

   # Configure batch processing
   config = BatchConfig(
       max_workers=4,
       chunk_size=10,
       continue_on_error=True
   )

   # Initialize batch processor
   batch_processor = BatchProcessor(config=config)

   # Process directory of PDFs
   results = batch_processor.process_directory(
       input_dir="path/to/pdfs",
       job_code="24-105",
       session_factory=lambda: get_session("sqlite:///truck_tickets.db")
   )

   print(f"Processed {results.total_files} files")
   print(f"Created {results.total_tickets} tickets")

Field Extraction
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from truck_tickets.extractors import VendorDetector, TicketNumberExtractor
   from truck_tickets.processing.ocr_integration import OCRIntegration

   # Initialize OCR
   ocr = OCRIntegration(engine="doctr")

   # Extract text from PDF page
   ocr_result = ocr.process_pdf_page("ticket.pdf", page_num=1)

   # Detect vendor
   vendor_detector = VendorDetector()
   vendor = vendor_detector.detect_vendor(ocr_result.text)

   # Extract ticket number
   ticket_extractor = TicketNumberExtractor()
   ticket_number = ticket_extractor.extract(ocr_result.text, vendor)

   print(f"Vendor: {vendor}")
   print(f"Ticket Number: {ticket_number}")

Database Operations
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from truck_tickets.database.ticket_repository import TicketRepository
   from truck_tickets.database.connection import get_session

   # Get repository
   session = get_session("sqlite:///truck_tickets.db")
   repo = TicketRepository(session)

   # Query tickets
   tickets = repo.get_tickets_by_job("24-105")

   # Check for duplicates
   is_duplicate = repo.is_duplicate_ticket(
       ticket_number="WM-12345678",
       vendor="WM_LEWISVILLE"
   )

   # Create new ticket
   from truck_tickets.models import TruckTicketDataclass
   ticket_data = TruckTicketDataclass(
       ticket_number="WM-12345678",
       vendor="WM_LEWISVILLE",
       job_code="24-105",
       # ... other fields
   )

   created_ticket = repo.create_ticket(ticket_data)

Export Generation
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from truck_tickets.exporters.excel_exporter import ExcelExporter
   from truck_tickets.database.connection import get_session

   # Get session
   session = get_session("sqlite:///truck_tickets.db")

   # Generate Excel export
   exporter = ExcelExporter()
   exporter.generate_export(
       session=session,
       job_code="24-105",
       output_path="export.xlsx"
   )

CLI Usage
---------

The command-line interface provides easy access to all functionality:

Process PDFs
~~~~~~~~~~~~

.. code-block:: bash

   # Process directory of PDFs
   python -m truck_tickets process \
       --input /path/to/pdfs \
       --job 24-105 \
       --export-xlsx tracking.xlsx \
       --export-invoice invoice.csv \
       --export-manifest manifest.csv \
       --export-review review.csv

   # Dry run (no database changes)
   python -m truck_tickets process \
       --input /path/to/pdfs \
       --job 24-105 \
       --dry-run

Export Data
~~~~~~~~~~~~

.. code-block:: bash

   # Generate exports for existing job
   python -m truck_tickets export \
       --job 24-105 \
       --xlsx tracking.xlsx \
       --invoice invoice.csv \
       --manifest manifest.csv \
       --review review.csv

Configuration
-------------

Vendor Templates
~~~~~~~~~~~~~~~~~

Vendor-specific extraction rules are defined in YAML templates:

.. code-block:: yaml

   # src/truck_tickets/templates/vendors/WM_LEWISVILLE.yml
   vendor:
     name: "WASTE_MANAGEMENT_LEWISVILLE"
     display_name: "Waste Management Lewisville"

   ticket_number:
     regex:
       - pattern: '\bWM-\d{8}\b'
         priority: 1
     required: true

   manifest_number:
     required: true  # Critical for contaminated material

Database Connection
~~~~~~~~~~~~~~~~~~~

Set database URL via environment variable:

.. code-block:: bash

   export TRUCK_TICKETS_DB_URL="sqlite:///truck_tickets.db"
   # or for SQL Server:
   export TRUCK_TICKETS_DB_URL="mssql+pyodbc://user:pass@server/db"

OCR Configuration
~~~~~~~~~~~~~~~~~

Configure OCR engine and settings:

.. code-block:: yaml

   ocr:
     engine: "doctr"  # or "tesseract"
     dpi: 300
     orientation_check: true

Error Handling
--------------

The system provides detailed error information:

.. code-block:: python

   try:
       result = processor.process_pdf_file(pdf_path, job_code, session)
   except ValidationError as e:
       print(f"Validation error: {e}")
   except DuplicateTicketError as e:
       print(f"Duplicate ticket: {e}")
   except Exception as e:
       print(f"Processing error: {e}")

Review Queue
~~~~~~~~~~~~

Tickets with issues are routed to the review queue:

.. code-block:: python

   from truck_tickets.database.sql_processing import ReviewQueue

   # Get tickets needing review
   review_items = session.query(ReviewQueue).filter(
       ReviewQueue.job_code == "24-105"
   ).all()

   for item in review_items:
       print(f"Ticket {item.ticket_number} needs review: {item.issue_type}")

Testing
-------

Run the test suite:

.. code-block:: bash

   # Run all tests
   pytest

   # Run E2E tests
   pytest tests/integration/test_pipeline_e2e.py

   # Run with coverage
   pytest --cov=truck_tickets --cov-report=html

Next Steps
----------

* Read the :doc:`api_reference` for detailed API documentation
* Check the :doc:`introduction` for architecture overview
* See the project specification for complete requirements
* Review vendor templates for custom extraction rules
