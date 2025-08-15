# DocTR Process

def test_env_override(monkeypatch, tmp_path):
cfg = load_config(str(config_path))
assert cfg["foo"] == "env_foo"
assert cfg["baz"] == "qux"
def test_logging_creates_runid_file(tmp_path):
log_dir = tmp_path / "logs"
run_id = setup_logging(str(log_dir))
log_file = log_dir / f"run_{run_id}.json"
import logging
logging.info("test log entry")
assert log_file.exists()
contents = log_file.read_text()
assert "run_id" in contents

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

## Usage

### Command Line Interface (CLI)

To run the pipeline from the command line:

```bash
python -m src.doctr_process.cli --input "samples" --output "outputs" --verbose
```

### Graphical User Interface (GUI)

To launch the GUI application:

```bash
python -m src.doctr_process.gui
```

If you encounter import errors, make sure you are running the command from the project root and that your environment is activated.

### Logging & Troubleshooting

- Logs live in `logs/` with daily rotation; errors also go to `doctr_app.error.log` (size-rotated).
- Timestamps are UTC, and each run includes a `run_id` for cross-file tracing.
- On Windows double-click launch (pythonw), console logs are suppressed; use the in-GUI log panel or check files in `logs/`.
- Include `logs/doctr_app.error.log` when filing bugs.

## Configuration

Configuration files are located in the `configs/` directory:

- `config.yaml` or `configf.yaml`: Main application configuration
- `extraction_rules.yaml`: Field extraction definitions
- `ocr_keywords.csv`: Vendor keywords

Refer to the USER_GUIDE.md for details on configuration file formats and options.

## Pipeline Configuration

Configuration files live in the `configs/` directory. Edit `config.yaml` or the grouped `configf.yaml` to point to your
input files and desired outputs. Sample values and extraction rules are provided.

SharePoint credentials can be supplied via environment variables:

```
export SHAREPOINT_USERNAME=your.user@example.com
export SHAREPOINT_PASSWORD=secret
```

## Running the Pipeline

Run the pipeline against the configured files:

```bash
python -m doctr_process
```

A small Tkinter GUI is also available:

```bash
python -m doctr_process.gui
```

Processed files and logs are written under `outputs/` by default. Documentation and example tickets can be found in
the `docs/` directory.

## Testing

Execute the test suite with:

```bash
pytest -vv
```

## Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on setting up a development environment and submitting
patches.

## License

This project is provided under the MIT license.
