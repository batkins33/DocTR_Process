"""
Minimal CLI entry point for doctr_process package.

This provides a basic CLI without complex imports for testing packaging.
"""

import argparse
import platform
import sys


def main():
    """Simple main function for CLI entry point."""
    parser = argparse.ArgumentParser(description="DocTR Process - OCR pipeline for tickets/invoices")
    parser.add_argument("--version", action="store_true", help="Print version info and exit")
    parser.add_argument("--input", help="Input file or folder")
    parser.add_argument("--output", help="Output folder")
    parser.add_argument("--no-gui", action="store_true", help="Run pipeline headless (no Tkinter)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.version:
        print(f"doctr_process 0.1.0 - Python {platform.python_version()}")
        print(f"Platform: {platform.platform()}")
        return
    
    print("DocTR Process CLI")
    print("Note: Full functionality requires fixing import issues.")
    print("Use 'python -m doctr_process' for full functionality once imports are resolved.")
    
    if args.input:
        print(f"Input: {args.input}")
    if args.output:
        print(f"Output: {args.output}")
    if args.no_gui:
        print("Mode: headless (no GUI)")
    if args.verbose:
        print("Logging: verbose")


if __name__ == "__main__":
    main()