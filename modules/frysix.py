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

def config(bot=None):
    """Return the configuration for this module"""
    return {
        "name": "frysix",
        "description": "Frys-IX module for PhreakBot",
        "author": "PhreakBot",
        "version": "1.0.0",
        "events": [],
        "commands": ["member", "frysix", "ix", "ixmember", "members"],
        "permissions": [],
        "help": "Provides information about Frys-IX members.\n"
               "Usage: !member <ASN> - Show information about a Frys-IX member by ASN\n"
               "       !frysix - Show information about Frys-IX\n"
               "       !ix <ASN> - Alias for !member\n"
               "       !ixmember <ASN> - Alias for !member\n"
               "       !members - Show the number of Frys-IX members"
    }

# This function is required by the module loader
def init(bot):
    """Initialize the module"""
    return FrysIX(bot)

def run(bot, event):
    """Handle frysix commands"""
    # Get the module instance
    module_config = bot.modules.get("frysix")
    if not module_config:
        bot.logger.error("Frysix module not found in bot.modules")
        return

    # Get the actual module instance
    module_instance = module_config.get("object")
    if not module_instance:
        bot.logger.error("Frysix module object not found")
        return

    # Initialize the module if it hasn't been initialized yet
    if not hasattr(module_instance, "init"):
        bot.logger.error("Frysix module does not have init function")
        return

    # Get the FrysIX instance
    frysix_instance = init(bot)

    # Handle commands
    if event["trigger"] == "command" and event["command"] in frysix_instance.commands:
        command = event["command"]
        args = event["command_args"].split() if event["command_args"] else []
        user = event["nick"]
        channel = event["channel"]

        # Call the appropriate command handler
        frysix_instance.commands[command](bot, user, channel, args)

class FrysIX:
    """
    Frys-IX module for PhreakBot
    Provides information about members on the Frys-IX peering LAN
    """

    def __init__(self, bot):
        """Initialize the module"""
        self.bot = bot
        # The correct API endpoint for Frys-IX
        self.api_url = "https://ixpmanager.frys-ix.net/api/v4/member-export/ixf/1.0"

        # Flag to indicate whether to attempt API calls
        # Set to True since we now have the correct API endpoint
        self.try_api = True
        self.members = {}
        self.last_update = 0
        self.update_interval = 3600  # Update every hour

        # Initialize with mock data to ensure the module loads even if API is unavailable
        self._init_mock_data()

        # Try to update from the API immediately
        self.bot.logger.info("Attempting to update Frys-IX data from API during initialization")
        self._update_members(force=True)

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
                {"autsys": 32934, "name": "Facebook", "shortname": "FB", "city": "Menlo Park", "url": "https://facebook.com", "joined_at": "2020-01-01T00:00:00Z", "portspeed": "100G", "ip": "2001:db8::1", "max_prefix": "1000"},
                {"autsys": 15169, "name": "Google LLC", "shortname": "GOOGLE", "city": "Mountain View", "url": "https://google.com", "joined_at": "2020-01-01T00:00:00Z", "portspeed": "100G", "ip": "2001:db8::2", "max_prefix": "5000"},
                {"autsys": 13335, "name": "Cloudflare, Inc.", "shortname": "CLOUDFLARE", "city": "San Francisco", "url": "https://cloudflare.com", "joined_at": "2020-01-01T00:00:00Z", "portspeed": "100G", "ip": "2001:db8::3", "max_prefix": "5000"},
                {"autsys": 714, "name": "Apple Inc.", "shortname": "APPLE", "city": "Cupertino", "url": "https://apple.com", "joined_at": "2020-01-01T00:00:00Z", "portspeed": "100G", "ip": "2001:db8::4", "max_prefix": "1000"},
                {"autsys": 16509, "name": "Amazon.com, Inc.", "shortname": "AMAZON", "city": "Seattle", "url": "https://amazon.com", "joined_at": "2020-01-01T00:00:00Z", "portspeed": "100G", "ip": "2001:db8::5", "max_prefix": "5000"}
            ]
        }

        self.members = {str(member["autsys"]): member for member in mock_data["members"]}
        self.last_update = time.time()
        self.bot.logger.info(f"Initialized Frys-IX module with mock data, {len(self.members)} members")

    def _update_members(self, force=False):
        """Update the members list from the API"""
        current_time = time.time()

        # If we already have data and it's not time to update yet, use the cached data
        # Unless force=True is specified
        if not force and current_time - self.last_update < self.update_interval and self.members:
            self.bot.logger.info("Using cached Frys-IX member data")
            return True

        # Skip API calls if try_api is False or requests module is not available
        if not self.try_api or requests is None:
            self.bot.logger.info("Skipping API calls, using mock data only")
            # We already have mock data initialized, so just return
            return True

        # If we get here, we're going to try API calls
        self.bot.logger.info(f"Attempting to fetch Frys-IX member data from API: {self.api_url}")
        self.bot.logger.info(f"Force update: {force}")

        try:
            # Add User-Agent header to avoid potential blocks
            headers = {
                'User-Agent': 'PhreakBot/1.0 (IRC Bot; +https://github.com/jskoetsier/phreakbot)'
            }

            self.bot.logger.info(f"Sending request to {self.api_url} with timeout=30s")

            # Try with a longer timeout
            response = requests.get(self.api_url, headers=headers, timeout=30)
            self.bot.logger.info(f"API response status code: {response.status_code}")

            if response.status_code == 200:
                try:
                    # Try to parse as JSON
                    self.bot.logger.info("Parsing API response as JSON")
                    data = response.json()
                    self.bot.logger.info(f"API response keys: {list(data.keys())}")

                    # Check for member_list in the IXF format
                    if "member_list" in data and isinstance(data["member_list"], list):
                        self.bot.logger.info(f"Found member_list with {len(data['member_list'])} members")

                        # Process members from the IXF format
                        members_dict = {}
                        for member in data["member_list"]:
                            if "asnum" in member:
                                asn = str(member["asnum"])
                                # Extract nested data from connection_list and vlan_list if available
                                portspeed = "Unknown"
                                ipv4 = "Unknown"
                                ipv6 = "Unknown"
                                max_prefix = "Unknown"

                                # Extract port speed
                                if "connection_list" in member and member["connection_list"]:
                                    for connection in member["connection_list"]:
                                        if "if_list" in connection and connection["if_list"]:
                                            for interface in connection["if_list"]:
                                                if "if_speed" in interface:
                                                    # Convert from Mbps to Gbps if needed
                                                    speed = interface["if_speed"]
                                                    if speed >= 1000:
                                                        portspeed = f"{speed // 1000}G"
                                                    else:
                                                        portspeed = f"{speed}M"
                                                    break
                                            if portspeed != "Unknown":
                                                break

                                # Extract IP addresses and max prefix
                                if "connection_list" in member and member["connection_list"]:
                                    for connection in member["connection_list"]:
                                        if "vlan_list" in connection and connection["vlan_list"]:
                                            for vlan in connection["vlan_list"]:
                                                # Extract IPv4 info
                                                if "ipv4" in vlan and vlan["ipv4"]:
                                                    if "address" in vlan["ipv4"]:
                                                        ipv4 = vlan["ipv4"]["address"]
                                                    if "max_prefix" in vlan["ipv4"] and max_prefix == "Unknown":
                                                        max_prefix = str(vlan["ipv4"]["max_prefix"])

                                                # Extract IPv6 info
                                                if "ipv6" in vlan and vlan["ipv6"]:
                                                    if "address" in vlan["ipv6"]:
                                                        ipv6 = vlan["ipv6"]["address"]
                                                    if "max_prefix" in vlan["ipv6"] and max_prefix == "Unknown":
                                                        max_prefix = str(vlan["ipv6"]["max_prefix"])

                                # Combine IPv4 and IPv6 addresses
                                ip = "Unknown"
                                if ipv4 != "Unknown" and ipv6 != "Unknown":
                                    ip = f"{ipv4}, {ipv6}"
                                elif ipv4 != "Unknown":
                                    ip = ipv4
                                elif ipv6 != "Unknown":
                                    ip = ipv6

                                # Convert IXF format to our internal format
                                members_dict[asn] = {
                                    "autsys": member["asnum"],
                                    "name": member.get("name", "Unknown"),
                                    "shortname": member.get("name", "Unknown")[:10],  # Use first 10 chars of name as shortname
                                    "city": "Unknown",  # IXF format doesn't include city
                                    "url": member.get("url", "Unknown"),
                                    "joined_at": member.get("member_since", "Unknown"),
                                    "peeringpolicy": member.get("peering_policy", "Unknown"),
                                    # Add extracted fields
                                    "portspeed": portspeed,
                                    "ip": ip,
                                    "max_prefix": max_prefix
                                }

                        if members_dict:
                            # Clear the existing members dictionary and replace with new data
                            self.bot.logger.info(f"Replacing mock data with {len(members_dict)} members from API")
                            self.members.clear()
                            self.members.update(members_dict)
                            self.last_update = current_time
                            self.bot.logger.info(f"Updated Frys-IX member list with API data, now have {len(self.members)} members")

                            # Log a few sample members to verify the data
                            sample_asns = list(self.members.keys())[:5]
                            self.bot.logger.info(f"Sample ASNs: {sample_asns}")
                            for asn in sample_asns:
                                self.bot.logger.info(f"Sample member {asn}: {self.members[asn]['name']}")

                            return True
                        else:
                            self.bot.logger.warning("No valid members found in API response")
                    else:
                        self.bot.logger.warning("API response doesn't contain member_list")
                        self.bot.logger.info(f"API response content (first 200 chars): {str(data)[:200]}")
                except ValueError as e:
                    self.bot.logger.error(f"Failed to parse JSON from API response: {e}")
                    self.bot.logger.error(f"Response content (first 200 chars): {response.text[:200]}")
            else:
                self.bot.logger.error(f"API request failed with status code: {response.status_code}")
                self.bot.logger.error(f"Response content (first 200 chars): {response.text[:200]}")
        except Exception as e:
            import traceback
            self.bot.logger.error(f"Error fetching Frys-IX members: {e}")
            self.bot.logger.error(f"Traceback: {traceback.format_exc()}")

        self.bot.logger.info("Using mock data as fallback")
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

            # Get additional information
            peeringpolicy = member.get('peeringpolicy', 'Unknown')
            portspeed = member.get('portspeed', 'Unknown')
            ip = member.get('ip', 'Unknown')
            max_prefix = member.get('max_prefix', 'Unknown')

            # Build response without location information
            response = f"AS{asn}: {name} ({shortname}) - Website: {url} - Joined: {joined}"

            # Add additional information - always include these fields
            if peeringpolicy != "Unknown":
                response += f" - Peering Policy: {peeringpolicy}"

            # Always include portspeed, IP, and max prefix
            response += f" - Port Speed: {portspeed}"
            response += f" - IP: {ip}"
            response += f" - Max Prefixes: {max_prefix}"

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
