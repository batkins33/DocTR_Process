"""Test script for database migration functionality.

This script tests the Alembic migration setup by:
1. Creating a fresh test database
2. Running migrations to create schema
3. Verifying all tables were created
4. Testing downgrade functionality
5. Testing stamp functionality

Usage:
    python test_migrations.py
"""

import logging
import sqlite3
import tempfile
from pathlib import Path

from .migration_manager import MigrationManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_migration_functionality():
    """Test complete migration workflow."""

    # Create temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        test_db_path = temp_file.name

    test_db_url = f"sqlite:///{test_db_path}"

    try:
        logger.info("Starting migration functionality tests...")

        # Initialize migration manager with test database
        manager = MigrationManager(test_db_url)

        # Test 1: Check initial status (no migrations)
        logger.info("Test 1: Checking initial migration status...")
        initial_status = manager.get_migration_status()
        assert (
            initial_status["current_revision"] is None
        ), "Expected no current revision"
        logger.info("✓ Initial status correct - no migrations applied")

        # Test 2: Run migrations
        logger.info("Test 2: Running initial migrations...")
        manager.run_migrations()
        logger.info("✓ Migrations completed")

        # Test 3: Verify tables were created
        logger.info("Test 3: Verifying database schema...")
        tables = get_database_tables(test_db_path)
        expected_tables = {
            "jobs",
            "materials",
            "destinations",
            "vendors",
            "ticket_types",
            "sources",
            "truck_tickets",
            "review_queue",
            "processing_runs",
            "alembic_version",
        }

        assert (
            tables == expected_tables
        ), f"Expected tables {expected_tables}, got {tables}"
        logger.info(f"✓ All expected tables created: {sorted(tables)}")

        # Test 4: Check migration status after upgrade
        logger.info("Test 4: Checking post-migration status...")
        post_status = manager.get_migration_status()
        assert post_status["current_revision"] is not None, "Expected current revision"
        assert post_status["needs_upgrade"] is False, "Expected no pending upgrades"
        logger.info(f"✓ Current revision: {post_status['current_revision']}")

        # Test 5: Test downgrade functionality
        logger.info("Test 5: Testing downgrade functionality...")
        manager.downgrade_migrations("base")

        # Check that alembic_version table is gone but other tables remain
        tables_after_downgrade = get_database_tables(test_db_path)
        assert (
            "alembic_version" not in tables_after_downgrade
        ), "Expected alembic_version table to be removed"
        logger.info("✓ Downgrade completed successfully")

        # Re-run migrations to restore state
        manager.run_migrations()

        # Test 6: Test stamp functionality
        logger.info("Test 6: Testing stamp functionality...")
        # Create a new database and stamp it
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file2:
            test_db_path2 = temp_file2.name

        test_db_url2 = f"sqlite:///{test_db_path2}"
        manager2 = MigrationManager(test_db_url2)

        # Create tables manually (simulating existing database)
        create_test_tables_manually(test_db_path2)

        # Stamp the database
        manager2.stamp_database()

        # Check status
        stamped_status = manager2.get_migration_status()
        assert (
            stamped_status["current_revision"] is not None
        ), "Expected stamped revision"
        logger.info("✓ Stamp functionality working")

        # Cleanup
        Path(test_db_path2).unlink()

        logger.info("🎉 All migration tests passed!")

    except Exception as e:
        logger.error(f"❌ Migration test failed: {e}")
        raise
    finally:
        # Cleanup test database
        Path(test_db_path).unlink(missing_ok=True)


def get_database_tables(db_path: str) -> set:
    """Get all table names from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    return tables


def create_test_tables_manually(db_path: str):
    """Create basic tables manually to simulate existing database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create a simple table to simulate existing database
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    """
    )

    conn.commit()
    conn.close()


def test_migration_manager_api():
    """Test the MigrationManager API methods."""

    logger.info("Testing MigrationManager API...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        test_db_path = temp_file.name

    test_db_url = f"sqlite:///{test_db_path}"

    try:
        manager = MigrationManager(test_db_url)

        # Test getting current revision (should be None)
        current = manager.get_current_revision()
        assert current is None, "Expected no current revision initially"

        # Test getting history (should be empty)
        history = manager.get_migration_history()
        assert isinstance(history, list), "Expected history to be a list"

        # Run migrations
        manager.run_migrations()

        # Test getting current revision after migration
        current = manager.get_current_revision()
        assert current is not None, "Expected current revision after migration"

        # Test getting history after migration
        history = manager.get_migration_history()
        assert len(history) > 0, "Expected non-empty history after migration"

        logger.info("✓ MigrationManager API tests passed")

    finally:
        Path(test_db_path).unlink(missing_ok=True)


def main():
    """Run all migration tests."""
    logger.info("Starting comprehensive migration tests...")

    test_migration_functionality()
    test_migration_manager_api()

    logger.info("🎉 All migration tests completed successfully!")


if __name__ == "__main__":
    main()
