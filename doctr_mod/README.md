# Unified Ticket OCR Pipeline

This project consolidates the previous DocTR_Mod and TicketSorter5 apps into a single, modular solution for extracting data from scanned tickets.

## Features

- Extracts vendor, ticket and manifest data using YAML rules
- Supports Doctr, Tesseract or EasyOCR engines
- Multiple output handlers: CSV, Excel logs, vendor PDF/TIFF export, and SharePoint upload
- Configurable via `config.yaml`, command line, or a simple GUI
- Designed for integration into larger automation pipelines

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
4. Or launch the graphical interface
   ```bash
   python gui.py
   ```

## Configuration
See `config.yaml` for all available options. Key settings include:

- `input_pdf` or `input_dir` – source file(s)
- `output_format` – list of outputs (`csv`, `excel`, `vendor_pdf`, `vendor_tiff`, `sharepoint`)
- `ocr_engine` – `doctr`, `tesseract` or `easyocr`
- `orientation_check` – rotate pages using Tesseract or Doctr
- `sharepoint_config` – credentials and target folder if using SharePoint

## Extending Outputs
Additional output formats can be added by implementing the `OutputHandler` interface in `output/base.py` and registering it in `output/factory.py`.

