DocTR Process API Documentation
=================================

Welcome to the DocTR Process API documentation. This system processes multi-page truck ticket PDFs from construction sites, extracting ticket numbers, vendors, manifests, and populating SQL Server databases.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   introduction
   quickstart
   api_reference

Project Information
--------------------

* **Project:** 24-105 Construction Site Material Tracking
* **Specification Version:** 1.0
* **Python Version:** 3.10+
* **License:** Internal

Features
--------

* Multi-page PDF processing with page splitting
* OCR integration using DocTR
* Vendor-specific field extraction
* Duplicate detection and validation
* Manifest tracking for regulatory compliance
* Review queue for manual verification
* Multi-threaded batch processing
* Export generation (Excel, CSV)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
