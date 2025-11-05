"""SQLAlchemy-based database schema setup and seed data.

This module provides database-agnostic schema creation and seeding using
SQLAlchemy ORM models. Works with SQLite, PostgreSQL, MySQL, and SQL Server.

Usage:
    # Create all tables
    create_all_tables(engine)

    # Seed reference data
    seed_reference_data(session)

    # Drop all tables (CAUTION!)
    drop_all_tables(engine)
"""

import logging
from datetime import date

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..models.sql_processing import (  # noqa: F401 - ensure tables are registered
    ProcessingRun,
    ReviewQueue,
)
from ..models.sql_reference import (
    Base,
    Destination,
    Job,
    Material,
    Source,
    TicketType,
    Vendor,
)
from ..models.sql_truck_ticket import (
    TruckTicket,  # noqa: F401 - ensure table is registered
)

logger = logging.getLogger(__name__)


def create_all_tables(engine: Engine) -> None:
    """Create all database tables from SQLAlchemy models.

    Args:
        engine: SQLAlchemy engine instance

    Example:
        ```python
        from sqlalchemy import create_engine

        engine = create_engine('sqlite:///truck_tickets.db')
        create_all_tables(engine)
        ```
    """
    logger.info("Creating all database tables...")

    try:
        Base.metadata.create_all(engine)
        logger.info("✅ All tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise


def drop_all_tables(engine: Engine) -> None:
    """Drop all database tables (CAUTION: destroys all data).

    Args:
        engine: SQLAlchemy engine instance

    Warning:
        This will permanently delete all data in the database!
    """
    logger.warning("⚠️  Dropping all tables - THIS WILL DESTROY ALL DATA")

    try:
        Base.metadata.drop_all(engine)
        logger.info("✅ All tables dropped successfully")
    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        raise


def seed_reference_data(
    session: Session,
    job_code: str = "24-105",
    job_name: str = "PHMS New Pediatric Campus",
) -> dict:
    """Seed all reference data for testing and production.

    Seeds:
        - 1 job (24-105)
        - 12 materials (contaminated, clean, import types)
        - 13 sources (construction site locations)
        - 3 destinations (disposal facilities)
        - 3 vendors (haulers)
        - 2 ticket types (IMPORT, EXPORT)

    Args:
        session: SQLAlchemy session
        job_code: Job code (default: "24-105")
        job_name: Job name (default: "PHMS New Pediatric Campus")

    Returns:
        Dictionary with counts of seeded records

    Example:
        ```python
        from sqlalchemy.orm import Session

        counts = seed_reference_data(session)
        print(f"Seeded {counts['materials']} materials")
        ```
    """
    logger.info("🌱 Seeding reference data...")

    counts = {
        "jobs": 0,
        "materials": 0,
        "sources": 0,
        "destinations": 0,
        "vendors": 0,
        "ticket_types": 0,
    }

    try:
        # 1. Seed Job
        job = session.query(Job).filter_by(job_code=job_code).first()
        if not job:
            job = Job(job_code=job_code, job_name=job_name, start_date=date(2024, 1, 1))
            session.add(job)
            session.flush()  # Get job_id
            counts["jobs"] = 1
            logger.info(f"  ✅ Created job: {job_code}")
        else:
            logger.info(f"  ℹ️  Job already exists: {job_code}")

        # 2. Seed Materials
        materials_data = [
            # Contaminated Materials (require manifests)
            {
                "material_name": "CLASS_2_CONTAMINATED",
                "material_class": "CONTAMINATED",
                "requires_manifest": True,
            },
            {
                "material_name": "CONTAMINATED_SOIL",
                "material_class": "CONTAMINATED",
                "requires_manifest": True,
            },
            # Clean Materials (no manifest required)
            {
                "material_name": "NON_CONTAMINATED",
                "material_class": "CLEAN",
                "requires_manifest": False,
            },
            {
                "material_name": "CLEAN_FILL",
                "material_class": "CLEAN",
                "requires_manifest": False,
            },
            # Spoils (waste from other subs)
            {
                "material_name": "SPOILS",
                "material_class": "WASTE",
                "requires_manifest": False,
            },
            # Import Materials (9 types from spec)
            {
                "material_name": "3X5",
                "material_class": "IMPORT",
                "requires_manifest": False,
            },
            {
                "material_name": "ASPHALT",
                "material_class": "IMPORT",
                "requires_manifest": False,
            },
            {
                "material_name": "C2",
                "material_class": "IMPORT",
                "requires_manifest": False,
            },
            {
                "material_name": "DIRT",
                "material_class": "IMPORT",
                "requires_manifest": False,
            },
            {
                "material_name": "FILL",
                "material_class": "IMPORT",
                "requires_manifest": False,
            },
            {
                "material_name": "FLEX",
                "material_class": "IMPORT",
                "requires_manifest": False,
            },
            {
                "material_name": "FLEXBASE",
                "material_class": "IMPORT",
                "requires_manifest": False,
            },
            {
                "material_name": "ROCK",
                "material_class": "IMPORT",
                "requires_manifest": False,
            },
            {
                "material_name": "UTILITY_STONE",
                "material_class": "IMPORT",
                "requires_manifest": False,
            },
        ]

        for mat_data in materials_data:
            existing = (
                session.query(Material)
                .filter_by(material_name=mat_data["material_name"])
                .first()
            )

            if not existing:
                material = Material(**mat_data)
                session.add(material)
                counts["materials"] += 1

        logger.info(f"  ✅ Seeded {counts['materials']} materials")

        # 3. Seed Sources (13 construction site locations from spec)
        sources_data = [
            # Main excavation areas
            {"source_name": "PODIUM", "description": "Podium excavation area"},
            {"source_name": "PIER_EX", "description": "Pier excavation area"},
            {"source_name": "MSE_WALL", "description": "MSE wall excavation"},
            {"source_name": "SPG", "description": "South Parking Garage"},
            {"source_name": "NPG", "description": "North Parking Garage"},
            # Additional excavation zones
            {"source_name": "TOWER_1", "description": "Tower 1 foundation"},
            {"source_name": "TOWER_2", "description": "Tower 2 foundation"},
            {
                "source_name": "UTILITY_TRENCH",
                "description": "Utility trench excavation",
            },
            {"source_name": "LOADING_DOCK", "description": "Loading dock area"},
            {"source_name": "EMERGENCY_ACCESS", "description": "Emergency access road"},
            # Spoils from other subs
            {
                "source_name": "PLUMBING_SUB",
                "description": "Spoils from plumbing subcontractor",
            },
            {
                "source_name": "ELECTRICAL_SUB",
                "description": "Spoils from electrical subcontractor",
            },
            {
                "source_name": "HVAC_SUB",
                "description": "Spoils from HVAC subcontractor",
            },
        ]

        for source_data in sources_data:
            existing = (
                session.query(Source)
                .filter_by(source_name=source_data["source_name"])
                .first()
            )

            if not existing:
                source = Source(job_id=job.job_id, **source_data)
                session.add(source)
                counts["sources"] += 1

        logger.info(f"  ✅ Seeded {counts['sources']} sources")

        # 4. Seed Destinations (3 disposal facilities from spec)
        destinations_data = [
            {
                "destination_name": "WASTE_MANAGEMENT_LEWISVILLE",
                "facility_type": "DISPOSAL",
                "address": "Lewisville, TX",
                "requires_manifest": True,
            },
            {
                "destination_name": "LDI_YARD",
                "facility_type": "DISPOSAL",
                "address": "LDI Yard",
                "requires_manifest": False,
            },
            {
                "destination_name": "POST_OAK_PIT",
                "facility_type": "REUSE",
                "address": "Post Oak Pit",
                "requires_manifest": False,
            },
        ]

        for dest_data in destinations_data:
            existing = (
                session.query(Destination)
                .filter_by(destination_name=dest_data["destination_name"])
                .first()
            )

            if not existing:
                destination = Destination(**dest_data)
                session.add(destination)
                counts["destinations"] += 1

        logger.info(f"  ✅ Seeded {counts['destinations']} destinations")

        # 5. Seed Vendors (disposal facilities that also act as vendors)
        vendors_data = [
            {
                "vendor_name": "WASTE_MANAGEMENT_LEWISVILLE",
                "vendor_code": "WM",
                "contact_info": "Waste Management Lewisville - Contaminated material disposal",
            },
            {
                "vendor_name": "LDI_YARD",
                "vendor_code": "LDI",
                "contact_info": "LDI Yard - Clean fill disposal",
            },
            {
                "vendor_name": "POST_OAK_PIT",
                "vendor_code": "POA",
                "contact_info": "Post Oak Pit - Material reuse site",
            },
        ]

        for vendor_data in vendors_data:
            existing = (
                session.query(Vendor)
                .filter_by(vendor_name=vendor_data["vendor_name"])
                .first()
            )

            if not existing:
                vendor = Vendor(**vendor_data)
                session.add(vendor)
                counts["vendors"] += 1

        logger.info(f"  ✅ Seeded {counts['vendors']} vendors")

        # 6. Seed Ticket Types
        ticket_types = ["EXPORT", "IMPORT"]

        for type_name in ticket_types:
            existing = session.query(TicketType).filter_by(type_name=type_name).first()

            if not existing:
                ticket_type = TicketType(type_name=type_name)
                session.add(ticket_type)
                counts["ticket_types"] += 1

        logger.info(f"  ✅ Seeded {counts['ticket_types']} ticket types")

        # Commit all changes
        session.commit()

        logger.info("🎉 Reference data seeding complete!")
        logger.info(f"   📊 Summary: {counts}")

        return counts

    except Exception as e:
        session.rollback()
        logger.error(f"❌ Failed to seed reference data: {e}")
        raise


def reset_database(engine: Engine, session: Session) -> None:
    """Drop all tables, recreate schema, and seed reference data.

    WARNING: This destroys all existing data!

    Args:
        engine: SQLAlchemy engine
        session: SQLAlchemy session

    Example:
        ```python
        # Complete database reset
        reset_database(engine, session)
        ```
    """
    logger.warning("🔄 Resetting database (drop + create + seed)...")

    # Drop all tables
    drop_all_tables(engine)

    # Create all tables
    create_all_tables(engine)

    # Seed reference data
    seed_reference_data(session)

    logger.info("✅ Database reset complete!")


def create_test_database(
    db_path: str = "test_truck_tickets.db",
) -> tuple[Engine, Session]:
    """Create a test database with schema and seed data.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Tuple of (engine, session)

    Example:
        ```python
        # Create test database
        engine, session = create_test_database("test.db")

        # Use for testing
        from src.truck_tickets.database import TicketRepository
        repo = TicketRepository(session)

        # Cleanup
        session.close()
        engine.dispose()
        ```
    """
    logger.info(f"📦 Creating test database: {db_path}")

    # Create engine
    engine = create_engine(f"sqlite:///{db_path}", echo=False)

    # Create session
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    # Create schema
    create_all_tables(engine)

    # Seed data
    seed_reference_data(session)

    logger.info("✅ Test database ready!")

    return engine, session


if __name__ == "__main__":
    """Command-line interface for schema management."""
    import argparse

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="Database schema management")
    parser.add_argument(
        "action",
        choices=["create", "drop", "seed", "reset", "test"],
        help="Action to perform",
    )
    parser.add_argument(
        "--db",
        default="sqlite:///truck_tickets.db",
        help="Database URL (default: sqlite:///truck_tickets.db)",
    )
    parser.add_argument(
        "--job", default="24-105", help="Job code for seeding (default: 24-105)"
    )

    args = parser.parse_args()

    # Create engine and session
    engine = create_engine(args.db, echo=False)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        if args.action == "create":
            create_all_tables(engine)
            logger.info("✅ Tables created")

        elif args.action == "drop":
            confirm = input("⚠️  WARNING: Drop all tables? Type 'yes' to confirm: ")
            if confirm.lower() == "yes":
                drop_all_tables(engine)
                logger.info("✅ Tables dropped")
            else:
                logger.info("❌ Cancelled")

        elif args.action == "seed":
            counts = seed_reference_data(session, job_code=args.job)
            logger.info("✅ Seeded: %s", counts)

        elif args.action == "reset":
            confirm = input(
                "⚠️  WARNING: Reset database (drop + create + seed)? Type 'yes' to confirm: "
            )
            if confirm.lower() == "yes":
                reset_database(engine, session)
                logger.info("✅ Database reset complete")
            else:
                logger.info("❌ Cancelled")

        elif args.action == "test":
            # Create test database
            test_engine, test_session = create_test_database("test_truck_tickets.db")
            logger.info("✅ Test database created: test_truck_tickets.db")
            test_session.close()
            test_engine.dispose()

    finally:
        session.close()
        engine.dispose()
