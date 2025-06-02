"""
Alternative database module using only standard library (no python-dotenv).
"""

import os
import logging
from typing import Optional, Tuple
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration from environment variables (standard library only)."""
    
    def __init__(self) -> None:
        # Manual .env file loading if python-dotenv is not available
        self._load_env_file()
        
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
    
    def _load_env_file(self, env_file: str = ".env") -> None:
        """Manually load .env file using standard library only."""
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
        except FileNotFoundError:
            logger.warning(f"Environment file {env_file} not found")
        except Exception as e:
            logger.warning(f"Error loading environment file: {e}")
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"host={self.host} port={self.port} dbname={self.database} user={self.user} password={self.password}"


# 残りのDatabaseManagerクラスは同じなので、元のファイルをそのまま使用
