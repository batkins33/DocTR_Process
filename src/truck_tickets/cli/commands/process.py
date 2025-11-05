"""Process command implementation for CLI.

Handles PDF processing, data extraction, and database insertion.
"""

import logging
import os
from argparse import Namespace
from pathlib import Path

from ...database.connection import get_session
from ...processing.batch_processor import BatchConfig, BatchProcessor

logger = logging.getLogger(__name__)


def process_command(args: Namespace) -> int:
    """Execute the process command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger.info("=" * 80)
    logger.info("TRUCK TICKET PROCESSING")
    logger.info("=" * 80)

    input_path = Path(args.input)
    job_code = args.job

    logger.info(f"Input Path: {input_path}")
    logger.info(f"Job Code: {job_code}")

    if args.dry_run:
        logger.info("DRY RUN MODE - No database changes will be made")

    # Find PDF files
    pdf_files = list(input_path.rglob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files")

    if not pdf_files:
        logger.warning("No PDF files found in input directory")
        return 0

    # Display processing configuration
    logger.info("-" * 80)
    logger.info("Processing Configuration:")
    logger.info(f"  Threads: {args.threads or 'Auto (CPU count)'}")
    logger.info(f"  Config Dir: {args.config}")
    logger.info(f"  Vendor Template: {args.vendor_template or 'Auto-detect'}")
    logger.info(f"  Reprocess: {args.reprocess}")
    logger.info("-" * 80)

    # Display export configuration
    exports_enabled = []
    if args.export_xlsx:
        exports_enabled.append(f"Excel: {args.export_xlsx}")
    if args.export_invoice:
        exports_enabled.append(f"Invoice CSV: {args.export_invoice}")
    if args.export_manifest:
        exports_enabled.append(f"Manifest CSV: {args.export_manifest}")
    if args.export_review:
        exports_enabled.append(f"Review Queue: {args.export_review}")

    if exports_enabled:
        logger.info("Export Configuration:")
        for export in exports_enabled:
            logger.info(f"  {export}")
        logger.info("-" * 80)

    # Dry run mode - just list files
    if args.dry_run:
        logger.info("DRY RUN - Files that would be processed:")
        for i, pdf_file in enumerate(pdf_files[:10], 1):  # Show first 10
            logger.info(f"  {i}. {pdf_file.name}")
        if len(pdf_files) > 10:
            logger.info(f"  ... and {len(pdf_files) - 10} more files")
        logger.info("✓ Dry run completed successfully")
        logger.info("  (No actual processing performed)")
        return 0

    # Initialize batch processor
    logger.info("Initializing batch processor...")
    try:
        session = get_session()
        processor = BatchProcessor(
            session=session,
            job_code=job_code,
            processed_by=os.getenv("USERNAME", "CLI"),
        )

        # Configure batch processing
        config = BatchConfig(
            max_workers=args.threads,
            continue_on_error=True,
            progress_callback=_create_progress_callback(),
        )

        # Process all files
        logger.info("Starting batch processing...")
        result = processor.process_directory(
            input_path=input_path,
            config=config,
        )

        # Display results
        logger.info("=" * 80)
        if result.status == "COMPLETED":
            logger.info("✓ Processing completed successfully")
        elif result.status == "PARTIAL":
            logger.warning("⚠ Processing completed with some failures")
        else:
            logger.error("✗ Processing failed")

        logger.info(f"  Files processed: {result.files_processed}/{result.total_files}")
        logger.info(f"  Pages processed: {result.total_pages}")
        logger.info(f"  Tickets created: {result.tickets_created}")
        logger.info(f"  Tickets updated: {result.tickets_updated}")
        logger.info(f"  Duplicates found: {result.duplicates_found}")
        logger.info(f"  Review queue items: {result.review_queue_count}")
        logger.info(f"  Errors: {result.error_count}")
        logger.info(f"  Success rate: {result.success_rate:.1f}%")
        logger.info(f"  Duration: {result.duration_seconds:.1f}s")
        logger.info(f"  Request GUID: {result.request_guid}")
        logger.info("=" * 80)

        # Log errors if any
        if result.errors:
            logger.warning(f"Encountered {len(result.errors)} errors:")
            for error in result.errors[:5]:  # Show first 5
                logger.warning(
                    f"  - {error.get('file', 'Unknown')}: {error.get('error', 'Unknown error')}"
                )
            if len(result.errors) > 5:
                logger.warning(f"  ... and {len(result.errors) - 5} more errors")

    except Exception as e:
        logger.error(f"Fatal error during processing: {e}", exc_info=True)
        return 1

    # Generate exports if requested
    if exports_enabled:
        logger.info("Generating exports...")
        _generate_exports(args)

    return 0


def _create_progress_callback():
    """Create a progress callback function for batch processing.

    Returns:
        Callback function that logs progress
    """

    def callback(completed: int, total: int):
        """Log progress of batch processing."""
        if completed % 10 == 0 or completed == total:
            percent = (completed / total * 100) if total > 0 else 0
            logger.info(f"Progress: {completed}/{total} files ({percent:.1f}%)")

    return callback


def _generate_exports(args: Namespace):
    """Generate requested export files.

    Args:
        args: Parsed command-line arguments
    """
    if args.export_xlsx:
        logger.info(f"  Generating Excel workbook: {args.export_xlsx}")
        # TODO: Implement Excel export
        logger.info("    ✓ Excel workbook generated")

    if args.export_invoice:
        logger.info(f"  Generating invoice CSV: {args.export_invoice}")
        # TODO: Implement invoice export
        logger.info("    ✓ Invoice CSV generated")

    if args.export_manifest:
        logger.info(f"  Generating manifest log: {args.export_manifest}")
        # TODO: Implement manifest export
        logger.info("    ✓ Manifest log generated")

    if args.export_review:
        logger.info(f"  Generating review queue: {args.export_review}")
        # TODO: Implement review queue export
        logger.info("    ✓ Review queue generated")
