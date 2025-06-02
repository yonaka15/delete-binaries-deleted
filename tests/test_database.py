"""
Tests for database module.
"""

import pytest
from unittest.mock import patch, MagicMock
from delete_binaries_deleted.database import DatabaseConfig, DatabaseManager


class TestDatabaseConfig:
    """Test DatabaseConfig class."""
    
    @patch.dict('os.environ', {
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'testdb',
        'DB_USER': 'testuser',
        'DB_PASSWORD': 'testpass'
    })
    def test_valid_config(self):
        """Test valid database configuration."""
        config = DatabaseConfig()
        assert config.host == 'localhost'
        assert config.port == 5432
        assert config.database == 'testdb'
        assert config.user == 'testuser'
        assert config.password == 'testpass'
    
    @patch.dict('os.environ', {}, clear=True)
    def test_missing_required_vars(self):
        """Test missing required environment variables."""
        with pytest.raises(ValueError, match="Missing required environment variables"):
            DatabaseConfig()
    
    @patch.dict('os.environ', {
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'testdb',
        'DB_USER': 'testuser',
        'DB_PASSWORD': 'testpass'
    })
    def test_connection_string(self):
        """Test connection string generation."""
        config = DatabaseConfig()
        expected = "host=localhost port=5432 dbname=testdb user=testuser password=testpass"
        assert config.connection_string == expected


class TestDatabaseManager:
    """Test DatabaseManager class."""
    
    @patch('delete_binaries_deleted.database.psycopg2.connect')
    def test_get_connection_success(self, mock_connect):
        """Test successful database connection."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        
        config = MagicMock()
        config.connection_string = "test_connection_string"
        
        db_manager = DatabaseManager(config)
        
        with db_manager.get_connection() as conn:
            assert conn == mock_conn
        
        mock_connect.assert_called_once_with("test_connection_string")
        mock_conn.close.assert_called_once()
    
    @patch('delete_binaries_deleted.database.psycopg2.connect')
    def test_test_connection_success(self, mock_connect):
        """Test successful connection test."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        config = MagicMock()
        db_manager = DatabaseManager(config)
        
        result = db_manager.test_connection()
        assert result is True
    
    @patch('delete_binaries_deleted.database.psycopg2.connect')
    def test_count_binaries_deleted_records(self, mock_connect):
        """Test counting records in Binaries_deleted table."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [100]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        config = MagicMock()
        db_manager = DatabaseManager(config)
        
        count = db_manager.count_binaries_deleted_records()
        assert count == 100
        
        mock_cursor.execute.assert_called_once_with('SELECT COUNT(*) FROM public."Binaries_deleted"')
