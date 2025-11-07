"""Seed data scripts for truck ticket processing database.

Provides comprehensive seed data for development, testing, and demonstration.
Includes reference data, sample tickets, and utilities for data management.
"""

import json
import logging
from datetime import date, timedelta

from .connection import DatabaseConnection
from .schema_setup import create_database_schema


class SeedDataManager:
    """Manages seed data operations for the truck ticket database."""

    def __init__(self, db: DatabaseConnection):
        """Initialize seed data manager.

        Args:
            db: Database connection instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

    def seed_all_reference_data(self, job_code: str = "24-105") -> None:
        """Seed all reference data tables.

        Args:
            job_code: Primary job code for the project
        """
        self.logger.info("Seeding all reference data...")

        # Create schema first
        create_database_schema(self.db)

        # Seed each reference table
        self.seed_jobs(job_code)
        self.seed_materials()
        self.seed_ticket_types()
        self.seed_vendors()
        self.seed_destinations()
        self.seed_sources(job_code)

        self.logger.info("All reference data seeded successfully")

    def seed_jobs(self, job_code: str = "24-105") -> None:
        """Seed jobs table with project information.

        Args:
            job_code: Job code to create
        """
        self.logger.info(f"Seeding jobs for job code: {job_code}")

        seed_sql = f"""
        -- Primary Project Job
        IF NOT EXISTS (SELECT * FROM jobs WHERE job_code = '{job_code}')
        BEGIN
            INSERT INTO jobs (job_code, job_name, start_date, end_date)
            VALUES (
                '{job_code}',
                'Construction Site Material Tracking - DFW Airport',
                '2024-01-01',
                '2025-12-31'
            );
            PRINT 'Seeded primary job: {job_code}';
        END

        -- Additional project phases
        IF NOT EXISTS (SELECT * FROM jobs WHERE job_code = '24-105-PHASE1')
        BEGIN
            INSERT INTO jobs (job_code, job_name, start_date, end_date)
            VALUES (
                '24-105-PHASE1',
                'Terminal Development - Phase 1',
                '2024-01-01',
                '2024-06-30'
            );
        END

        IF NOT EXISTS (SELECT * FROM jobs WHERE job_code = '24-105-PHASE2')
        BEGIN
            INSERT INTO jobs (job_code, job_name, start_date, end_date)
            VALUES (
                '24-105-PHASE2',
                'Terminal Development - Phase 2',
                '2024-07-01',
                '2025-12-31'
            );
        END
        """

        self.db.execute_script(seed_sql)
        self.logger.info("Jobs seeded successfully")

    def seed_materials(self) -> None:
        """Seed materials table with all material types."""
        self.logger.info("Seeding materials...")

        seed_sql = """
        -- Contaminated Materials (require manifest)
        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'CLASS_2_CONTAMINATED')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('CLASS_2_CONTAMINATED', 'CONTAMINATED', 1);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'CLASS_3_CONTAMINATED')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('CLASS_3_CONTAMINATED', 'CONTAMINATED', 1);

        -- Clean Materials (no manifest required)
        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'NON_CONTAMINATED')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('NON_CONTAMINATED', 'CLEAN', 0);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'CLEAN_FILL')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('CLEAN_FILL', 'CLEAN', 0);

        -- Waste Materials
        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'SPOILS')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('SPOILS', 'WASTE', 0);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'GENERAL_WASTE')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('GENERAL_WASTE', 'WASTE', 0);

        -- Import Materials
        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'ROCK')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('ROCK', 'IMPORT', 0);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'FLEXBASE')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('FLEXBASE', 'IMPORT', 0);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'ASPHALT')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('ASPHALT', 'IMPORT', 0);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'CONCRETE')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('CONCRETE', 'IMPORT', 0);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'UTILITY_STONE')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('UTILITY_STONE', 'IMPORT', 0);

        -- Specialized Materials
        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = '3X5_ROCK')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('3X5_ROCK', 'IMPORT', 0);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'FLEX')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('FLEX', 'IMPORT', 0);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'DIRT')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('DIRT', 'IMPORT', 0);

        IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'FILL')
            INSERT INTO materials (material_name, material_class, requires_manifest)
            VALUES ('FILL', 'IMPORT', 0);
        """

        self.db.execute_script(seed_sql)
        self.logger.info("Materials seeded successfully")

    def seed_ticket_types(self) -> None:
        """Seed ticket_types table."""
        self.logger.info("Seeding ticket types...")

        seed_sql = """
        IF NOT EXISTS (SELECT * FROM ticket_types WHERE type_name = 'IMPORT')
            INSERT INTO ticket_types (type_name) VALUES ('IMPORT');

        IF NOT EXISTS (SELECT * FROM ticket_types WHERE type_name = 'EXPORT')
            INSERT INTO ticket_types (type_name) VALUES ('EXPORT');

        IF NOT EXISTS (SELECT * FROM ticket_types WHERE type_name = 'TRANSFER')
            INSERT INTO ticket_types (type_name) VALUES ('TRANSFER');
        """

        self.db.execute_script(seed_sql)
        self.logger.info("Ticket types seeded successfully")

    def seed_vendors(self) -> None:
        """Seed vendors table with known haulers."""
        self.logger.info("Seeding vendors...")

        seed_sql = """
        -- Waste Management Facilities
        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'WASTE_MANAGEMENT_DFW_RDF')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('WASTE_MANAGEMENT_DFW_RDF', 'WM-DFW', 'Waste Management DFW RDF Facility');

        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'WASTE_MANAGEMENT_SKYLINE_RDF')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('WASTE_MANAGEMENT_SKYLINE_RDF', 'WM-SKY', 'Waste Management Skyline RDF Facility');

        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'REPUBLIC_SERVICES')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('REPUBLIC_SERVICES', 'REPUBLIC', 'Republic Services');

        -- Local Disposal Facilities
        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'LDI_YARD')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('LDI_YARD', 'LDI', 'Lindamood Disposal Inc. Yard');

        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'POST_OAK_PIT')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('POST_OAK_PIT', 'POA', 'Post Oak Pit - Reuse Facility');

        -- Material Suppliers
        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'AUSTIN_ASPHALT')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('AUSTIN_ASPHALT', 'AA', 'Austin Asphalt Plant');

        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'ARCOSA_AGGREGATES')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('ARCOSA_AGGREGATES', 'ARCOSA', 'Arcosa Aggregates');

        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'VULCAN_MATERIALS')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('VULCAN_MATERIALS', 'VULCAN', 'Vulcan Materials Company');

        -- Transport Companies
        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'BECK_TRUCKING')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('BECK_TRUCKING', 'BECK', 'Beck Trucking - Spoils Hauling');

        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'NTX_TRUCKING')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('NTX_TRUCKING', 'NTX', 'North Texas Trucking');

        IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'UTX_TRUCKING')
            INSERT INTO vendors (vendor_name, vendor_code, contact_info)
            VALUES ('UTX_TRUCKING', 'UTX', 'Universal Texas Trucking');
        """

        self.db.execute_script(seed_sql)
        self.logger.info("Vendors seeded successfully")

    def seed_destinations(self) -> None:
        """Seed destinations table with disposal and reuse facilities."""
        self.logger.info("Seeding destinations...")

        seed_sql = """
        -- Disposal Facilities (require manifest for contaminated materials)
        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'WASTE_MANAGEMENT_DFW_RDF')
            INSERT INTO destinations (destination_name, facility_type, address, requires_manifest)
            VALUES ('WASTE_MANAGEMENT_DFW_RDF', 'DISPOSAL', 'DFW RDF Facility, Lewisville, TX', 1);

        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'WASTE_MANAGEMENT_SKYLINE_RDF')
            INSERT INTO destinations (destination_name, facility_type, address, requires_manifest)
            VALUES ('WASTE_MANAGEMENT_SKYLINE_RDF', 'DISPOSAL', 'Skyline RDF Facility, Arlington, TX', 1);

        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'REPUBLIC_SERVICES')
            INSERT INTO destinations (destination_name, facility_type, address, requires_manifest)
            VALUES ('REPUBLIC_SERVICES', 'DISPOSAL', 'Republic Services Landfill, TX', 1);

        -- Local Disposal (no manifest for clean materials)
        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'LDI_YARD')
            INSERT INTO destinations (destination_name, facility_type, address)
            VALUES ('LDI_YARD', 'DISPOSAL', 'Lindamood Disposal Inc. Yard, TX');

        -- Reuse Facilities (no manifest required)
        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'POST_OAK_PIT')
            INSERT INTO destinations (destination_name, facility_type, address)
            VALUES ('POST_OAK_PIT', 'REUSE', 'Post Oak Pit, TX');

        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'BECK_SPOILS')
            INSERT INTO destinations (destination_name, facility_type, address)
            VALUES ('BECK_SPOILS', 'REUSE', 'Beck Spoils Site, TX');

        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'NTX_SPOILS')
            INSERT INTO destinations (destination_name, facility_type, address)
            VALUES ('NTX_SPOILS', 'REUSE', 'North Texas Spoils Site, TX');

        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'UTX_SPOILS')
            INSERT INTO destinations (destination_name, facility_type, address)
            VALUES ('UTX_SPOILS', 'REUSE', 'Universal Texas Spoils Site, TX');

        -- Material Supplier Plants (Import destinations)
        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'AUSTIN_ASPHALT_PLANT')
            INSERT INTO destinations (destination_name, facility_type, address)
            VALUES ('AUSTIN_ASPHALT_PLANT', 'SUPPLIER', 'Austin Asphalt Plant, Austin, TX');

        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'ARCOSA_PLANT')
            INSERT INTO destinations (destination_name, facility_type, address)
            VALUES ('ARCOSA_PLANT', 'SUPPLIER', 'Arcosa Aggregates Plant, TX');

        IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'VULCAN_PLANT')
            INSERT INTO destinations (destination_name, facility_type, address)
            VALUES ('VULCAN_PLANT', 'SUPPLIER', 'Vulcan Materials Plant, TX');
        """

        self.db.execute_script(seed_sql)
        self.logger.info("Destinations seeded successfully")

    def seed_sources(self, job_code: str = "24-105") -> None:
        """Seed sources table with construction site locations.

        Args:
            job_code: Job code to associate sources with
        """
        self.logger.info(f"Seeding sources for job: {job_code}")

        seed_sql = f"""
        DECLARE @job_id INT = (SELECT job_id FROM jobs WHERE job_code = '{job_code}');

        -- Foundation and Structure Sources
        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'PIER_EX')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('PIER_EX', @job_id, 'Pier Excavation Area');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'MSE_WALL')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('MSE_WALL', @job_id, 'Mechanically Stabilized Earth Wall Area');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'SOUTH_MSE_WALL')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('SOUTH_MSE_WALL', @job_id, 'South MSE Wall Section');

        -- Garage and Parking Structures
        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'ZONE_E_GARAGE')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('ZONE_E_GARAGE', @job_id, 'Zone E Garage Structure');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'SPG')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('SPG', @job_id, 'South Parking Garage');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'SOUTH_PARKING_GARAGE')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('SOUTH_PARKING_GARAGE', @job_id, 'South Parking Garage Structure');

        -- Terminal and Podium Areas
        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'PODIUM')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('PODIUM', @job_id, 'Terminal Podium Structure');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'TERMINAL_FOUNDATION')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('TERMINAL_FOUNDATION', @job_id, 'Main Terminal Foundation');

        -- Site Development Areas
        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'POND')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('POND', @job_id, 'Storm Water Pond Construction');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'SOUTH_FILL')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('SOUTH_FILL', @job_id, 'South Site Fill Area');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'TRACT_2')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('TRACT_2', @job_id, 'Tract 2 Development Area');

        -- Spoils and Off-site Areas
        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'BECK_SPOILS')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('BECK_SPOILS', @job_id, 'Beck Spoils Storage Area');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'NTX_SPOILS')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('NTX_SPOILS', @job_id, 'North Texas Spoils Storage');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'UTX_SPOILS')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('UTX_SPOILS', @job_id, 'Universal Texas Spoils Storage');

        -- Utility and Infrastructure
        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'UTILITY_CORRIDOR')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('UTILITY_CORRIDOR', @job_id, 'Utility Installation Corridor');

        IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'ROAD_WIDENING')
            INSERT INTO sources (source_name, job_id, description)
            VALUES ('ROAD_WIDENING', @job_id, 'Access Road Widening Area');
        """

        self.db.execute_script(seed_sql)
        self.logger.info("Sources seeded successfully")

    def seed_sample_tickets(self, count: int = 50) -> None:
        """Seed sample truck tickets for testing and demonstration.

        Args:
            count: Number of sample tickets to create
        """
        self.logger.info(f"Seeding {count} sample truck tickets...")

        # Get reference data IDs
        refs_sql = """
        SELECT
            j.job_id, m.material_id, s.source_id, d.destination_id,
            v.vendor_id, tt.ticket_type_id
        FROM jobs j
        CROSS JOIN materials m
        CROSS JOIN sources s
        CROSS JOIN destinations d
        CROSS JOIN vendors v
        CROSS JOIN ticket_types tt
        WHERE j.job_code = '24-105'
        AND m.material_name IN ('CLASS_2_CONTAMINATED', 'NON_CONTAMINATED', 'ROCK', 'ASPHALT')
        AND s.source_name IN ('PIER_EX', 'MSE_WALL', 'SPG', 'PODIUM')
        AND d.destination_name IN ('WASTE_MANAGEMENT_DFW_RDF', 'LDI_YARD', 'POST_OAK_PIT')
        AND v.vendor_name IN ('WASTE_MANAGEMENT_DFW_RDF', 'LDI_YARD', 'AUSTIN_ASPHALT')
        """

        refs = self.db.execute_query(refs_sql)

        if not refs:
            raise ValueError(
                "Reference data not found. Run seed_all_reference_data() first."
            )

        # Generate sample tickets
        start_date = date(2024, 1, 1)

        for i in range(count):
            # Select random reference data
            ref = refs[i % len(refs)]

            # Generate ticket data
            ticket_date = start_date + timedelta(days=i % 365)
            ticket_number = f"TK-{2024 + (i // 365):04d}-{(i % 365) + 1:03d}"

            # Generate realistic quantities
            if ref["material_name"] in ["CLASS_2_CONTAMINATED", "NON_CONTAMINATED"]:
                quantity = round(20.0 + (i % 30) * 0.5, 2)  # 20-35 tons
                unit = "TONS"
            else:
                quantity = round(10.0 + (i % 20) * 0.5, 2)  # 10-20 tons
                unit = "TONS"

            # Determine ticket type based on material
            if ref["material_name"] in ["ROCK", "ASPHALT", "CONCRETE"]:
                ticket_type = "IMPORT"
            else:
                ticket_type = "EXPORT"

            # Get ticket type ID
            type_sql = f"SELECT ticket_type_id FROM ticket_types WHERE type_name = '{ticket_type}'"
            type_result = self.db.execute_query(type_sql)

            if type_result:
                ticket_type_id = type_result[0]["ticket_type_id"]
            else:
                ticket_type_id = ref["ticket_type_id"]

            # Insert ticket
            insert_sql = f"""
            INSERT INTO truck_tickets (
                ticket_number, ticket_date, quantity, quantity_unit,
                job_id, material_id, source_id, destination_id,
                vendor_id, ticket_type_id, file_id, file_page,
                processed_by
            ) VALUES (
                '{ticket_number}', '{ticket_date}', {quantity}, '{unit}',
                {ref['job_id']}, {ref['material_id']}, {ref['source_id']},
                {ref['destination_id']}, {ref['vendor_id']}, {ticket_type_id},
                'sample_ticket_{i+1}.pdf', 1, 'SEED_DATA'
            )
            """

            self.db.execute_script(insert_sql)

        self.logger.info(f"Successfully seeded {count} sample truck tickets")

    def clear_all_data(self, keep_reference: bool = True) -> None:
        """Clear all data from tables.

        Args:
            keep_reference: If True, preserves reference data (jobs, materials, etc.)
        """
        self.logger.warning("Clearing data from database...")

        if keep_reference:
            # Clear only transactional data
            clear_sql = """
            DELETE FROM truck_tickets;
            DELETE FROM review_queue;
            DELETE FROM processing_runs;
            PRINT 'Transactional data cleared (reference data preserved)';
            """
        else:
            # Clear everything
            clear_sql = """
            DELETE FROM truck_tickets;
            DELETE FROM review_queue;
            DELETE FROM processing_runs;
            DELETE FROM sources;
            DELETE FROM destinations;
            DELETE FROM vendors;
            DELETE FROM materials;
            DELETE FROM ticket_types;
            DELETE FROM jobs;
            PRINT 'All data cleared';
            """

        self.db.execute_script(clear_sql)
        self.logger.info("Data cleared successfully")

    def get_seed_summary(self) -> dict:
        """Get summary of seeded data.

        Returns:
            Dictionary with counts of all seeded data
        """
        summary_sql = """
        SELECT
            (SELECT COUNT(*) FROM jobs) as jobs_count,
            (SELECT COUNT(*) FROM materials) as materials_count,
            (SELECT COUNT(*) FROM sources) as sources_count,
            (SELECT COUNT(*) FROM destinations) as destinations_count,
            (SELECT COUNT(*) FROM vendors) as vendors_count,
            (SELECT COUNT(*) FROM ticket_types) as ticket_types_count,
            (SELECT COUNT(*) FROM truck_tickets) as tickets_count,
            (SELECT COUNT(*) FROM review_queue) as review_count,
            (SELECT COUNT(*) FROM processing_runs) as runs_count;
        """

        result = self.db.execute_query(summary_sql)

        if result:
            return dict(result[0])
        else:
            return {}

    def export_seed_data(self, output_path: str) -> None:
        """Export all seed data to JSON file.

        Args:
            output_path: Path to save JSON export
        """
        self.logger.info(f"Exporting seed data to {output_path}")

        # Export each table
        tables = [
            "jobs",
            "materials",
            "sources",
            "destinations",
            "vendors",
            "ticket_types",
        ]

        export_data = {}

        for table in tables:
            data = self.db.execute_query(f"SELECT * FROM {table}")
            export_data[table] = data

        # Write to file
        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        self.logger.info(f"Seed data exported to {output_path}")


def create_seed_manager(db: DatabaseConnection | None = None) -> SeedDataManager:
    """Create seed data manager instance.

    Args:
        db: Database connection (creates from environment if None)

    Returns:
        SeedDataManager instance
    """
    if db is None:
        db = DatabaseConnection.from_env()

    return SeedDataManager(db)


if __name__ == "__main__":
    """Command line interface for seed data operations."""
    import argparse
    import sys

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(
        description="Truck Ticket Database Seed Data Manager"
    )
    parser.add_argument(
        "--reference", action="store_true", help="Seed reference data only"
    )
    parser.add_argument(
        "--tickets", type=int, default=50, help="Number of sample tickets to create"
    )
    parser.add_argument(
        "--all", action="store_true", help="Seed all data (reference + tickets)"
    )
    parser.add_argument("--clear", action="store_true", help="Clear all data")
    parser.add_argument(
        "--clear-all", action="store_true", help="Clear all data including reference"
    )
    parser.add_argument("--summary", action="store_true", help="Show seed data summary")
    parser.add_argument("--export", type=str, help="Export seed data to JSON file")
    parser.add_argument("--job-code", default="24-105", help="Job code for seeding")

    args = parser.parse_args()

    try:
        # Create database connection
        db = DatabaseConnection.from_env()
        manager = SeedDataManager(db)

        if args.summary:
            summary = manager.get_seed_summary()
            print("Seed Data Summary:")  # noqa: T201
            for table, count in summary.items():
                print(f"  {table}: {count}")  # noqa: T201

        elif args.export:
            manager.export_seed_data(args.export)
            print(f"Data exported to {args.export}")  # noqa: T201

        elif args.clear_all:
            manager.clear_all_data(keep_reference=False)
            print("All data cleared")  # noqa: T201

        elif args.clear:
            manager.clear_all_data(keep_reference=True)
            print("Transactional data cleared (reference data preserved)")  # noqa: T201

        elif args.reference:
            manager.seed_all_reference_data(args.job_code)
            print(f"Reference data seeded for job {args.job_code}")  # noqa: T201

        elif args.all:
            manager.seed_all_reference_data(args.job_code)
            manager.seed_sample_tickets(args.tickets)
            print(  # noqa: T201
                f"All data seeded: reference + {args.tickets} sample tickets"
            )

        elif args.tickets:
            manager.seed_sample_tickets(args.tickets)
            print(f"Seeded {args.tickets} sample tickets")  # noqa: T201

        else:
            # Default: show help
            parser.print_help()

        db.close()

    except Exception as e:
        logging.error(f"Seed data operation failed: {e}")
        sys.exit(1)
