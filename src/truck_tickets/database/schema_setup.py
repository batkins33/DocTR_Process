"""SQL Server database schema setup for truck ticket processing.

Creates all required tables, indexes, and constraints as specified in the
Truck Ticket Processing Complete Specification.
"""

import logging
from typing import Optional

from .connection import DatabaseConnection


# SQL Server schema based on specification
SCHEMA_SQL = """
-- ==========================================
-- TRUCK TICKETS DATABASE SCHEMA
-- Project 24-105: Construction Site Material Tracking
-- ==========================================

-- Table: jobs
-- Stores construction project information
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'jobs')
BEGIN
    CREATE TABLE jobs (
        job_id INT PRIMARY KEY IDENTITY(1,1),
        job_code VARCHAR(50) NOT NULL UNIQUE,
        job_name VARCHAR(255),
        start_date DATE,
        end_date DATE,
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
    PRINT 'Created table: jobs';
END
GO

-- Table: materials
-- Stores material types (contaminated, clean, import materials)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'materials')
BEGIN
    CREATE TABLE materials (
        material_id INT PRIMARY KEY IDENTITY(1,1),
        material_name VARCHAR(100) NOT NULL UNIQUE,
        material_class VARCHAR(50),
        requires_manifest BIT DEFAULT 0,
        created_at DATETIME DEFAULT GETDATE()
    );
    PRINT 'Created table: materials';
END
GO

-- Table: sources
-- Stores source locations on construction site
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'sources')
BEGIN
    CREATE TABLE sources (
        source_id INT PRIMARY KEY IDENTITY(1,1),
        source_name VARCHAR(100) NOT NULL UNIQUE,
        job_id INT,
        description VARCHAR(255),
        FOREIGN KEY (job_id) REFERENCES jobs(job_id),
        created_at DATETIME DEFAULT GETDATE()
    );
    PRINT 'Created table: sources';
END
GO

-- Table: destinations
-- Stores destination facilities (disposal, reuse, landfill)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'destinations')
BEGIN
    CREATE TABLE destinations (
        destination_id INT PRIMARY KEY IDENTITY(1,1),
        destination_name VARCHAR(100) NOT NULL UNIQUE,
        facility_type VARCHAR(50),
        address VARCHAR(500),
        requires_manifest BIT DEFAULT 0,
        created_at DATETIME DEFAULT GETDATE()
    );
    PRINT 'Created table: destinations';
END
GO

-- Table: vendors
-- Stores vendor/hauler company information
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'vendors')
BEGIN
    CREATE TABLE vendors (
        vendor_id INT PRIMARY KEY IDENTITY(1,1),
        vendor_name VARCHAR(100) NOT NULL UNIQUE,
        vendor_code VARCHAR(50),
        contact_info VARCHAR(500),
        created_at DATETIME DEFAULT GETDATE()
    );
    PRINT 'Created table: vendors';
END
GO

-- Table: ticket_types
-- Stores ticket type (IMPORT or EXPORT)
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ticket_types')
BEGIN
    CREATE TABLE ticket_types (
        ticket_type_id INT PRIMARY KEY IDENTITY(1,1),
        type_name VARCHAR(20) NOT NULL UNIQUE
    );
    PRINT 'Created table: ticket_types';
    
    -- Insert default types
    IF NOT EXISTS (SELECT * FROM ticket_types WHERE type_name = 'IMPORT')
        INSERT INTO ticket_types (type_name) VALUES ('IMPORT');
    IF NOT EXISTS (SELECT * FROM ticket_types WHERE type_name = 'EXPORT')
        INSERT INTO ticket_types (type_name) VALUES ('EXPORT');
END
GO

-- Table: truck_tickets (Main Transaction Table)
-- Stores extracted truck ticket data
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'truck_tickets')
BEGIN
    CREATE TABLE truck_tickets (
        ticket_id INT PRIMARY KEY IDENTITY(1,1),
        ticket_number VARCHAR(50) NOT NULL,
        ticket_date DATE NOT NULL,
        quantity DECIMAL(10,2),
        quantity_unit VARCHAR(20),
        
        -- Foreign Keys
        job_id INT NOT NULL,
        material_id INT NOT NULL,
        source_id INT,
        destination_id INT,
        vendor_id INT,
        ticket_type_id INT NOT NULL,
        
        -- File/Processing Metadata
        file_id VARCHAR(255),
        file_page INT,
        request_guid VARCHAR(50),
        
        -- Regulatory/Compliance
        manifest_number VARCHAR(50),
        
        -- Audit Trail
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE(),
        processed_by VARCHAR(100),
        
        -- Constraints
        FOREIGN KEY (job_id) REFERENCES jobs(job_id),
        FOREIGN KEY (material_id) REFERENCES materials(material_id),
        FOREIGN KEY (source_id) REFERENCES sources(source_id),
        FOREIGN KEY (destination_id) REFERENCES destinations(destination_id),
        FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
        FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(ticket_type_id)
    );
    PRINT 'Created table: truck_tickets';
END
GO

-- Uniqueness guard (soft constraint)
-- Prevents duplicate tickets from same vendor
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ticket_vendor_unique')
BEGIN
    CREATE UNIQUE INDEX idx_ticket_vendor_unique 
    ON truck_tickets(ticket_number, vendor_id)
    WHERE ticket_number IS NOT NULL AND vendor_id IS NOT NULL;
    PRINT 'Created index: idx_ticket_vendor_unique';
END
GO

-- Performance indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_ticket_date')
BEGIN
    CREATE INDEX idx_ticket_date ON truck_tickets(ticket_date);
    PRINT 'Created index: idx_ticket_date';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_job_date')
BEGIN
    CREATE INDEX idx_job_date ON truck_tickets(job_id, ticket_date);
    PRINT 'Created index: idx_job_date';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_manifest')
BEGIN
    CREATE INDEX idx_manifest ON truck_tickets(manifest_number) 
    WHERE manifest_number IS NOT NULL;
    PRINT 'Created index: idx_manifest';
END
GO

-- Table: review_queue
-- Stores pages that require manual review
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'review_queue')
BEGIN
    CREATE TABLE review_queue (
        review_id INT PRIMARY KEY IDENTITY(1,1),
        page_id VARCHAR(255),
        reason VARCHAR(100),
        severity VARCHAR(20),
        file_path VARCHAR(500),
        page_num INT,
        detected_fields NVARCHAR(MAX),
        suggested_fixes NVARCHAR(MAX),
        resolved BIT DEFAULT 0,
        resolved_by VARCHAR(100),
        resolved_at DATETIME,
        created_at DATETIME DEFAULT GETDATE()
    );
    PRINT 'Created table: review_queue';
END
GO

-- Table: processing_runs
-- Audit ledger for batch processing runs
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'processing_runs')
BEGIN
    CREATE TABLE processing_runs (
        run_id INT PRIMARY KEY IDENTITY(1,1),
        request_guid VARCHAR(50) UNIQUE,
        started_at DATETIME,
        completed_at DATETIME,
        files_count INT,
        pages_count INT,
        ok_count INT,
        error_count INT,
        review_count INT,
        processed_by VARCHAR(100),
        status VARCHAR(20)
    );
    PRINT 'Created table: processing_runs';
END
GO

PRINT 'Database schema setup complete!';
"""


def create_database_schema(db: DatabaseConnection) -> None:
    """Create all required database tables and indexes.
    
    Args:
        db: DatabaseConnection instance
    """
    logging.info("Creating database schema...")
    
    try:
        db.execute_script(SCHEMA_SQL)
        logging.info("Database schema created successfully")
    except Exception as e:
        logging.error(f"Failed to create database schema: {e}")
        raise


def drop_all_tables(db: DatabaseConnection) -> None:
    """Drop all tables (CAUTION: destroys all data).
    
    Args:
        db: DatabaseConnection instance
    """
    logging.warning("Dropping all tables - THIS WILL DESTROY ALL DATA")
    
    drop_sql = """
    -- Drop in reverse order of dependencies
    IF OBJECT_ID('truck_tickets', 'U') IS NOT NULL DROP TABLE truck_tickets;
    IF OBJECT_ID('review_queue', 'U') IS NOT NULL DROP TABLE review_queue;
    IF OBJECT_ID('processing_runs', 'U') IS NOT NULL DROP TABLE processing_runs;
    IF OBJECT_ID('sources', 'U') IS NOT NULL DROP TABLE sources;
    IF OBJECT_ID('destinations', 'U') IS NOT NULL DROP TABLE destinations;
    IF OBJECT_ID('vendors', 'U') IS NOT NULL DROP TABLE vendors;
    IF OBJECT_ID('materials', 'U') IS NOT NULL DROP TABLE materials;
    IF OBJECT_ID('ticket_types', 'U') IS NOT NULL DROP TABLE ticket_types;
    IF OBJECT_ID('jobs', 'U') IS NOT NULL DROP TABLE jobs;
    
    PRINT 'All tables dropped';
    """
    
    try:
        db.execute_script(drop_sql)
        logging.info("All tables dropped successfully")
    except Exception as e:
        logging.error(f"Failed to drop tables: {e}")
        raise


def seed_reference_data(db: DatabaseConnection, job_code: str = "24-105") -> None:
    """Seed reference data for initial testing.
    
    Args:
        db: DatabaseConnection instance
        job_code: Job code to create (default: 24-105)
    """
    logging.info("Seeding reference data...")
    
    seed_sql = f"""
    -- Seed Job
    IF NOT EXISTS (SELECT * FROM jobs WHERE job_code = '{job_code}')
    BEGIN
        INSERT INTO jobs (job_code, job_name, start_date) 
        VALUES ('{job_code}', 'Construction Site Material Tracking', '2024-01-01');
        PRINT 'Seeded job: {job_code}';
    END
    GO
    
    -- Seed Materials
    IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'CLASS_2_CONTAMINATED')
        INSERT INTO materials (material_name, material_class, requires_manifest) 
        VALUES ('CLASS_2_CONTAMINATED', 'CONTAMINATED', 1);
    
    IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'NON_CONTAMINATED')
        INSERT INTO materials (material_name, material_class, requires_manifest) 
        VALUES ('NON_CONTAMINATED', 'CLEAN', 0);
    
    IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'SPOILS')
        INSERT INTO materials (material_name, material_class, requires_manifest) 
        VALUES ('SPOILS', 'WASTE', 0);
    
    -- Import materials
    IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'ROCK')
        INSERT INTO materials (material_name, material_class) VALUES ('ROCK', 'IMPORT');
    IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'FLEXBASE')
        INSERT INTO materials (material_name, material_class) VALUES ('FLEXBASE', 'IMPORT');
    IF NOT EXISTS (SELECT * FROM materials WHERE material_name = 'ASPHALT')
        INSERT INTO materials (material_name, material_class) VALUES ('ASPHALT', 'IMPORT');
    
    PRINT 'Seeded materials';
    GO
    
    -- Seed Sources
    DECLARE @job_id INT = (SELECT job_id FROM jobs WHERE job_code = '{job_code}');
    
    IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'PODIUM')
        INSERT INTO sources (source_name, job_id) VALUES ('PODIUM', @job_id);
    IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'PIER_EX')
        INSERT INTO sources (source_name, job_id) VALUES ('PIER_EX', @job_id);
    IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'MSE_WALL')
        INSERT INTO sources (source_name, job_id) VALUES ('MSE_WALL', @job_id);
    IF NOT EXISTS (SELECT * FROM sources WHERE source_name = 'SPG')
        INSERT INTO sources (source_name, job_id) VALUES ('SPG', @job_id);
    
    PRINT 'Seeded sources';
    GO
    
    -- Seed Destinations
    IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'WASTE_MANAGEMENT_LEWISVILLE')
        INSERT INTO destinations (destination_name, facility_type, requires_manifest) 
        VALUES ('WASTE_MANAGEMENT_LEWISVILLE', 'DISPOSAL', 1);
    
    IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'LDI_YARD')
        INSERT INTO destinations (destination_name, facility_type) 
        VALUES ('LDI_YARD', 'DISPOSAL');
    
    IF NOT EXISTS (SELECT * FROM destinations WHERE destination_name = 'POST_OAK_PIT')
        INSERT INTO destinations (destination_name, facility_type) 
        VALUES ('POST_OAK_PIT', 'REUSE');
    
    PRINT 'Seeded destinations';
    GO
    
    -- Seed Vendors
    IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'WASTE_MANAGEMENT_LEWISVILLE')
        INSERT INTO vendors (vendor_name, vendor_code) 
        VALUES ('WASTE_MANAGEMENT_LEWISVILLE', 'WM');
    
    IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'LDI_YARD')
        INSERT INTO vendors (vendor_name) VALUES ('LDI_YARD');
    
    IF NOT EXISTS (SELECT * FROM vendors WHERE vendor_name = 'POST_OAK_PIT')
        INSERT INTO vendors (vendor_name) VALUES ('POST_OAK_PIT');
    
    PRINT 'Seeded vendors';
    GO
    
    PRINT 'Reference data seeding complete!';
    """
    
    try:
        db.execute_script(seed_sql)
        logging.info("Reference data seeded successfully")
    except Exception as e:
        logging.error(f"Failed to seed reference data: {e}")
        raise


if __name__ == "__main__":
    # Example usage
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Get connection from environment or use defaults
    try:
        db = DatabaseConnection.from_env()
    except ValueError:
        print("Using default connection (localhost)")
        db = DatabaseConnection(server="localhost")
    
    if "--test" in sys.argv:
        if db.test_connection():
            print("✓ Database connection successful")
        else:
            print("✗ Database connection failed")
            sys.exit(1)
    
    elif "--drop" in sys.argv:
        confirm = input("WARNING: This will DROP ALL TABLES. Type 'yes' to confirm: ")
        if confirm.lower() == "yes":
            drop_all_tables(db)
            print("✓ All tables dropped")
        else:
            print("Cancelled")
    
    elif "--seed" in sys.argv:
        seed_reference_data(db)
        print("✓ Reference data seeded")
    
    else:
        # Default: create schema
        create_database_schema(db)
        print("✓ Database schema created")
        
        # Offer to seed data
        seed = input("Seed reference data? (y/n): ")
        if seed.lower() == 'y':
            seed_reference_data(db)
            print("✓ Reference data seeded")
    
    db.close()
