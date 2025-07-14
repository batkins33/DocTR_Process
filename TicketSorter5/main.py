import argparse
import logging

from processor.run import run_input
from tqdm import tqdm
from utils.loader import load_configs


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="📄 Ticket Sorter with OCR & Template Matching")
    parser.add_argument("--file", help="Path to the file or folder to process", required=True)
    parser.add_argument("--compare", action="store_true", help="Run OCR engine comparison mode")
    args = parser.parse_args()

    config = load_configs()

    if args.compare:
        from processor.run import run_comparison_mode
        run_comparison_mode(args.file, config)
    else:
        def console_progress(idx, total):
            if not hasattr(console_progress, "bar"):
                console_progress.bar = tqdm(total=total)
            console_progress.bar.n = idx
            console_progress.bar.refresh()
            if idx == total:
                console_progress.bar.close()
        run_input(args.file, config, progress_callback=console_progress)


if __name__ == "__main__":
    main()
