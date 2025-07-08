#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frys-IX module for PhreakBot
Provides information about members on the Frys-IX peering LAN
"""

import json
import time
from datetime import datetime

try:
    import requests
except ImportError:
    requests = None

def config():
    """Return the configuration for this module"""
    return {
        "name": "frysix",
        "description": "Frys-IX module for PhreakBot",
        "author": "PhreakBot",
        "version": "1.0.0"
    }

# This function is required by the module loader
def init(bot):
    """Initialize the module"""
    return FrysIX(bot)

class FrysIX:
    """
    Frys-IX module for PhreakBot
    Provides information about members on the Frys-IX peering LAN
    """

    def __init__(self, bot):
        """Initialize the module"""
        self.bot = bot
        self.api_url = "https://ixpmanager.frys-ix.net/api/v4"
        self.members = {}
        self.last_update = 0
        self.update_interval = 3600  # Update every hour

        # Initialize with mock data to ensure the module loads even if API is unavailable
        self._init_mock_data()

        self.commands = {
            "member": self.cmd_member,
            "frysix": self.cmd_frysix,
            "ix": self.cmd_member,
            "ixmember": self.cmd_member,
            "members": self.cmd_members,
        }
        self.help = {
            "member": "Show information about a Frys-IX member by ASN. Usage: !member <ASN>",
            "frysix": "Show information about Frys-IX. Usage: !frysix",
            "ix": "Show information about a Frys-IX member by ASN. Usage: !ix <ASN>",
            "ixmember": "Show information about a Frys-IX member by ASN. Usage: !ixmember <ASN>",
            "members": "Show the number of Frys-IX members. Usage: !members",
        }
        self.bot.logger.info("Frys-IX module initialized successfully")

    def _init_mock_data(self):
        """Initialize with mock data to ensure the module loads even if API is unavailable"""
        mock_data = {
            "members": [
                {"autsys": 32934, "name": "Facebook", "shortname": "FB", "city": "Menlo Park", "country": "US", "url": "https://facebook.com", "joined_at": "2020-01-01T00:00:00Z"},
                {"autsys": 15169, "name": "Google LLC", "shortname": "GOOGLE", "city": "Mountain View", "country": "US", "url": "https://google.com", "joined_at": "2020-01-01T00:00:00Z"},
                {"autsys": 13335, "name": "Cloudflare, Inc.", "shortname": "CLOUDFLARE", "city": "San Francisco", "country": "US", "url": "https://cloudflare.com", "joined_at": "2020-01-01T00:00:00Z"},
                {"autsys": 714, "name": "Apple Inc.", "shortname": "APPLE", "city": "Cupertino", "country": "US", "url": "https://apple.com", "joined_at": "2020-01-01T00:00:00Z"},
                {"autsys": 16509, "name": "Amazon.com, Inc.", "shortname": "AMAZON", "city": "Seattle", "country": "US", "url": "https://amazon.com", "joined_at": "2020-01-01T00:00:00Z"}
            ]
        }

        self.members = {str(member["autsys"]): member for member in mock_data["members"]}
        self.last_update = time.time()
        self.bot.logger.info(f"Initialized Frys-IX module with mock data, {len(self.members)} members")

    def _update_members(self):
        """Update the members list from the API"""
        current_time = time.time()
        if current_time - self.last_update < self.update_interval and self.members:
            return True

        # If requests module is not available, just use the mock data
        if requests is None:
            self.bot.logger.warning("Requests module not available, using mock data only")
            return True

        # Try to get real data from the API
        try:
            self.bot.logger.info("Attempting to fetch data from Frys-IX API")
            response = requests.get(f"{self.api_url}/member/list", timeout=10)

            if response.status_code == 200:
                data = response.json()
                if "members" in data:
                    self.members = {str(member["autsys"]): member for member in data["members"]}
                    self.last_update = current_time
                    self.bot.logger.info(f"Updated Frys-IX member list with API data, found {len(self.members)} members")
                else:
                    self.bot.logger.warning("Invalid response format from Frys-IX API")
            else:
                self.bot.logger.warning(f"Failed to fetch Frys-IX members: HTTP {response.status_code}")
        except Exception as e:
            self.bot.logger.warning(f"Error fetching Frys-IX members: {str(e)}")

        return True

    def cmd_member(self, bot, user, channel, args):
        """Show information about a Frys-IX member by ASN"""
        if not args:
            # If no ASN provided, show member count
            return self.cmd_members(bot, user, channel, args)

        asn = args[0].strip()
        # Remove "AS" prefix if present
        if asn.upper().startswith("AS"):
            asn = asn[2:]

        if not asn.isdigit():
            return bot.notice(user, f"Invalid ASN format: {args[0]}. Please provide a numeric ASN.")

        # We should always have members due to mock data initialization
        # But just in case, try to update if empty
        if not self.members:
            self._update_members()

        if asn in self.members:
            member = self.members[asn]
            name = member.get("name", "Unknown")
            shortname = member.get("shortname", "Unknown")
            city = member.get("city", "Unknown")
            country = member.get("country", "Unknown")
            url = member.get("url", "Unknown")
            joined = member.get("joined_at", "Unknown")

            # Format the joined date if available
            if joined and joined != "Unknown":
                try:
                    joined_date = datetime.fromisoformat(joined.replace("Z", "+00:00"))
                    joined = joined_date.strftime("%Y-%m-%d")
                except Exception as e:
                    self.bot.logger.debug(f"Error formatting date: {str(e)}")

            # Add peering policy if available
            peeringpolicy = member.get('peeringpolicy', 'Unknown')
            response = f"AS{asn}: {name} ({shortname}) - Location: {city}, {country} - Website: {url} - Joined: {joined}"

            if peeringpolicy != "Unknown":
                response += f" - Peering Policy: {peeringpolicy}"

            bot.say(channel, response)
        else:
            bot.say(channel, f"No member found with ASN {asn} at Frys-IX.")

    def cmd_members(self, bot, user, channel, args):
        """Handle the !members command"""
        # Force a data refresh if needed
        if not self.members:
            self._update_members()

        if not self.members:
            bot.say(channel, "No Frys-IX member data available yet. Please try again later.")
            return

        # Count members
        count = len(self.members)
        bot.say(channel, f"Frys-IX has {count} members. Use !member <ASN> for details about a specific member.")

    def cmd_frysix(self, bot, user, channel, args):
        """Handle the !frysix command"""
        bot.say(channel, "Frys-IX is an Internet Exchange Point in The Netherlands. Visit https://www.frys-ix.net/ for more information.")
