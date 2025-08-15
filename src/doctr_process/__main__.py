import argparse
import logging
import platform
from pathlib import Path

from . import pipeline
from .logging_setup import setup_logging


def main():
    ap = argparse.ArgumentParser(description="OCR pipeline app")
    ap.add_argument("--no-gui", action="store_true", help="Run pipeline headless (no Tkinter)")
    ap.add_argument("--input", help="Input file or folder")
    ap.add_argument("--output", help="Output folder")
    ap.add_argument("--log-level", default="INFO", help="DEBUG/INFO/WARN/ERROR")
    ap.add_argument("--log-dir", default="logs", help="Directory for log files")
    ap.add_argument("--verbose", action="store_true", help="Shortcut for --log-level=DEBUG (overrides --log-level)")
    ap.add_argument("--version", action="store_true", help="Print version info and exit")
    args = ap.parse_args()

    if args.version:
        print("doctr_app - Python", platform.python_version())
        return

    level = "DEBUG" if args.verbose else args.log_level
    setup_logging(app_name="doctr_app", log_dir=args.log_dir, level=level)

    logger = logging.getLogger(__name__)
    logger.info("Startup: python=%s, platform=%s, log_level=%s",
                platform.python_version(), platform.platform(), level)
    try:
        import PIL, fitz  # type: ignore
        logger.info("Deps: PIL=%s, fitz=%s", getattr(PIL, "__version__", "?"), getattr(fitz, "__doc__", "?")[:20])
    except Exception:
        logger.info("Deps: (could not resolve versions)")

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

        config_data = {
            "output_dir": str(out),
            "ocr_engine": "doctr",
            "orientation_check": "tesseract",
            "run_type": "initial",
            "output_format": ["csv"],
            "batch_mode": inp.is_dir(),
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
    from . import gui
    if hasattr(gui, "launch_gui"):
        gui.launch_gui()
    else:
        logger.error("gui.launch_gui() not found")
        raise SystemExit(4)


if __name__ == "__main__":
    main()
