#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared pytest configuration and fixtures for PhreakBot tests.
"""

import json
import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_config(tmp_path):
    """
    Create a mock configuration file for testing.

    Returns:
        str: Path to temporary config file
    """
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

    with open(config_file, "w") as f:
        json.dump(config_data, f)

    return str(config_file)


@pytest.fixture
def bot(mock_config):
    """
    Create a PhreakBot instance for testing.

    Args:
        mock_config: Fixture providing mock config file

    Returns:
        PhreakBot: Bot instance with mocked database
    """
    from phreakbot import PhreakBot

    with patch("phreakbot.psycopg2.pool.ThreadedConnectionPool"):
        bot = PhreakBot(mock_config)
        bot.db_connection = Mock()
        bot.db_pool = Mock()
        bot.output = []  # Ensure output list exists
        yield bot


@pytest.fixture
def mock_event():
    """
    Create a mock IRC event for testing.

    Returns:
        dict: Mock event dictionary
    """
    return {
        "trigger": "command",
        "command": "test",
        "command_args": "",
        "nick": "testuser",
        "hostmask": "test!user@example.com",
        "channel": "#test",
        "text": "!test",
        "user_info": None,
    }


@pytest.fixture
def mock_db_cursor():
    """
    Create a mock database cursor.

    Returns:
        Mock: Mock cursor object
    """
    cursor = Mock()
    cursor.fetchone = Mock(return_value=None)
    cursor.fetchall = Mock(return_value=[])
    cursor.execute = Mock()
    return cursor


@pytest.fixture
def test_module(tmp_path):
    """
    Create a test module file.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        str: Path to test module
    """
    module_dir = tmp_path / "test_modules"
    module_dir.mkdir()

    module_file = module_dir / "test_module.py"
    module_content = '''
def config(bot):
    """Module configuration"""
    return {
        "events": ["join", "part"],
        "commands": ["test"],
        "permissions": ["user"],
        "help": {
            "test": "Test command - Usage: !test"
        }
    }

def run(bot, event):
    """Module run function"""
    if event.get("trigger") == "command" and event.get("command") == "test":
        bot.add_response("Test command executed!")
        return True
    elif event.get("trigger") == "event":
        return True
    return False
'''

    with open(module_file, "w") as f:
        f.write(module_content)

    return str(module_file)


# Configure pytest
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "irc: IRC protocol tests")
    config.addinivalue_line("markers", "module: Module tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_db: Tests requiring database")
    config.addinivalue_line("markers", "requires_irc: Tests requiring IRC server")
