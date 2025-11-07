"""Database migration management utilities for the truck ticket system.

This module provides helper functions for managing Alembic database migrations,
including running migrations, creating new migrations, and checking migration status.

Usage:
    # Run all pending migrations
    run_migrations()

    # Create a new migration
    create_migration("add_new_column")

    # Check migration status
    status = get_migration_status()
    print(status)
"""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from .connection import DatabaseConnection

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations using Alembic."""

    def __init__(self, database_url: str | None = None):
        """Initialize migration manager.

        Args:
            database_url: Database connection URL. If None, uses environment variables.
        """
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.alembic_ini_path = self.migrations_dir / "alembic.ini"

        # Configure Alembic
        self.alembic_cfg = Config(str(self.alembic_ini_path))
        self.alembic_cfg.set_main_option("script_location", str(self.migrations_dir))

        # Set database URL
        if database_url:
            self.alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        else:
            # Use environment variables or default
            try:
                db_connection = DatabaseConnection.from_env()
                self.alembic_cfg.set_main_option(
                    "sqlalchemy.url", db_connection.connection_url
                )
            except Exception:
                # Fallback to SQLite for development
                self.alembic_cfg.set_main_option(
                    "sqlalchemy.url", "sqlite:///truck_tickets.db"
                )

    def run_migrations(self, target_revision: str = "head") -> None:
        """Run database migrations to bring schema up to date.

        Args:
            target_revision: Target revision to migrate to. Defaults to "head".
        """
        logger.info(f"Running migrations to revision: {target_revision}")
        try:
            command.upgrade(self.alembic_cfg, target_revision)
            logger.info("Migrations completed successfully")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise

    def downgrade_migrations(self, target_revision: str = "-1") -> None:
        """Downgrade database to a specific revision.

        Args:
            target_revision: Target revision to downgrade to. Defaults to one revision back.
        """
        logger.info(f"Downgrading migrations to revision: {target_revision}")
        try:
            command.downgrade(self.alembic_cfg, target_revision)
            logger.info("Downgrade completed successfully")
        except Exception as e:
            logger.error(f"Downgrade failed: {e}")
            raise

    def create_migration(self, message: str, autogenerate: bool = True) -> str:
        """Create a new migration file.

        Args:
            message: Descriptive message for the migration
            autogenerate: Whether to autogenerate migration from model changes

        Returns:
            Path to the created migration file
        """
        logger.info(f"Creating migration: {message}")
        try:
            revision = command.revision(
                self.alembic_cfg, message=message, autogenerate=autogenerate
            )
            logger.info(f"Migration created: {revision}")
            return revision
        except Exception as e:
            logger.error(f"Migration creation failed: {e}")
            raise

    def get_current_revision(self) -> str | None:
        """Get the current database revision.

        Returns:
            Current revision identifier or None if no migrations applied
        """
        try:
            return command.current(self.alembic_cfg)
        except Exception as e:
            logger.error(f"Failed to get current revision: {e}")
            return None

    def get_migration_history(self) -> list:
        """Get the history of all migrations.

        Returns:
            List of migration revision information
        """
        try:
            return command.history(self.alembic_cfg)
        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return []

    def get_migration_status(self) -> dict:
        """Get comprehensive migration status.

        Returns:
            Dictionary containing migration status information
        """
        try:
            current = self.get_current_revision()
            history = self.get_migration_history()

            return {
                "current_revision": current,
                "total_migrations": len(history),
                "needs_upgrade": current != "head" if current else True,
                "migration_history": history,
            }
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {"error": str(e)}

    def stamp_database(self, revision: str = "head") -> None:
        """Mark the database with a specific revision without running migrations.

        Useful for existing databases that need to be brought under migration control.

        Args:
            revision: Revision to stamp the database with
        """
        logger.info(f"Stamping database with revision: {revision}")
        try:
            command.stamp(self.alembic_cfg, revision)
            logger.info("Database stamped successfully")
        except Exception as e:
            logger.error(f"Stamping failed: {e}")
            raise


# Convenience functions for common operations
def run_migrations(database_url: str | None = None) -> None:
    """Run all pending migrations."""
    manager = MigrationManager(database_url)
    manager.run_migrations()


def create_migration(message: str, database_url: str | None = None) -> str:
    """Create a new migration."""
    manager = MigrationManager(database_url)
    return manager.create_migration(message)


def get_migration_status(database_url: str | None = None) -> dict:
    """Get migration status."""
    manager = MigrationManager(database_url)
    return manager.get_migration_status()


def downgrade_database(
    target_revision: str = "-1", database_url: str | None = None
) -> None:
    """Downgrade database."""
    manager = MigrationManager(database_url)
    manager.downgrade_migrations(target_revision)


def stamp_existing_database(database_url: str | None = None) -> None:
    """Stamp an existing database with current revision."""
    manager = MigrationManager(database_url)
    manager.stamp_database()


# CLI integration
def main():
    """Command-line interface for migration management."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Truck Ticket Database Migration Manager"
    )
    parser.add_argument(
        "command",
        choices=["upgrade", "downgrade", "current", "history", "create", "stamp"],
    )
    parser.add_argument("--revision", default="head", help="Target revision")
    parser.add_argument("--message", help="Migration message (for create command)")
    parser.add_argument(
        "--autogenerate",
        action="store_true",
        help="Autogenerate migration (for create command)",
    )

    args = parser.parse_args()

    manager = MigrationManager()

    if args.command == "upgrade":
        manager.run_migrations(args.revision)
    elif args.command == "downgrade":
        manager.downgrade_migrations(args.revision)
    elif args.command == "current":
        print(f"Current revision: {manager.get_current_revision()}")  # noqa: T201
    elif args.command == "history":
        history = manager.get_migration_history()
        for rev in history:
            print(rev)  # noqa: T201
    elif args.command == "create":
        if not args.message:
            print("Error: --message is required for create command")  # noqa: T201
            return
        manager.create_migration(args.message, args.autogenerate)
    elif args.command == "stamp":
        manager.stamp_database(args.revision)


if __name__ == "__main__":
    main()
