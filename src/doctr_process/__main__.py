"""Module entrypoint for DocTR Process."""

from doctr_process.pipeline import main

from .cli import main


if __name__ == "__main__":
    main()
