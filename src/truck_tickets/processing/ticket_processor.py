"""Main ticket processor orchestrating the complete pipeline.

This module implements the master pipeline that coordinates all components:
PDF → Pages → OCR → Vendor Detection → Field Extraction → Normalization →
Duplicate Check → Manifest Validation → DB Insert OR Review Queue

Pipeline Flow:
    1. PDF Splitting: Split multi-page PDF into individual pages
    2. OCR: Extract text from each page using DocTR
    3. Vendor Detection: Identify vendor from page content
    4. Field Extraction: Extract all ticket fields (ticket#, date, quantity, etc.)
    5. Normalization: Convert to canonical formats
    6. Validation: Check duplicates and manifest requirements
    7. Database: Insert ticket or route to review queue
"""

import hashlib
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from PIL import Image
from sqlalchemy.orm import Session

from ..database import (
    DuplicateTicketError,
    ForeignKeyNotFoundError,
    TicketRepository,
    ValidationError,
)
from ..database.file_tracker import FileTracker
from ..extractors import (
    DateExtractor,
    ManifestNumberExtractor,
    QuantityExtractor,
    TicketNumberExtractor,
    TruckNumberExtractor,
    VendorDetector,
)
from ..models.sql_processing import ReviewQueue
from ..utils import parse_filename
from ..utils.file_hash import calculate_file_hash
from .ocr_integration import OCRIntegration

logger = logging.getLogger(__name__)


class ProcessingResult:
    """Result of processing a single ticket page.

    Attributes:
        success: Whether processing succeeded
        ticket_id: Created ticket ID (if successful)
        page_num: Page number processed
        file_path: Source file path
        error: Error message (if failed)
        review_queue_id: Review queue ID (if routed to review)
        extracted_data: Raw extracted data
        confidence_scores: Confidence scores for each field
    """

    def __init__(
        self,
        success: bool,
        page_num: int,
        file_path: str,
        ticket_id: int | None = None,
        error: str | None = None,
        review_queue_id: int | None = None,
        extracted_data: dict[str, Any] | None = None,
        confidence_scores: dict[str, float] | None = None,
    ):
        self.success = success
        self.ticket_id = ticket_id
        self.page_num = page_num
        self.file_path = file_path
        self.error = error
        self.review_queue_id = review_queue_id
        self.extracted_data = extracted_data or {}
        self.confidence_scores = confidence_scores or {}

    def __repr__(self) -> str:
        if self.success:
            return f"<ProcessingResult(success=True, ticket_id={self.ticket_id}, page={self.page_num})>"
        return f"<ProcessingResult(success=False, error='{self.error}', page={self.page_num})>"


class TicketProcessor:
    """Main processor orchestrating the complete ticket processing pipeline.

    This processor coordinates all components to transform PDF pages into
    structured database records with comprehensive validation and error handling.

    Pipeline Stages:
        1. **OCR**: Extract text from page image
        2. **Vendor Detection**: Identify vendor for template selection
        3. **Field Extraction**: Extract all ticket fields
        4. **Normalization**: Convert to canonical formats
        5. **Validation**: Duplicate check + manifest validation
        6. **Database**: Insert ticket or route to review queue

    Example:
        ```python
        processor = TicketProcessor(session, job_name="24-105")

        # Process single page
        result = processor.process_page(
            page_image=image,
            page_num=1,
            file_path="batch1/file1.pdf"
        )

        if result.success:
            print(f"✅ Created ticket {result.ticket_id}")
        else:
            print(f"❌ Error: {result.error}")

        # Process entire PDF
        results = processor.process_pdf("batch1/file1.pdf")
        print(f"Processed {len(results)} pages")
        ```

    Attributes:
        session: SQLAlchemy database session
        repository: TicketRepository instance
        job_name: Default job name for tickets
        extractors: Dictionary of field extractors
        vendor_detector: VendorDetector instance
    """

    def __init__(
        self,
        session: Session,
        job_name: str = "24-105",
        ticket_type_name: str = "EXPORT",
        ocr_engine: str = "doctr",
        check_duplicate_files: bool = True,
    ):
        """Initialize ticket processor.

        Args:
            session: SQLAlchemy database session
            job_name: Default job name (e.g., "24-105")
            ticket_type_name: Default ticket type ("EXPORT" or "IMPORT")
            ocr_engine: OCR engine to use ("doctr", "tesseract", "easyocr")
            check_duplicate_files: Whether to check for duplicate files (default: True)
        """
        self.session = session
        self.repository = TicketRepository(session)
        self.file_tracker = FileTracker(session)
        self.job_name = job_name
        self.ticket_type_name = ticket_type_name
        self.check_duplicate_files = check_duplicate_files

        # Initialize OCR integration
        self.ocr = OCRIntegration(engine=ocr_engine)

        # Initialize extractors
        self.vendor_detector = VendorDetector()
        self.extractors = {
            "ticket_number": TicketNumberExtractor(),
            "manifest_number": ManifestNumberExtractor(),
            "date": DateExtractor(),
            "quantity": QuantityExtractor(),
            "truck_number": TruckNumberExtractor(),
        }

        logger.info(
            f"TicketProcessor initialized for job '{job_name}' with {ocr_engine} OCR"
        )

    def extract_text_from_page(self, page_image: Image.Image) -> str:
        """Extract text from page image using OCR.

        Args:
            page_image: PIL Image object

        Returns:
            Extracted text string
        """
        try:
            result = self.ocr.process_image(page_image)
            return result["text"]
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    def process_pdf(
        self, pdf_path: str | Path, request_guid: str | None = None
    ) -> list[ProcessingResult]:
        """Process entire PDF file.

        Args:
            pdf_path: Path to PDF file
            request_guid: Optional batch processing GUID

        Returns:
            List of ProcessingResult objects, one per page
        """
        pdf_path = Path(pdf_path)
        logger.info(f"Processing PDF: {pdf_path.name}")

        try:
            # Calculate file hash for duplicate detection
            file_hash = calculate_file_hash(pdf_path)
            logger.debug(f"File hash: {file_hash[:16]}...")

            # Check for duplicate file
            if self.check_duplicate_files:
                duplicate_result = self.file_tracker.check_duplicate_file(
                    pdf_path, file_hash=file_hash
                )

                if duplicate_result.is_duplicate:
                    logger.warning(
                        f"Duplicate file detected: {duplicate_result.message}"
                    )
                    return [
                        ProcessingResult(
                            success=False,
                            error_message=f"DUPLICATE_FILE: {duplicate_result.message}",
                            page_num=1,
                            file_path=str(pdf_path),
                            extracted_data={
                                "duplicate_of": duplicate_result.original_file_path,
                                "original_tickets": duplicate_result.ticket_ids,
                                "ticket_count": duplicate_result.ticket_count,
                            },
                        )
                    ]

            # Extract OCR results for all pages
            ocr_results = self.ocr.process_pdf(pdf_path)
            logger.info(f"OCR completed for {len(ocr_results)} pages")

            # Process each page
            results = []
            for ocr_result in ocr_results:
                result = self.process_page(
                    page_text=ocr_result["text"],
                    page_num=ocr_result["page_num"],
                    file_path=str(pdf_path),
                    file_hash=file_hash,  # Use file-level hash, not page hash
                    request_guid=request_guid,
                )
                results.append(result)

            logger.info(
                f"Processed {len(results)} pages from {pdf_path.name}: "
                f"{sum(1 for r in results if r.success)} successful"
            )
            return results

        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}", exc_info=True)
            # Return error result
            return [
                ProcessingResult(
                    success=False,
                    error_message=f"PDF processing failed: {str(e)}",
                    page_num=1,
                    file_path=str(pdf_path),
                )
            ]

    def detect_vendor(
        self, text: str, filename_vendor: str | None = None
    ) -> tuple[str | None, float]:
        """Detect vendor from page text.

        Args:
            text: OCR text from page
            filename_vendor: Vendor hint from filename (highest precedence)

        Returns:
            Tuple of (vendor_name, confidence)
        """
        return self.vendor_detector.detect(text, filename_vendor=filename_vendor)

    def extract_fields(
        self,
        text: str,
        vendor_name: str | None = None,
        filename_hints: dict[str, str | None] | None = None,
    ) -> dict[str, tuple[Any, float]]:
        """Extract all ticket fields from text.

        Args:
            text: OCR text from page
            vendor_name: Detected vendor name (for template selection)
            filename_hints: Hints from filename (date, vendor, etc.)

        Returns:
            Dictionary mapping field names to (value, confidence) tuples
        """
        extracted = {}
        hints = filename_hints or {}

        # Extract each field
        for field_name, extractor in self.extractors.items():
            try:
                # Pass filename hints to extractors that support them
                kwargs = {"vendor": vendor_name}
                if field_name == "date" and hints.get("date"):
                    kwargs["filename_date"] = hints["date"]

                result = extractor.extract(text, **kwargs)

                # Special handling for quantity: (quantity, unit, confidence)
                if (
                    field_name == "quantity"
                    and isinstance(result, tuple)
                    and len(result) == 3
                ):
                    qty, unit, conf = result
                    extracted["quantity"] = (qty, conf)
                    extracted["quantity_unit"] = (unit, conf)
                else:
                    value, confidence = result
                    extracted[field_name] = (value, confidence)
            except Exception as e:
                logger.error(f"Error extracting {field_name}: {e}")
                extracted[field_name] = (None, 0.0)

        return extracted

    def normalize_material_name(self, raw_material: str | None) -> str | None:
        """Normalize material name to canonical format.

        Args:
            raw_material: Raw material text from OCR

        Returns:
            Canonical material name or None

        Note:
            This is a simplified version. In production, use ML classifier
            or lookup table with fuzzy matching.
        """
        if not raw_material:
            return None

        material_upper = raw_material.upper()

        # Simple keyword matching
        if "CLASS" in material_upper and "2" in material_upper:
            return "CLASS_2_CONTAMINATED"
        elif "CONTAMINATED" in material_upper:
            return "CLASS_2_CONTAMINATED"
        elif "CLEAN" in material_upper or "NON" in material_upper:
            return "NON_CONTAMINATED"
        elif "SPOILS" in material_upper:
            return "SPOILS"

        # Default to contaminated for safety (requires manifest)
        logger.warning(
            f"Unknown material '{raw_material}', defaulting to CLASS_2_CONTAMINATED"
        )
        return "CLASS_2_CONTAMINATED"

    def normalize_destination_name(self, raw_destination: str | None) -> str | None:
        """Normalize destination name to canonical format.

        Args:
            raw_destination: Raw destination text from OCR

        Returns:
            Canonical destination name or None
        """
        if not raw_destination:
            return None

        dest_upper = raw_destination.upper()

        # Simple keyword matching
        if "WASTE" in dest_upper and "MANAGEMENT" in dest_upper:
            return "WASTE_MANAGEMENT_LEWISVILLE"
        elif "WM" in dest_upper and "LEWISVILLE" in dest_upper:
            return "WASTE_MANAGEMENT_LEWISVILLE"
        elif "LDI" in dest_upper and "YARD" in dest_upper:
            return "LDI_YARD"
        elif "POST" in dest_upper and "OAK" in dest_upper:
            return "POST_OAK_PIT"

        return None

    def normalize_source_name(self, raw_source: str | None) -> str | None:
        """Normalize source name to canonical format.

        Args:
            raw_source: Raw source text from OCR

        Returns:
            Canonical source name or None
        """
        if not raw_source:
            return None

        source_upper = raw_source.upper()

        # Simple keyword matching for known sources
        if (
            "SPG" in source_upper
            or "SOUTH" in source_upper
            and "PARKING" in source_upper
        ):
            return "SPG"
        elif (
            "NPG" in source_upper
            or "NORTH" in source_upper
            and "PARKING" in source_upper
        ):
            return "NPG"

        return None

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file.

        Args:
            file_path: Path to file

        Returns:
            Hex string of SHA-256 hash
        """
        sha256 = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return ""

    def process_page(
        self,
        page_text: str,
        page_num: int,
        file_path: str,
        file_hash: str | None = None,
        request_guid: str | None = None,
    ) -> ProcessingResult:
        """Process a single ticket page through the complete pipeline.

        Pipeline:
            1. Vendor Detection
            2. Field Extraction
            3. Normalization
            4. Duplicate Check
            5. Manifest Validation
            6. Database Insert OR Review Queue

        Args:
            page_text: OCR text from page
            page_num: Page number in source file
            file_path: Source file path
            file_hash: SHA-256 hash of source file (optional)
            request_guid: Batch processing GUID (optional)

        Returns:
            ProcessingResult with success status and details
        """
        try:
            # Stage 0: Parse filename for hints (highest precedence)
            filename_hints = parse_filename(file_path)
            logger.debug(f"Filename hints: {filename_hints}")

            # Stage 1: Vendor Detection (with filename hint)
            vendor_name, vendor_confidence = self.detect_vendor(
                page_text, filename_vendor=filename_hints.get("vendor")
            )

            if not vendor_name or vendor_confidence < 0.5:
                logger.warning(f"Low vendor confidence: {vendor_confidence}")

            # Stage 2: Field Extraction (with filename hints)
            extracted = self.extract_fields(page_text, vendor_name, filename_hints)

            # Unpack extracted values
            ticket_number, ticket_conf = extracted.get("ticket_number", (None, 0.0))
            manifest_number, manifest_conf = extracted.get(
                "manifest_number", (None, 0.0)
            )
            ticket_date_str, date_conf = extracted.get("date", (None, 0.0))
            quantity, quantity_conf = extracted.get("quantity", (None, 0.0))
            truck_number, truck_conf = extracted.get("truck_number", (None, 0.0))
            quantity_unit, _ = extracted.get("quantity_unit", (None, 0.0))

            # Convert date string (YYYY-MM-DD) to date object
            ticket_date_obj = None
            if isinstance(ticket_date_str, str) and ticket_date_str:
                try:
                    ticket_date_obj = datetime.fromisoformat(ticket_date_str).date()
                except Exception:
                    logger.error(f"Invalid date format: {ticket_date_str}")

            # Calculate overall confidence (average of key fields)
            overall_confidence = (ticket_conf + date_conf + quantity_conf) / 3.0

            # Stage 3: Validation - Check critical fields
            if not ticket_number:
                return self._create_review_entry(
                    page_num=page_num,
                    file_path=file_path,
                    reason="MISSING_TICKET_NUMBER",
                    severity="CRITICAL",
                    extracted_data=extracted,
                )

            if not ticket_date_obj:
                return self._create_review_entry(
                    page_num=page_num,
                    file_path=file_path,
                    reason="INVALID_DATE",
                    severity="CRITICAL",
                    extracted_data=extracted,
                )

            # Stage 4: Normalization
            # TODO: Extract material, source, destination from text
            # For now, use defaults
            material_name = self.normalize_material_name("CLASS_2_CONTAMINATED")
            destination_name = self.normalize_destination_name(
                "WASTE_MANAGEMENT_LEWISVILLE"
            )
            source_name = self.normalize_source_name(None)

            # Stage 5: Database Insert with Validation
            try:
                ticket = self.repository.create(
                    ticket_number=ticket_number,
                    ticket_date=ticket_date_obj,
                    job_name=self.job_name,
                    material_name=material_name,
                    ticket_type_name=self.ticket_type_name,
                    source_name=source_name,
                    destination_name=destination_name,
                    vendor_name=vendor_name,
                    manifest_number=manifest_number,
                    quantity=Decimal(str(quantity)) if quantity else None,
                    quantity_unit=quantity_unit or "TONS",
                    truck_number=truck_number,
                    file_id=file_path,
                    file_page=page_num,
                    file_hash=file_hash,
                    request_guid=request_guid,
                    extraction_confidence=Decimal(str(overall_confidence)),
                    check_duplicates=True,
                    validate_manifest=True,
                )

                logger.info(
                    f"✅ Created ticket {ticket.ticket_id} from {file_path}#page{page_num}"
                )

                return ProcessingResult(
                    success=True,
                    ticket_id=ticket.ticket_id,
                    page_num=page_num,
                    file_path=file_path,
                    extracted_data={
                        "ticket_number": ticket_number,
                        "ticket_date": (
                            str(ticket_date_obj) if ticket_date_obj else ticket_date_str
                        ),
                        "manifest_number": manifest_number,
                        "quantity": float(quantity) if quantity else None,
                        "vendor": vendor_name,
                    },
                    confidence_scores={
                        "ticket_number": ticket_conf,
                        "date": date_conf,
                        "manifest": manifest_conf,
                        "quantity": quantity_conf,
                        "overall": overall_confidence,
                    },
                )

            except ForeignKeyNotFoundError as e:
                logger.error(f"Foreign key error: {e}")
                return self._create_review_entry(
                    page_num=page_num,
                    file_path=file_path,
                    reason=f"FOREIGN_KEY_ERROR: {str(e)}",
                    severity="CRITICAL",
                    extracted_data=extracted,
                )

            except ValidationError as e:
                logger.warning(f"Validation error: {e}")
                return self._create_review_entry(
                    page_num=page_num,
                    file_path=file_path,
                    reason=f"VALIDATION_ERROR: {str(e)}",
                    severity="CRITICAL",
                    extracted_data=extracted,
                )

            except DuplicateTicketError as e:
                logger.warning(f"Duplicate detected: {e}")
                return self._create_review_entry(
                    page_num=page_num,
                    file_path=file_path,
                    reason=f"DUPLICATE_TICKET: {str(e)}",
                    severity="WARNING",
                    extracted_data=extracted,
                )

        except Exception as e:
            logger.error(
                f"Unexpected error processing page {page_num}: {e}", exc_info=True
            )
            return ProcessingResult(
                success=False,
                page_num=page_num,
                file_path=file_path,
                error=f"PROCESSING_ERROR: {str(e)}",
            )

    def _create_review_entry(
        self,
        page_num: int,
        file_path: str,
        reason: str,
        severity: str,
        extracted_data: dict[str, Any],
    ) -> ProcessingResult:
        """Create review queue entry for failed processing.

        Args:
            page_num: Page number
            file_path: Source file path
            reason: Failure reason
            severity: Severity level (CRITICAL, WARNING, INFO)
            extracted_data: Extracted field data

        Returns:
            ProcessingResult with review queue ID
        """
        try:
            import json

            review_entry = ReviewQueue(
                page_id=f"{file_path}#page{page_num}",
                reason=reason,
                severity=severity,
                file_path=file_path,
                page_num=page_num,
                detected_fields=json.dumps(extracted_data),
                suggested_fixes=json.dumps(
                    {"action": "Manual review required", "reason": reason}
                ),
                resolved=False,
            )

            self.session.add(review_entry)
            self.session.commit()

            logger.warning(f"⚠️ Routed to review queue: {reason} (page {page_num})")

            return ProcessingResult(
                success=False,
                page_num=page_num,
                file_path=file_path,
                error=reason,
                review_queue_id=review_entry.review_id,
                extracted_data=extracted_data,
            )

        except Exception as e:
            logger.error(f"Error creating review entry: {e}")
            return ProcessingResult(
                success=False,
                page_num=page_num,
                file_path=file_path,
                error=f"REVIEW_QUEUE_ERROR: {str(e)}",
            )

    def get_processing_statistics(self) -> dict[str, int]:
        """Get statistics about processed tickets.

        Returns:
            Dictionary with processing statistics
        """
        stats = {
            "total_tickets": (
                self.repository.count_by_job(
                    self.repository.get_job_by_name(self.job_name).job_id
                )
                if self.repository.get_job_by_name(self.job_name)
                else 0
            ),
            "duplicates": len(self.repository.get_duplicates()),
            "requiring_review": len(self.repository.get_requiring_review()),
        }

        return stats
