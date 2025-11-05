#!/usr/bin/env python3
"""
OCR PDF Text Embedder - Creates searchable PDFs with invisible text layers
Uses DocTR for OCR and PyMuPDF for PDF text embedding
"""

import argparse
import logging
import os
import sys
import time
import traceback

# DocTR imports
from doctr.io import DocumentFile
from doctr.models import ocr_predictor

# PDF processing
try:
    import fitz  # PyMuPDF for text embedding
except ImportError:
    fitz = None

try:
    import pdfplumber  # For text layer detection
except ImportError:
    pdfplumber = None

# Setup logging
log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def has_text_layer(pdf_path: str) -> bool:
    """Quick check for embedded text before OCR."""
    if not pdfplumber:
        log.warning("pdfplumber not available, assuming no text layer")
        return False

    try:
        with pdfplumber.open(pdf_path) as pdf:
            return any(page.extract_text().strip() for page in pdf.pages)
    except Exception as e:
        log.warning(f"Text layer check failed on {pdf_path}: {e}")
        return False


def embed_text_in_pdf(input_path: str, ocr_result, output_path: str):
    """Embed OCR text into PDF as invisible searchable text layer."""
    if not fitz:
        raise ImportError("PyMuPDF is required. Install with: pip install PyMuPDF")

    log.info("📄 Embedding OCR text into PDF...")

    # Open the original PDF
    doc = fitz.open(input_path)

    try:
        for page_num, (pdf_page, ocr_page) in enumerate(zip(doc, ocr_result.pages)):
            if page_num % 10 == 0 or page_num == len(doc) - 1:
                log.info(f"📝 Embedding text on page {page_num + 1}/{len(doc)}")

            # Get page dimensions
            page_rect = pdf_page.rect
            page_width = page_rect.width
            page_height = page_rect.height

            # Process OCR blocks and embed text
            for block in ocr_page.blocks:
                for line in block.lines:
                    for word in line.words:
                        try:
                            # Get word geometry (normalized 0-1 coordinates from DocTR)
                            word_bbox = word.geometry

                            # Convert to PDF coordinates
                            x0 = word_bbox[0][0] * page_width
                            y0 = word_bbox[0][1] * page_height
                            x1 = word_bbox[1][0] * page_width
                            y1 = word_bbox[1][1] * page_height

                            # Create invisible text overlay
                            text_rect = fitz.Rect(x0, y0, x1, y1)
                            font_size = max(
                                1, abs(y1 - y0) * 0.8
                            )  # Scale font to box height

                            # Insert invisible text (white text on white background)
                            pdf_page.insert_text(
                                text_rect.tl,
                                word.value,
                                fontsize=font_size,
                                color=(1, 1, 1),  # White color = invisible
                                overlay=True,
                            )
                        except Exception as e:
                            # Skip problematic words but continue processing
                            log.debug(f"Skipped word on page {page_num + 1}: {e}")
                            continue

        # Save the searchable PDF
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        log.info(f"✅ Searchable PDF saved: {output_path}")

    finally:
        doc.close()


def run_ocr(input_path: str, force: bool = False) -> str:
    """Run OCR and create searchable PDF with embedded text layer."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")

    stem, ext = os.path.splitext(input_path)
    out_path = f"{stem}_ocr.pdf"

    # Skip OCR if not needed
    if os.path.exists(out_path) and not force:
        log.info(f"✅ Output already exists: {out_path}")
        return out_path

    if not force and has_text_layer(input_path):
        log.info(f"📑 Text layer detected; copying {input_path} → {out_path}")
        try:
            import shutil

            shutil.copy2(input_path, out_path)
            return out_path
        except Exception as e:
            log.warning(f"Copy failed: {e}, proceeding with OCR")

    start = time.time()
    input_size = os.path.getsize(input_path) / (1024 * 1024)
    log.info(f"📥 Loading {input_path} ({input_size:.1f} MB)")

    try:
        # Load document and run OCR
        doc = DocumentFile.from_pdf(input_path)
        log.info(f"📄 Document loaded: {len(doc)} pages")

        model = ocr_predictor(pretrained=True)
        log.info("🔍 Running OCR...")

        result = model(doc)
        log.info(f"🔍 OCR completed on {len(result.pages)} pages")

        # Embed text into PDF
        embed_text_in_pdf(input_path, result, out_path)

        # Verify the result
        if os.path.exists(out_path):
            output_size = os.path.getsize(out_path) / (1024 * 1024)
            log.info(f"✅ Output file: {output_size:.1f} MB")

            # Test searchability
            if has_text_layer(out_path):
                log.info("✅ PDF is now searchable!")
            else:
                log.warning("⚠️ Text layer may not be properly embedded")
        else:
            raise Exception("Output file was not created")

    except Exception as e:
        log.error(f"❌ OCR failed: {e}")
        traceback.print_exc()
        # Create error log
        error_path = f"{stem}_ocr_error.txt"
        with open(error_path, "w", encoding="utf-8") as f:
            f.write(f"OCR Error: {e}\n")
            f.write(f"File: {input_path}\n")
            f.write(f"Time: {time.ctime()}\n")
            f.write(f"Traceback:\n{traceback.format_exc()}\n")
        raise

    elapsed = time.time() - start
    log.info(
        f"✅ Done: {len(doc)} pages in {elapsed:.1f}s ({elapsed/len(doc):.2f}s/page)"
    )
    return out_path


def main():
    """Command line interface for OCR PDF embedding."""
    parser = argparse.ArgumentParser(
        description="Create searchable PDFs using DocTR OCR and invisible text embedding"
    )
    parser.add_argument("input", help="Path to PDF file")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force OCR even if text layer already exists",
    )
    parser.add_argument(
        "-o", "--output", help="Output PDF path (default: <input>_ocr.pdf)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        output_path = run_ocr(args.input, force=args.force)
        print(f"\n✅ SUCCESS: Searchable PDF created at {output_path}")
        return 0
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        if args.debug:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
