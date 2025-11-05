"""Main CLI entry point for truck ticket processing.

Issue #19: CLI Interface
Provides command-line interface for batch processing truck tickets.
"""
import argparse
import logging
import sys
from pathlib import Path

from ..version import __version__


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="ticketiq",
        description="Truck Ticket Processing System - Extract and track construction material tickets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single date folder
  ticketiq process --input "C:\\tickets\\2024-10-17" --job 24-105

  # Process with all exports
  ticketiq process --input "C:\\tickets\\2024-10-17" --job 24-105 \\
    --export-xlsx tracking.xlsx \\
    --export-invoice invoice_match.csv \\
    --export-manifest manifest_log.csv

  # Dry run to preview
  ticketiq process --input "C:\\tickets\\2024-10-17" --job 24-105 --dry-run --verbose

For more information, visit: https://github.com/batkins33/DocTR_Process
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Process command
    process_parser = subparsers.add_parser(
        "process", help="Process truck ticket PDFs and extract data"
    )

    # Required arguments
    process_parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to folder containing PDF files (date folder or root)",
    )

    process_parser.add_argument(
        "--job", type=str, required=True, help='Job code (e.g., "24-105")'
    )

    # Export options
    export_group = process_parser.add_argument_group("export options")

    export_group.add_argument(
        "--export-xlsx",
        type=str,
        metavar="PATH",
        help="Output path for Excel tracking workbook (5 sheets)",
    )

    export_group.add_argument(
        "--export-invoice",
        type=str,
        metavar="PATH",
        help="Output path for invoice matching CSV (pipe-delimited)",
    )

    export_group.add_argument(
        "--export-manifest",
        type=str,
        metavar="PATH",
        help="Output path for manifest log CSV (regulatory compliance)",
    )

    export_group.add_argument(
        "--export-review",
        type=str,
        metavar="PATH",
        help="Output path for review queue CSV (manual review items)",
    )

    # Processing options
    processing_group = process_parser.add_argument_group("processing options")

    processing_group.add_argument(
        "--threads",
        type=int,
        default=None,
        metavar="N",
        help="Number of parallel processing threads (default: CPU count)",
    )

    processing_group.add_argument(
        "--config",
        type=str,
        default="./config",
        metavar="PATH",
        help="Path to custom config directory (default: ./config)",
    )

    processing_group.add_argument(
        "--vendor-template",
        type=str,
        metavar="NAME",
        help="Specific vendor template to use (e.g., WM_LEWISVILLE)",
    )

    processing_group.add_argument(
        "--reprocess",
        action="store_true",
        help="Allow reprocessing of previously processed files",
    )

    processing_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without database insert",
    )

    # Output options
    output_group = process_parser.add_argument_group("output options")

    output_group.add_argument(
        "--verbose", "-v", action="store_true", help="Detailed logging output"
    )

    output_group.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress non-error output"
    )

    output_group.add_argument(
        "--log-file",
        type=str,
        metavar="PATH",
        help="Write logs to file instead of console",
    )

    # Export command (standalone export from database)
    export_parser = subparsers.add_parser(
        "export", help="Export data from database without processing"
    )

    export_parser.add_argument(
        "--job", type=str, required=True, help='Job code (e.g., "24-105")'
    )

    export_parser.add_argument(
        "--xlsx", type=str, metavar="PATH", help="Output path for Excel workbook"
    )

    export_parser.add_argument(
        "--invoice", type=str, metavar="PATH", help="Output path for invoice CSV"
    )

    export_parser.add_argument(
        "--manifest", type=str, metavar="PATH", help="Output path for manifest CSV"
    )

    export_parser.add_argument(
        "--review", type=str, metavar="PATH", help="Output path for review queue CSV"
    )

    export_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Detailed logging output"
    )

    return parser


def setup_logging(verbose: bool = False, quiet: bool = False, log_file: str = None):
    """Configure logging based on CLI arguments.

    Args:
        verbose: Enable debug-level logging
        quiet: Suppress non-error output
        log_file: Optional path to log file
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # Configure format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure handlers
    handlers = []

    if log_file:
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(file_handler)
    else:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        handlers.append(console_handler)

    # Configure root logger
    logging.basicConfig(level=level, format=log_format, datefmt=date_format, handlers=handlers, force=True)

    # Suppress noisy third-party loggers
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)


def validate_args(args: argparse.Namespace) -> bool:
    """Validate command-line arguments.

    Args:
        args: Parsed arguments

    Returns:
        True if valid, False otherwise
    """
    logger = logging.getLogger(__name__)

    # Validate input path exists
    if hasattr(args, "input"):
        input_path = Path(args.input)
        if not input_path.exists():
            logger.error(f"Input path does not exist: {args.input}")
            return False

        if not input_path.is_dir():
            logger.error(f"Input path must be a directory: {args.input}")
            return False

    # Validate config path exists (only if not default)
    if hasattr(args, "config") and args.config != "./config":
        config_path = Path(args.config)
        if not config_path.exists():
            logger.error(f"Config directory does not exist: {args.config}")
            return False

    # Validate at least one export option for export command
    if args.command == "export":
        if not any([args.xlsx, args.invoice, args.manifest, args.review]):
            logger.error("At least one export option must be specified")
            return False

    return True


def main(argv=None):
    """Main CLI entry point.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0

    # Setup logging
    setup_logging(
        verbose=getattr(args, "verbose", False),
        quiet=getattr(args, "quiet", False),
        log_file=getattr(args, "log_file", None),
    )

    logger = logging.getLogger(__name__)
    logger.info(f"TicketIQ v{__version__} - Truck Ticket Processing System")

    # Validate arguments
    if not validate_args(args):
        return 1

    try:
        if args.command == "process":
            from .commands.process import process_command

            return process_command(args)

        elif args.command == "export":
            from .commands.export import export_command

            return export_command(args)

        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        logger.warning("\nProcessing interrupted by user")
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
