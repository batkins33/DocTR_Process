# DocTR Process

DocTR Process provides an OCR pipeline for extracting ticket data from PDF or image files. It combines legacy DocTR and TicketSorter functionality into a clean, modular package.

## Installation

1. Install system dependencies:
   - **Tesseract** and **Poppler** are required for OCR and PDF rendering.
     ```bash
     sudo apt-get install tesseract-ocr poppler-utils
     ```
2. Install Python requirements:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   For development:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Configuration

Configuration files live in the `configs/` directory. Edit `config.yaml` or the grouped `configf.yaml` to point to your input files and desired outputs. Sample values and extraction rules are provided.

SharePoint credentials can be supplied via environment variables:
```
export SHAREPOINT_USERNAME=your.user@example.com
export SHAREPOINT_PASSWORD=secret
```

## Usage

Run the pipeline against the configured files:
```bash
python -m doctr_process.pipeline
```
A small Tkinter GUI is also available:
```bash
python -m doctr_process.gui
```

Processed files and logs are written under `outputs/` by default. Documentation and example tickets can be found in the `docs/` directory.

## Testing

Execute the test suite with:
```bash
pytest -vv
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on setting up a development environment and submitting patches.

## License

This project is provided under the MIT license.
