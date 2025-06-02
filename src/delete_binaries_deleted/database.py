"""
Database connection and operations module.
"""

import os
import logging
from typing import Optional, Tuple
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration from environment variables."""
    
    def __init__(self) -> None:
        self.host = os.getenv("DB_HOST")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        
        # Validate required environment variables
        required_vars = ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password}"


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None) -> None:
        self.config = config or DatabaseConfig()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper cleanup."""
        conn = None
        try:
            conn = psycopg2.connect(self.config.connection_string)
            logger.info("Database connection established")
            yield conn
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
                logger.info("Database connection closed")
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def count_binaries_deleted_records(self) -> int:
        """Count total records in Binaries_deleted table."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT COUNT(*) FROM public."Binaries_deleted"')
                    count = cursor.fetchone()[0]
                    logger.info(f"Total records in Binaries_deleted: {count}")
                    return count
        except Exception as e:
            logger.error(f"Error counting records: {e}")
            raise
    
    def get_binaries_deleted_batch(self, batch_size: int = 400, offset: int = 0) -> list:
        """Get a batch of records from Binaries_deleted table."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = '''
                    SELECT "BinaryId" FROM public."Binaries_deleted"
                    ORDER BY "BinaryId" ASC 
                    LIMIT %s OFFSET %s
                    '''
                    cursor.execute(query, (batch_size, offset))
                    records = cursor.fetchall()
                    logger.debug(f"Retrieved {len(records)} records (offset: {offset})")
                    return records
        except Exception as e:
            logger.error(f"Error retrieving batch: {e}")
            raise
    
    def delete_binaries_deleted_batch(self, binary_ids: list) -> int:
        """Delete a batch of records by BinaryId."""
        if not binary_ids:
            return 0
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Use parameterized query to prevent SQL injection
                    placeholders = ','.join(['%s'] * len(binary_ids))
                    query = f'DELETE FROM public."Binaries_deleted" WHERE "BinaryId" IN ({placeholders})'
                    
                    cursor.execute(query, binary_ids)
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    logger.info(f"Deleted {deleted_count} records")
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"Error deleting batch: {e}")
            raise
