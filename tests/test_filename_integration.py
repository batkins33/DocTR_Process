"""Integration tests for filename parser with TicketProcessor."""
import pytest
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.truck_tickets.database import (
    create_all_tables,
    seed_reference_data,
)
from src.truck_tickets.processing.ticket_processor import TicketProcessor


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all_tables(engine)
    session_factory = sessionmaker(bind=engine)
    sess = session_factory()
    seed_reference_data(sess, job_code="24-105", job_name="PHMS New Pediatric Campus")
    try:
        yield sess
    finally:
        sess.close()
        engine.dispose()


def test_filename_vendor_hint_overrides_weak_ocr(session):
    """Test that filename vendor hint overrides weak OCR text."""
    processor = TicketProcessor(session, job_name="24-105", ticket_type_name="EXPORT")
    
    # Structured filename with vendor hint
    file_path = "batch1/24-105__2025-10-17__SPG__EXPORT__CLASS_2_CONTAMINATED__WASTE_MANAGEMENT_LEWISVILLE.pdf"
    
    # Weak OCR text (no clear vendor keywords)
    page_text = (
        "Ticket: WM-40000001\n"
        "Date: 10/17/2025\n"
        "Quantity: 12.5 TONS\n"
        "Manifest: WM-MAN-2024-001234\n"
    )
    
    result = processor.process_page(
        page_text=page_text,
        page_num=1,
        file_path=file_path
    )
    
    assert result.success is True
    assert result.ticket_id is not None
    # Vendor should be detected from filename, not OCR
    assert result.extracted_data.get('vendor') == "WASTE_MANAGEMENT_LEWISVILLE"


def test_filename_date_hint_overrides_ocr(session):
    """Test that filename date hint overrides OCR date."""
    processor = TicketProcessor(session, job_name="24-105", ticket_type_name="EXPORT")
    
    # Structured filename with date hint
    file_path = "batch1/24-105__2025-10-17__SPG__EXPORT.pdf"
    
    # OCR text with different date (or no date)
    page_text = (
        "Waste Management Lewisville\n"
        "Ticket: WM-50000001\n"
        "Quantity: 10.0 TONS\n"
        "Manifest: WM-MAN-2024-009999\n"
    )
    
    result = processor.process_page(
        page_text=page_text,
        page_num=1,
        file_path=file_path
    )
    
    assert result.success is True
    # Date should come from filename
    assert result.extracted_data.get('ticket_date') == "2025-10-17"


def test_filename_partial_hints_with_ocr_fallback(session):
    """Test that partial filename hints work with OCR fallback."""
    processor = TicketProcessor(session, job_name="24-105", ticket_type_name="EXPORT")
    
    # Filename with only job and date
    file_path = "batch1/24-105__2025-10-17.pdf"
    
    # OCR text provides vendor and other fields
    page_text = (
        "Waste Management Lewisville\n"
        "Ticket: WM-60000001\n"
        "Date: 10/18/2025\n"  # This should be overridden by filename
        "Quantity: 15.0 TONS\n"
        "Manifest: WM-MAN-2024-111111\n"
    )
    
    result = processor.process_page(
        page_text=page_text,
        page_num=1,
        file_path=file_path
    )
    
    assert result.success is True
    # Date from filename
    assert result.extracted_data.get('ticket_date') == "2025-10-17"
    # Vendor from OCR
    assert result.extracted_data.get('vendor') == "WASTE_MANAGEMENT_LEWISVILLE"


def test_unstructured_filename_uses_ocr_only(session):
    """Test that unstructured filenames fall back to OCR extraction."""
    processor = TicketProcessor(session, job_name="24-105", ticket_type_name="EXPORT")
    
    # Unstructured filename
    file_path = "batch1/random_scan_001.pdf"
    
    # OCR text provides all fields
    page_text = (
        "Waste Management Lewisville\n"
        "Ticket: WM-70000001\n"
        "Date: 10/17/2025\n"
        "Quantity: 20.0 TONS\n"
        "Manifest: WM-MAN-2024-222222\n"
    )
    
    result = processor.process_page(
        page_text=page_text,
        page_num=1,
        file_path=file_path
    )
    
    assert result.success is True
    # All from OCR
    assert result.extracted_data.get('vendor') == "WASTE_MANAGEMENT_LEWISVILLE"
    assert result.extracted_data.get('ticket_date') == "2025-10-17"


def test_filename_with_all_components(session):
    """Test filename with all components parsed correctly."""
    processor = TicketProcessor(session, job_name="24-105", ticket_type_name="EXPORT")
    
    # Full structured filename
    file_path = "24-105__2025-10-17__SPG__EXPORT__CLASS_2_CONTAMINATED__WASTE_MANAGEMENT_LEWISVILLE.pdf"
    
    # Minimal OCR (just ticket number and manifest)
    page_text = (
        "Ticket: WM-80000001\n"
        "Manifest: WM-MAN-2024-333333\n"
        "Quantity: 25.0 TONS\n"
    )
    
    result = processor.process_page(
        page_text=page_text,
        page_num=1,
        file_path=file_path
    )
    
    assert result.success is True
    # Vendor and date from filename
    assert result.extracted_data.get('vendor') == "WASTE_MANAGEMENT_LEWISVILLE"
    assert result.extracted_data.get('ticket_date') == "2025-10-17"
