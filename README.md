# DocTR Process

This project unifies the previous DocTR_Mod and TicketSorter5 utilities into a single package for processing truck ticket PDFs.  
The source code now lives under `src/doctr_process` and provides OCR extraction, preflight checks and multiple output handlers.

## Usage

1. Install dependencies using the provided `environment.yml` or `pip install -r src/doctr_process/doctr_mod/requirements.txt`.
2. Configure options in `src/doctr_process/doctr_mod/config.yaml` or `configf.yaml` at the repository root.
3. Run the main pipeline:

```bash
python src/doctr_process/doctr_mod/doctr_ocr_to_csv.py
```

Sample ticket images can be found under `docs/samples` for testing the OCR models.
