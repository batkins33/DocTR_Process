"""SQL Server database connection management."""

import logging
import os
from contextlib import contextmanager
from typing import Optional

try:
    import pyodbc
except ImportError:
    pyodbc = None


class DatabaseConnection:
    """Manages SQL Server database connections."""
    
    def __init__(
        self,
        server: str,
        database: str = "TruckTicketsDB",
        driver: str = "{ODBC Driver 17 for SQL Server}",
        username: Optional[str] = None,
        password: Optional[str] = None,
        trusted_connection: bool = True,
    ):
        """Initialize database connection parameters.
        
        Args:
            server: SQL Server instance name (e.g., 'localhost' or 'SERVER\\INSTANCE')
            database: Database name (default: TruckTicketsDB)
            driver: ODBC driver name
            username: SQL Server username (if not using Windows auth)
            password: SQL Server password (if not using Windows auth)
            trusted_connection: Use Windows authentication if True
        """
        if pyodbc is None:
            raise ImportError(
                "pyodbc is required for SQL Server connectivity. "
                "Install with: pip install pyodbc"
            )
        
        self.server = server
        self.database = database
        self.driver = driver
        self.username = username
        self.password = password
        self.trusted_connection = trusted_connection
        self._connection = None
        
        logging.info(f"Database connection configured for {server}/{database}")
    
    @property
    def connection_string(self) -> str:
        """Build ODBC connection string."""
        if self.trusted_connection:
            return (
                f"DRIVER={self.driver};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"Trusted_Connection=yes;"
            )
        else:
            return (
                f"DRIVER={self.driver};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
    
    def connect(self):
        """Establish database connection."""
        if self._connection is None:
            try:
                self._connection = pyodbc.connect(
                    self.connection_string,
                    timeout=30,
                    autocommit=False
                )
                logging.info("Database connection established")
            except pyodbc.Error as e:
                logging.error(f"Failed to connect to database: {e}")
                raise
        return self._connection
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logging.info("Database connection closed")
    
    @contextmanager
    def cursor(self):
        """Context manager for database cursor.
        
        Usage:
            with db.cursor() as cur:
                cur.execute("SELECT * FROM jobs")
                rows = cur.fetchall()
        """
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Database operation failed: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_script(self, sql_script: str):
        """Execute a SQL script (multiple statements).
        
        Args:
            sql_script: SQL script with multiple statements separated by GO
        """
        # Split on GO statements
        statements = [s.strip() for s in sql_script.split('GO') if s.strip()]
        
        with self.cursor() as cur:
            for statement in statements:
                if statement:
                    cur.execute(statement)
        
        logging.info(f"Executed {len(statements)} SQL statements")
    
    def test_connection(self) -> bool:
        """Test database connectivity.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.cursor() as cur:
                cur.execute("SELECT 1")
                return True
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False
    
    @classmethod
    def from_env(cls) -> "DatabaseConnection":
        """Create connection from environment variables.
        
        Expected variables:
            TRUCK_TICKETS_DB_SERVER
            TRUCK_TICKETS_DB_NAME (optional, defaults to TruckTicketsDB)
            TRUCK_TICKETS_DB_USERNAME (optional for Windows auth)
            TRUCK_TICKETS_DB_PASSWORD (optional for Windows auth)
        """
        server = os.getenv("TRUCK_TICKETS_DB_SERVER")
        if not server:
            raise ValueError("TRUCK_TICKETS_DB_SERVER environment variable not set")
        
        database = os.getenv("TRUCK_TICKETS_DB_NAME", "TruckTicketsDB")
        username = os.getenv("TRUCK_TICKETS_DB_USERNAME")
        password = os.getenv("TRUCK_TICKETS_DB_PASSWORD")
        
        # Use Windows auth if no username/password provided
        trusted = not (username and password)
        
        return cls(
            server=server,
            database=database,
            username=username,
            password=password,
            trusted_connection=trusted,
        )
