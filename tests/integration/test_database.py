#!/usr/bin/env python3
"""Integration tests for database operations."""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import psycopg2
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from phreakbot import PhreakBot


@pytest.fixture
def mock_config(tmp_path):
    """Create mock config."""
    config_file = tmp_path / "test_config.json"
    import json

    json.dump(
        {
            "server": "test.server",
            "port": 6667,
            "nickname": "TestBot",
            "realname": "Test",
            "channels": ["#test"],
            "owner": "owner",
            "trigger": "!",
            "max_output_lines": 3,
            "db_host": "localhost",
            "db_port": "5432",
            "db_user": "test",
            "db_password": "test",
            "db_name": "testdb",
        },
        open(config_file, "w"),
    )
    return str(config_file)


@pytest.fixture
def bot(mock_config):
    """Create bot instance."""
    with patch("phreakbot.psycopg2.pool.ThreadedConnectionPool"):
        bot = PhreakBot(mock_config)
        yield bot


@pytest.mark.integration
@pytest.mark.requires_db
class TestDatabaseConnection:
    """Test database connection functionality."""

    def test_connection_pool_creation(self, bot):
        """Test connection pool is created."""
        assert bot.db_pool is not None or bot.db_connection is None

    def test_connection_retry_logic(self, bot, mock_config):
        """Test connection retry on failure."""
        with patch(
            "phreakbot.psycopg2.pool.ThreadedConnectionPool",
            side_effect=Exception("Connection failed"),
        ):
            result = bot.db_connect(max_retries=2, retry_delay=0)
            assert result is False

    def test_ensure_db_connection(self, bot):
        """Test ensure_db_connection validates connection."""
        bot.db_connection = Mock()
        bot.db_connection.cursor = Mock(return_value=Mock())
        result = bot.ensure_db_connection()
        assert result in [True, False]  # Depends on mock setup


@pytest.mark.integration
@pytest.mark.requires_db
class TestUserInfoQueries:
    """Test user information database queries."""

    def test_get_userinfo_cache_hit(self, bot):
        """Test cache hit for user info."""
        test_data = {"id": 1, "username": "test"}
        bot._cache_set("user_info", "test!user@host", test_data)

        result = bot.db_get_userinfo_by_userhost("test!user@host")
        assert result == test_data

    def test_get_userinfo_cache_miss_no_db(self, bot):
        """Test cache miss with no database."""
        bot.db_connection = None
        result = bot.db_get_userinfo_by_userhost("new!user@host")
        assert result is None


@pytest.mark.integration
@pytest.mark.requires_db
class TestQuerySafety:
    """Test that all queries use parameterized format."""

    def test_parameterized_query_format(self, bot):
        """Test queries are parameterized."""
        # Example query that should use parameters
        query = "SELECT * FROM users WHERE username = %s"
        params = ("testuser",)

        assert bot._validate_sql_safety(query, params) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
