#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for core PhreakBot event handling and routing."""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phreakbot import PhreakBot


@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration file."""
    config_file = tmp_path / "test_config.json"
    import json

    config_data = {
        "server": "irc.test.server",
        "port": 6667,
        "nickname": "TestBot",
        "realname": "Test Bot",
        "channels": ["#test", "#another"],
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
    """Create a PhreakBot instance for testing."""
    with patch("phreakbot.psycopg2.pool.ThreadedConnectionPool"):
        bot = PhreakBot(mock_config)
        bot.db_pool = Mock()
        yield bot


class TestOutputHelpers:
    """Test output helper methods."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_say(self, bot):
        """Test say helper delegates to message."""
        bot.message = AsyncMock()
        await bot.say("#test", "hello")
        bot.message.assert_awaited_once_with("#test", "hello")

    @pytest.mark.unit
    def test_reply(self, bot):
        """Test reply adds reply message to output queue."""
        output = []
        bot._active_output = output
        bot.reply("hello there")
        assert len(output) == 1
        assert output[0]["type"] == "reply"
        assert output[0]["msg"] == "hello there"

    @pytest.mark.unit
    def test_add_response_say(self, bot):
        """Test add_response adds say message."""
        output = []
        bot._active_output = output
        bot.add_response("hello")
        assert len(output) == 1
        assert output[0]["type"] == "say"
        assert output[0]["msg"] == "hello"

    @pytest.mark.unit
    def test_add_response_private(self, bot):
        """Test add_response adds private message."""
        output = []
        bot._active_output = output
        bot.add_response("secret", private=True)
        assert len(output) == 1
        assert output[0]["type"] == "private"
        assert output[0]["msg"] == "secret"

    @pytest.mark.unit
    def test_add_response_no_active_output(self, bot):
        """Test add_response does nothing when no active output."""
        bot._active_output = None
        bot.add_response("hello")
        # Should not raise


class TestProcessOutput:
    """Test _process_output method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_output_empty(self, bot):
        """Test empty output does nothing."""
        bot.message = AsyncMock()
        await bot._process_output({"channel": "#test"}, [])
        bot.message.assert_not_awaited()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_output_say(self, bot):
        """Test say output type."""
        bot.message = AsyncMock()
        output = [{"type": "say", "msg": "hello"}]
        await bot._process_output({"channel": "#test"}, output)
        bot.message.assert_awaited_once_with("#test", "hello")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_output_reply(self, bot):
        """Test reply output type."""
        bot.message = AsyncMock()
        output = [{"type": "reply", "msg": "hello"}]
        event = {"channel": "#test", "nick": "user"}
        await bot._process_output(event, output)
        bot.message.assert_awaited_once_with("#test", "user, hello")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_output_private(self, bot):
        """Test private output type."""
        bot.message = AsyncMock()
        output = [{"type": "private", "msg": "secret"}]
        event = {"channel": "#test", "nick": "user"}
        await bot._process_output(event, output)
        bot.message.assert_awaited_once_with("user", "secret")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_process_output_combined(self, bot):
        """Test output is combined when exceeding max_output_lines."""
        bot.config["max_output_lines"] = 2
        bot.message = AsyncMock()
        output = [
            {"type": "say", "msg": "line1"},
            {"type": "say", "msg": "line2"},
            {"type": "say", "msg": "line3"},
        ]
        await bot._process_output({"channel": "#test"}, output)
        bot.message.assert_awaited_once_with("#test", "line1 | line2 | line3")


class TestOnConnect:
    """Test on_connect event handler."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_connect_joins_channels(self, bot):
        """Test on_connect joins configured channels."""
        bot.join = AsyncMock()
        bot.network = "testnet"
        await bot.on_connect()
        assert bot.join.await_count == 2
        bot.join.assert_any_await("#test")
        bot.join.assert_any_await("#another")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_connect_join_failure(self, bot):
        """Test on_connect handles join failure gracefully."""
        bot.join = AsyncMock(side_effect=[None, Exception("banned")])
        bot.network = "testnet"
        await bot.on_connect()
        assert bot.join.await_count == 2


class TestOnDisconnect:
    """Test on_disconnect event handler."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_disconnect_expected(self, bot):
        """Test expected disconnect."""
        await bot.on_disconnect(expected=True)
        # Should not raise

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_disconnect_unexpected(self, bot):
        """Test unexpected disconnect."""
        await bot.on_disconnect(expected=False)
        # Should not raise


class TestOnJoinPartQuit:
    """Test on_join, on_part, on_quit event handlers."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_join(self, bot):
        """Test on_join calls _handle_event."""
        with patch.object(bot, "_handle_event", new_callable=AsyncMock) as mock_handle:
            await bot.on_join("#test", "user")
            mock_handle.assert_awaited_once_with("user", "#test", "join")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_part(self, bot):
        """Test on_part calls _handle_event."""
        with patch.object(bot, "_handle_event", new_callable=AsyncMock) as mock_handle:
            await bot.on_part("#test", "user", "leaving")
            mock_handle.assert_awaited_once_with("user", "#test", "part")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_quit(self, bot):
        """Test on_quit calls _handle_event."""
        with patch.object(bot, "_handle_event", new_callable=AsyncMock) as mock_handle:
            await bot.on_quit("user", "quit message")
            mock_handle.assert_awaited_once_with("user", None, "quit")


class TestOnNames:
    """Test on_names event handler."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_names(self, bot):
        """Test on_names routes to modules."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.modules = {}
        with patch.object(bot, "_route_to_modules") as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            await bot.on_names("#test", {"user1": "", "user2": "@"})
            mock_route.assert_called_once()
            args = mock_route.call_args[0]
            assert args[0]["signal"] == "namreply"
            assert args[0]["names"] == ["user1", "user2"]
            mock_process.assert_awaited_once()


class TestOnCTCP:
    """Test on_ctcp event handler."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_ctcp(self, bot):
        """Test on_ctcp routes to modules."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock) as mock_whois, patch.object(
            bot, "_route_to_modules"
        ) as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            mock_whois.return_value = {"username": "user", "hostname": "host.com"}
            await bot.on_ctcp("user", "#test", "VERSION", "")
            mock_route.assert_called_once()
            args = mock_route.call_args[0]
            assert args[0]["signal"] == "ctcp"
            assert args[0]["ctcp_command"] == "VERSION"
            mock_process.assert_awaited_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_on_ctcp_whois_failure(self, bot):
        """Test on_ctcp handles whois failure gracefully."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock, side_effect=Exception("fail")), patch.object(
            bot, "_route_to_modules"
        ) as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            await bot.on_ctcp("user", "#test", "VERSION", "")
            mock_route.assert_called_once()
            args = mock_route.call_args[0]
            assert args[0]["hostmask"] == "user!unknown@unknown"
            mock_process.assert_awaited_once()


class TestHandleMessage:
    """Test _handle_message method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_non_command(self, bot):
        """Test non-command message is routed as event."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock) as mock_whois, patch.object(
            bot, "_route_to_modules"
        ) as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            mock_whois.return_value = {"username": "user", "hostname": "host.com"}
            await bot._handle_message("user", "#test", "hello world", False)
            mock_route.assert_called_once()
            args = mock_route.call_args[0]
            assert args[0]["trigger"] == "event"
            assert args[0]["text"] == "hello world"
            mock_process.assert_awaited_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_command(self, bot):
        """Test command message is routed as command."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock) as mock_whois, patch.object(
            bot, "_check_rate_limit", return_value=True
        ), patch.object(
            bot, "_route_to_modules"
        ) as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            mock_whois.return_value = {"username": "user", "hostname": "host.com"}
            await bot._handle_message("user", "#test", "!testcmd arg1 arg2", False)
            mock_route.assert_called_once()
            args = mock_route.call_args[0]
            assert args[0]["trigger"] == "command"
            assert args[0]["command"] == "testcmd"
            assert args[0]["command_args"] == "arg1 arg2"
            mock_process.assert_awaited_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_private(self, bot):
        """Test private message handling."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock) as mock_whois, patch.object(
            bot, "_route_to_modules"
        ) as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            mock_whois.return_value = {"username": "user", "hostname": "host.com"}
            await bot._handle_message("user", "user", "hello", True)
            mock_route.assert_called_once()
            args = mock_route.call_args[0]
            assert args[0]["is_privmsg"] is True
            assert args[0]["channel"] == "user"
            mock_process.assert_awaited_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_rate_limited(self, bot):
        """Test rate-limited message is rejected."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        with patch.object(bot, "whois", new_callable=AsyncMock) as mock_whois, patch.object(
            bot, "_check_rate_limit", return_value=False
        ), patch.object(
            bot, "message", new_callable=AsyncMock
        ) as mock_message:
            mock_whois.return_value = {"username": "user", "hostname": "host.com"}
            await bot._handle_message("user", "#test", "!testcmd", False)
            mock_message.assert_awaited_once_with("#test", "user: Rate limit exceeded. Please slow down.")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_cached_hostmask(self, bot):
        """Test cached hostmask is used."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.user_hostmasks["user"] = "user!cached@host.com"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock) as mock_whois, patch.object(
            bot, "_route_to_modules"
        ) as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            await bot._handle_message("user", "#test", "hello", False)
            mock_whois.assert_not_awaited()
            args = mock_route.call_args[0]
            assert args[0]["hostmask"] == "user!cached@host.com"
            mock_process.assert_awaited_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_message_whois_none(self, bot):
        """Test whois returning None is handled."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock) as mock_whois, patch.object(
            bot, "_route_to_modules"
        ) as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            mock_whois.return_value = None
            await bot._handle_message("user", "#test", "hello", False)
            args = mock_route.call_args[0]
            assert args[0]["hostmask"] == "user!unknown@unknown"
            mock_process.assert_awaited_once()


class TestHandleEvent:
    """Test _handle_event method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_event_join(self, bot):
        """Test join event handling."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock) as mock_whois, patch.object(
            bot, "_route_to_modules"
        ) as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            mock_whois.return_value = {"username": "user", "hostname": "host.com"}
            await bot._handle_event("user", "#test", "join")
            mock_route.assert_called_once()
            args = mock_route.call_args[0]
            assert args[0]["signal"] == "join"
            assert args[0]["hostmask"] == "user!user@host.com"
            mock_process.assert_awaited_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_event_quit_removes_hostmask(self, bot):
        """Test quit event removes cached hostmask."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.user_hostmasks["user"] = "user!user@host.com"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock) as mock_whois, patch.object(
            bot, "_route_to_modules"
        ), patch.object(bot, "_process_output", new_callable=AsyncMock):
            mock_whois.return_value = {"username": "user", "hostname": "host.com"}
            await bot._handle_event("user", None, "quit")
            assert "user" not in bot.user_hostmasks

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_event_whois_failure(self, bot):
        """Test _handle_event handles whois failure."""
        bot.network = "testnet"
        bot.nickname = "TestBot"
        bot.modules = {}
        with patch.object(bot, "whois", new_callable=AsyncMock, side_effect=Exception("fail")), patch.object(
            bot, "_route_to_modules"
        ) as mock_route, patch.object(
            bot, "_process_output", new_callable=AsyncMock
        ) as mock_process:
            await bot._handle_event("user", "#test", "part")
            mock_route.assert_called_once()
            args = mock_route.call_args[0]
            assert args[0]["hostmask"] == "user!unknown@unknown"
            mock_process.assert_awaited_once()


class TestDispatchEvent:
    """Test _dispatch_event method."""

    @pytest.mark.unit
    def test_dispatch_event_command_found(self, bot):
        """Test dispatching to a module that handles a command."""
        mock_module = Mock()
        mock_module.run = Mock()
        bot.modules = {
            "testmod": {
                "commands": ["testcmd"],
                "events": [],
                "permissions": ["user"],
                "object": mock_module,
            }
        }
        event = {
            "trigger": "command",
            "command": "testcmd",
            "nick": "user",
            "hostmask": "user!host",
            "channel": "#test",
            "command_args": "",
            "signal": "pubmsg",
        }
        with patch.object(bot, "_check_permissions", return_value=True):
            bot._dispatch_event(event)
        mock_module.run.assert_called_once_with(bot, event)

    @pytest.mark.unit
    def test_dispatch_event_command_no_permission(self, bot):
        """Test dispatching when user lacks permissions."""
        mock_module = Mock()
        mock_module.run = Mock()
        bot.modules = {
            "testmod": {
                "commands": ["testcmd"],
                "events": [],
                "permissions": ["admin"],
                "object": mock_module,
            }
        }
        event = {
            "trigger": "command",
            "command": "testcmd",
            "nick": "user",
            "hostmask": "user!host",
            "channel": "#test",
            "command_args": "",
            "signal": "pubmsg",
        }
        with patch.object(bot, "_check_permissions", return_value=False):
            bot._dispatch_event(event)
        mock_module.run.assert_not_called()

    @pytest.mark.unit
    def test_dispatch_event_event_signal(self, bot):
        """Test dispatching an event signal."""
        mock_module = Mock()
        mock_module.run = Mock()
        bot.modules = {
            "testmod": {
                "commands": [],
                "events": ["join"],
                "permissions": ["user"],
                "object": mock_module,
            }
        }
        event = {
            "trigger": "event",
            "command": "",
            "nick": "user",
            "hostmask": "user!host",
            "channel": "#test",
            "signal": "join",
        }
        bot._dispatch_event(event)
        mock_module.run.assert_called_once_with(bot, event)

    @pytest.mark.unit
    def test_dispatch_event_module_error(self, bot):
        """Test dispatching handles module errors gracefully."""
        mock_module = Mock()
        mock_module.run = Mock(side_effect=Exception("boom"))
        bot.modules = {
            "testmod": {
                "commands": ["testcmd"],
                "events": [],
                "permissions": ["user"],
                "object": mock_module,
            }
        }
        event = {
            "trigger": "command",
            "command": "testcmd",
            "nick": "user",
            "hostmask": "user!host",
            "channel": "#test",
            "command_args": "",
            "signal": "pubmsg",
        }
        with patch.object(bot, "_check_permissions", return_value=True):
            bot._dispatch_event(event)
        # Should not raise

    @pytest.mark.unit
    def test_dispatch_event_no_handler(self, bot):
        """Test dispatching when no module handles the command."""
        bot.modules = {
            "testmod": {
                "commands": ["othercmd"],
                "events": [],
                "permissions": ["user"],
                "object": Mock(),
            }
        }
        event = {
            "trigger": "command",
            "command": "testcmd",
            "nick": "user",
            "hostmask": "user!host",
            "channel": "#test",
            "command_args": "",
            "signal": "pubmsg",
        }
        with patch.object(bot, "_check_permissions", return_value=True):
            bot._dispatch_event(event)
        # Should not raise

    @pytest.mark.unit
    def test_dispatch_event_infoitems_custom_command(self, bot):
        """Test infoitems custom command handler is checked first."""
        mock_infoitems = Mock()
        mock_infoitems.handle_custom_command = Mock(return_value=True)
        bot.modules = {
            "infoitems": {
                "object": mock_infoitems,
                "commands": [],
                "events": [],
                "permissions": ["user"],
            }
        }
        event = {
            "trigger": "command",
            "command": "somecmd",
            "nick": "user",
            "hostmask": "user!host",
            "channel": "#test",
            "command_args": "",
            "signal": "pubmsg",
        }
        bot._dispatch_event(event)
        mock_infoitems.handle_custom_command.assert_called_once_with(bot, event)


class TestRouteToModules:
    """Test _route_to_modules method."""

    @pytest.mark.unit
    def test_route_to_modules_sets_active_output(self, bot):
        """Test _route_to_modules sets and clears _active_output."""
        output = []
        event = {"trigger": "event", "signal": "join"}
        with patch.object(bot, "_dispatch_event"):
            bot._route_to_modules(event, output)
        assert bot._active_output is None

    @pytest.mark.unit
    def test_route_to_modules_exception_cleanup(self, bot):
        """Test _active_output is cleared even on exception."""
        output = []
        event = {"trigger": "event", "signal": "join"}
        with patch.object(bot, "_dispatch_event", side_effect=Exception("boom")):
            with pytest.raises(Exception):
                bot._route_to_modules(event, output)
        assert bot._active_output is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
