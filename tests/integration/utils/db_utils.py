"""Database utilities for integration tests.

Provides setup/teardown of SQLite test database with schema
and reference data for end-to-end pipeline testing.
"""

import logging
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from src.truck_tickets.database.sqlalchemy_schema_setup import (
    create_all_tables,
    seed_reference_data,
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Create temporary SQLite database for integration tests."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    db_url = f"sqlite:///{temp_file.name}"
    logger.debug(f"Created test SQLite DB: {db_url}")
    return db_url


@pytest.fixture(scope="session")
def test_engine(test_db_url: str):
    """SQLAlchemy engine for test database."""
    engine = create_engine(test_db_url, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def test_db_session(test_engine):
    """Database session with full schema and reference data."""
    # Create all tables
    create_all_tables(test_engine)

    # Insert reference data
    session_local = sessionmaker(bind=test_engine)
    session = session_local()

    try:
        seed_reference_data(session)
        session.commit()
    except Exception:
        session.rollback()
        raise

    yield session

    session.close()


@pytest.fixture
def temp_db_session():
    """Session with full schema for isolated test."""
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    db_url = f"sqlite:///{temp_file.name}"

    engine = create_engine(db_url, echo=False)

    create_all_tables(engine)

    session_local = sessionmaker(bind=engine)
    session = session_local()

    try:
        seed_reference_data(session)
        session.commit()
    except Exception:
        session.rollback()
        raise

    yield session

    session.close()
    engine.dispose()


def verify_test_db(session: Session) -> dict[str, int]:
    """Verify test database has expected reference data.

    Returns:
        Dictionary with table row counts
    """
    result = {}

    tables = [
        "jobs",
        "materials",
        "sources",
        "destinations",
        "vendors",
        "ticket_types",
    ]

    for table in tables:
        try:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            result[table] = count
        except Exception as e:
            logger.warning(f"Could not count rows in {table}: {e}")
            result[table] = 0

    return result


def cleanup_test_db(session: Session) -> None:
    """Clean up test database after test run."""
    try:
        # Clear transaction tables but keep reference data
        tables_to_clear = [
            "truck_tickets",
            "review_queue",
            "processing_runs",
        ]

        for table in tables_to_clear:
            try:
                session.execute(text(f"DELETE FROM {table}"))
            except Exception as e:
                logger.warning(f"Could not clear {table}: {e}")

        session.commit()
    except Exception as e:
        logger.error(f"Error cleaning up test DB: {e}")
        session.rollback()
