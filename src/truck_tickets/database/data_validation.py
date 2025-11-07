"""Data validation and cleanup utilities for truck ticket database.

Provides validation rules, data quality checks, and cleanup operations
to maintain data integrity and consistency.
"""

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any

from .connection import DatabaseConnection


class DataValidator:
    """Validates truck ticket data for quality and consistency."""

    def __init__(self, db: DatabaseConnection):
        """Initialize data validator.

        Args:
            db: Database connection instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.errors = []
        self.warnings = []

    def validate_ticket_number(self, ticket_number: str) -> tuple[bool, str | None]:
        """Validate ticket number format.

        Args:
            ticket_number: Ticket number to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not ticket_number:
            return False, "Ticket number is required"

        # Remove whitespace
        ticket_number = str(ticket_number).strip()

        # Check minimum length
        if len(ticket_number) < 3:
            return False, "Ticket number too short (minimum 3 characters)"

        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r"^[A-Za-z0-9\-_\s]+$", ticket_number):
            return False, "Ticket number contains invalid characters"

        # Check for reasonable maximum length
        if len(ticket_number) > 50:
            return False, "Ticket number too long (maximum 50 characters)"

        return True, None

    def validate_quantity(
        self, quantity: Any, unit: str | None = None
    ) -> tuple[bool, str | None]:
        """Validate quantity and unit.

        Args:
            quantity: Quantity value to validate
            unit: Quantity unit

        Returns:
            Tuple of (is_valid, error_message)
        """
        if quantity is None:
            return True, None  # Quantity is optional

        try:
            # Convert to decimal
            quantity_float = float(quantity)

            # Check for reasonable values
            if quantity_float < 0:
                return False, "Quantity cannot be negative"

            if quantity_float > 999999.99:
                return False, "Quantity too large (maximum 999,999.99)"

            # Check decimal precision
            if abs(quantity_float * 100 - round(quantity_float * 100)) > 0.01:
                return False, "Quantity has too many decimal places (maximum 2)"

            # Validate unit if provided
            if unit:
                valid_units = ["TONS", "CY", "LBS", "GALLONS", "LOADS", "UNITS"]
                if unit.upper() not in valid_units:
                    self.warnings.append(f"Unusual quantity unit: {unit}")

        except (ValueError, TypeError):
            return False, "Quantity must be a valid number"

        return True, None

    def validate_date(self, ticket_date: Any) -> tuple[bool, str | None]:
        """Validate ticket date.

        Args:
            ticket_date: Date to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if ticket_date is None:
            return False, "Ticket date is required"

        try:
            if isinstance(ticket_date, str):
                # Try to parse common date formats
                date_formats = [
                    "%Y-%m-%d",
                    "%m/%d/%Y",
                    "%m-%d-%Y",
                    "%Y/%m/%d",
                ]

                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(ticket_date.strip(), fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return False, f"Invalid date format: {ticket_date}"

            elif isinstance(ticket_date, date):
                parsed_date = ticket_date

            else:
                return False, "Date must be a date object or string"

            # Check reasonable date range
            if parsed_date < date(2020, 1, 1):
                return False, "Date too old (before 2020)"

            if parsed_date > date.today() + timedelta(days=30):
                return False, "Date too far in future"

        except Exception as e:
            return False, f"Invalid date: {e}"

        return True, None

    def validate_reference_data(
        self, table: str, id_field: str, id_value: int
    ) -> tuple[bool, str | None]:
        """Validate that reference data exists.

        Args:
            table: Table name to check
            id_field: ID field name
            id_value: ID value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if id_value is None:
            return True, None  # Optional foreign key

        try:
            check_sql = f"SELECT COUNT(*) as count FROM {table} WHERE {id_field} = ?"
            result = self.db.execute_query(check_sql, [id_value])

            if result and result[0]["count"] > 0:
                return True, None
            else:
                return False, f"Invalid {table[:-1]} ID: {id_value}"

        except Exception as e:
            return False, f"Error validating {table} reference: {e}"

    def validate_ticket_data(self, ticket_data: dict) -> dict:
        """Validate complete truck ticket data.

        Args:
            ticket_data: Dictionary containing ticket data

        Returns:
            Dictionary with validation results
        """
        self.errors.clear()
        self.warnings.clear()

        # Validate each field
        validations = [
            ("ticket_number", self.validate_ticket_number),
            ("ticket_date", self.validate_date),
            (
                "quantity",
                lambda q: self.validate_quantity(q, ticket_data.get("quantity_unit")),
            ),
            ("job_id", lambda jid: self.validate_reference_data("jobs", "job_id", jid)),
            (
                "material_id",
                lambda mid: self.validate_reference_data(
                    "materials", "material_id", mid
                ),
            ),
            (
                "source_id",
                lambda sid: self.validate_reference_data("sources", "source_id", sid),
            ),
            (
                "destination_id",
                lambda did: self.validate_reference_data(
                    "destinations", "destination_id", did
                ),
            ),
            (
                "vendor_id",
                lambda vid: self.validate_reference_data("vendors", "vendor_id", vid),
            ),
            (
                "ticket_type_id",
                lambda ttid: self.validate_reference_data(
                    "ticket_types", "ticket_type_id", ttid
                ),
            ),
        ]

        for field, validator in validations:
            value = ticket_data.get(field)
            is_valid, error = validator(value)

            if not is_valid:
                self.errors.append(f"{field}: {error}")

        # Cross-field validations
        self._validate_cross_fields(ticket_data)

        return {
            "is_valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def _validate_cross_fields(self, ticket_data: dict) -> None:
        """Validate cross-field dependencies."""

        # Check that EXPORT tickets have destinations
        if ticket_data.get("ticket_type_id"):
            # Get ticket type name
            type_sql = "SELECT type_name FROM ticket_types WHERE ticket_type_id = ?"
            type_result = self.db.execute_query(
                type_sql, [ticket_data["ticket_type_id"]]
            )

            if type_result and type_result[0]["type_name"] == "EXPORT":
                if not ticket_data.get("destination_id"):
                    self.errors.append("EXPORT tickets must have a destination")

        # Check that IMPORT tickets have reasonable quantities
        if ticket_data.get("quantity") and ticket_data.get("ticket_type_id"):
            type_sql = "SELECT type_name FROM ticket_types WHERE ticket_type_id = ?"
            type_result = self.db.execute_query(
                type_sql, [ticket_data["ticket_type_id"]]
            )

            if type_result and type_result[0]["type_name"] == "IMPORT":
                try:
                    quantity = float(ticket_data["quantity"])
                    if quantity > 100:  # Unusually large import
                        self.warnings.append("Large quantity for IMPORT ticket")
                except (ValueError, TypeError):
                    pass


class DataCleaner:
    """Cleans and standardizes truck ticket data."""

    def __init__(self, db: DatabaseConnection):
        """Initialize data cleaner.

        Args:
            db: Database connection instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

    def clean_ticket_number(self, ticket_number: str) -> str:
        """Clean and standardize ticket number.

        Args:
            ticket_number: Raw ticket number

        Returns:
            Cleaned ticket number
        """
        if not ticket_number:
            return ""

        # Remove extra whitespace
        cleaned = str(ticket_number).strip()

        # Standardize separators
        cleaned = re.sub(r"[._\s]+", "-", cleaned)

        # Remove multiple consecutive hyphens
        cleaned = re.sub(r"-+", "-", cleaned)

        # Remove leading/trailing hyphens
        cleaned = cleaned.strip("-")

        # Convert to uppercase
        cleaned = cleaned.upper()

        return cleaned

    def clean_vendor_name(self, vendor_name: str) -> str:
        """Clean and standardize vendor name.

        Args:
            vendor_name: Raw vendor name

        Returns:
            Cleaned vendor name
        """
        if not vendor_name:
            return ""

        # Remove extra whitespace
        cleaned = str(vendor_name).strip()

        # Standardize common variations
        replacements = {
            r"\bWM\b": "WASTE_MANAGEMENT",
            r"\bWASTE\s+MANAGEMENT\b": "WASTE_MANAGEMENT",
            r"\bREPUBLIC\s+SERVICES?\b": "REPUBLIC_SERVICES",
            r"\bLDI\b": "LDI_YARD",
            r"\bPOST\s+OAK\b": "POST_OAK_PIT",
        }

        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        return cleaned

    def clean_material_name(self, material_name: str) -> str:
        """Clean and standardize material name.

        Args:
            material_name: Raw material name

        Returns:
            Cleaned material name
        """
        if not material_name:
            return ""

        # Remove extra whitespace
        cleaned = str(material_name).strip().upper()

        # Standardize common variations
        replacements = {
            r"CLASS\s*2": "CLASS_2",
            r"CLASS\s*3": "CLASS_3",
            r"NON\s*CONTAMINATED": "NON_CONTAMINATED",
            r"CLEAN\s+FILL": "CLEAN_FILL",
            r"FLEX\s*BASE": "FLEXBASE",
            r"3\s*X\s*5": "3X5",
        }

        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned)

        return cleaned

    def standardize_quantity_unit(self, unit: str) -> str:
        """Standardize quantity unit.

        Args:
            unit: Raw quantity unit

        Returns:
            Standardized unit
        """
        if not unit:
            return ""

        unit = str(unit).strip().upper()

        # Common unit mappings
        unit_mappings = {
            "T": "TONS",
            "TON": "TONS",
            "TONS": "TONS",
            "CY": "CY",
            "CUBIC YARD": "CY",
            "CUBIC YARDS": "CY",
            "LBS": "LBS",
            "POUNDS": "LBS",
            "GAL": "GALLONS",
            "GALLONS": "GALLONS",
            "LOAD": "LOADS",
            "LOADS": "LOADS",
            "UNIT": "UNITS",
            "UNITS": "UNITS",
        }

        return unit_mappings.get(unit, unit)

    def clean_ticket_data(self, ticket_data: dict) -> dict:
        """Clean complete ticket data.

        Args:
            ticket_data: Raw ticket data

        Returns:
            Cleaned ticket data
        """
        cleaned = ticket_data.copy()

        # Clean each field
        if "ticket_number" in cleaned:
            cleaned["ticket_number"] = self.clean_ticket_number(
                cleaned["ticket_number"]
            )

        if "quantity_unit" in cleaned:
            cleaned["quantity_unit"] = self.standardize_quantity_unit(
                cleaned["quantity_unit"]
            )

        # Note: Material, vendor, source, destination names would be cleaned
        # before lookup to get their respective IDs

        return cleaned


class DataQualityReporter:
    """Generates data quality reports for the truck ticket database."""

    def __init__(self, db: DatabaseConnection):
        """Initialize data quality reporter.

        Args:
            db: Database connection instance
        """
        self.db = db
        self.logger = logging.getLogger(__name__)

    def generate_quality_report(self) -> dict:
        """Generate comprehensive data quality report.

        Returns:
            Dictionary containing quality metrics and issues
        """
        report = {
            "summary": self._get_summary_stats(),
            "completeness": self._check_completeness(),
            "consistency": self._check_consistency(),
            "duplicates": self._check_duplicates(),
            "outliers": self._check_outliers(),
            "recommendations": [],
        }

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)

        return report

    def _get_summary_stats(self) -> dict:
        """Get summary statistics."""
        sql = """
        SELECT
            COUNT(*) as total_tickets,
            COUNT(DISTINCT ticket_number) as unique_tickets,
            MIN(ticket_date) as earliest_date,
            MAX(ticket_date) as latest_date,
            AVG(quantity) as avg_quantity,
            COUNT(DISTINCT job_id) as unique_jobs,
            COUNT(DISTINCT material_id) as unique_materials,
            COUNT(DISTINCT vendor_id) as unique_vendors
        FROM truck_tickets
        WHERE ticket_date IS NOT NULL
        """

        result = self.db.execute_query(sql)
        return dict(result[0]) if result else {}

    def _check_completeness(self) -> dict:
        """Check data completeness."""
        sql = """
        SELECT
            COUNT(*) as total,
            COUNT(ticket_number) as has_ticket_number,
            COUNT(ticket_date) as has_date,
            COUNT(quantity) as has_quantity,
            COUNT(job_id) as has_job,
            COUNT(material_id) as has_material,
            COUNT(vendor_id) as has_vendor,
            COUNT(source_id) as has_source,
            COUNT(destination_id) as has_destination
        FROM truck_tickets
        """

        result = self.db.execute_query(sql)

        if result:
            total = result[0]["total"]
            completeness = {}

            for field, count in result[0].items():
                if field != "total":
                    completeness[field] = {
                        "count": count,
                        "percentage": (count / total * 100) if total > 0 else 0,
                    }

            return completeness

        return {}

    def _check_consistency(self) -> list[dict]:
        """Check data consistency issues."""
        issues = []

        # Check for tickets with invalid foreign keys
        fk_checks = [
            ("job_id", "jobs", "job_id"),
            ("material_id", "materials", "material_id"),
            ("vendor_id", "vendors", "vendor_id"),
            ("source_id", "sources", "source_id"),
            ("destination_id", "destinations", "destination_id"),
            ("ticket_type_id", "ticket_types", "ticket_type_id"),
        ]

        for field, table, pk in fk_checks:
            sql = f"""
            SELECT COUNT(*) as invalid_count
            FROM truck_tickets t
            LEFT JOIN {table} r ON t.{field} = r.{pk}
            WHERE t.{field} IS NOT NULL AND r.{pk} IS NULL
            """

            result = self.db.execute_query(sql)
            if result and result[0]["invalid_count"] > 0:
                issues.append(
                    {
                        "type": "invalid_foreign_key",
                        "field": field,
                        "count": result[0]["invalid_count"],
                    }
                )

        return issues

    def _check_duplicates(self) -> list[dict]:
        """Check for duplicate tickets."""
        sql = """
        SELECT ticket_number, vendor_id, COUNT(*) as duplicate_count
        FROM truck_tickets
        WHERE ticket_number IS NOT NULL AND vendor_id IS NOT NULL
        GROUP BY ticket_number, vendor_id
        HAVING COUNT(*) > 1
        """

        result = self.db.execute_query(sql)
        return list(result) if result else []

    def _check_outliers(self) -> list[dict]:
        """Check for data outliers."""
        outliers = []

        # Check for unusual quantities
        sql = """
        SELECT
            'quantity' as field,
            COUNT(*) as count,
            MIN(quantity) as min_value,
            MAX(quantity) as max_value,
            AVG(quantity) as avg_value
        FROM truck_tickets
        WHERE quantity IS NOT NULL
        HAVING MAX(quantity) > 1000 OR MIN(quantity) < 0
        """

        result = self.db.execute_query(sql)
        if result:
            outliers.extend([dict(row) for row in result])

        # Check for dates outside expected range
        sql = """
        SELECT
            'date' as field,
            COUNT(*) as count,
            MIN(ticket_date) as min_value,
            MAX(ticket_date) as max_value
        FROM truck_tickets
        WHERE ticket_date < '2020-01-01' OR ticket_date > DATEADD(day, 30, GETDATE())
        """

        result = self.db.execute_query(sql)
        if result:
            outliers.extend([dict(row) for row in result])

        return outliers

    def _generate_recommendations(self, report: dict) -> list[str]:
        """Generate data quality recommendations."""
        recommendations = []

        # Check completeness
        completeness = report.get("completeness", {})
        for field, stats in completeness.items():
            if stats["percentage"] < 95:
                recommendations.append(
                    f"Improve {field} completeness (currently {stats['percentage']:.1f}%)"
                )

        # Check consistency
        consistency_issues = report.get("consistency", [])
        if consistency_issues:
            recommendations.append("Fix invalid foreign key references")

        # Check duplicates
        duplicates = report.get("duplicates", [])
        if duplicates:
            recommendations.append("Review and resolve duplicate tickets")

        # Check outliers
        outliers = report.get("outliers", [])
        if outliers:
            recommendations.append("Review data outliers for data entry errors")

        return recommendations

    def export_quality_report(self, output_path: str) -> None:
        """Export quality report to JSON file.

        Args:
            output_path: Path to save report
        """
        import json

        report = self.generate_quality_report()

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Quality report exported to {output_path}")


# Utility functions


def validate_and_clean_ticket(ticket_data: dict, db: DatabaseConnection) -> dict:
    """Validate and clean ticket data in one operation.

    Args:
        ticket_data: Raw ticket data
        db: Database connection

    Returns:
        Dictionary with cleaned data and validation results
    """
    validator = DataValidator(db)
    cleaner = DataCleaner(db)

    # Clean data first
    cleaned_data = cleaner.clean_ticket_data(ticket_data)

    # Validate cleaned data
    validation_result = validator.validate_ticket_data(cleaned_data)

    return {"data": cleaned_data, "validation": validation_result}


def run_data_quality_check(
    db: DatabaseConnection, output_path: str | None = None
) -> dict:
    """Run complete data quality check.

    Args:
        db: Database connection
        output_path: Optional path to save report

    Returns:
        Quality report dictionary
    """
    reporter = DataQualityReporter(db)
    report = reporter.generate_quality_report()

    if output_path:
        reporter.export_quality_report(output_path)

    return report
