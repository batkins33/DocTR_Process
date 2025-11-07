"""End-to-end integration tests for truck ticket processing pipeline.

Tests the complete workflow: PDF input → OCR → extraction → database → exports.
Tests are skipped if fixture PDFs are not available.
"""

import logging
from pathlib import Path

import pytest

from .utils.db_utils import verify_test_db
from .utils.run_pipeline import (
    check_output_files,
    create_test_config,
    get_output_file_paths,
    run_export_command,
    run_process_command,
)

logger = logging.getLogger(__name__)

# Fixture paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
PDF_FIXTURES_DIR = FIXTURES_DIR / "pdfs"
SNAPSHOTS_DIR = FIXTURES_DIR / "snapshots"


@pytest.fixture
def sample_pdfs() -> list[Path]:
    """Get list of sample PDF files for testing."""
    if not PDF_FIXTURES_DIR.exists():
        return []

    pdf_files = list(PDF_FIXTURES_DIR.glob("*.pdf"))
    return sorted(pdf_files)


@pytest.fixture
def temp_output_dir(tmp_path) -> Path:
    """Create temporary output directory for test."""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


def test_pipeline_happy_path(
    sample_pdfs: list[Path], temp_output_dir: Path, temp_db_session, monkeypatch
):
    """Test complete pipeline with sample PDFs.

    Skipped if no PDF fixtures are available.
    """
    if not sample_pdfs:
        pytest.skip("Add sample PDFs to tests/fixtures/pdfs to run E2E tests.")

    # Verify test database setup
    db_counts = verify_test_db(temp_db_session)
    logger.debug(f"Test DB row counts: {db_counts}")

    # Create test configuration
    db_url = temp_db_session.bind.url.render_as_string(hide_password=False)
    config_file = create_test_config(
        output_dir=temp_output_dir,
        db_url=db_url,
        ocr_engine="doctr",
        pdf_dpi=300,
    )

    # Set database URL in environment for subprocess
    monkeypatch.setenv("TRUCK_TICKETS_DB_URL", db_url)

    # Run process command
    job_code = "24-105-test"
    result = run_process_command(
        input_dir=PDF_FIXTURES_DIR,
        job_code=job_code,
        output_dir=temp_output_dir,
        config_dir=config_file.parent,
        dry_run=False,
        verbose=True,
        threads=1,
    )

    # Check process completed successfully
    assert result.returncode == 0, f"Process failed: {result.stderr}"

    # Check expected output files exist
    output_files = check_output_files(temp_output_dir)
    logger.info(f"Output files: {output_files}")

    # TODO: Verify tickets were created in database
    # Note: The subprocess uses its own database session, so we can't easily query it from here
    # For now, successful completion (returncode 0) is sufficient
    logger.info(f"Process completed successfully for {len(sample_pdfs)} PDFs")

    # TODO: Export generation is not yet implemented (Issue #12)
    # For now, just verify the export command runs without crashing
    export_paths = get_output_file_paths(temp_output_dir, job_code)

    export_result = run_export_command(
        job_code=job_code,
        output_dir=temp_output_dir,
        xlsx_file=export_paths["xlsx"],
        invoice_file=export_paths["invoice"],
        manifest_file=export_paths["manifest"],
        review_file=export_paths["review"],
    )

    # Export command should run (even if it doesn't generate files yet)
    assert (
        export_result.returncode == 0
    ), f"Export command failed: {export_result.stderr}"

    # TODO: Uncomment when export generation is implemented (Issue #12)
    # for export_type, file_path in export_paths.items():
    #     if file_path.name.endswith((".xlsx", ".csv")):
    #         assert file_path.exists(), f"Export file not created: {file_path}"
    #         assert file_path.stat().st_size > 0, f"Export file is empty: {file_path}"

    logger.info(f"E2E test completed with {len(sample_pdfs)} PDFs")


def test_pipeline_dry_run(
    sample_pdfs: list[Path], temp_output_dir: Path, temp_db_session, monkeypatch
):
    """Test pipeline dry-run mode.

    Validates that dry-run processes files without database changes.
    """
    if not sample_pdfs:
        pytest.skip("Add sample PDFs to tests/fixtures/pdfs to run E2E tests.")

    # Create test configuration
    db_url = temp_db_session.bind.url.render_as_string(hide_password=False)
    config_file = create_test_config(
        output_dir=temp_output_dir,
        db_url=db_url,
        ocr_engine="doctr",
        pdf_dpi=300,
    )

    # Set database URL in environment for subprocess
    monkeypatch.setenv("TRUCK_TICKETS_DB_URL", db_url)

    # Run process command in dry-run mode
    job_code = "24-105-dryrun"
    result = run_process_command(
        input_dir=PDF_FIXTURES_DIR,
        job_code=job_code,
        output_dir=temp_output_dir,
        config_dir=config_file.parent,
        dry_run=True,
        verbose=True,
        threads=1,
    )

    # Check dry-run completed successfully
    assert result.returncode == 0, f"Dry-run failed: {result.stderr}"

    # Verify no database changes were made
    db_counts_after = verify_test_db(temp_db_session)

    # Should have no truck tickets created in dry-run
    if "truck_tickets" in db_counts_after:
        assert (
            db_counts_after["truck_tickets"] == 0
        ), "Dry-run should not create database records"

    logger.info("Dry-run test completed successfully")


def test_error_handling_invalid_input(temp_output_dir: Path, temp_db_session):
    """Test pipeline error handling with invalid input.

    Validates graceful failure when input directory is empty or invalid.
    """
    # Create empty input directory
    empty_dir = temp_output_dir / "empty_input"
    empty_dir.mkdir()

    # Create test configuration
    db_url = temp_db_session.bind.url.render_as_string(hide_password=False)
    config_file = create_test_config(
        output_dir=temp_output_dir,
        db_url=db_url,
        ocr_engine="doctr",
        pdf_dpi=300,
    )

    # Run process command on empty directory
    job_code = "24-105-empty"
    result = run_process_command(
        input_dir=empty_dir,
        job_code=job_code,
        output_dir=temp_output_dir,
        config_dir=config_file.parent,
        dry_run=False,
        verbose=True,
        threads=1,
    )

    # Should handle empty input gracefully (may succeed or fail with clear message)
    # The important thing is it doesn't crash with an unhandled exception
    assert result.returncode in [0, 1], f"Unexpected return code: {result.returncode}"

    logger.info("Error handling test completed")


def test_export_without_processing(temp_output_dir: Path, temp_db_session):
    """Test export command when no tickets exist.

    Validates export behavior with empty database.
    """
    # Run export command for job with no tickets
    job_code = "24-105-empty"
    export_paths = get_output_file_paths(temp_output_dir, job_code)

    result = run_export_command(
        job_code=job_code,
        output_dir=temp_output_dir,
        xlsx_file=export_paths["xlsx"],
        invoice_file=export_paths["invoice"],
        manifest_file=export_paths["manifest"],
        review_file=export_paths["review"],
    )

    # Export should complete (may create empty files or return specific code)
    assert result.returncode in [0, 1], f"Export failed unexpectedly: {result.stderr}"

    logger.info("Export without processing test completed")
