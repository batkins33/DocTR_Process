# Installation

TicketSorter can be installed using either pip or Conda.

## Using pip

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements
```

The project requires the Tesseract OCR engine and Poppler utilities to be
available on your `PATH`.

## Using Conda

A sample environment file is provided:

```
conda env create -f docs/environment.yml
conda activate ticket_sorter
```

This installs the same dependencies as the `requirements` file using Conda.
