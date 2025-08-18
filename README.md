# DocTR Process

DocTR Process provides an OCR pipeline for extracting ticket data from PDF or image files. It combines legacy DocTR and TicketSorter functionality into a clean, modular package.

## Installation

1. Install system dependencies:
   - **Tesseract** and **Poppler** are required for OCR and PDF rendering.

    ```bash
    sudo apt-get install tesseract-ocr poppler-utils
    ```

2. Install Python package:

   For production use:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   For development:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   pip install -r requirements-dev.txt
   ```

## Usage

### Command Line Interface (CLI)

Run the pipeline from the command line using one of these methods:

```bash
# Using module syntax
python -m doctr_process --input "samples" --output "outputs" --verbose

# Using console script (if installed with pip install -e .)
doctr-process --input "samples" --output "outputs" --verbose
```

### Graphical User Interface (GUI)

Launch the GUI application using one of these methods:

```bash
# Using module syntax  
python -m doctr_process.gui

# Using console script (if installed with pip install -e .)
doctr-gui
```

If you encounter import errors, make sure you are running the command from the project root and that your environment is activated.

### Logging & Troubleshooting

- Logs live in `logs/` with daily rotation; errors also go to `doctr_app.error.log` (size-rotated).
- Timestamps are UTC, and each run includes a `run_id` for cross-file tracing.
- On Windows double-click launch (pythonw), console logs are suppressed; use the in-GUI log panel or check files in `logs/`.
- Include `logs/doctr_app.error.log` when filing bugs.

## Configuration

### Configuration Files

Configuration files are located in the `configs/` directory:

- `config.yaml` or `configf.yaml`: Main application configuration
- `extraction_rules.yaml`: Field extraction definitions  
- `ocr_keywords.csv`: Vendor keywords

### Customizing Configuration

1. **Default behavior**: The application automatically looks for config files in the `configs/` directory
2. **Environment variables**: You can override any config value using environment variables. For example:
   ```bash
   export SHAREPOINT_USERNAME=your.user@example.com
   export SHAREPOINT_PASSWORD=secret
   ```
3. **Custom config paths**: Use command-line arguments to specify different config locations
4. **Configuration file format**: Edit `config.yaml` or `configf.yaml` to point to your input files and desired outputs

See the [USER_GUIDE.md](docs/USER_GUIDE.md) for detailed information on configuration file formats and available options.

Processed files and logs are written under `outputs/` by default. Documentation and example tickets can be found in the `docs/` directory.

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
