from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.truck_tickets.database import (
    create_all_tables,
    seed_reference_data,
)
from src.truck_tickets.database.ticket_repository import (
    DuplicateTicketError,
    TicketRepository,
    ValidationError,
)
from src.truck_tickets.models.sql_processing import ReviewQueue
from src.truck_tickets.models.sql_truck_ticket import TruckTicket
from src.truck_tickets.processing.ticket_processor import TicketProcessor


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    create_all_tables(engine)
    SessionLocal = sessionmaker(bind=engine)
    sess = SessionLocal()
    seed_reference_data(sess, job_code="24-105", job_name="PHMS New Pediatric Campus")
    try:
        yield sess
    finally:
        sess.close()
        engine.dispose()


def test_repository_create_non_contaminated_succeeds(session):
    repo = TicketRepository(session)
    t = repo.create(
        ticket_number="WM-1001",
        ticket_date=date(2024, 10, 17),
        job_name="24-105",
        material_name="NON_CONTAMINATED",
        ticket_type_name="EXPORT",
        vendor_name="WASTE_MANAGEMENT",
        quantity=Decimal("12.5"),
        quantity_unit="TONS",
    )
    assert t.ticket_id is not None
    # Fetch back
    fetched = session.query(TruckTicket).filter_by(ticket_number="WM-1001").one()
    assert fetched.quantity == Decimal("12.5")


def test_repository_missing_manifest_for_contaminated_raises(session):
    repo = TicketRepository(session)
    with pytest.raises(ValidationError):
        repo.create(
            ticket_number="WM-2001",
            ticket_date=date(2024, 10, 18),
            job_name="24-105",
            material_name="CLASS_2_CONTAMINATED",
            ticket_type_name="EXPORT",
            vendor_name="WASTE_MANAGEMENT",
            quantity=Decimal("10.0"),
            quantity_unit="TONS",
            manifest_number=None,
        )


def test_repository_duplicate_raises(session):
    repo = TicketRepository(session)
    # First insert
    repo.create(
        ticket_number="WM-3001",
        ticket_date=date(2024, 10, 18),
        job_name="24-105",
        material_name="NON_CONTAMINATED",
        ticket_type_name="EXPORT",
        vendor_name="WASTE_MANAGEMENT",
        quantity=Decimal("9.0"),
        quantity_unit="TONS",
    )
    # Duplicate within window (same number + vendor)
    with pytest.raises(DuplicateTicketError):
        repo.create(
            ticket_number="WM-3001",
            ticket_date=date(2024, 10, 19),
            job_name="24-105",
            material_name="NON_CONTAMINATED",
            ticket_type_name="EXPORT",
            vendor_name="WASTE_MANAGEMENT",
            quantity=Decimal("9.0"),
            quantity_unit="TONS",
        )


def test_processor_success_page_processing(session):
    processor = TicketProcessor(session, job_name="24-105", ticket_type_name="EXPORT")
    page_text = (
        "Waste Management Lewisville\n"
        "Ticket: WM-40000001\n"
        "Date: 10/17/2025\n"
        "Quantity: 12.5 TONS\n"
        "Manifest: WM-MAN-2024-001234\n"
        "Truck 123\n"
    )
    result = processor.process_page(
        page_text=page_text, page_num=1, file_path="batch1/file1.pdf"
    )
    assert result.success is True
    assert result.ticket_id is not None


def test_processor_duplicate_routes_review_queue(session):
    processor = TicketProcessor(session, job_name="24-105", ticket_type_name="EXPORT")
    page_text = (
        "Waste Management Lewisville\n"
        "Ticket: WM-50000001\n"
        "Date: 10/17/2025\n"
        "Quantity: 10.0 TONS\n"
        "Manifest: WM-MAN-2024-009999\n"
    )
    # First pass - succeed
    first = processor.process_page(
        page_text=page_text, page_num=1, file_path="batch1/file2.pdf"
    )
    assert first.success is True

    # Second pass - duplicate should route to review
    second = processor.process_page(
        page_text=page_text, page_num=1, file_path="batch1/file2.pdf"
    )
    assert second.success is False
    assert second.review_queue_id is not None

    review = session.query(ReviewQueue).get(second.review_queue_id)
    assert review is not None
    assert "DUPLICATE_TICKET" in review.reason
