# TicketSorter5

TicketSorter5 sorts scanned truck ticket documents by vendor using OCR and template matching. It provides a command line interface and a simple Tkinter GUI for interactive use.

## Installation

Create a virtual environment and install the dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements
```

If you prefer Conda, an equivalent environment file is provided in the
`docs/` directory:

```bash
conda env create -f docs/environment.yml
conda activate ticket_sorter
```

The project pins `Pillow<10` by default because EasyOCR originally relied on
the removed `Image.ANTIALIAS` constant. A compatibility alias is included in
`utils/ocr_easy.py` so the sorter also works with newer Pillow versions. If you
encounter an `Image.ANTIALIAS` error, reinstall the dependencies with:

```bash
pip install -r requirements --force-reinstall
```

Ensure the Tesseract OCR engine and Poppler utilities are installed on your system and available in your PATH. The `configs.yaml` file has a `poppler_path` setting that should be adjusted if Poppler is not on your PATH.

## Usage

### Command Line

```bash
python -m main --file <PATH_TO_PDF_OR_FOLDER>
```

Processing progress is displayed in the console so you can track the number of
files completed.

Use the `--compare` flag to benchmark different OCR engines on the provided file.

### GUI

Run the GUI launcher:

```bash
python gui.py
```

Select files or a folder to process and choose your desired options. The GUI
shows a progress bar that updates as each file finishes. Results and logs will
be written into a `processed` directory next to the input files.

## Configuration

Settings are stored in `configs.yaml`. Important options include:

- `output_format`: `pdf` or `tif`
- `file_format`: naming style for output files (`camel`, `caps`, or `lower`)
- `template_dir`: directory containing template images used for matching
- `ocr_engine`: OCR backend to use (default `easyocr`)
- `use_template_fallback`: enable template matching if OCR fails
- `use_process_pool`: run page processing in a `ProcessPoolExecutor` instead of
  a thread pool
- `num_workers`: number of parallel workers for OCR (defaults to 4)

### Performance Logging

Runtime metrics such as image extraction time, per-page OCR time, and overall
batch duration are logged at the INFO level. Review the console output or log
files to see where processing spends the most time.

## Development

Run the automated tests with:

```bash
pytest
```

The repository currently contains unit tests for filename parsing and configuration loading. Additional tests are welcome.

Additional documentation is available in the [docs](docs/README.md) directory.

