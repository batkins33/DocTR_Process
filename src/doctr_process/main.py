"""Main entry point for doctr_process."""

import argparse
import logging
import platform
from pathlib import Path

from doctr_process import pipeline
from doctr_process.logging_setup import setup_logging


def main():
    """Main entry point for the doctr_process application."""
    ap = argparse.ArgumentParser(
        description="DocTR Process - OCR pipeline for extracting ticket data from PDF or image files",
        epilog="Examples:\n  %(prog)s --input samples --output outputs --no-gui\n  %(prog)s --version",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--no-gui", action="store_true", help="Run pipeline headless (no Tkinter GUI)")
    ap.add_argument("--input", help="Input file or folder path")
    ap.add_argument("--output", help="Output folder path")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be processed without running OCR")
    ap.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARN", "ERROR"], help="Set logging level")
    ap.add_argument("--log-dir", default="logs", help="Directory for log files")
    ap.add_argument("--verbose", action="store_true", help="Enable verbose logging (same as --log-level=DEBUG)")
    ap.add_argument("--separate-files", action="store_true", help="Create separate output files for each input file in batch mode")
    ap.add_argument("--version", action="store_true", help="Show version information and exit")
    
    # Post-OCR correction flags
    ap.add_argument("--corrections-file", default="data/corrections.jsonl", help="Path to corrections memory file")
    ap.add_argument("--dict-vendors", help="Path to CSV file with vendor names")
    ap.add_argument("--dict-materials", help="Path to CSV file with material names")
    ap.add_argument("--dict-costcodes", help="Path to CSV file with cost codes")
    ap.add_argument("--no-fuzzy", action="store_true", help="Disable fuzzy dictionary matching")
    ap.add_argument("--learn-low", action="store_true", help="Allow storing fuzzy matches ≥90 score")
    ap.add_argument("--learn-high", action="store_true", help="Require fuzzy matches ≥95 score (default)")
    args = ap.parse_args()

    if args.version:
        print("doctr_process - Python", platform.python_version())
        return

    level = "DEBUG" if args.verbose else args.log_level
    
    # Validate log_dir to prevent path traversal
    if '..' in args.log_dir or Path(args.log_dir).is_absolute():
        raise ValueError(f"Invalid log directory path: {args.log_dir}")
    
    setup_logging(app_name="doctr_app", log_dir=args.log_dir, level=level)

    logger = logging.getLogger(__name__)
    logger.info("Startup: python=%s, platform=%s, log_level=%s",
                platform.python_version(), platform.platform(), level)

    if args.no_gui:
        if not args.input or not args.output:
            logger.error("Headless mode requires --input and --output")
            raise SystemExit(2)
        inp = Path(args.input)
        out = Path(args.output)
        out.mkdir(parents=True, exist_ok=True)
        logger.info("Running headless: input=%s output=%s", inp, out)

        # Create a temporary config for headless mode
        import tempfile
        import yaml

        if args.dry_run:
            logger.info("DRY RUN - Would process:")
            if inp.is_dir():
                files = []
                for pattern in ["*.pdf", "*.tif", "*.tiff", "*.jpg", "*.jpeg", "*.png"]:
                    files.extend(inp.glob(pattern))
                logger.info("  Input directory: %s (%d files)", inp, len(files))
                for f in files[:5]:  # Show first 5 files
                    logger.info("    - %s", f.name)
                if len(files) > 5:
                    logger.info("    ... and %d more files", len(files) - 5)
            else:
                logger.info("  Input file: %s", inp)
            logger.info("  Output directory: %s", out)
            logger.info("  OCR engine: doctr")
            logger.info("  Output format: csv")
            return

        config_data = {
            "output_dir": str(out),
            "ocr_engine": "doctr",
            "orientation_check": "tesseract",
            "run_type": "initial",
            "output_format": ["csv"],
            "batch_mode": inp.is_dir(),
            # Post-OCR correction settings
            "corrections_file": args.corrections_file,
            "dict_vendors": args.dict_vendors,
            "dict_materials": args.dict_materials,
            "dict_costcodes": args.dict_costcodes,
            "no_fuzzy": args.no_fuzzy,
            "learn_threshold": 90 if args.learn_low else 95,
            "dry_run": args.dry_run,
            "separate_file_outputs": args.separate_files,
        }

        if inp.is_dir():
            config_data["input_dir"] = str(inp)
        else:
            config_data["input_pdf"] = str(inp)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.safe_dump(config_data, f)
            temp_config_path = f.name

        try:
            if hasattr(pipeline, "run_pipeline"):
                pipeline.run_pipeline(temp_config_path)
            else:
                logger.error("pipeline.run_pipeline(...) not found")
                raise SystemExit(3)
        finally:
            # Clean up temporary config file
            try:
                Path(temp_config_path).unlink()
            except Exception:
                pass
        return

    # Otherwise run the GUI
    from doctr_process import gui
    try:
        gui.main()
    except Exception as e:
        logger.error("GUI failed to start: %s", e)
        raise SystemExit(4)


if __name__ == "__main__":
    main()