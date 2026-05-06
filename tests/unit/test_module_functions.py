#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for individual PhreakBot modules.

Tests ASN, MAC, IP, Karma, Quotes, and URLs modules with mocked dependencies.
"""

import sys
import os
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_bot():
    """Create a mock bot with response capture."""
    bot = Mock()
    bot._active_output = []
    bot.logger = Mock()

    def add_response(msg, private=False):
        bot._active_output.append({"type": "private" if private else "say", "msg": msg})

    def reply(msg):
        bot._active_output.append({"type": "reply", "msg": msg})

    bot.add_response = Mock(side_effect=add_response)
    bot.reply = Mock(side_effect=reply)
    return bot


@pytest.fixture
def mock_db_cursor():
    """Create a mock database cursor."""
    cursor = Mock()
    cursor.fetchone = Mock(return_value=None)
    cursor.fetchall = Mock(return_value=[])
    cursor.execute = Mock()
    cursor.close = Mock()
    return cursor


@pytest.fixture
def mock_db_conn(mock_db_cursor):
    """Create a mock database connection."""
    conn = Mock()
    conn.cursor = Mock(return_value=mock_db_cursor)
    conn.commit = Mock()
    conn.rollback = Mock()
    return conn


# ---------------------------------------------------------------------------
# ASN Module Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAsnModule:
    """Tests for the ASN lookup module."""

    def test_config_returns_expected_structure(self, mock_bot):
        from modules import asn
        cfg = asn.config(mock_bot)
        assert cfg["commands"] == ["asn"]
        assert "user" in cfg["permissions"]
        assert "asn" in cfg["help"]

    def test_run_with_empty_args(self, mock_bot):
        from modules import asn
        event = {"command": "asn", "command_args": "  "}
        asn.run(mock_bot, event)
        assert any("Please provide" in r["msg"] for r in mock_bot._active_output)

    def test_run_with_as_number(self, mock_bot):
        from modules import asn
        with patch("modules.asn.lookup_asn_by_number") as mock_lookup:
            event = {"command": "asn", "command_args": "AS15169"}
            asn.run(mock_bot, event)
            mock_lookup.assert_called_once_with(mock_bot, "15169")

    def test_run_with_as_number_no_prefix(self, mock_bot):
        from modules import asn
        with patch("modules.asn.lookup_asn_by_number") as mock_lookup:
            event = {"command": "asn", "command_args": "15169"}
            asn.run(mock_bot, event)
            mock_lookup.assert_called_once_with(mock_bot, "15169")

    def test_run_with_ip_address(self, mock_bot):
        from modules import asn
        with patch("modules.asn.lookup_asn_by_ip") as mock_lookup:
            event = {"command": "asn", "command_args": "8.8.8.8"}
            asn.run(mock_bot, event)
            mock_lookup.assert_called_once_with(mock_bot, "8.8.8.8")

    def test_run_with_invalid_input(self, mock_bot):
        from modules import asn
        event = {"command": "asn", "command_args": "not-an-ip"}
        asn.run(mock_bot, event)
        assert any("Invalid input" in r["msg"] for r in mock_bot._active_output)

    def test_lookup_asn_by_ip_success_with_as_prefix(self, mock_bot):
        from modules import asn
        mock_resp = Mock()
        mock_resp.json.return_value = {
            "org": "AS15169 Google LLC",
            "city": "Mountain View",
            "region": "California",
            "country": "US",
        }
        mock_resp.raise_for_status = Mock()
        with patch("modules.asn.requests.get", return_value=mock_resp):
            asn.lookup_asn_by_ip(mock_bot, "8.8.8.8")
        assert any("AS15169" in r["msg"] and "Google LLC" in r["msg"] for r in mock_bot._active_output)

    def test_lookup_asn_by_ip_success_without_as_prefix(self, mock_bot):
        from modules import asn
        mock_resp = Mock()
        mock_resp.json.return_value = {"org": "Some Org", "country": "US"}
        mock_resp.raise_for_status = Mock()
        with patch("modules.asn.requests.get", return_value=mock_resp):
            asn.lookup_asn_by_ip(mock_bot, "1.1.1.1")
        assert any("Some Org" in r["msg"] for r in mock_bot._active_output)

    def test_lookup_asn_by_ip_exception(self, mock_bot):
        from modules import asn
        with patch("modules.asn.requests.get", side_effect=Exception("timeout")):
            asn.lookup_asn_by_ip(mock_bot, "8.8.8.8")
        assert any("Error looking up ASN" in r["msg"] for r in mock_bot._active_output)

    def test_lookup_asn_by_number_success(self, mock_bot):
        from modules import asn
        mock_resp = Mock()
        mock_resp.json.return_value = {"status": "ok", "data": {"holder": "Google LLC"}}
        mock_resp.raise_for_status = Mock()
        reg_resp = Mock()
        reg_resp.status_code = 200
        reg_resp.json.return_value = {
            "objects": {
                "object": [
                    {
                        "attributes": {
                            "attribute": [
                                {"name": "created", "value": "2000-01-01"},
                                {"name": "country", "value": "US"},
                            ]
                        }
                    }
                ]
            }
        }
        with patch("modules.asn.requests.get", side_effect=[mock_resp, reg_resp]):
            asn.lookup_asn_by_number(mock_bot, "15169")
        assert any("Google LLC" in r["msg"] and "US" in r["msg"] for r in mock_bot._active_output)

    def test_lookup_asn_by_number_status_not_ok(self, mock_bot):
        from modules import asn
        mock_resp = Mock()
        mock_resp.json.return_value = {"status": "error"}
        mock_resp.raise_for_status = Mock()
        with patch("modules.asn.requests.get", return_value=mock_resp):
            asn.lookup_asn_by_number(mock_bot, "15169")
        assert any("Failed to look up" in r["msg"] for r in mock_bot._active_output)

    def test_lookup_asn_by_number_exception(self, mock_bot):
        from modules import asn
        with patch("modules.asn.requests.get", side_effect=Exception("boom")):
            asn.lookup_asn_by_number(mock_bot, "15169")
        assert any("Error looking up ASN" in r["msg"] for r in mock_bot._active_output)

    def test_format_location_with_all_parts(self):
        from modules import asn
        result = asn.format_location("US", "CA", "SF")
        assert result == "SF, CA, US"

    def test_format_location_avoids_duplicate(self):
        from modules import asn
        result = asn.format_location("US", "SF", "SF")
        assert result == "SF, US"

    def test_format_location_empty(self):
        from modules import asn
        result = asn.format_location("", "", "")
        assert result == "Unknown"


# ---------------------------------------------------------------------------
# MAC Module Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestMacModule:
    """Tests for the MAC address lookup module."""

    def test_config_returns_expected_structure(self, mock_bot):
        from modules import mac
        cfg = mac.config(mock_bot)
        assert "mac" in cfg["commands"]

    def test_run_with_empty_args(self, mock_bot):
        from modules import mac
        event = {"command": "mac", "command_args": "  "}
        mac.run(mock_bot, event)
        assert any("Please provide a MAC address" in r["msg"] for r in mock_bot._active_output)

    def test_run_with_invalid_mac(self, mock_bot):
        from modules import mac
        event = {"command": "mac", "command_args": "00:00"}
        mac.run(mock_bot, event)
        assert any("Invalid MAC address format" in r["msg"] for r in mock_bot._active_output)

    def test_run_success(self, mock_bot):
        from modules import mac
        with patch("modules.mac.get_mac_info", return_value="MAC: 00:11:22:33:44:55 | Vendor: Cisco"):
            event = {"command": "mac", "command_args": "00:11:22:33:44:55"}
            mac.run(mock_bot, event)
        assert any("Cisco" in r["msg"] for r in mock_bot._active_output)

    def test_run_exception(self, mock_bot):
        from modules import mac
        with patch("modules.mac.get_mac_info", side_effect=Exception("fail")):
            event = {"command": "mac", "command_args": "00:11:22:33:44:55"}
            mac.run(mock_bot, event)
        assert any("Error looking up MAC" in r["msg"] for r in mock_bot._active_output)

    def test_clean_mac_address_valid(self):
        from modules import mac
        assert mac.clean_mac_address("00:11:22:33:44:55") == "001122334455"
        assert mac.clean_mac_address("00-11-22-33-44-55") == "001122334455"
        assert mac.clean_mac_address("001122334455") == "001122334455"

    def test_clean_mac_address_too_short(self):
        from modules import mac
        assert mac.clean_mac_address("00:00") is None

    def test_clean_mac_address_truncates_long(self):
        from modules import mac
        assert mac.clean_mac_address("00112233445566778899") == "001122334455"

    def test_get_mac_info_primary_api(self):
        from modules import mac
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "vendorDetails": {"companyName": "Cisco Systems", "companyAddress": "San Jose, CA"},
            "blockDetails": {"blockType": "MA-L"},
        }
        with patch("modules.mac.requests.get", return_value=mock_resp):
            result = mac.get_mac_info("001122334455")
        assert "Cisco Systems" in result
        assert "MA-L" in result

    def test_get_mac_info_fallback_api(self):
        from modules import mac
        primary = Mock()
        primary.status_code = 404
        fallback = Mock()
        fallback.status_code = 200
        fallback.text = "Apple Inc"
        with patch("modules.mac.requests.get", side_effect=[primary, fallback]):
            result = mac.get_mac_info("AABBCCDDEEFF")
        assert "Apple Inc" in result

    def test_get_mac_info_both_apis_fail(self):
        from modules import mac
        primary = Mock()
        primary.status_code = 404
        fallback = Mock()
        fallback.status_code = 404
        with patch("modules.mac.requests.get", side_effect=[primary, fallback]):
            result = mac.get_mac_info("AABBCCDDEEFF")
        assert "Unknown" in result

    def test_get_mac_info_exception(self):
        from modules import mac
        with patch("modules.mac.requests.get", side_effect=Exception("boom")):
            result = mac.get_mac_info("AABBCC")
        assert "Error processing MAC" in result

    def test_format_mac_for_display_full(self):
        from modules import mac
        assert mac.format_mac_for_display("001122334455") == "00:11:22:33:44:55"

    def test_format_mac_for_display_partial(self):
        from modules import mac
        assert mac.format_mac_for_display("001122") == "00:11:22:00:00:00"


# ---------------------------------------------------------------------------
# IP Module Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestIpModule:
    """Tests for the IP lookup module."""

    def test_config_returns_expected_structure(self, mock_bot):
        from modules import ip as ip_module
        cfg = ip_module.config(mock_bot)
        assert "ip" in cfg["commands"]

    def test_run_with_empty_args(self, mock_bot):
        from modules import ip as ip_module
        event = {"command": "ip", "command_args": "  "}
        ip_module.run(mock_bot, event)
        assert any("Please provide" in r["msg"] for r in mock_bot._active_output)

    def test_run_with_ip_address(self, mock_bot):
        from modules import ip as ip_module
        with patch("modules.ip.get_ip_info", return_value="IP: 8.8.8.8 | Type: IPv4, Global"):
            event = {"command": "ip", "command_args": "8.8.8.8"}
            ip_module.run(mock_bot, event)
        assert any("8.8.8.8" in r["msg"] for r in mock_bot._active_output)

    def test_run_with_hostname(self, mock_bot):
        from modules import ip as ip_module
        addr_info = [(2, 1, 6, "", ("93.184.216.34", 0))]
        with patch("modules.ip.socket.getaddrinfo", return_value=addr_info):
            with patch("modules.ip.get_ip_info", return_value="IP info"):
                event = {"command": "ip", "command_args": "example.com"}
                ip_module.run(mock_bot, event)
        assert any("IP info" in r["msg"] for r in mock_bot._active_output)

    def test_run_hostname_resolution_failure(self, mock_bot):
        from modules import ip as ip_module
        with patch("modules.ip.socket.getaddrinfo", side_effect=ip_module.socket.gaierror):
            event = {"command": "ip", "command_args": "bad.host"}
            ip_module.run(mock_bot, event)
        assert any("Could not resolve hostname" in r["msg"] for r in mock_bot._active_output)

    def test_run_exception(self, mock_bot):
        from modules import ip as ip_module
        with patch("modules.ip.socket.getaddrinfo", side_effect=Exception("boom")):
            event = {"command": "ip", "command_args": "example.com"}
            ip_module.run(mock_bot, event)
        assert any("Error looking up IP" in r["msg"] for r in mock_bot._active_output)

    def test_get_ip_info_private(self):
        from modules import ip as ip_module
        result = ip_module.get_ip_info("192.168.1.1")
        assert "Private" in result
        assert "IPv4" in result

    def test_get_ip_info_loopback(self):
        from modules import ip as ip_module
        result = ip_module.get_ip_info("127.0.0.1")
        assert "Loopback" in result

    def test_get_ip_info_public_with_geo(self):
        from modules import ip as ip_module
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "country": "US", "regionName": "CA", "city": "SF",
            "isp": "Example ISP", "org": "Example Org", "as": "AS12345",
        }
        with patch("modules.ip.requests.get", return_value=mock_resp):
            result = ip_module.get_ip_info("8.8.8.8")
        assert "Example ISP" in result
        assert "AS12345" in result

    def test_get_ip_info_public_geo_fail(self):
        from modules import ip as ip_module
        with patch("modules.ip.requests.get", side_effect=Exception("timeout")):
            result = ip_module.get_ip_info("1.1.1.1")
        assert "IPv4" in result
        assert "Global" in result

    def test_get_ip_info_exception(self):
        from modules import ip as ip_module
        with patch("modules.ip.ipaddress.ip_address", side_effect=Exception("bad")):
            result = ip_module.get_ip_info("bad-ip")
        assert "Error processing IP" in result


# ---------------------------------------------------------------------------
# Karma Module Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestKarmaModule:
    """Tests for the karma module."""

    def test_config_returns_expected_structure(self, mock_bot):
        from modules import karma
        cfg = karma.config(mock_bot)
        assert "karma" in cfg["commands"]
        assert "topkarma" in cfg["commands"]
        assert "pubmsg" in cfg["events"]

    def test_run_wrong_command(self, mock_bot):
        from modules import karma
        event = {"trigger": "command", "command": "nope"}
        assert karma.run(mock_bot, event) is False

    def test_run_karma_command(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        event = {"trigger": "command", "command": "karma", "command_args": "python"}
        karma.run(mock_bot, event)
        mock_db_cursor.execute.assert_called()

    def test_run_topkarma_command(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        event = {"trigger": "command", "command": "topkarma", "command_args": ""}
        karma.run(mock_bot, event)
        assert mock_db_cursor.execute.call_count >= 2

    def test_run_pubmsg_karma_pattern(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = {"id": 1, "karma": 5}
        event = {"trigger": "event", "signal": "pubmsg", "text": "!python++", "nick": "other"}
        karma.run(mock_bot, event)
        assert any("python now has" in r["msg"] for r in mock_bot._active_output)

    def test_handle_karma_self_karma(self, mock_bot):
        from modules import karma
        event = {"text": "!python++", "nick": "python"}
        karma._handle_karma_pattern(mock_bot, event)
        assert any("can't give karma to yourself" in r["msg"] for r in mock_bot._active_output)

    def test_handle_karma_no_db(self, mock_bot):
        from modules import karma
        mock_bot.db_get.return_value = None
        event = {"text": "!python++", "nick": "other"}
        karma._handle_karma_pattern(mock_bot, event)
        assert any("Database connection is not available" in r["msg"] for r in mock_bot._active_output)

    def test_handle_karma_upvote_existing(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = {"id": 1, "karma": 5}
        event = {"text": "!python++", "nick": "other"}
        karma._handle_karma_pattern(mock_bot, event)
        assert any("python now has 6 karma" in r["msg"] for r in mock_bot._active_output)

    def test_handle_karma_upvote_new(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.side_effect = [None, {"karma": 1}]
        event = {"text": "!python++", "nick": "other"}
        karma._handle_karma_pattern(mock_bot, event)
        assert any("python now has 1 karma" in r["msg"] for r in mock_bot._active_output)

    def test_handle_karma_downvote_existing(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = {"id": 1, "karma": 5}
        event = {"text": "!python--", "nick": "other"}
        karma._handle_karma_pattern(mock_bot, event)
        assert any("python now has 4 karma" in r["msg"] for r in mock_bot._active_output)

    def test_handle_karma_downvote_new(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.side_effect = [None, {"karma": -1}]
        event = {"text": "!python--", "nick": "other"}
        karma._handle_karma_pattern(mock_bot, event)
        assert any("python now has -1 karma" in r["msg"] for r in mock_bot._active_output)

    def test_handle_karma_with_reason(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.side_effect = [{"id": 1, "karma": 5}, {"id": 1}]
        # Note: KARMA_PATTERN requires reason to start with # (e.g. "!item++ #reason")
        event = {"text": "!python++ #great language", "nick": "other"}
        karma._handle_karma_pattern(mock_bot, event)
        calls = [c for c in mock_db_cursor.execute.call_args_list if "phreakbot_karma_why" in str(c)]
        assert len(calls) > 0

    def test_handle_karma_exception(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.execute.side_effect = Exception("db error")
        event = {"text": "!python++", "nick": "other"}
        result = karma._handle_karma_pattern(mock_bot, event)
        assert result is True
        mock_db_conn.rollback.assert_called_once()

    def test_cmd_karma_no_args(self, mock_bot):
        from modules import karma
        event = {"command_args": "  "}
        karma._cmd_karma(mock_bot, event)
        assert any("Usage: !karma" in r["msg"] for r in mock_bot._active_output)

    def test_cmd_karma_no_karma(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = None
        event = {"command_args": "unknownitem"}
        karma._cmd_karma(mock_bot, event)
        assert any("has no karma" in r["msg"] for r in mock_bot._active_output)

    def test_cmd_karma_with_reasons(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = {"karma": 10}
        mock_db_cursor.fetchall.return_value = [
            {"direction": "up", "reason": "awesome"},
            {"direction": "down", "reason": "bugs"},
        ]
        event = {"command_args": "python"}
        karma._cmd_karma(mock_bot, event)
        assert any("+1 for awesome" in r["msg"] and "-1 for bugs" in r["msg"] for r in mock_bot._active_output)

    def test_cmd_karma_exception(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.execute.side_effect = Exception("db error")
        event = {"command_args": "python"}
        karma._cmd_karma(mock_bot, event)
        mock_bot.logger.error.assert_called()

    def test_cmd_topkarma_default_limit(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchall.return_value = [{"item": "python", "karma": 10}]
        event = {"command_args": ""}
        karma._cmd_topkarma(mock_bot, event)
        assert any("Top 1 positive karma" in r["msg"] for r in mock_bot._active_output)

    def test_cmd_topkarma_custom_limit(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchall.return_value = []
        event = {"command_args": "3"}
        karma._cmd_topkarma(mock_bot, event)
        assert mock_db_cursor.execute.call_args[0][1] == (3,)

    def test_cmd_topkarma_limit_capped(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchall.return_value = []
        event = {"command_args": "50"}
        karma._cmd_topkarma(mock_bot, event)
        assert mock_db_cursor.execute.call_args[0][1] == (10,)

    def test_cmd_topkarma_no_db(self, mock_bot):
        from modules import karma
        mock_bot.db_get.return_value = None
        event = {"command_args": ""}
        karma._cmd_topkarma(mock_bot, event)
        assert any("Database connection is not available" in r["msg"] for r in mock_bot._active_output)

    def test_cmd_topkarma_empty_results(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchall.return_value = []
        event = {"command_args": ""}
        karma._cmd_topkarma(mock_bot, event)
        assert any("No positive karma found" in r["msg"] for r in mock_bot._active_output)
        assert any("No negative karma found" in r["msg"] for r in mock_bot._active_output)

    def test_cmd_topkarma_exception(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import karma
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.execute.side_effect = Exception("db error")
        event = {"command_args": ""}
        karma._cmd_topkarma(mock_bot, event)
        mock_bot.logger.error.assert_called()


# ---------------------------------------------------------------------------
# Quotes Module Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestQuotesModule:
    """Tests for the quotes module."""

    def test_config_returns_expected_structure(self, mock_bot):
        from modules import quotes
        cfg = quotes.config(mock_bot)
        assert "quote" in cfg["commands"]
        assert "addquote" in cfg["commands"]

    def test_run_show_quote(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = (1, "hello world", "user1", "#test", datetime(2024, 1, 1))
        event = {"command": "quote", "command_args": "", "user_info": None, "channel": "#test"}
        quotes.run(mock_bot, event)
        assert any("Quote #1" in r["msg"] for r in mock_bot._active_output)

    def test_run_add_quote(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        # First fetchone: duplicate check returns None, second: INSERT RETURNING id returns (42,)
        mock_db_cursor.fetchone.side_effect = [None, (42,)]
        event = {
            "command": "addquote", "command_args": "hello world",
            "user_info": {"id": 42}, "channel": "#test",
        }
        quotes.run(mock_bot, event)
        assert any("added successfully" in r["msg"] for r in mock_bot._active_output)

    def test_run_delete_quote(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_bot._is_owner.return_value = True
        mock_db_cursor.fetchone.side_effect = [(1,), None]
        event = {
            "command": "delquote", "command_args": "1",
            "user_info": {"is_admin": True}, "hostmask": "owner!user@host",
        }
        quotes.run(mock_bot, event)
        assert any("deleted successfully" in r["msg"] for r in mock_bot._active_output)

    def test_run_search_quotes(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchall.return_value = [
            (1, "hello world", "user1", "#test", datetime(2024, 1, 1))
        ]
        event = {"command": "searchquote", "command_args": "hello", "channel": "#test"}
        quotes.run(mock_bot, event)
        assert any("Found 1 quotes" in r["msg"] for r in mock_bot._active_output)

    def test_show_quote_no_quotes(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = None
        event = {"command_args": "", "channel": "#test"}
        quotes._show_quote(mock_bot, event)
        assert any("No quotes found" in r["msg"] for r in mock_bot._active_output)

    def test_show_quote_by_id(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = (5, "test quote", "user2", "#test", datetime(2024, 2, 2))
        event = {"command_args": "5", "channel": "#test"}
        quotes._show_quote(mock_bot, event)
        assert any("Quote #5" in r["msg"] for r in mock_bot._active_output)

    def test_show_quote_by_search(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = (2, "hello", "user1", "#test", datetime(2024, 1, 1))
        event = {"command_args": "hello", "channel": "#test"}
        quotes._show_quote(mock_bot, event)
        assert any("Quote #2" in r["msg"] for r in mock_bot._active_output)

    def test_search_quotes_no_term(self, mock_bot):
        from modules import quotes
        event = {"command_args": ""}
        quotes._search_quotes(mock_bot, event)
        assert any("Please provide a search term" in r["msg"] for r in mock_bot._active_output)

    def test_search_quotes_no_results(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchall.return_value = []
        event = {"command_args": "xyz", "channel": "#test"}
        quotes._search_quotes(mock_bot, event)
        assert any("No quotes found matching" in r["msg"] for r in mock_bot._active_output)

    def test_search_quotes_with_results(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchall.return_value = [
            (1, "quote one", "u1", "#test", datetime(2024, 1, 1)),
            (2, "quote two", "u2", "#test", datetime(2024, 2, 1)),
        ]
        event = {"command_args": "quote", "channel": "#test"}
        quotes._search_quotes(mock_bot, event)
        assert any("Found 2 quotes" in r["msg"] for r in mock_bot._active_output)

    def test_add_quote_no_text(self, mock_bot):
        from modules import quotes
        event = {"command_args": "", "channel": "#test"}
        quotes._add_quote(mock_bot, event)
        assert any("Please provide a quote to add" in r["msg"] for r in mock_bot._active_output)

    def test_add_quote_not_registered(self, mock_bot):
        from modules import quotes
        event = {"command_args": "hello", "user_info": None, "channel": "#test"}
        quotes._add_quote(mock_bot, event)
        assert any("registered user" in r["msg"] for r in mock_bot._active_output)

    def test_add_quote_duplicate(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = (1,)
        event = {"command_args": "hello", "user_info": {"id": 1}, "channel": "#test"}
        quotes._add_quote(mock_bot, event)
        assert any("already exists" in r["msg"] for r in mock_bot._active_output)

    def test_add_quote_success(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.side_effect = [None, (42,)]
        event = {"command_args": "new quote", "user_info": {"id": 1}, "channel": "#test"}
        quotes._add_quote(mock_bot, event)
        assert any("Quote #42 added" in r["msg"] for r in mock_bot._active_output)

    def test_add_quote_exception(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.execute.side_effect = Exception("db fail")
        event = {"command_args": "new quote", "user_info": {"id": 1}, "channel": "#test"}
        quotes._add_quote(mock_bot, event)
        mock_db_conn.rollback.assert_called_once()
        assert any("Error adding quote" in r["msg"] for r in mock_bot._active_output)

    def test_delete_quote_no_permission(self, mock_bot):
        from modules import quotes
        mock_bot._is_owner.return_value = False
        event = {"command_args": "1", "user_info": {"is_admin": False}, "hostmask": "user!host"}
        quotes._delete_quote(mock_bot, event)
        assert any("Only the bot owner and admins" in r["msg"] for r in mock_bot._active_output)

    def test_delete_quote_invalid_id(self, mock_bot):
        from modules import quotes
        mock_bot._is_owner.return_value = True
        event = {"command_args": "abc", "user_info": {"is_admin": True}, "hostmask": "owner!host"}
        quotes._delete_quote(mock_bot, event)
        assert any("valid quote ID" in r["msg"] for r in mock_bot._active_output)

    def test_delete_quote_not_found(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot._is_owner.return_value = True
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.return_value = None
        event = {"command_args": "99", "user_info": {"is_admin": True}, "hostmask": "owner!host"}
        quotes._delete_quote(mock_bot, event)
        assert any("Quote #99 not found" in r["msg"] for r in mock_bot._active_output)

    def test_delete_quote_success(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot._is_owner.return_value = True
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.fetchone.side_effect = [(1,), None]
        event = {"command_args": "1", "user_info": {"is_admin": True}, "hostmask": "owner!host"}
        quotes._delete_quote(mock_bot, event)
        assert any("Quote #1 deleted successfully" in r["msg"] for r in mock_bot._active_output)

    def test_delete_quote_exception(self, mock_bot, mock_db_conn, mock_db_cursor):
        from modules import quotes
        mock_bot._is_owner.return_value = True
        mock_bot.db_get.return_value = mock_db_conn
        mock_db_cursor.execute.side_effect = Exception("db fail")
        event = {"command_args": "1", "user_info": {"is_admin": True}, "hostmask": "owner!host"}
        quotes._delete_quote(mock_bot, event)
        mock_db_conn.rollback.assert_called_once()


# ---------------------------------------------------------------------------
# URLs Module Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestUrlsModule:
    """Tests for the URLs module."""

    def test_config_returns_expected_structure(self, mock_bot):
        from modules import urls
        cfg = urls.config(mock_bot)
        assert "pubmsg" in cfg["events"]
        assert cfg["commands"] == []

    def test_run_not_pubmsg(self, mock_bot):
        from modules import urls
        event = {"trigger": "command", "signal": "privmsg", "text": "http://example.com"}
        assert urls.run(mock_bot, event) is None

    def test_run_no_urls(self, mock_bot):
        from modules import urls
        event = {"trigger": "event", "signal": "pubmsg", "text": "hello world"}
        assert urls.run(mock_bot, event) is None

    def test_run_unsafe_url(self, mock_bot):
        from modules import urls
        with patch("modules.urls.is_url_safe", return_value=(False, "private IP")):
            event = {"trigger": "event", "signal": "pubmsg", "text": "http://192.168.1.1"}
            urls.run(mock_bot, event)
        mock_bot.logger.warning.assert_called_once()

    def test_run_success(self, mock_bot):
        from modules import urls
        with patch("modules.urls.is_url_safe", return_value=(True, "")):
            with patch("modules.urls.get_url_title", return_value="Example Domain"):
                event = {"trigger": "event", "signal": "pubmsg", "text": "http://example.com"}
                urls.run(mock_bot, event)
        assert any("Example Domain" in r["msg"] for r in mock_bot._active_output)

    def test_run_exception(self, mock_bot):
        from modules import urls
        with patch("modules.urls.is_url_safe", return_value=(True, "")):
            with patch("modules.urls.get_url_title", side_effect=Exception("fetch error")):
                event = {"trigger": "event", "signal": "pubmsg", "text": "http://example.com"}
                urls.run(mock_bot, event)
        mock_bot.logger.error.assert_called_once()

    def test_extract_urls_with_http(self):
        from modules import urls
        text = "Check out http://example.com and https://test.org/page"
        result = urls.extract_urls(text)
        assert "http://example.com" in result
        assert "https://test.org/page" in result

    def test_extract_urls_with_www(self):
        from modules import urls
        text = "Visit www.example.com for more"
        result = urls.extract_urls(text)
        assert "www.example.com" in result

    def test_get_url_title_with_prefix(self):
        from modules import urls
        mock_resp = Mock()
        mock_resp.text = "<html><head><title>My Title</title></head><body></body></html>"
        mock_resp.raise_for_status = Mock()
        with patch("modules.urls.requests.get", return_value=mock_resp):
            result = urls.get_url_title("http://example.com")
        assert result == "My Title"

    def test_get_url_title_adds_prefix(self):
        from modules import urls
        mock_resp = Mock()
        mock_resp.text = "<html><head><title>Title</title></head><body></body></html>"
        mock_resp.raise_for_status = Mock()
        with patch("modules.urls.requests.get", return_value=mock_resp) as mock_get:
            urls.get_url_title("example.com")
        assert "http://example.com" in mock_get.call_args[0][0]

    def test_get_url_title_no_title_tag(self):
        from modules import urls
        mock_resp = Mock()
        mock_resp.text = "<html><body>No title</body></html>"
        mock_resp.raise_for_status = Mock()
        with patch("modules.urls.requests.get", return_value=mock_resp):
            result = urls.get_url_title("http://example.com")
        assert result is None

    def test_get_url_title_exception(self):
        from modules import urls
        with patch("modules.urls.requests.get", side_effect=Exception("timeout")):
            result = urls.get_url_title("http://example.com")
        assert result is None

    def test_get_url_title_truncates_long_title(self):
        from modules import urls
        long_title = "A" * 250
        mock_resp = Mock()
        mock_resp.text = f"<html><head><title>{long_title}</title></head><body></body></html>"
        mock_resp.raise_for_status = Mock()
        with patch("modules.urls.requests.get", return_value=mock_resp):
            result = urls.get_url_title("http://example.com")
        assert len(result) == 200
        assert result.endswith("...")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
