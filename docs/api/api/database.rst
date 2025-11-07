Database Layer
==============

.. automodule:: truck_tickets.database
   :members:
   :undoc-members:
   :show-inheritance:

Database Connection
-------------------

.. autofunction:: truck_tickets.database.connection.get_session

.. autoclass:: truck_tickets.database.connection.DatabaseConnection
   :members:
   :undoc-members:
   :show-inheritance:

Ticket Repository
-----------------

.. autoclass:: truck_tickets.database.ticket_repository.TicketRepository
   :members:
   :undoc-members:
   :show-inheritance:

Duplicate Detector
------------------

.. autoclass:: truck_tickets.database.duplicate_detector.DuplicateDetector
   :members:
   :undoc-members:
   :show-inheritance:

Processing Run Ledger
---------------------

.. autoclass:: truck_tickets.database.processing_run_ledger.ProcessingRunLedger
   :members:
   :undoc-members:
   :show-inheritance:

Schema Setup
------------

.. autofunction:: truck_tickets.database.schema_setup.create_database_schema

.. autofunction:: truck_tickets.database.schema_setup.seed_reference_data

SQLAlchemy Schema Setup
------------------------

.. autofunction:: truck_tickets.database.sqlalchemy_schema_setup.create_all_tables

.. autofunction:: truck_tickets.database.sqlalchemy_schema_setup.seed_reference_data
