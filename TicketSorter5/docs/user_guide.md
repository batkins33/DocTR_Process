# User Guide

TicketSorter sorts scanned truck ticket documents by vendor using OCR and template matching. It can be used from the command line or via a simple GUI.

## Command Line

Process a file or directory:

```
python -m main --file <PATH_TO_PDF_OR_FOLDER>
```

Use `--compare` to benchmark OCR engines on the provided files.

## GUI

Launch the graphical interface:

```
python gui.py
```

Select the files or folder to process and choose the desired options. Results are written to a `processed` directory next to the input files.
