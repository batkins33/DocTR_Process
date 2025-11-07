"""Pipeline execution utilities for integration tests.

Provides helpers to invoke truck_tickets CLI and programmatic
pipeline entry points with test configuration.
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run_truck_tickets_cli(
    args: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """Run truck_tickets CLI command.

    Args:
        args: CLI arguments (e.g., ["process", "--input", "...", "--job", "24-105"])
        cwd: Working directory for command
        env: Environment variables
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess with return code and output
    """
    cmd = [sys.executable, "-m", "truck_tickets"] + args

    if env is None:
        env = {}

    # Set test environment variables
    # Include current environment to preserve conda/system settings
    import os

    test_env = os.environ.copy()
    test_env.update(
        {
            "PYTHONPATH": str(Path(__file__).parent.parent.parent.parent),
            "PYTHONHASHSEED": "0",  # Fix hash randomization error in subprocess
            **env,
        }
    )

    # Pass database URL via environment if not already set
    if "TRUCK_TICKETS_DB_URL" not in test_env and "TRUCK_TICKETS_DB_URL" in os.environ:
        test_env["TRUCK_TICKETS_DB_URL"] = os.environ["TRUCK_TICKETS_DB_URL"]

    logger.debug(f"Running CLI: {' '.join(cmd)}")
    logger.debug(f"Working dir: {cwd or Path.cwd()}")

    result = subprocess.run(
        cmd,
        cwd=cwd or Path.cwd(),
        env=test_env,
        capture_output=capture_output,
        text=True,
    )

    if result.returncode != 0:
        logger.warning(f"CLI failed with code {result.returncode}")
        if capture_output:
            logger.warning(f"stderr: {result.stderr}")

    return result


def run_process_command(
    input_dir: Path,
    job_code: str,
    output_dir: Path,
    config_dir: Path | None = None,
    dry_run: bool = False,
    verbose: bool = False,
    threads: int = 1,
) -> subprocess.CompletedProcess:
    """Run truck_tickets process command.

    Args:
        input_dir: Directory containing PDF files
        job_code: Job code (e.g., "24-105")
        output_dir: Output directory for results (used for export paths)
        config_dir: Custom config directory
        dry_run: Run in dry-run mode
        verbose: Enable verbose logging
        threads: Number of processing threads

    Returns:
        CompletedProcess with execution result
    """
    args = [
        "process",
        "--input",
        str(input_dir),
        "--job",
        job_code,
    ]

    # Add export paths if not dry-run
    if not dry_run:
        args.extend(
            [
                "--export-xlsx",
                str(output_dir / f"{job_code}_tracking.xlsx"),
                "--export-invoice",
                str(output_dir / f"{job_code}_invoice.csv"),
                "--export-manifest",
                str(output_dir / f"{job_code}_manifest.csv"),
                "--export-review",
                str(output_dir / f"{job_code}_review.csv"),
            ]
        )

    if config_dir:
        args.extend(["--config", str(config_dir)])

    if dry_run:
        args.append("--dry-run")

    if verbose:
        args.append("--verbose")

    args.extend(["--threads", str(threads)])

    return run_truck_tickets_cli(args)


def run_export_command(
    job_code: str,
    output_dir: Path,
    xlsx_file: Path | None = None,
    invoice_file: Path | None = None,
    manifest_file: Path | None = None,
    review_file: Path | None = None,
) -> subprocess.CompletedProcess:
    """Run truck_tickets export command.

    Args:
        job_code: Job code to export
        output_dir: Output directory for exports (not used, kept for compatibility)
        xlsx_file: Path for Excel export
        invoice_file: Path for invoice CSV export
        manifest_file: Path for manifest CSV export
        review_file: Path for review queue CSV export

    Returns:
        CompletedProcess with execution result
    """
    args = ["export", "--job", job_code]

    if xlsx_file:
        args.extend(["--xlsx", str(xlsx_file)])

    if invoice_file:
        args.extend(["--invoice", str(invoice_file)])

    if manifest_file:
        args.extend(["--manifest", str(manifest_file)])

    if review_file:
        args.extend(["--review", str(review_file)])

    return run_truck_tickets_cli(args)


def create_test_config(
    output_dir: Path,
    db_url: str,
    ocr_engine: str = "doctr",
    pdf_dpi: int = 300,
) -> Path:
    """Create test configuration file.

    Args:
        output_dir: Output directory for results
        db_url: Database connection URL
        ocr_engine: OCR engine to use
        pdf_dpi: DPI for PDF processing

    Returns:
        Path to created config file
    """
    config_content = f"""
# Test configuration for integration tests
ocr_engine: {ocr_engine}
pdf_dpi: {pdf_dpi}
output_dir: {output_dir}
database_url: {db_url}
batch_mode: true
skip_ocr: false
force_ocr: true
verbose: true
log_level: DEBUG
"""

    config_file = output_dir / "test_config.yaml"
    config_file.write_text(config_content.strip())

    return config_file


def check_output_files(output_dir: Path) -> dict[str, bool]:
    """Check which expected output files exist.

    Args:
        output_dir: Directory to check

    Returns:
        Dictionary mapping file types to existence status
    """
    expected_files = {
        "processing_log": output_dir / "processing.log",
        "error_log": output_dir / "errors.log",
    }

    result = {}
    for file_type, file_path in expected_files.items():
        result[file_type] = file_path.exists()

    return result


def get_output_file_paths(output_dir: Path, job_code: str) -> dict[str, Path]:
    """Get expected output file paths for a job.

    Args:
        output_dir: Base output directory
        job_code: Job code

    Returns:
        Dictionary mapping export types to file paths
    """
    job_dir = output_dir / job_code

    return {
        "xlsx": job_dir / f"{job_code}_tracking_export.xlsx",
        "invoice": job_dir / f"{job_code}_invoice_match.csv",
        "manifest": job_dir / f"{job_code}_manifest_log.csv",
        "review": job_dir / f"{job_code}_review_queue.csv",
    }
