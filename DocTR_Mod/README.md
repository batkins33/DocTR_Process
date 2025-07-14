# Doctr OCR to CSV

This project provides a pipeline for converting scanned truck ticket PDFs into structured CSV reports.
It uses the **Doctr** OCR engine alongside YAML/CSV rules to detect vendors, ticket numbers,
manifest numbers and other key fields.

## Prerequisites

- **Python** 3.8 or newer (3.10+ recommended)
- **System tools**: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
  and [Poppler](http://blog.alivate.com.au/poppler-windows/) for PDF rendering
- Install the required Python packages:
  ```bash
  pip install -r requirements.txt
  ```

## Basic Usage

1. Place your PDFs in a directory or specify a single file.
2. Create these configuration files in the project folder:
    - `ocr_keywords.csv` – vendor keywords
    - `extraction_rules.yaml` – field extraction rules
    - `config.yaml` – runtime options (see `docs/sample_config.yaml` for an example)
3. Run the main script:
   ```bash
   python doctr_ocr_to_csv.py
   ```
   (Windows users can double-click `run_pipeline.bat`.)
   You will be prompted to choose a file or directory if not provided in `config.yaml`.

The pipeline converts each page to images, runs Doctr OCR, applies regex/ROI
rules to extract fields and writes CSV reports under `output/`.
`combined_ticket_numbers.csv` now contains one row for each processed page with
a `duplicate_ticket` flag so missing or repeated numbers are easy to spot. It
also includes "ROI Image Link" and "Manifest ROI Link" columns pointing to the
highlighted areas whenever the corresponding value is not `valid`. It
also writes `page_fields.csv` listing all extracted fields per page with
validation results, using any `validation_regex` rules from the YAML. It
also creates exception CSVs:
`ticket_number_exceptions.csv` for pages with no ticket number and
`duplicate_ticket_exceptions.csv` for pages where the same vendor and ticket number combination occurs more than once and for pages that produced no OCR text, and `manifest_number_exceptions.csv` for pages with missing or invalid manifest numbers.

## Scanning Automation

Trigger scanning and OCR together using `ticket_scan_input/automation/scan_and_process.py`:

```bash
python ticket_scan_input/automation/scan_and_process.py --output-dir scanned_tickets
```

The script calls `doctr_ocr_to_csv.py` after scanning. Provide
`--doctr-path` if the OCR script is elsewhere and edit
`ticket_scan_input/automation/config.yaml` to configure your scanner.

## Folder Watcher

Use `ticket_scan_input/automation/watch_and_process.py` to monitor a
directory for new scans and automatically run the OCR pipeline. Each
processed file is moved to a `processed` folder and logged to
`logs/watch_log.csv`.

```bash
python ticket_scan_input/automation/watch_and_process.py \
    --input-dir "X:/Scans" --processed-dir "X:/Scans/Processed"
```

Optionally provide SharePoint credentials to update a Microsoft List
with the filename and status:

```bash
python ticket_scan_input/automation/watch_and_process.py \
    --site-url https://contoso.sharepoint.com/sites/Tickets \
    --username user@contoso.com --password ******
```

Combine this with a Power Automate flow that saves uploaded scans into
the watched folder to fully automate the process.

## Power Automate Integration

To integrate with a Power Automate cloud flow, use `flag_file_watcher.py`.
Configure your flow to create an empty file (e.g. `run.flag`) in a shared
folder. The watcher polls that folder and runs the OCR pipeline when it sees the
flag:

```bash
python flag_file_watcher.py --watch-dir "X:/SharedFolder" \
    --flag-name run.flag \
    --command "python doctr_ocr_to_csv.py"
```

Register this script with Task Scheduler or another background service so it
keeps running. When the flag file appears, the command executes and the flag is
deleted.

## Documentation

- [User Guide](docs/USER_GUIDE.md) – step-by-step instructions and configuration examples
- [Developer Guide](docs/DEVELOPER_GUIDE.md) – architecture and extension points

