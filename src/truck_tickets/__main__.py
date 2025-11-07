"""Entry point for running truck_tickets as a module.

Usage:
    python -m truck_tickets process --input path/to/pdfs --job 24-105
"""

import os
import sys

# Fix for Python 3.13 + Windows asyncio issue with SQLAlchemy
# Set environment variable to use selector event loop
if sys.platform == "win32" and sys.version_info >= (3, 13):
    os.environ["PYTHONASYNCIODEBUG"] = "0"

from .cli.main import main

if __name__ == "__main__":
    sys.exit(main())
