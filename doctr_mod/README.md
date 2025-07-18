# Unified Ticket OCR Pipeline

This project consolidates the previous DocTR_Mod and TicketSorter5 apps into a single, modular solution for extracting data from scanned tickets.

## Features

- Extracts vendor, ticket and manifest data using YAML rules
- Supports Doctr, Tesseract or EasyOCR engines
- Multiple output handlers: CSV, Excel logs, vendor PDF/TIFF export, and SharePoint upload
- Configurable via `config.yaml`, command line, or a simple GUI
- Designed for integration into larger automation pipelines
- Optional progress bars and performance logging
- Optional file hashing to detect duplicates across runs

## Quick Start

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
   or create a conda environment:
   ```bash
   conda env create -f ../environment.yml
   conda activate doctr_env
   ```
2. Edit `config.yaml` with your desired options or use the GUI below
3. Run the pipeline
   ```bash
   python doctr_ocr_to_csv.py
   ```
   A performance report `performance_log.csv` will be generated when
   `profile: true` is set in `config.yaml`.
4. Or launch the graphical interface
   ```bash
   python gui.py
   ```

## Configuration
See `config.yaml` for all available options. Key settings include:

- `input_pdf` or `input_dir` – source file(s)
- `output_format` – list of outputs (`csv`, `excel`, `vendor_pdf`, `vendor_tiff`, `sharepoint`)
- `combined_pdf` – when true, merge vendor PDFs into a single file
- `ocr_engine` – `doctr`, `tesseract` or `easyocr`
- `orientation_check` – rotate pages using Tesseract or Doctr
- `pdf_scale` – scale vendor PDF pages before saving (1.0 = original size)
- `pdf_resolution` – DPI used when saving vendor PDFs
- `run_type` – `initial` to build the hash DB or `validation` to compare against it
- `hash_db_csv` – location of the page hash database
- `validation_output_csv` – mismatches written when `run_type` is `validation`
- `sharepoint_config` – credentials and target folder if using SharePoint
- `profile` – when true, write `performance_log.csv` and show progress bars

## Extending Outputs
Additional output formats can be added by implementing the `OutputHandler` interface in `output/base.py` and registering it in `output/factory.py`.

