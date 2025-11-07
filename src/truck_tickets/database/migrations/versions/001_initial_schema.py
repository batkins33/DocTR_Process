"""Initial database schema for truck ticket system

Revision ID: 001
Revises:
Create Date: 2024-11-07 15:01:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema with all 9 tables."""

    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("job_code", sa.String(length=50), nullable=False),
        sa.Column("job_name", sa.String(length=200), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("job_id"),
        sa.UniqueConstraint("job_code"),
    )
    op.create_index(op.f("ix_jobs_job_code"), "jobs", ["job_code"], unique=False)

    # Create materials table
    op.create_table(
        "materials",
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("material_name", sa.String(length=100), nullable=False),
        sa.Column("material_class", sa.String(length=50), nullable=True),
        sa.Column("requires_manifest", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("material_id"),
        sa.UniqueConstraint("material_name"),
    )
    op.create_index(
        op.f("ix_materials_material_name"), "materials", ["material_name"], unique=False
    )

    # Create destinations table
    op.create_table(
        "destinations",
        sa.Column("destination_id", sa.Integer(), nullable=False),
        sa.Column("destination_name", sa.String(length=200), nullable=False),
        sa.Column("facility_type", sa.String(length=100), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("requires_manifest", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("destination_id"),
        sa.UniqueConstraint("destination_name"),
    )
    op.create_index(
        op.f("ix_destinations_destination_name"),
        "destinations",
        ["destination_name"],
        unique=False,
    )

    # Create vendors table
    op.create_table(
        "vendors",
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("vendor_name", sa.String(length=200), nullable=False),
        sa.Column("vendor_code", sa.String(length=50), nullable=True),
        sa.Column("vendor_type", sa.String(length=100), nullable=True),
        sa.Column("contact_info", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("vendor_id"),
        sa.UniqueConstraint("vendor_name"),
    )
    op.create_index(
        op.f("ix_vendors_vendor_name"), "vendors", ["vendor_name"], unique=False
    )

    # Create ticket_types table
    op.create_table(
        "ticket_types",
        sa.Column("ticket_type_id", sa.Integer(), nullable=False),
        sa.Column("type_name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("ticket_type_id"),
        sa.UniqueConstraint("type_name"),
    )
    op.create_index(
        op.f("ix_ticket_types_type_name"), "ticket_types", ["type_name"], unique=False
    )

    # Create sources table
    op.create_table(
        "sources",
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=200), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("source_type", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.job_id"],
        ),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint("source_name"),
    )
    op.create_index(
        op.f("ix_sources_source_name"), "sources", ["source_name"], unique=False
    )
    op.create_index("ix_sources_job_id", "sources", ["job_id"], unique=False)

    # Create truck_tickets table (main table)
    op.create_table(
        "truck_tickets",
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("ticket_number", sa.String(length=100), nullable=False),
        sa.Column("ticket_date", sa.Date(), nullable=True),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("quantity_unit", sa.String(length=20), nullable=True),
        sa.Column("truck_number", sa.String(length=50), nullable=True),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("material_id", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("destination_id", sa.Integer(), nullable=True),
        sa.Column("vendor_id", sa.Integer(), nullable=True),
        sa.Column("ticket_type_id", sa.Integer(), nullable=True),
        sa.Column("manifest_number", sa.String(length=100), nullable=True),
        sa.Column("processed_by", sa.String(length=100), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("review_required", sa.Boolean(), nullable=True),
        sa.Column("review_reason", sa.String(length=200), nullable=True),
        sa.Column("duplicate_of", sa.Integer(), nullable=True),
        sa.Column("file_id", sa.String(length=100), nullable=True),
        sa.Column("file_page", sa.Integer(), nullable=True),
        sa.Column("file_hash", sa.String(length=64), nullable=True),
        sa.Column("request_guid", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["destination_id"],
            ["destinations.destination_id"],
        ),
        sa.ForeignKeyConstraint(
            ["duplicate_of"],
            ["truck_tickets.ticket_id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.job_id"],
        ),
        sa.ForeignKeyConstraint(
            ["material_id"],
            ["materials.material_id"],
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.source_id"],
        ),
        sa.ForeignKeyConstraint(
            ["ticket_type_id"],
            ["ticket_types.ticket_type_id"],
        ),
        sa.ForeignKeyConstraint(
            ["vendor_id"],
            ["vendors.vendor_id"],
        ),
        sa.PrimaryKeyConstraint("ticket_id"),
        sa.UniqueConstraint("ticket_number", "vendor_id", name="uq_ticket_vendor"),
    )
    op.create_index(
        "ix_truck_tickets_ticket_date", "truck_tickets", ["ticket_date"], unique=False
    )
    op.create_index(
        "ix_truck_tickets_job_date",
        "truck_tickets",
        ["ticket_date", "job_id"],
        unique=False,
    )
    op.create_index(
        "ix_truck_tickets_manifest_number",
        "truck_tickets",
        ["manifest_number"],
        unique=False,
    )
    op.create_index(
        "ix_truck_tickets_request_guid", "truck_tickets", ["request_guid"], unique=False
    )
    op.create_index(
        "ix_truck_tickets_file_hash", "truck_tickets", ["file_hash"], unique=False
    )
    op.create_index(
        op.f("ix_truck_tickets_ticket_number"),
        "truck_tickets",
        ["ticket_number"],
        unique=False,
    )

    # Create review_queue table
    op.create_table(
        "review_queue",
        sa.Column("review_id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(length=200), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("page_num", sa.Integer(), nullable=True),
        sa.Column("detected_fields", sa.Text(), nullable=True),
        sa.Column("suggested_fixes", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=True),
        sa.Column("resolved_by", sa.String(length=100), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["truck_tickets.ticket_id"],
        ),
        sa.PrimaryKeyConstraint("review_id"),
    )
    op.create_index(
        "ix_review_queue_ticket_id", "review_queue", ["ticket_id"], unique=False
    )

    # Create processing_runs table
    op.create_table(
        "processing_runs",
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("request_guid", sa.String(length=36), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("files_count", sa.Integer(), nullable=True),
        sa.Column("pages_count", sa.Integer(), nullable=True),
        sa.Column("tickets_created", sa.Integer(), nullable=True),
        sa.Column("tickets_updated", sa.Integer(), nullable=True),
        sa.Column("duplicates_found", sa.Integer(), nullable=True),
        sa.Column("review_queue_count", sa.Integer(), nullable=True),
        sa.Column("error_count", sa.Integer(), nullable=True),
        sa.Column("processed_by", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("config_snapshot", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("run_id"),
        sa.UniqueConstraint("request_guid"),
    )
    op.create_index(
        op.f("ix_processing_runs_request_guid"),
        "processing_runs",
        ["request_guid"],
        unique=False,
    )


def downgrade() -> None:
    """Drop all tables in reverse order of creation."""

    # Drop tables in reverse order to handle foreign key constraints
    op.drop_index(op.f("ix_processing_runs_request_guid"), table_name="processing_runs")
    op.drop_table("processing_runs")

    op.drop_index("ix_review_queue_ticket_id", table_name="review_queue")
    op.drop_table("review_queue")

    op.drop_index(op.f("ix_truck_tickets_ticket_number"), table_name="truck_tickets")
    op.drop_index("ix_truck_tickets_file_hash", table_name="truck_tickets")
    op.drop_index("ix_truck_tickets_request_guid", table_name="truck_tickets")
    op.drop_index("ix_truck_tickets_manifest_number", table_name="truck_tickets")
    op.drop_index("ix_truck_tickets_job_date", table_name="truck_tickets")
    op.drop_index("ix_truck_tickets_ticket_date", table_name="truck_tickets")
    op.drop_table("truck_tickets")

    op.drop_index("ix_sources_job_id", table_name="sources")
    op.drop_index(op.f("ix_sources_source_name"), table_name="sources")
    op.drop_table("sources")

    op.drop_index(op.f("ix_ticket_types_type_name"), table_name="ticket_types")
    op.drop_table("ticket_types")

    op.drop_index(op.f("ix_vendors_vendor_name"), table_name="vendors")
    op.drop_table("vendors")

    op.drop_index(op.f("ix_destinations_destination_name"), table_name="destinations")
    op.drop_table("destinations")

    op.drop_index(op.f("ix_materials_material_name"), table_name="materials")
    op.drop_table("materials")

    op.drop_index(op.f("ix_jobs_job_code"), table_name="jobs")
    op.drop_table("jobs")
