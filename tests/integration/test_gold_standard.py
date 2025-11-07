"""Gold standard integration tests with ground truth comparison.

This module implements Issue #16: Integration test framework
Tests end-to-end pipeline with gold standard comparison:
- PDF input → database records + Excel output
- Compare against known ground truth
- Measure accuracy and performance
- Generate detailed test reports

Gold Standard Format:
    tests/fixtures/gold_standard/
    ├── pdfs/
    │   └── sample_ticket_001.pdf
    └── ground_truth/
        └── sample_ticket_001.json  # Expected extraction results
"""

import json
import logging
import time
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from src.truck_tickets.models.sql_truck_ticket import TruckTicket
from src.truck_tickets.processing.ticket_processor import TicketProcessor

logger = logging.getLogger(__name__)

# Paths
GOLD_STANDARD_DIR = Path(__file__).parent.parent / "fixtures" / "gold_standard"
GOLD_PDFS_DIR = GOLD_STANDARD_DIR / "pdfs"
GROUND_TRUTH_DIR = GOLD_STANDARD_DIR / "ground_truth"


class GoldStandardComparison:
    """Compare extraction results against ground truth.

    Attributes:
        ground_truth: Expected values from gold standard
        extracted: Actual extracted values
        field_comparisons: Detailed field-by-field comparison
        accuracy: Overall accuracy score
    """

    def __init__(self, ground_truth: dict[str, Any], extracted: dict[str, Any]):
        self.ground_truth = ground_truth
        self.extracted = extracted
        self.field_comparisons = {}
        self.accuracy = 0.0
        self._compare()

    def _compare(self):
        """Compare all fields and calculate accuracy."""
        total_fields = 0
        correct_fields = 0

        for field_name, expected_value in self.ground_truth.items():
            total_fields += 1
            actual_value = self.extracted.get(field_name)

            is_correct = self._compare_values(expected_value, actual_value)

            self.field_comparisons[field_name] = {
                "expected": expected_value,
                "actual": actual_value,
                "correct": is_correct,
            }

            if is_correct:
                correct_fields += 1

        self.accuracy = (
            (correct_fields / total_fields * 100) if total_fields > 0 else 0.0
        )

    def _compare_values(self, expected: Any, actual: Any) -> bool:
        """Compare two values with type-aware comparison.

        Args:
            expected: Expected value from ground truth
            actual: Actual extracted value

        Returns:
            True if values match
        """
        # Handle None
        if expected is None and actual is None:
            return True
        if expected is None or actual is None:
            return False

        # Handle dates
        if isinstance(expected, str) and isinstance(actual, date):
            try:
                expected_date = date.fromisoformat(expected)
                return expected_date == actual
            except ValueError:
                pass

        # Handle decimals/floats
        if isinstance(expected, (int, float)) and isinstance(actual, (Decimal, float)):
            return abs(float(expected) - float(actual)) < 0.01

        # Handle strings (case-insensitive)
        if isinstance(expected, str) and isinstance(actual, str):
            return expected.strip().upper() == actual.strip().upper()

        # Default comparison
        return expected == actual

    def get_incorrect_fields(self) -> list[str]:
        """Get list of incorrectly extracted fields."""
        return [
            field
            for field, comparison in self.field_comparisons.items()
            if not comparison["correct"]
        ]

    def __repr__(self) -> str:
        return f"<GoldStandardComparison(accuracy={self.accuracy:.1f}%, incorrect={len(self.get_incorrect_fields())})>"


@pytest.fixture
def gold_standard_pdfs():
    """Fixture providing list of gold standard PDF files."""
    if not GOLD_PDFS_DIR.exists():
        pytest.skip(f"Gold standard PDFs directory not found: {GOLD_PDFS_DIR}")

    pdf_files = list(GOLD_PDFS_DIR.glob("*.pdf"))

    if not pdf_files:
        pytest.skip(f"No PDF files found in: {GOLD_PDFS_DIR}")

    return pdf_files


@pytest.fixture
def ground_truth_data():
    """Fixture providing ground truth data for gold standard tests."""
    if not GROUND_TRUTH_DIR.exists():
        pytest.skip(f"Ground truth directory not found: {GROUND_TRUTH_DIR}")

    ground_truth = {}

    for json_file in GROUND_TRUTH_DIR.glob("*.json"):
        with open(json_file) as f:
            data = json.load(f)
            ground_truth[json_file.stem] = data

    if not ground_truth:
        pytest.skip(f"No ground truth files found in: {GROUND_TRUTH_DIR}")

    return ground_truth


class TestGoldStandardPipeline:
    """Test complete pipeline with gold standard comparison."""

    def test_single_ticket_extraction(
        self, temp_db_session, gold_standard_pdfs, ground_truth_data
    ):
        """Test extraction of single ticket against ground truth.

        This test processes a single PDF and compares the extracted
        values against known ground truth.
        """
        # Get first PDF and its ground truth
        pdf_file = gold_standard_pdfs[0]
        pdf_stem = pdf_file.stem

        if pdf_stem not in ground_truth_data:
            pytest.skip(f"No ground truth found for {pdf_stem}")

        ground_truth = ground_truth_data[pdf_stem]

        # Process PDF
        processor = TicketProcessor(temp_db_session, job_name="24-105")

        start_time = time.time()
        results = processor.process_pdf_file(str(pdf_file))
        processing_time = time.time() - start_time

        # Verify processing succeeded
        assert len(results) > 0, "No pages processed"
        assert results[0].success, f"Processing failed: {results[0].error}"

        # Get extracted ticket
        ticket_id = results[0].ticket_id
        assert ticket_id is not None, "No ticket created"

        ticket = temp_db_session.get(TruckTicket, ticket_id)
        assert ticket is not None, "Ticket not found in database"

        # Extract values for comparison
        extracted = {
            "ticket_number": ticket.ticket_number,
            "ticket_date": ticket.ticket_date,
            "quantity": float(ticket.quantity) if ticket.quantity else None,
            "quantity_unit": ticket.quantity_unit,
            "manifest_number": ticket.manifest_number,
            "truck_number": ticket.truck_number,
        }

        # Compare against ground truth
        comparison = GoldStandardComparison(ground_truth, extracted)

        # Log results
        logger.info(f"Gold Standard Test: {pdf_stem}")
        logger.info(f"  Accuracy: {comparison.accuracy:.1f}%")
        logger.info(f"  Processing Time: {processing_time:.2f}s")

        if comparison.get_incorrect_fields():
            logger.warning(f"  Incorrect fields: {comparison.get_incorrect_fields()}")
            for field in comparison.get_incorrect_fields():
                comp = comparison.field_comparisons[field]
                logger.warning(
                    f"    {field}: expected={comp['expected']}, actual={comp['actual']}"
                )

        # Assert accuracy threshold
        assert comparison.accuracy >= 95.0, (
            f"Accuracy {comparison.accuracy:.1f}% below threshold (95%). "
            f"Incorrect fields: {comparison.get_incorrect_fields()}"
        )

        # Assert processing time
        assert (
            processing_time <= 3.0
        ), f"Processing time {processing_time:.2f}s exceeds threshold (3.0s)"

    def test_batch_gold_standard_processing(
        self, temp_db_session, gold_standard_pdfs, ground_truth_data
    ):
        """Test batch processing of all gold standard PDFs.

        This test processes all gold standard PDFs and generates
        a comprehensive accuracy report.
        """
        processor = TicketProcessor(temp_db_session, job_name="24-105")

        results_summary = {
            "total_pdfs": 0,
            "successful": 0,
            "failed": 0,
            "total_accuracy": 0.0,
            "processing_times": [],
            "comparisons": [],
        }

        for pdf_file in gold_standard_pdfs:
            pdf_stem = pdf_file.stem

            if pdf_stem not in ground_truth_data:
                logger.warning(f"Skipping {pdf_stem}: no ground truth")
                continue

            ground_truth = ground_truth_data[pdf_stem]
            results_summary["total_pdfs"] += 1

            try:
                # Process PDF
                start_time = time.time()
                results = processor.process_pdf_file(str(pdf_file))
                processing_time = time.time() - start_time

                results_summary["processing_times"].append(processing_time)

                if not results or not results[0].success:
                    results_summary["failed"] += 1
                    logger.error(f"Failed to process {pdf_stem}")
                    continue

                # Get extracted ticket
                ticket_id = results[0].ticket_id
                ticket = temp_db_session.get(TruckTicket, ticket_id)

                if not ticket:
                    results_summary["failed"] += 1
                    logger.error(f"Ticket not found for {pdf_stem}")
                    continue

                # Extract values
                extracted = {
                    "ticket_number": ticket.ticket_number,
                    "ticket_date": ticket.ticket_date,
                    "quantity": float(ticket.quantity) if ticket.quantity else None,
                    "quantity_unit": ticket.quantity_unit,
                    "manifest_number": ticket.manifest_number,
                    "truck_number": ticket.truck_number,
                }

                # Compare
                comparison = GoldStandardComparison(ground_truth, extracted)
                results_summary["comparisons"].append(comparison)
                results_summary["successful"] += 1

                logger.info(
                    f"{pdf_stem}: {comparison.accuracy:.1f}% accuracy, {processing_time:.2f}s"
                )

            except Exception as e:
                results_summary["failed"] += 1
                logger.error(f"Error processing {pdf_stem}: {e}")

        # Calculate overall metrics
        if results_summary["comparisons"]:
            avg_accuracy = sum(
                c.accuracy for c in results_summary["comparisons"]
            ) / len(results_summary["comparisons"])
            results_summary["total_accuracy"] = avg_accuracy

        avg_time = (
            sum(results_summary["processing_times"])
            / len(results_summary["processing_times"])
            if results_summary["processing_times"]
            else 0.0
        )

        # Log summary
        logger.info("=" * 60)
        logger.info("Gold Standard Batch Processing Summary")
        logger.info("=" * 60)
        logger.info(f"Total PDFs: {results_summary['total_pdfs']}")
        logger.info(f"Successful: {results_summary['successful']}")
        logger.info(f"Failed: {results_summary['failed']}")
        logger.info(f"Average Accuracy: {results_summary['total_accuracy']:.1f}%")
        logger.info(f"Average Processing Time: {avg_time:.2f}s")
        logger.info("=" * 60)

        # Assert thresholds
        assert results_summary["successful"] > 0, "No PDFs processed successfully"
        assert (
            results_summary["total_accuracy"] >= 95.0
        ), f"Average accuracy {results_summary['total_accuracy']:.1f}% below threshold (95%)"
        assert (
            avg_time <= 3.0
        ), f"Average processing time {avg_time:.2f}s exceeds threshold (3.0s)"


class TestGoldStandardExportGeneration:
    """Test export generation with gold standard data."""

    def test_excel_export_generation(self, temp_db_session, gold_standard_pdfs):
        """Test Excel export generation after processing gold standard PDFs."""
        pytest.skip("Requires export generation implementation")

    def test_invoice_csv_generation(self, temp_db_session):
        """Test invoice CSV generation with gold standard data."""
        pytest.skip("Requires export generation implementation")

    def test_manifest_log_generation(self, temp_db_session):
        """Test manifest log generation with gold standard data."""
        pytest.skip("Requires export generation implementation")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
