#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for core PhreakBot functionality.

Tests security features, input sanitization, rate limiting, and core methods.
"""

import os
import sys
import time
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Add parent directory to path to import phreakbot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phreakbot import PhreakBot


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration file."""
    config_file = tmp_path / "test_config.json"
    config_data = {
        "server": "irc.test.server",
        "port": 6667,
        "nickname": "TestBot",
        "realname": "Test Bot",
        "channels": ["#test"],
        "owner": "test_owner",
        "trigger": "!",
        "max_output_lines": 3,
        "db_host": "localhost",
        "db_port": "5432",
        "db_user": "testuser",
        "db_password": "testpass",
        "db_name": "testdb",
    }

    import json

    with open(config_file, "w") as f:
        json.dump(config_data, f)

    return str(config_file)


@pytest.fixture
def bot(mock_config):
    """Create a PhreakBot instance for testing."""
    with patch("phreakbot.psycopg2.pool.ThreadedConnectionPool"):
        bot = PhreakBot(mock_config)
        bot.db_connection = Mock()
        bot.db_pool = Mock()
        yield bot


class TestInputSanitization:
    """Test input sanitization methods."""

    @pytest.mark.unit
    def test_sanitize_input_basic(self, bot):
        """Test basic input sanitization."""
        result = bot._sanitize_input("Hello World")
        assert result == "Hello World"

    @pytest.mark.unit
    def test_sanitize_input_max_length(self, bot):
        """Test input truncation to max length."""
        long_input = "A" * 1000
        result = bot._sanitize_input(long_input, max_length=100)
        assert len(result) == 100

    @pytest.mark.unit
    def test_sanitize_input_null_bytes(self, bot):
        """Test null byte removal."""
        result = bot._sanitize_input("test\x00admin")
        assert result == "testadmin"
        assert "\x00" not in result

    @pytest.mark.unit
    def test_sanitize_input_sql_injection(self, bot):
        """Test SQL injection pattern filtering."""
        dangerous_inputs = [
            "'; DROP TABLE users--",
            "test; DELETE FROM data",
            "value; UPDATE settings",
        ]

        for dangerous in dangerous_inputs:
            result = bot._sanitize_input(dangerous, allow_special_chars=False)
            assert "DROP" not in result or "--" not in result
            assert "DELETE" not in result or ";" not in result
            assert "UPDATE" not in result or ";" not in result

    @pytest.mark.unit
    def test_sanitize_input_shell_injection(self, bot):
        """Test shell injection pattern filtering."""
        result = bot._sanitize_input("test$(rm -rf /)", allow_special_chars=False)
        assert "$(" not in result

        result = bot._sanitize_input("test`whoami`", allow_special_chars=False)
        assert "`" not in result

    @pytest.mark.unit
    def test_sanitize_input_allow_special_chars(self, bot):
        """Test that special chars are preserved when allowed."""
        result = bot._sanitize_input(
            "test; SELECT * FROM users", allow_special_chars=True
        )
        assert ";" in result  # Should be preserved when allowed

    @pytest.mark.unit
    def test_sanitize_channel_name_valid(self, bot):
        """Test valid channel name sanitization."""
        result = bot._sanitize_channel_name("#test-channel_123")
        assert result == "#test-channel_123"

    @pytest.mark.unit
    def test_sanitize_channel_name_invalid_prefix(self, bot):
        """Test invalid channel prefix handling."""
        result = bot._sanitize_channel_name("test")
        assert result == "#unknown"

    @pytest.mark.unit
    def test_sanitize_channel_name_injection(self, bot):
        """Test channel name injection attempt."""
        result = bot._sanitize_channel_name("#test';DROP--")
        assert result == "#testDROP"
        assert "'" not in result
        assert ";" not in result

    @pytest.mark.unit
    def test_sanitize_channel_name_max_length(self, bot):
        """Test channel name length limit."""
        long_name = "#" + "a" * 100
        result = bot._sanitize_channel_name(long_name)
        assert len(result) <= 50

    @pytest.mark.unit
    def test_sanitize_nickname_valid(self, bot):
        """Test valid nickname sanitization."""
        result = bot._sanitize_nickname("TestUser123")
        assert result == "TestUser123"

    @pytest.mark.unit
    def test_sanitize_nickname_invalid_chars(self, bot):
        """Test removal of invalid characters from nickname."""
        result = bot._sanitize_nickname("user$(whoami)")
        assert result == "userwhoami"
        assert "$" not in result
        assert "(" not in result
        assert ")" not in result

    @pytest.mark.unit
    def test_sanitize_nickname_max_length(self, bot):
        """Test nickname length limit."""
        long_nick = "a" * 100
        result = bot._sanitize_nickname(long_nick)
        assert len(result) <= 30


class TestRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.unit
    def test_rate_limit_within_limits(self, bot):
        """Test that users within limits are allowed."""
        hostmask = "user!test@example.com"

        # Should allow first command
        assert bot._check_rate_limit(hostmask) is True

    @pytest.mark.unit
    def test_rate_limit_per_minute_exceeded(self, bot):
        """Test per-minute rate limit enforcement."""
        hostmask = "spammer!test@example.com"

        # Simulate max_commands_per_minute commands
        for i in range(bot.rate_limit["max_commands_per_minute"]):
            assert bot._check_rate_limit(hostmask) is True

        # Next command should trigger ban
        assert bot._check_rate_limit(hostmask) is False

        # User should be banned
        assert hostmask in bot.rate_limit["banned_users"]

    @pytest.mark.unit
    def test_rate_limit_per_10_seconds_exceeded(self, bot):
        """Test per-10-seconds rate limit enforcement."""
        hostmask = "rapidfire!test@example.com"

        # Simulate commands in quick succession
        for i in range(bot.rate_limit["max_commands_per_10_seconds"]):
            assert bot._check_rate_limit(hostmask) is True

        # Next command should be rejected
        assert bot._check_rate_limit(hostmask) is False

        # But should not be banned yet (only rejected)
        # Wait a bit and try again
        time.sleep(1)
        # Should still be limited

    @pytest.mark.unit
    def test_rate_limit_global_exceeded(self, bot):
        """Test global rate limit enforcement."""
        # Simulate multiple users hitting global limit
        for i in range(bot.rate_limit["max_global_commands_per_second"]):
            hostmask = f"user{i}!test@example.com"
            assert bot._check_rate_limit(hostmask) is True

        # Next user should be rejected due to global limit
        new_user = "newuser!test@example.com"
        assert bot._check_rate_limit(new_user) is False

    @pytest.mark.unit
    def test_rate_limit_ban_expiry(self, bot):
        """Test that bans expire after ban_duration."""
        hostmask = "tempban!test@example.com"

        # Manually ban the user
        current_time = time.time()
        bot.rate_limit["banned_users"][hostmask] = current_time - 1  # Expired ban

        # Should unban automatically
        assert bot._check_rate_limit(hostmask) is True
        assert hostmask not in bot.rate_limit["banned_users"]

    @pytest.mark.unit
    def test_rate_limit_timestamp_cleanup(self, bot):
        """Test that old timestamps are cleaned up."""
        hostmask = "cleanup!test@example.com"

        # Add old timestamps
        current_time = time.time()
        bot.rate_limit["user_commands"][hostmask] = [
            current_time - 120,  # 2 minutes ago (should be cleaned)
            current_time - 30,  # 30 seconds ago (should remain)
            current_time,  # Now (should remain)
        ]

        bot._check_rate_limit(hostmask)

        # Should have cleaned up old timestamp
        assert len(bot.rate_limit["user_commands"][hostmask]) <= 3


class TestSQLSafety:
    """Test SQL safety validation."""

    @pytest.mark.unit
    def test_validate_sql_safety_valid_query(self, bot):
        """Test validation of safe parameterized query."""
        query = "SELECT * FROM users WHERE username = %s"
        params = ("testuser",)

        assert bot._validate_sql_safety(query, params) is True

    @pytest.mark.unit
    def test_validate_sql_safety_multiple_params(self, bot):
        """Test validation with multiple parameters."""
        query = "INSERT INTO items (name, value, channel) VALUES (%s, %s, %s)"
        params = ("test", "value", "#channel")

        assert bot._validate_sql_safety(query, params) is True

    @pytest.mark.unit
    def test_validate_sql_safety_no_params_no_placeholders(self, bot):
        """Test query with no parameters and no placeholders."""
        query = "SELECT * FROM users"
        params = ()

        assert bot._validate_sql_safety(query, params) is True

    @pytest.mark.unit
    def test_validate_sql_safety_params_without_placeholders(self, bot):
        """Test detection of parameters without placeholders."""
        query = "SELECT * FROM users WHERE username = 'test'"
        params = ("testuser",)

        assert bot._validate_sql_safety(query, params) is False

    @pytest.mark.unit
    def test_validate_sql_safety_dangerous_pattern_or(self, bot):
        """Test detection of SQL injection OR pattern."""
        query = "SELECT * FROM users WHERE username = %s OR '1'='1"
        params = ("testuser",)

        assert bot._validate_sql_safety(query, params) is False

    @pytest.mark.unit
    def test_validate_sql_safety_dangerous_pattern_drop(self, bot):
        """Test detection of DROP statement in query."""
        query = "SELECT * FROM users; DROP TABLE users"
        params = ()

        assert bot._validate_sql_safety(query, params) is False


class TestPermissionValidation:
    """Test permission validation functionality."""

    @pytest.mark.unit
    def test_check_permissions_missing_fields(self, bot):
        """Test that events with missing fields are rejected."""
        event = {
            "nick": "testuser",
            # Missing required fields
        }

        assert bot._check_permissions(event, ["user"]) is False

    @pytest.mark.unit
    def test_check_permissions_banned_user(self, bot):
        """Test that banned users cannot execute commands."""
        event = {
            "nick": "banneduser",
            "hostmask": "banned!test@example.com",
            "channel": "#test",
            "trigger": "command",
            "user_info": None,
        }

        # Ban the user
        bot.rate_limit["banned_users"]["banned!test@example.com"] = time.time() + 300

        assert bot._check_permissions(event, ["user"]) is False

    @pytest.mark.unit
    def test_check_permissions_invalid_permissions_structure(self, bot):
        """Test that invalid permission structures are rejected."""
        event = {
            "nick": "testuser",
            "hostmask": "user!test@example.com",
            "channel": "#test",
            "trigger": "command",
            "user_info": {"permissions": "not_a_dict"},  # Invalid structure
        }

        with patch.object(bot, "_is_owner", return_value=False):
            assert bot._check_permissions(event, ["admin"]) is False

    @pytest.mark.unit
    def test_check_permissions_user_permission_granted(self, bot):
        """Test that 'user' permission is granted to everyone."""
        event = {
            "nick": "testuser",
            "hostmask": "user!test@example.com",
            "channel": "#test",
            "trigger": "command",
            "user_info": None,
        }

        with patch.object(bot, "_is_owner", return_value=False):
            assert bot._check_permissions(event, ["user"]) is True

    @pytest.mark.unit
    def test_check_permissions_owner_claim_command(self, bot):
        """Test that owner claim command is always allowed."""
        event = {
            "nick": "newowner",
            "hostmask": "owner!test@example.com",
            "channel": "#test",
            "trigger": "command",
            "command": "owner",
            "command_args": "claim",
            "user_info": None,
        }

        assert bot._check_permissions(event, ["owner"]) is True

    @pytest.mark.unit
    def test_check_permissions_bot_self(self, bot):
        """Test that bot itself bypasses permission checks."""
        event = {
            "nick": bot.nickname,
            "hostmask": f"{bot.nickname}!bot@test",
            "channel": "#test",
            "trigger": "command",
            "user_info": None,
        }

        assert bot._check_permissions(event, ["owner"]) is True


class TestCaching:
    """Test caching functionality."""

    @pytest.mark.unit
    def test_cache_set_and_get(self, bot):
        """Test basic cache set and get operations."""
        bot._cache_set("test_type", "test_key", "test_value")
        result = bot._cache_get("test_type", "test_key")

        assert result == "test_value"

    @pytest.mark.unit
    def test_cache_expiry(self, bot):
        """Test that cached items expire after TTL."""
        bot._cache_set("test_type", "test_key", "test_value")

        # Manually expire the cache
        cache_key = "test_type:test_key"
        bot.cache["cache_timestamps"][cache_key] = time.time() - 400  # Expired

        result = bot._cache_get("test_type", "test_key")
        assert result is None

    @pytest.mark.unit
    def test_cache_invalidate_specific(self, bot):
        """Test invalidating a specific cache entry."""
        bot._cache_set("test_type", "key1", "value1")
        bot._cache_set("test_type", "key2", "value2")

        bot._cache_invalidate("test_type", "key1")

        assert bot._cache_get("test_type", "key1") is None
        assert bot._cache_get("test_type", "key2") == "value2"

    @pytest.mark.unit
    def test_cache_invalidate_all(self, bot):
        """Test invalidating all cache entries of a type."""
        bot._cache_set("test_type", "key1", "value1")
        bot._cache_set("test_type", "key2", "value2")

        bot._cache_invalidate("test_type")

        assert bot._cache_get("test_type", "key1") is None
        assert bot._cache_get("test_type", "key2") is None


class TestConfigurationManagement:
    """Test configuration loading and management."""

    @pytest.mark.unit
    def test_load_config_sets_defaults(self, bot):
        """Test that default values are set for missing config options."""
        assert bot.config["server"] == "irc.test.server"
        assert bot.config["port"] == 6667
        assert bot.config["trigger"] == "!"
        assert bot.config["max_output_lines"] == 3

    @pytest.mark.unit
    def test_trigger_regex_compiled(self, bot):
        """Test that trigger regex is properly compiled."""
        assert bot.trigger_re is not None
        assert bot.trigger_re.pattern == "^!"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
