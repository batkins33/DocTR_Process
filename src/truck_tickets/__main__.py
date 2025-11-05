"""Entry point for running truck_tickets as a module.

Usage:
    python -m truck_tickets process --input path/to/pdfs --job 24-105
"""
import sys

from .cli.main import main

if __name__ == "__main__":
    sys.exit(main())
