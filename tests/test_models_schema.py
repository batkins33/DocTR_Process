from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from src.truck_tickets.models import (
    Base,
)
from src.truck_tickets.models import (
    DestinationModel as Destination,
)
from src.truck_tickets.models import (
    JobModel as Job,
)
from src.truck_tickets.models import (
    MaterialModel as Material,
)
from src.truck_tickets.models import (
    SourceModel as Source,
)
from src.truck_tickets.models import (
    TicketTypeModel as TicketType,
)
from src.truck_tickets.models import (
    TruckTicketModel as TruckTicket,
)
from src.truck_tickets.models import (
    VendorModel as Vendor,
)


def make_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return engine, SessionLocal()


def seed_min_refs(session):
    job = Job(job_code="24-105", job_name="Test Job")
    mat = Material(
        material_name="NON_CONTAMINATED",
        material_class="CLEAN",
        requires_manifest=False,
    )
    ttype = TicketType(type_name="EXPORT")
    vend = Vendor(vendor_name="WASTE_MANAGEMENT", vendor_code="WM")

    session.add_all([job, mat, ttype, vend])
    session.flush()
    return job, mat, ttype, vend


def test_unique_ticket_number_per_vendor():
    engine, session = make_session()
    try:
        job, mat, ttype, vend = seed_min_refs(session)

        t1 = TruckTicket(
            ticket_number="WM-0001",
            ticket_date=date(2024, 10, 1),
            job_id=job.job_id,
            material_id=mat.material_id,
            ticket_type_id=ttype.ticket_type_id,
            vendor_id=vend.vendor_id,
        )
        session.add(t1)
        session.commit()

        # Duplicate with same vendor should violate unique constraint
        t2 = TruckTicket(
            ticket_number="WM-0001",
            ticket_date=date(2024, 10, 2),
            job_id=job.job_id,
            material_id=mat.material_id,
            ticket_type_id=ttype.ticket_type_id,
            vendor_id=vend.vendor_id,
        )
        session.add(t2)
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.close()
        engine.dispose()


def test_relationship_inserts_minimums():
    engine, session = make_session()
    try:
        job, mat, ttype, vend = seed_min_refs(session)
        src = Source(source_name="SPG", job_id=job.job_id)
        dest = Destination(destination_name="LDI_YARD", facility_type="DISPOSAL")
        session.add_all([src, dest])
        session.flush()

        t = TruckTicket(
            ticket_number="WM-0002",
            ticket_date=date(2024, 10, 3),
            job_id=job.job_id,
            material_id=mat.material_id,
            ticket_type_id=ttype.ticket_type_id,
            vendor_id=vend.vendor_id,
            source_id=src.source_id,
            destination_id=dest.destination_id,
            manifest_number=None,
        )
        session.add(t)
        session.commit()

        fetched = session.query(TruckTicket).filter_by(ticket_number="WM-0002").one()
        assert fetched.job_id == job.job_id
        assert fetched.material_id == mat.material_id
        assert fetched.vendor_id == vend.vendor_id
        assert fetched.source_id == src.source_id
        assert fetched.destination_id == dest.destination_id
    finally:
        session.close()
        engine.dispose()
