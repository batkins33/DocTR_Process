import argparse
import logging
import platform
from pathlib import Path

try:
    from doctr_process import pipeline
except ModuleNotFoundError:  # pragma: no cover - for direct script execution
    import sys, pathlib
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
    from doctr_process import pipeline  # type: ignore

try:
    from doctr_process.logging_setup import setup_logging
except ModuleNotFoundError:  # pragma: no cover - for direct script execution
    import sys, pathlib
    sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
    from doctr_process.logging_setup import setup_logging  # type: ignore


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
        # Adjust if your pipeline API differs:
        if hasattr(pipeline, "run_pipeline"):
            pipeline.run_pipeline(str(inp), str(out))
        else:
            logger.error("pipeline.run_pipeline(...) not found")
            raise SystemExit(3)
        return

    # Otherwise run the GUI
    try:
        from doctr_process import gui
    except ModuleNotFoundError:  # pragma: no cover - for direct script execution
        import sys, pathlib
        sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
        from doctr_process import gui  # type: ignore
    if hasattr(gui, "launch_gui"):
        gui.launch_gui()
    else:
        logger.error("gui.launch_gui() not found")
        raise SystemExit(4)


if __name__ == "__main__":
    main()
