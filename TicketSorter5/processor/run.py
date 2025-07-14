# PATCHED: run.py
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
from processor.file_handler import archive_original, get_dynamic_paths
from processor.hybrid_ocr import process_pages
from processor.image_ops import extract_images_from_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from utils.ocr_wrapper import read_text

# ✅ Disable MKLDNN to prevent inference crashes in some environments
os.environ["FLAGS_use_mkldnn"] = "0"


def run_input(filepath, config, progress_callback=None):
    path = Path(filepath)
    batch_start = time.perf_counter()

    if ";" in str(filepath):
        paths = [Path(p) for p in str(filepath).split(";") if p.strip()]
    elif path.is_dir():
        paths = sorted([f for f in path.glob("*.pdf") if not f.name.startswith(".")])
    else:
        paths = [path]

    results = []
    ocr_text_log = []
    total = len(paths)
    logging.info(f"🗂️ Batch processing {total} file(s)...")
    if progress_callback:
        progress_callback(0, total)

    for idx, file in enumerate(paths, 1):
        file_start = time.perf_counter()
        out_dir, _, _ = get_dynamic_paths(file)
        if out_dir.exists():
            logging.info(f"⏭️ {idx}/{total} Skipping already processed: {file.name}")
            results.append((file.name, "skipped"))
            continue
        logging.info(f"📄 {idx}/{total} Processing: {file.name}")
        try:
            ocr_logs = _run_single(file, config)
            ocr_text_log.extend(ocr_logs)
            results.append((file.name, "ok"))
        except Exception as e:
            logging.error(f"❌ Failed: {file} → {e}")
            results.append((file.name, "failed"))
        finally:
            logging.info(
                f"⏱️ {file.name} processed in {time.perf_counter() - file_start:.2f}s"
            )
            if progress_callback:
                progress_callback(idx, total)

    if total > 1:
        ok = sum(1 for _, r in results if r == "ok")
        skipped = sum(1 for _, r in results if r == "skipped")
        failed = sum(1 for _, r in results if r == "failed")
        failed_list = [f for f, r in results if r == "failed"]

        msg = f"Processed {ok} files.\nSkipped: {skipped}\nFailed: {failed}"
        if failed_list:
            msg += f"\n\nFailed Files:\n" + "\n".join(failed_list)

        messagebox.showinfo("Batch Complete", msg)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_path = Path.cwd() / f"batch_summary_{ts}.csv"
        try:
            pd.DataFrame(results, columns=["File", "Status"]).to_csv(
                csv_path, index=False
            )
            logging.info(f"📄 Saved summary: {csv_path}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to save summary CSV: {e}")

        try:
            truncated_logs = [
                (fname, page, vendor, text[:2000])
                for fname, page, vendor, text in ocr_text_log
            ]
            ocr_df = pd.DataFrame(
                truncated_logs, columns=["Filename", "Page", "Vendor", "OCR Text"]
            )
            ocr_path = Path.cwd() / f"ocr_text_log_{ts}.csv"
            ocr_df.to_csv(ocr_path, index=False)
            logging.info(f"🧾 OCR log saved to: {ocr_path}")

            overlay_path = Path.cwd() / f"ocr_overlay_{ts}.pdf"
            overlay_pdf_path = overlay_path.with_name(overlay_path.stem + "_full.pdf")
            c = canvas.Canvas(str(overlay_path), pagesize=letter)
            for fname, page, vendor, text in truncated_logs:
                label = f"{fname} - Page {page} - {vendor}"
                c.setFont("Helvetica", 6)
                c.drawString(30, 15, label + ": " + text[:150])
                c.showPage()
            c.save()

            original_pdf = PdfReader(paths[0])
            overlay_pdf = PdfReader(overlay_path)
            writer = PdfWriter()
            for i, page in enumerate(original_pdf.pages):
                base = page
                if i < len(overlay_pdf.pages):
                    overlay = overlay_pdf.pages[i]
                    base.merge_page(overlay)
                writer.add_page(base)

            with open(overlay_pdf_path, "wb") as f:
                writer.write(f)

            logging.info(f"📎 Merged overlay PDF saved: {overlay_pdf_path}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to save overlay PDF: {e}")

    logging.info(f"🕒 Total batch time: {time.perf_counter() - batch_start:.2f}s")


def _run_single(filepath, config):
    path = Path(filepath)
    logging.info(f"🚀 Processing: {filepath}")
    func_start = time.perf_counter()
    base_name = path.stem
    combined_name = base_name + ".pdf"
    out_dir, log_dir, combined_dir = get_dynamic_paths(filepath, combined_name)

    extract_start = time.perf_counter()
    pages = extract_images_from_file(filepath, config["poppler_path"])
    logging.info(
        f"Extracted {len(pages)} pages from {filepath} in {time.perf_counter() - extract_start:.2f}s"
    )
    logging.info("Finished extracting images")

    ocr_logs = []

    for i, page in enumerate(pages):
        page_start = time.perf_counter()
        try:
            engine = config.get("ocr_engine", "tesseract")
            text_result = read_text(image=page)
            text = text_result.get("text", "")
            conf = text_result.get("confidence")
            ocr_logs.append((path.name, i + 1, engine, text.strip()))
        except Exception as e:
            logging.warning(f"⚠️ OCR failed on page {i + 1}: {e}")
            ocr_logs.append((path.name, i + 1, engine, "[OCR Failed]"))
        finally:
            logging.info(
                f"⏱️ Page {i + 1} OCR time: {time.perf_counter() - page_start:.2f}s"
            )

    logging.info("Finished running OCR")

    proc_start = time.perf_counter()
    if config.get("two_page_scan", False):
        fronts = pages[::2]
        backs = pages[1::2]
        process_pages(fronts, filepath, config, "")
        process_pages(backs, filepath, config, "_back")
    else:
        process_pages(pages, filepath, config)
    logging.info(
        f"⏱️ Page grouping completed in {time.perf_counter() - proc_start:.2f}s"
    )
    logging.info("Finished sorting tickets")

    if config.get("rename_original", False):
        archive_original(filepath)

    logging.info(f"✅ Output written to: {out_dir}")
    logging.info(f"🕒 File processed in {time.perf_counter() - func_start:.2f}s")
    return ocr_logs


def run_all_pdfs_in_dir(root_dir, config):
    root_path = Path(root_dir)
    for file in root_path.rglob("*.pdf"):
        out_dir, _, _ = get_dynamic_paths(file)
        if out_dir.exists():
            logging.info(f"🔁 Skipping already processed file: {file}")
            continue
        run_input(file, config)


def run_processor_in_thread(filepath, config):
    import threading

    thread = threading.Thread(target=run_input, args=(filepath, config))
    thread.start()


def run_comparison_mode(filepath, config):
    from datetime import datetime

    path = Path(filepath)
    pages = extract_images_from_file(filepath, config["poppler_path"])
    initialize_engines()

    all_results = []

    for i, page in enumerate(pages):
        page_results = []
        for engine in ("tesseract", "paddle", "easyocr"):
            try:
                res = read_text(image=page)
                page_results.append(
                    {
                        "Filename": path.name,
                        "Page": i + 1,
                        "Engine": engine,
                        "Confidence": res.get("confidence"),
                        "Text": res.get("text", "").replace("\n", " ")[:1000],
                    }
                )
            except Exception as e:
                page_results.append(
                    {
                        "Filename": path.name,
                        "Page": i + 1,
                        "Engine": engine,
                        "Confidence": None,
                        "Text": f"[ERROR: {e}]",
                    }
                )
        all_results.extend(page_results)
        plot_engine_scores(all_results)

    df = pd.DataFrame(all_results)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path.cwd() / f"ocr_engine_comparison_{ts}.xlsx"
    df.to_excel(out_path, index=False)
    logging.info(f"📊 OCR comparison saved to {out_path}")


import matplotlib.pyplot as plt


def plot_engine_scores(results):
    df = pd.DataFrame(results)
    engine_avg = df.groupby("Engine")["Confidence"].mean().sort_values()

    engine_avg.plot(kind="barh", color="steelblue")
    plt.title("Average OCR Confidence per Engine")
    plt.xlabel("Confidence")
    plt.tight_layout()
    plt.savefig("ocr_confidence_scores.png")
    logging.info("📊 Heatmap saved to: ocr_confidence_scores.png")
