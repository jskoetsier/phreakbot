#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for PhreakBot module system.

Tests module loading, unloading, and module functionality.
"""

import importlib.util
import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add parent directory to path
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
        # Clear modules loaded during init
        bot.modules = {}
        yield bot


@pytest.fixture
def test_module(tmp_path):
    """Create a test module file."""
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
    if event["trigger"] == "command" and event["command"] == "test":
        bot.add_response("Test command executed!")
        return True
    elif event["trigger"] == "event":
        # Handle events
        return True
    return False
'''

    with open(module_file, "w") as f:
        f.write(module_content)

    return str(module_file)


class TestModuleLoading:
    """Test module loading functionality."""

    @pytest.mark.module
    def test_load_module_success(self, bot, test_module):
        """Test successful module loading."""
        result = bot.load_module(test_module)

        assert result is True
        assert "test_module" in bot.modules
        assert "test" in bot.modules["test_module"]["commands"]
        assert "join" in bot.modules["test_module"]["events"]
        assert "user" in bot.modules["test_module"]["permissions"]

    @pytest.mark.module
    def test_load_module_missing_config(self, bot, tmp_path):
        """Test loading module without config function."""
        module_file = tmp_path / "bad_module.py"
        with open(module_file, "w") as f:
            f.write("# Module without config function\n")

        result = bot.load_module(str(module_file))
        assert result is False

    @pytest.mark.module
    def test_load_module_invalid_config(self, bot, tmp_path):
        """Test loading module with invalid config."""
        module_file = tmp_path / "invalid_module.py"
        with open(module_file, "w") as f:
            f.write(
                """
def config(bot):
    return {
        # Missing required keys
        "commands": ["test"]
    }
"""
            )

        result = bot.load_module(str(module_file))
        assert result is False

    @pytest.mark.module
    def test_load_module_syntax_error(self, bot, tmp_path):
        """Test loading module with syntax error."""
        module_file = tmp_path / "syntax_error.py"
        with open(module_file, "w") as f:
            f.write("def invalid syntax here")

        result = bot.load_module(str(module_file))
        assert result is False


class TestModuleUnloading:
    """Test module unloading functionality."""

    @pytest.mark.module
    def test_unload_module_success(self, bot, test_module):
        """Test successful module unloading."""
        bot.load_module(test_module)
        assert "test_module" in bot.modules

        result = bot.unload_module("test_module")

        assert result is True
        assert "test_module" not in bot.modules

    @pytest.mark.module
    def test_unload_nonexistent_module(self, bot):
        """Test unloading a module that doesn't exist."""
        result = bot.unload_module("nonexistent_module")
        assert result is False


class TestModuleExecution:
    """Test module execution."""

    @pytest.mark.module
    def test_module_command_execution(self, bot, test_module):
        """Test executing a module command."""
        bot.load_module(test_module)

        event = {
            "trigger": "command",
            "command": "test",
            "command_args": "",
            "nick": "testuser",
            "hostmask": "test!user@host",
            "channel": "#test",
            "text": "!test",
            "user_info": None,
        }

        # Execute the module
        bot.modules["test_module"]["object"].run(bot, event)

        # Check that response was added
        assert len(bot.output) > 0
        assert bot.output[0]["msg"] == "Test command executed!"

    @pytest.mark.module
    def test_module_event_handling(self, bot, test_module):
        """Test module event handling."""
        bot.load_module(test_module)

        event = {
            "trigger": "event",
            "signal": "join",
            "nick": "testuser",
            "hostmask": "test!user@host",
            "channel": "#test",
            "text": "",
            "user_info": None,
        }

        # Module should handle the event
        result = bot.modules["test_module"]["object"].run(bot, event)
        assert result is True


class TestModuleConfiguration:
    """Test module configuration handling."""

    @pytest.mark.module
    def test_module_has_required_keys(self, bot, test_module):
        """Test that loaded module has all required configuration keys."""
        bot.load_module(test_module)
        module_config = bot.modules["test_module"]

        required_keys = ["events", "commands", "help", "object"]
        for key in required_keys:
            assert key in module_config

    @pytest.mark.module
    def test_module_help_structure(self, bot, test_module):
        """Test that module help is properly structured."""
        bot.load_module(test_module)
        module_config = bot.modules["test_module"]

        assert isinstance(module_config["help"], dict)
        assert "test" in module_config["help"]


class TestModulePermissions:
    """Test module permission handling."""

    @pytest.mark.module
    def test_module_permission_check(self, bot, test_module):
        """Test that module permissions are checked."""
        bot.load_module(test_module)

        # Module requires 'user' permission
        assert "user" in bot.modules["test_module"]["permissions"]


class TestMultipleModules:
    """Test loading and managing multiple modules."""

    @pytest.mark.module
    def test_load_multiple_modules(self, bot, tmp_path):
        """Test loading multiple modules simultaneously."""
        # Create two modules
        for i in range(2):
            module_file = tmp_path / f"module_{i}.py"
            with open(module_file, "w") as f:
                f.write(
                    f"""
def config(bot):
    return {{
        "events": [],
        "commands": ["cmd{i}"],
        "permissions": ["user"],
        "help": {{"cmd{i}": "Command {i}"}}
    }}

def run(bot, event):
    return True
"""
                )
            bot.load_module(str(module_file))

        assert len(bot.modules) == 2
        assert "module_0" in bot.modules
        assert "module_1" in bot.modules

    @pytest.mark.module
    def test_unload_one_of_multiple_modules(self, bot, tmp_path):
        """Test unloading one module while others remain."""
        # Load two modules
        for i in range(2):
            module_file = tmp_path / f"module_{i}.py"
            with open(module_file, "w") as f:
                f.write(
                    f"""
def config(bot):
    return {{
        "events": [],
        "commands": ["cmd{i}"],
        "permissions": ["user"],
        "help": {{"cmd{i}": "Command {i}"}}
    }}

def run(bot, event):
    return True
"""
                )
            bot.load_module(str(module_file))

        # Unload one module
        bot.unload_module("module_0")

        assert "module_0" not in bot.modules
        assert "module_1" in bot.modules


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
