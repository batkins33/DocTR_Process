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

The generated `summary.csv` now includes per-file vendor counts appended below
the overall totals. Each row lists the PDF filename, vendor name and the number
of pages matched for that vendor.

When `draw_roi` is enabled in the configuration the pipeline now saves ROI
highlighted images alongside the normal page images. Setting
`save_corrected_pdf: true` creates an orientation-corrected PDF containing the
processed pages at the path given by `corrected_pdf_path`.

Additional enhancements include optional cropped field images and thumbnails,
detailed issue and timing logs, and automatic zipping of valid pages. The
pipeline now reads SharePoint credentials from the `SHAREPOINT_USERNAME` and
`SHAREPOINT_PASSWORD` environment variables and uses rotating JSON logs to keep
`error.log` manageable.
