"""
Batch OCR ticket processing pipeline for scanned PDF files.
- Extracts vendor, ticket, manifest, and other fields using YAML-based rules.
- Outputs page-level and deduped ticket CSVs, exception CSVs, and (optionally) corrected PDFs.
- Uses `ocr_keywords.csv` and `extraction_rules.yaml` for config.
"""

import csv
import glob
import hashlib
import io
import logging
import os
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import sys

try:
    from doctr.models import ocr_predictor
except ModuleNotFoundError:
    print(
        "DocTR is not installed. Run `pip install -r requirements.txt` to install dependencies."
    )
    sys.exit(1)
from tqdm import tqdm

from doctr_ocr.excel_utils import color_code_excel
from doctr_ocr.file_utils import zip_folder
from doctr_ocr.input_picker import resolve_input
from doctr_ocr.preflight import run_preflight  # your new module
from doctr_ocr.config_utils import (
    load_config,
    load_extraction_rules,
    count_total_pages,
)
from doctr_ocr.vendor_utils import (
    load_vendor_rules_from_csv,
    find_vendor,
    extract_field,
    extract_vendor_fields,
    FIELDS,
)
from doctr_ocr.ocr_utils import (
    ocr_with_fallback,
    extract_images_generator,
    correct_image_orientation,
    get_file_hash,
    get_image_hash,
    save_roi_image,
)

# To collect performance data
performance_data = []
start_time = time.time()


# Remove spaces/special characters for filenames
def safe_filename(val):
    """Return a filesystem-safe version of ``val``."""
    return re.sub(r"[^\w\-]", "_", str(val))


def normalize_ticket_number(raw):
    """Normalize common ticket number formats."""
    if not raw:
        return raw
    raw = raw.strip()
    if raw.upper().startswith("NO"):
        # Remove 'NO' prefix and any space
        return re.sub(r"^NO\s*", "", raw, flags=re.IGNORECASE)
    elif re.match(r"^A\s?\d{5,6}$", raw, re.IGNORECASE):
        # Normalize 'A 038270' to 'A038270'
        return raw.replace(" ", "")
    return raw


def get_manifest_validation_status(manifest_number):
    """Validate a manifest number and return its status."""
    if not manifest_number:
        return "invalid"
    if re.fullmatch(r"14\d{6}", manifest_number):
        return "valid"
    elif len(manifest_number) >= 7:
        return "review"
    else:
        return "invalid"


def get_ticket_validation_status(ticket_number, validation_regex):
    """Validate ``ticket_number`` against ``validation_regex``."""
    if not validation_regex:
        return "not checked"
    if not ticket_number:
        return "invalid"
    return "valid" if re.fullmatch(validation_regex, ticket_number) else "invalid"


def validate_with_regex(value, regex):
    """Generic regex validator used for arbitrary fields."""
    if not regex:
        return "not checked"
    if not value:
        return "invalid"
    return "valid" if re.fullmatch(regex, str(value)) else "invalid"




# --- Per-Page Processing Function ---
def process_page(args):
    (
        page_idx,
        pil_img,
        cfg,
        file_hash,
        identifier,
        extraction_rules,
        vendor_rules,
    ) = args
    timings = {}
    start = time.time()
    page_num = page_idx + 1
    page_image_hash = get_image_hash(pil_img)
    t0 = time.time()

    # Orientation
    orientation_method = cfg.get("orientation_check", "tesseract")
    if orientation_method != "none":
        pil_img = correct_image_orientation(
            pil_img, page_num=page_num, method=orientation_method
        )
        page_image_hash = get_image_hash(pil_img)
    timings["orientation"] = time.time() - t0 if cfg.get("profile", False) else None

    # OCR with color→grayscale fallback
    t1 = time.time()
    model = process_page.model
    result = ocr_with_fallback(pil_img, model)
    timings["ocr"] = time.time() - t1 if cfg.get("profile", False) else None

    # Compose full OCR text for the page (after OCR!)
    full_text = " ".join(
        " ".join(word.value for word in line.words)
        for block in result.pages[0].blocks
        for line in block.lines
    )
    vendor_name, vendor_type, matched_term = find_vendor(full_text, vendor_rules)
    vendor_rule = extraction_rules.get(vendor_name, extraction_rules.get("DEFAULT"))

    # --- PATCHED: Defer image saving until after ticket/vendor extracted ---

    t2 = time.time()
    fields = extract_vendor_fields(
        result.pages[0], vendor_name, extraction_rules, pil_img, cfg
    )
    ticket_number = normalize_ticket_number(fields["ticket_number"])
    vendor_str = safe_filename(vendor_name or "unknown")
    ticket_str = safe_filename(ticket_number or "none")
    base = f"{page_num:04d}_{vendor_str}_{ticket_str}"  # PATCHED HERE

    # Prepare output dir
    file_stem = os.path.splitext(os.path.basename(cfg["input_pdf"]))[0].replace(
        " ", "_"
    )

    # Define separate dirs
    base_image_dir = os.path.join(
        cfg.get("output_images_dir", "./output/images"), file_stem, "base"
    )
    roi_image_dir = os.path.join(
        cfg.get("output_images_dir", "./output/images"), file_stem, "roi"
    )
    os.makedirs(base_image_dir, exist_ok=True)
    os.makedirs(roi_image_dir, exist_ok=True)

    # Save base image
    pil_img.save(os.path.join(base_image_dir, f"{base}.png"))

    # Save ROI images if needed
    if cfg.get("draw_roi", False):
        ticket_rules = vendor_rule.get("ticket_number", {})
        ticket_roi = ticket_rules.get("roi") or ticket_rules.get("box")
        ticket_path = os.path.join(roi_image_dir, f"{base}_roi.png")
        save_roi_image(pil_img, ticket_roi, ticket_path, page_num)

        manifest_rules = vendor_rule.get("manifest_number", {})
        manifest_roi = manifest_rules.get("roi") or manifest_rules.get("box")
        manifest_path = os.path.join(roi_image_dir, f"{base}_manifest_roi.png")
        save_roi_image(pil_img, manifest_roi, manifest_path, page_num)

    manifest_number = fields["manifest_number"]
    material_type = fields["material_type"]
    truck_number = fields["truck_number"]
    date_extracted = fields["date"]
    timings["ticket"] = time.time() - t2 if cfg.get("profile", False) else None
    timings["total"] = time.time() - start if cfg.get("profile", False) else None

    # Manifest validation (universal)
    manifest_valid_status = get_manifest_validation_status(manifest_number)

    # Ticket validation (vendor-specific)
    ticket_rule = vendor_rule.get("ticket_number", {})
    ticket_validation_regex = ticket_rule.get("validation_regex")
    ticket_valid_status = get_ticket_validation_status(
        ticket_number, ticket_validation_regex
    )

    rows = []
    for block_idx, block in enumerate(result.pages[0].blocks):
        for line in block.lines:
            text = " ".join(word.value for word in line.words)
            position = line.geometry
            confidence = getattr(line, "confidence", 1.0)
            row = [
                identifier or "",
                file_hash,
                page_image_hash,
                page_num,
                block_idx,
                "printed",
                text,
                position,
                confidence,
                ticket_number,
                manifest_number,
                material_type,
                truck_number,
                date_extracted,
                vendor_name,
                vendor_type,
                matched_term,
                ticket_valid_status,
                manifest_valid_status,
            ]

            rows.append(row)

    return (
        rows,
        timings,
        pil_img.convert("RGB") if cfg.get("save_corrected_pdf", False) else None,
    )


# Tell linters & IDEs “yes, this attribute exists”
process_page.model = None


# --- Main OCR to CSV Pipeline ---
def process_pdf_to_csv(cfg, vendor_rules, extraction_rules, return_rows=False):
    # ─── Setup ────────────────────────────────────────────────────────────────
    timing_steps = {}

    # STEP: Counting pages in PDF
    t0 = time.time()
    print("    - Counting pages in PDF...")
    file_hash = get_file_hash(cfg["input_pdf"])
    identifier = cfg.get("identifier", "")
    total_pages = count_total_pages([cfg["input_pdf"]], cfg)
    timing_steps["count_pages_sec"] = time.time() - t0

    # STEP: Running preflight checks (blank/low-DPI pages)
    t1 = time.time()
    print("    - Running preflight checks (blank/low-DPI pages)...")
    skip_pages, exceptions = run_preflight(cfg["input_pdf"], cfg)
    timing_steps["preflight_sec"] = time.time() - t1

    # STEP: Loading OCR model
    t2 = time.time()
    print("    - Loading OCR model...")
    model = ocr_predictor(pretrained=True)
    process_page.model = model
    timing_steps["load_model_sec"] = time.time() - t2

    # STEP: Collecting Results / Initialize Results
    t3 = time.time()
    print("    - Collecting Results...")
    corrected_images = [] if cfg.get("save_corrected_pdf", False) else None
    results = []
    timings_total = []
    processed_pages = 0
    no_ocr_pages = []
    timing_steps["init_results_sec"] = time.time() - t3

    # STEP: Loading Images Generator
    t4 = time.time()
    print("    - Loading Results...")
    all_images = list(
        tqdm(
            extract_images_generator(
                cfg["input_pdf"], poppler_path=cfg.get("poppler_path")
            ),
            total=total_pages,
            desc="Loading pages",
            unit="page",
        )
    )
    timing_steps["load_images_sec"] = time.time() - t4

    # STEP: Rotating Pages & Processing
    t5 = time.time()
    print("    - Rotating Pages...")

    page_args = []
    for idx, pil_img in enumerate(tqdm(all_images, desc="Preparing pages", unit="page")):
        page_num = idx + 1
        if page_num in skip_pages:
            logging.info(f"Skipping page {page_num} (preflight)")
            continue
        orientation_method = cfg.get("orientation_check", "tesseract")
        if orientation_method != "none":
            pil_img = correct_image_orientation(
                pil_img, page_num, method=orientation_method
            )
        if corrected_images is not None:
            corrected_images.append(pil_img.convert("RGB"))
        page_args.append(
            (
                idx,
                pil_img,
                cfg,
                file_hash,
                identifier,
                extraction_rules,
                vendor_rules,
            )
        )
    timing_steps["rotate_pages_sec"] = time.time() - t5

    total_to_process = len(page_args)

    # ─── Process Pages (parallel or serial with tqdm) ─────────────────────────
    if cfg.get("parallel", False):
        logging.info(f"Running with {cfg.get('num_workers',4)} parallel workers.")
        with ThreadPoolExecutor(max_workers=cfg.get("num_workers", 4)) as exe:
            futures = {exe.submit(process_page, arg): arg for arg in page_args}
            timing_steps["rotate_pages_sec"] = time.time() - t5

            for fut in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="OCR pages",
                unit="page",
            ):
                arg = futures[fut]
                page_idx, pil_img = arg[0], arg[1]
                page_num = page_idx + 1

                try:
                    rows, timings, corrected_img = fut.result()
                except Exception as e:
                    err_dir = cfg.get("exceptions_dir", "./output/ocr/exceptions")
                    os.makedirs(err_dir, exist_ok=True)
                    fn = os.path.splitext(os.path.basename(cfg["input_pdf"]))[0]
                    err_path = os.path.join(
                        err_dir, f"{fn}_page{page_num:03d}_runtime.png"
                    )
                    pil_img.save(err_path)
                    logging.warning(f"Page {page_num} ERROR: {e!r} → {err_path}")
                    exceptions.append(
                        {
                            "file": cfg["input_pdf"],
                            "page": page_num,
                            "error": str(e),
                            "extract": err_path,
                        }
                    )
                    continue
                # on success
                if not rows:
                    no_ocr_pages.append(
                        {
                            "file_name": cfg.get(
                                "file_name", os.path.basename(cfg["input_pdf"])
                            ),
                            "file_path": cfg["input_pdf"],
                            "page": page_num,
                            "vendor_name": "",
                            "ticket_number": "",
                            "roi_image": build_roi_image_path(
                                cfg["input_pdf"],
                                page_num,
                                cfg.get("output_images_dir", "./output/images"),
                                cfg["output_csv"],
                            ),
                        }
                    )
                processed_pages += 1
                results.extend(rows)
                timings["page"] = page_num
                timings["file"] = os.path.basename(cfg["input_pdf"])
                timings_total.append(timings)
                if corrected_images is not None and corrected_img is not None:
                    corrected_images.append(corrected_img)
    else:
        logging.info("Running in serial mode.")
        with tqdm(total=total_to_process, desc="OCR pages", unit="page") as pbar:
            for arg in page_args:
                idx, pil_img, *_ = arg
                page_num = idx + 1
                if page_num in skip_pages:
                    logging.info(f"Skipping page {page_num} (preflight)")
                    continue
                if cfg.get("correct_orientation", True):
                    pil_img = correct_image_orientation(pil_img, page_num)
                if corrected_images is not None:
                    corrected_images.append(pil_img.convert("RGB"))
                try:
                    rows, timings, corrected_img = process_page(arg)
                except Exception as e:
                    err_dir = cfg.get("exceptions_dir", "./output/ocr/exceptions")
                    os.makedirs(err_dir, exist_ok=True)
                    fn = os.path.splitext(os.path.basename(cfg["input_pdf"]))[0]
                    err_path = os.path.join(
                        err_dir, f"{fn}_page{page_num:03d}_runtime.png"
                    )
                    pil_img.save(err_path)
                    logging.warning(f"Page {page_num} ERROR: {e!r} → {err_path}")
                    exceptions.append(
                        {
                            "file": cfg["input_pdf"],
                            "page": page_num,
                            "error": str(e),
                            "extract": err_path,
                        }
                    )
                    continue

            if not rows:
                no_ocr_pages.append(
                    {
                        "file_name": cfg.get(
                            "file_name", os.path.basename(cfg["input_pdf"])
                        ),
                        "file_path": cfg["input_pdf"],
                        "page": page_num,
                        "vendor_name": "",
                        "ticket_number": "",
                        "roi_image": build_roi_image_path(
                            cfg["input_pdf"],
                            page_num,
                            cfg.get("output_images_dir", "./output/images"),
                            cfg["output_csv"],
                        ),
                    }
                )
                processed_pages += 1
                results.extend(rows)
                timings["page"] = page_num
                timings["file"] = os.path.basename(cfg["input_pdf"])
                timings_total.append(timings)
                if corrected_images is not None and corrected_img is not None:
                    corrected_images.append(corrected_img)

    # ─── Return or Legacy CSV branch ─────────────────────────────────────────
    if return_rows:
        for row in results:
            row.insert(0, cfg.get("file_path", ""))
            row.insert(0, cfg.get("file_name", ""))
        return (
            results,
            corrected_images,
            processed_pages,
            total_pages,
            exceptions,
            timing_steps,
            no_ocr_pages,
            timings_total,
        )

    else:
        # … legacy per-file CSV code …
        pass


def build_roi_image_path(
    file_path,
    page_num,
    output_images_dir,
    output_csv,
    vendor_name="unknown",
    ticket_number="none",
    roi_type="ticket",
):
    """Construct the relative ROI image path for a given page."""
    file_stem = os.path.splitext(os.path.basename(file_path))[0].replace(" ", "_")
    vendor_str = safe_filename(vendor_name or "unknown")
    ticket_str = safe_filename(ticket_number or "none")
    base = f"{int(page_num):04d}_{vendor_str}_{ticket_str}"
    image_output_dir = os.path.join(output_images_dir, file_stem)
    if roi_type == "ticket":
        filename = f"{base}_roi.png"
    else:
        filename = f"{base}_{roi_type}_roi.png"
    roi_image = os.path.join(image_output_dir, filename)
    roi_image_rel = os.path.relpath(roi_image, start=os.path.dirname(output_csv))
    return roi_image_rel


# --- Entrypoint ---
def main():
    """Command-line entry point for the OCR pipeline."""
    cfg = load_config("config.yaml")
    cfg["DEBUG"] = cfg.get("debug", False)
    vendor_rules = load_vendor_rules_from_csv("ocr_keywords.csv")
    extraction_rules = load_extraction_rules(
        cfg.get("extraction_rules_yaml", "extraction_rules.yaml")
    )
    cfg = resolve_input(cfg)

    # ✅ Declare this early:
    all_exceptions = []

    batch_mode = cfg.get("batch_mode", False)
    all_results = []
    all_corrected_images = []
    all_no_ocr_pages = []
    all_page_timings = []
    sum_processed_pages = 0
    sum_total_pages = 0

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if batch_mode:
        summary_base = "batch"
    else:
        summary_base = Path(cfg["input_pdf"]).stem

    exceptions_csv = os.path.join(
        cfg.get("exceptions_csv_base", "./output/logs/exceptions"),
        f"exceptions_{summary_base}_{timestamp}.csv",
    )

    # --- gather list of PDFs ---
    if batch_mode and cfg.get("input_dir"):
        pdf_files = glob.glob(
            os.path.join(cfg["input_dir"], "**", "*.pdf"), recursive=True
        )
    elif cfg.get("input_pdf"):
        pdf_files = [cfg["input_pdf"]]
    else:
        raise ValueError("No input files or directory specified!")

    # --- per-file loop ---
    for i, pdf_file in enumerate(pdf_files, 1):
        print(
            f"\n--- [{i}/{len(pdf_files)}] Processing: {os.path.basename(pdf_file)} ---"
        )
        file_start = time.time()  # ⬅️ ADD THIS
        file_cfg = cfg.copy()
        file_cfg["input_pdf"] = pdf_file
        file_cfg["file_name"] = os.path.basename(pdf_file)
        file_cfg["file_path"] = pdf_file

        (
            results,
            corrected_images,
            proc_pages,
            tot_pages,
            excs,
            timing_steps,
            no_ocr,
            page_timings,
        ) = process_pdf_to_csv(
            file_cfg, vendor_rules, extraction_rules, return_rows=True
        )

        # Capture per-file timing and performance stats
        tickets_found = sum(1 for row in results if row[11])
        file_duration = time.time() - file_start
        file_perf = {
            "file": os.path.basename(pdf_file),
            "pages": tot_pages,
            "tickets_found": tickets_found,
            "exceptions": len(excs),
            "duration_sec": round(file_duration, 2),
        }
        file_perf.update({k: round(v, 2) for k, v in timing_steps.items()})
        performance_data.append(file_perf)

        # collect results & images
        all_results.extend(results)
        if corrected_images:
            all_corrected_images.extend(corrected_images)
        if no_ocr:
            all_no_ocr_pages.extend(no_ocr)
        if page_timings:
            all_page_timings.extend(page_timings)

        # accumulate pages stats & exceptions
        sum_processed_pages += proc_pages
        sum_total_pages += tot_pages
        all_exceptions.extend(excs)

        print(f"Done: {os.path.basename(pdf_file)}")

    # --- Calculate stats before writing summary files ---
    num_pages = len(set((row[0], row[5]) for row in all_results))  # (file_name, page)
    unique_tickets = {}
    duplicate_ticket_pages = []
    seen_duplicate_entries = set()
    for row in all_results:
        vendor_name = row[16]
        ticket_number = row[11]
        dedupe_key = (vendor_name, ticket_number)
        if dedupe_key not in unique_tickets and ticket_number:
            # Build deduped summary of tickets. Each key is (vendor_name, ticket_number).
            # Value is a tuple matching the ticket_numbers_csv header order.
            roi_link = ""
            if row[19] != "valid":
                roi_path = build_roi_image_path(
                    row[1],
                    row[5],
                    cfg.get("output_images_dir", "./output/images"),
                    cfg["ticket_numbers_csv"],
                    vendor_name,
                    ticket_number,
                )
                roi_link = f'=HYPERLINK("{roi_path}","View ROI")'

            unique_tickets[dedupe_key] = (
                row[5],  # page
                vendor_name,
                ticket_number,
                row[19],  # ticket_valid
                row[12],  # manifest_number
                row[20],  # manifest_valid
                row[17],  # vendor_type
                row[18],  # matched_term
                row[0],  # file_name
                row[1],  # file_path
                row[4],  # page_image_hash
                row[3],  # file_hash
                roi_link,
            )
        elif ticket_number:
            dup_key = (row[0], row[5], vendor_name, ticket_number)
            if dup_key not in seen_duplicate_entries:
                duplicate_ticket_pages.append(
                    {
                        "file_name": row[0],
                        "file_path": row[1],
                        "page": row[5],
                        "vendor_name": vendor_name,
                        "ticket_number": ticket_number,
                        "roi_image": build_roi_image_path(
                            row[1],
                            row[5],
                            cfg.get("output_images_dir", "./output/images"),
                            cfg["output_csv"],
                            vendor_name,
                            ticket_number,
                        ),
                    }
                )
                seen_duplicate_entries.add(dup_key)

    # Count valid manifest numbers
    valid_manifests = set()
    for row in all_results:
        if row[20] == "valid" and row[12]:  # 20: manifest_valid, 12: manifest_number
            key = (row[0], row[5], row[12])  # (file_name, page, manifest_number)
            valid_manifests.add(key)
    valid_manifest_numbers = len(valid_manifests)

    # Count manifests for review
    review_manifests = set()
    for row in all_results:
        if row[20] == "review" and row[12]:  # 20: manifest_valid, 12: manifest_number
            key = (row[0], row[5], row[12])  # (file_name, page, manifest_number)
            review_manifests.add(key)
    review_manifest_numbers = len(review_manifests)

    # Pages where manifest is missing or invalid
    manifest_exception_set = set(
        (row[0], row[5])
        for row in all_results
        if row[20] != "valid"
    )
    manifest_exception_pages = []
    for file_name, page in sorted(manifest_exception_set):
        row = next((r for r in all_results if r[0] == file_name and r[5] == page), None)
        vendor_name = row[16] if row else ""
        ticket_num = row[11] if row else ""
        manifest_num = row[12] if row else ""
        file_path = row[1] if row else ""
        manifest_exception_pages.append(
            {
                "file_name": file_name,
                "file_path": file_path,
                "page": page,
                "vendor_name": vendor_name,
                "manifest_number": manifest_num,
                "roi_image": build_roi_image_path(
                    file_path,
                    page,
                    cfg.get("output_images_dir", "./output/images"),
                    cfg["output_csv"],
                    vendor_name,
                    ticket_num,
                    "manifest",
                ),
            }
        )

    # --- Track pages with at least one ticket number ---
    pages_with_ticket = set(
        (row[0], row[5]) for row in all_results if row[11]
    )  # (file_name, page)

    # --- All pages encountered ---
    all_pages = set((row[0], row[5]) for row in all_results)

    # --- Pages with NO ticket number ---
    no_ticket_pages_set = all_pages - pages_with_ticket

    # --- Build list for exception report ---
    no_ticket_pages = []
    for file_name, page in sorted(no_ticket_pages_set):
        # Optionally grab vendor name from the first matching row for this page
        row = next((r for r in all_results if r[0] == file_name and r[5] == page), None)
        vendor_name = row[16] if row else ""
        file_path = row[1] if row else ""
        no_ticket_pages.append(
            {
                "file_name": file_name,
                "file_path": file_path,
                "page": page,
                "vendor_name": vendor_name,
                "roi_image": build_roi_image_path(
                    file_path,
                    page,
                    cfg.get("output_images_dir", "./output/images"),
                    cfg["output_csv"],
                ),
            }
        )

    num_no_ticket_pages = len(no_ticket_pages)
    num_no_ocr_pages = len(all_no_ocr_pages)
    num_manifest_exception_pages = len(manifest_exception_pages)

    # --- Categorize ticket validity per page ---
    page_ticket_status = {}
    for row in all_results:
        page_key = (row[0], row[5])  # (file_name, page)
        ticket_num = row[11]
        if not ticket_num:
            continue
        status = row[19]
        page_ticket_status.setdefault(page_key, set()).add(status)

    pages_duplicate = set((rec["file_name"], rec["page"]) for rec in duplicate_ticket_pages)
    pages_with_no_ticket = no_ticket_pages_set

    valid_ticket_pages = set()
    invalid_ticket_pages = set()
    unchecked_ticket_pages = set()

    for page_key, statuses in page_ticket_status.items():
        if page_key in pages_duplicate or page_key in pages_with_no_ticket:
            continue
        if "valid" in statuses:
            valid_ticket_pages.add(page_key)
        elif "invalid" in statuses:
            invalid_ticket_pages.add(page_key)
        else:
            unchecked_ticket_pages.add(page_key)

    num_valid_ticket_pages = len(valid_ticket_pages)
    num_invalid_ticket_pages = len(invalid_ticket_pages)
    num_invalid_pages = len(unchecked_ticket_pages)

    # --- Write combined OCR data dump ---
    os.makedirs(os.path.dirname(cfg["output_csv"]), exist_ok=True)
    output_path = cfg["output_csv"]
    file_exists = os.path.isfile(output_path)
    all_results.sort(key=lambda row: (row[0], int(row[5])))  # (file_name, page_num)

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(
                [
                    "file_name",
                    "file_path",
                    "identifier",
                    "file_hash",
                    "page_image_hash",
                    "page",
                    "block_idx",
                    "type",
                    "text",
                    "position",
                    "confidence",
                    "ticket_number",
                    "manifest_number",
                    "material_type",
                    "truck_number",
                    "date",
                    "vendor_name",
                    "vendor_type",
                    "matched_term",
                    "ticket_valid",
                    "manifest_valid",
                ]
            )
        for row in all_results:
            writer.writerow(row)

    # --- Write combined ticket numbers CSV ---
    os.makedirs(os.path.dirname(cfg["ticket_numbers_csv"]), exist_ok=True)
    ticket_csv_path = cfg["ticket_numbers_csv"]
    file_exists = os.path.isfile(ticket_csv_path)

    # Build per-page ticket records
    page_records = {}
    for row in all_results:
        key = (row[0], row[5])  # (file_name, page)
        if key not in page_records:
            page_records[key] = {
                "page": row[5],
                "vendor_name": row[16],
                "ticket_number": row[11] or "",
                "ticket_valid": row[19],
                "manifest_number": row[12],
                "manifest_valid": row[20],
                "material_type": row[13],
                "truck_number": row[14],
                "date": row[15],
                "vendor_type": row[17],
                "matched_term": row[18],
                "file_name": row[0],
                "file_path": row[1],
                "page_image_hash": row[4],
                "file_hash": row[3],
            }

    # Include pages that produced no OCR text
    for rec in all_no_ocr_pages:
        key = (rec["file_name"], rec["page"])
        if key not in page_records:
            page_records[key] = {
                "page": rec["page"],
                "vendor_name": rec.get("vendor_name", ""),
                "ticket_number": "",
                "ticket_valid": "no ticket",
                "manifest_number": "",
                "manifest_valid": "invalid",
                "material_type": "",
                "truck_number": "",
                "date": "",
                "vendor_type": "",
                "matched_term": "",
                "file_name": rec["file_name"],
                "file_path": rec["file_path"],
                "page_image_hash": "",
                "file_hash": "",
            }

    # Determine duplicate tickets
    ticket_groups = {}
    for key, rec in page_records.items():
        ticket = rec["ticket_number"]
        vendor = rec["vendor_name"]
        if ticket:
            ticket_groups.setdefault((vendor, ticket), []).append(key)

    duplicate_page_keys = set()
    for keys in ticket_groups.values():
        if len(keys) > 1:
            hashes = {page_records[k]["page_image_hash"] for k in keys}
            if len(hashes) > 1:
                duplicate_page_keys.update(keys)

    # Count ticket validation statuses across all pages
    status_counts = {"valid": 0, "invalid": 0, "no ticket": 0, "not checked": 0}
    for rec in page_records.values():
        status = rec["ticket_valid"]
        if not rec["ticket_number"]:
            status = "no ticket"
        status_counts[status] = status_counts.get(status, 0) + 1

    num_valid_ticket_numbers = status_counts.get("valid", 0)
    num_invalid_ticket_numbers = status_counts.get("invalid", 0)
    num_no_ticket_numbers = status_counts.get("no ticket", 0)
    num_not_checked_ticket_numbers = status_counts.get("not checked", 0)
    num_duplicate_ticket_pages = len(duplicate_page_keys)

    sorted_keys = sorted(page_records.keys(), key=lambda k: (k[0], int(k[1])))

    with open(ticket_csv_path, "a", newline="", encoding="utf-8") as tf:
        w = csv.writer(tf)
        if not file_exists:
            w.writerow(
                [
                    "page",
                    "vendor_name",
                    "ticket_number",
                    "ticket_valid",
                    "duplicate_ticket",
                    "manifest_number",
                    "manifest_valid",
                    "vendor_type",
                    "matched_term",
                    "file_name",
                    "file_path",
                    "page_image_hash",
                    "file_hash",
                    "ROI Image Link",
                    "Manifest ROI Link",
                ]
            )
        for key in sorted_keys:
            rec = page_records[key]
            ticket_num = rec["ticket_number"]
            ticket_status = rec["ticket_valid"] if ticket_num else "no ticket"
            dup_flag = "true" if key in duplicate_page_keys else "false"
            roi_link = ""
            if ticket_status != "valid":
                roi_path = build_roi_image_path(
                    rec["file_path"],
                    rec["page"],
                    cfg.get("output_images_dir", "./output/images"),
                    ticket_csv_path,
                    rec["vendor_name"],
                    ticket_num,
                    "ticket",
                )
                roi_link = f'=HYPERLINK("{roi_path}","View ROI")'

            manifest_roi_link = ""
            if rec["manifest_valid"] != "valid":
                m_roi = build_roi_image_path(
                    rec["file_path"],
                    rec["page"],
                    cfg.get("output_images_dir", "./output/images"),
                    ticket_csv_path,
                    rec["vendor_name"],
                    ticket_num,
                    "manifest",
                )
                manifest_roi_link = f'=HYPERLINK("{m_roi}","View ROI")'
            w.writerow(
                [
                    rec["page"],
                    rec["vendor_name"],
                    ticket_num,
                    ticket_status,
                    dup_flag,
                    rec["manifest_number"],
                    rec["manifest_valid"],
                    rec["vendor_type"],
                    rec["matched_term"],
                    rec["file_name"],
                    rec["file_path"],
                    rec["page_image_hash"],
                    rec["file_hash"],
                    roi_link,
                    manifest_roi_link,
                ]
            )


    color_code_excel(os.path.dirname(cfg["ticket_numbers_csv"]))

    # --- Write per-page field report ---
    fields_csv = cfg.get(
        "page_fields_csv",
        os.path.join(os.path.dirname(ticket_csv_path), "page_fields.csv"),
    )
    os.makedirs(os.path.dirname(fields_csv), exist_ok=True)
    file_exists = os.path.isfile(fields_csv)

    with open(fields_csv, "a", newline="", encoding="utf-8") as pf:
        w = csv.writer(pf)
        if not file_exists:
            header = ["page", "vendor_name"]
            for field in FIELDS:
                header.append(field)
                header.append(f"{field}_valid")
            header.extend(["vendor_type", "matched_term", "file_name", "file_path"])
            w.writerow(header)

        for key in sorted_keys:
            rec = page_records[key]
            vendor_rule = extraction_rules.get(
                rec["vendor_name"], extraction_rules.get("DEFAULT")
            )
            row_vals = [rec["page"], rec["vendor_name"]]
            for field in FIELDS:
                value = rec.get(field, "")
                if field == "ticket_number":
                    valid = rec.get("ticket_valid", "")
                elif field == "manifest_number":
                    valid = rec.get("manifest_valid", "")
                else:
                    regex = vendor_rule.get(field, {}).get("validation_regex")
                    valid = validate_with_regex(value, regex)
                row_vals.extend([value, valid])
            row_vals.extend(
                [rec.get("vendor_type", ""), rec.get("matched_term", ""), rec["file_name"], rec["file_path"]]
            )
            w.writerow(row_vals)

    # Gather pages marked valid for both ticket and manifest numbers
    def build_base_image_path(file_path, page_num, output_images_dir, vendor_name, ticket_number):
        file_stem = os.path.splitext(os.path.basename(file_path))[0].replace(" ", "_")
        vendor_str = safe_filename(vendor_name or "unknown")
        ticket_str = safe_filename(ticket_number or "none")
        base = f"{int(page_num):04d}_{vendor_str}_{ticket_str}.png"
        return os.path.join(output_images_dir, file_stem, "base", base)

    output_dir = cfg.get("output_images_dir", "./output/images")
    valid_pages_dir = os.path.join(output_dir, "valid_pages")
    os.makedirs(valid_pages_dir, exist_ok=True)

    for rec in page_records.values():
        if rec.get("ticket_valid") == "valid" and rec.get("manifest_valid") == "valid":
            src = build_base_image_path(
                rec.get("file_path", ""),
                rec.get("page"),
                output_dir,
                rec.get("vendor_name"),
                rec.get("ticket_number"),
            )
            if os.path.isfile(src):
                shutil.copy2(src, os.path.join(valid_pages_dir, os.path.basename(src)))

    zip_folder(valid_pages_dir, os.path.join(output_dir, "valid_pages.zip"))

    # --- Write ROI exception report for pages with no ticket ---
    roi_ex_csv = cfg["ticket_number_exceptions_csv"]
    os.makedirs(os.path.dirname(roi_ex_csv), exist_ok=True)
    file_exists = os.path.isfile(roi_ex_csv)

    with open(roi_ex_csv, "a", newline="", encoding="utf-8") as ef:
        w = csv.writer(ef)
        if not file_exists:
            w.writerow(
                ["file_name", "file_path", "page", "vendor_name", "ROI Image Link"]
            )
        for rec in no_ticket_pages:
            link = f'=HYPERLINK("{rec["roi_image"]}","View ROI")'
            w.writerow(
                [
                    rec["file_name"],
                    rec["file_path"],
                    rec["page"],
                    rec["vendor_name"],
                    link,
                ]
            )

    # --- Write duplicate ticket & no-OCR pages report ---
    dup_ex_csv = cfg.get(
        "duplicate_ticket_exceptions_csv",
        os.path.join(os.path.dirname(roi_ex_csv), "duplicate_ticket_exceptions.csv"),
    )
    os.makedirs(os.path.dirname(dup_ex_csv), exist_ok=True)
    file_exists = os.path.isfile(dup_ex_csv)
    with open(dup_ex_csv, "a", newline="", encoding="utf-8") as df:
        w = csv.writer(df)
        if not file_exists:
            w.writerow(
                [
                    "file_name",
                    "file_path",
                    "page",
                    "vendor_name",
                    "ticket_number",
                    "ROI Image Link",
                ]
            )
        for rec in duplicate_ticket_pages:
            link = f'=HYPERLINK("{rec["roi_image"]}","View ROI")'
            w.writerow(
                [
                    rec["file_name"],
                    rec["file_path"],
                    rec["page"],
                    rec["vendor_name"],
                    rec["ticket_number"],
                    link,
                ]
            )
        for rec in all_no_ocr_pages:
            link = f'=HYPERLINK("{rec["roi_image"]}","View ROI")'
            w.writerow(
                [
                    rec["file_name"],
                    rec["file_path"],
                    rec["page"],
                    rec.get("vendor_name", ""),
                    rec.get("ticket_number", ""),
                    link,
                ]
            )

    # --- Write manifest number exceptions report ---
    man_ex_csv = cfg.get(
        "manifest_number_exceptions_csv",
        os.path.join(os.path.dirname(roi_ex_csv), "manifest_number_exceptions.csv"),
    )
    os.makedirs(os.path.dirname(man_ex_csv), exist_ok=True)
    file_exists = os.path.isfile(man_ex_csv)
    with open(man_ex_csv, "a", newline="", encoding="utf-8") as mf:
        w = csv.writer(mf)
        if not file_exists:
            w.writerow(
                [
                    "file_name",
                    "file_path",
                    "page",
                    "vendor_name",
                    "manifest_number",
                    "ROI Image Link",
                ]
            )
        for rec in manifest_exception_pages:
            link = f'=HYPERLINK("{rec["roi_image"]}","View ROI")'
            w.writerow(
                [
                    rec["file_name"],
                    rec["file_path"],
                    rec["page"],
                    rec["vendor_name"],
                    rec["manifest_number"],
                    link,
                ]
            )

    # --- Write exception report ONLY if exceptions exist ---
    if all_exceptions:
        os.makedirs(os.path.dirname(exceptions_csv), exist_ok=True)
        with open(exceptions_csv, "w", newline="", encoding="utf-8") as ef:
            writer = csv.writer(ef)
            writer.writerow(["file", "page", "error", "extract"])
            for ex in all_exceptions:
                writer.writerow([ex["file"], ex["page"], ex["error"], ex["extract"]])
        logging.info(f"Wrote exception report to {exceptions_csv}")
    else:
        logging.info("No exceptions encountered — skipping exception report.")

    # --- Write updated summary report CSV ---
    summary_dir = cfg.get("summary_report_dir", "./output/logs")
    summary_csv = os.path.join(summary_dir, f"summary_{summary_base}_{timestamp}.csv")
    process_csv = os.path.join(summary_dir, "process_analysis.csv")
    os.makedirs(os.path.dirname(summary_csv), exist_ok=True)

    with open(summary_csv, "w", newline="", encoding="utf-8") as sf:
        writer = csv.writer(sf)
        writer.writerow(["statistic", "value"])
        writer.writerow(["Files processed", len(pdf_files)])
        writer.writerow(["Total pages", sum_total_pages])
        writer.writerow(["Pages processed", sum_processed_pages])
        writer.writerow(["Pages not processed", sum_total_pages - sum_processed_pages])
        writer.writerow(["OCR data fields", len(all_results)])
        writer.writerow(["Unique tickets", len(unique_tickets)])
        writer.writerow(["Valid manifest numbers", valid_manifest_numbers])
        writer.writerow(["Manifest numbers for review", review_manifest_numbers])
        writer.writerow(["Valid ticket numbers", num_valid_ticket_numbers])
        writer.writerow(["Invalid ticket numbers", num_invalid_ticket_numbers])
        writer.writerow(["No-ticket numbers", num_no_ticket_numbers])
        writer.writerow(["Duplicate ticket numbers", num_duplicate_ticket_pages])
        writer.writerow(["Not-checked ticket numbers", num_not_checked_ticket_numbers])
        writer.writerow(["Pages with no OCR text", num_no_ocr_pages])
        writer.writerow(["Manifest number exceptions", num_manifest_exception_pages])
        writer.writerow(["Process analysis CSV", os.path.basename(process_csv)])
    logging.info(f"Wrote summary report to {summary_csv}")

    # --- Write per-page timing analysis CSV ---
    if all_page_timings:
        with open(process_csv, "w", newline="", encoding="utf-8") as pf:
            fieldnames = [
                "file",
                "page",
                "orientation_sec",
                "ocr_sec",
                "ticket_sec",
                "total_sec",
            ]
            writer = csv.DictWriter(pf, fieldnames=fieldnames)
            writer.writeheader()
            for rec in all_page_timings:
                formatted = {
                    "file": rec["file"],
                    "page": rec["page"],
                    "orientation_sec": rec.get("orientation"),
                    "ocr_sec": rec.get("ocr"),
                    "ticket_sec": rec.get("ticket"),
                    "total_sec": rec.get("total"),
                }
                writer.writerow(formatted)
        logging.info(f"Wrote process timing report to {process_csv}")

    # --- Save corrected PDF, only after all pages processed ---
    if cfg.get("save_corrected_pdf", False) and all_corrected_images:
        corrected_pdf_path = cfg.get(
            "corrected_pdf_path", "./output/final_pdf/corrected_pages.pdf"
        )
        try:
            os.makedirs(os.path.dirname(corrected_pdf_path), exist_ok=True)
            all_corrected_images[0].save(
                corrected_pdf_path,
                save_all=True,
                append_images=all_corrected_images[1:],
                resolution=300,
            )
            logging.info(f"Rotated/corrected PDF saved as {corrected_pdf_path}")
        except Exception as e:
            logging.error(f"Could not save corrected PDF: {e}")

    # Write performance CSV
    perf_csv = "./output/ocr/performance_report.csv"
    os.makedirs(os.path.dirname(perf_csv), exist_ok=True)
    file_exists = os.path.isfile(perf_csv)

    perf_fieldnames = [
        "file",
        "pages",
        "tickets_found",
        "exceptions",
        "duration_sec",
        "count_pages_sec",
        "preflight_sec",
        "load_model_sec",
        "init_results_sec",
        "load_images_sec",
        "rotate_pages_sec",
    ]

    with open(perf_csv, "a", newline="", encoding="utf-8") as pf:
        writer = csv.DictWriter(pf, fieldnames=perf_fieldnames)
        if not file_exists:
            writer.writeheader()  # <--- Write header if new file
        writer.writerows(performance_data)  # <--- Actually write the data rows!

    logging.info(f"Wrote performance report to {perf_csv}")

    # --- Console printout (matching CSV) ---
    print(f"--- Summary ---")
    print(f"Files processed:     {len(pdf_files)}")
    print(f"Total pages:         {sum_total_pages}")
    print(f"Pages processed:     {sum_processed_pages}")
    print(f"Pages not processed: {sum_total_pages - sum_processed_pages}")
    print(f"OCR data fields:     {len(all_results)}")
    print(f"Unique tickets:      {len(unique_tickets)}")
    print(f"Valid manifests:     {valid_manifest_numbers}")
    print(f"Manifests for review:{review_manifest_numbers}")
    print(f"Valid ticket numbers:  {num_valid_ticket_numbers}")
    print(f"Invalid ticket numbers:{num_invalid_ticket_numbers}")
    print(f"No-ticket numbers:     {num_no_ticket_numbers}")
    print(f"Duplicate ticket numbers: {num_duplicate_ticket_pages}")
    print(f"Not-checked ticket numbers:{num_not_checked_ticket_numbers}")
    print(f"No-OCR pages:        {num_no_ocr_pages}")
    print(f"Manifest exceptions: {num_manifest_exception_pages}")
    print(
        f"All done! Results saved to {cfg['output_csv']} and {cfg['ticket_numbers_csv']}"
    )


elapsed = time.time() - start_time
logging.info(f"Total processing time: {elapsed:.2f} seconds")

if __name__ == "__main__":
    main()
