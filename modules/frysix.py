#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Frys-IX member information module for PhreakBot

import json
import requests
import threading
import time
from datetime import datetime

# Global variables to store member data
members_data = {}
last_check_time = None
member_asns = set()  # To track existing members for change detection
lock = threading.RLock()  # Thread-safe lock for accessing shared data

# API endpoint
FRYSIX_API_URL = "https://ixpmanager.frys-ix.net/api/v4/member-export/ixf/1.0"

def config(bot):
    """Return module configuration"""
    return {
        "events": ["welcome"],  # Start the background thread when the bot connects
        "commands": ["member", "frysix"],
        "permissions": ["user"],
        "help": "Get information about Frys-IX members.\n"
        "Usage: !member <ASN> - Look up a member by ASN number\n"
        "       !frysix list - List all members\n"
        "       !frysix stats - Show statistics about Frys-IX"
    }

def run(bot, event):
    """Handle commands and events"""
    # Start background thread on welcome event
    if event["signal"] == "welcome":
        start_background_thread(bot)
        return

    # Handle commands
    if event["command"] in ["member", "frysix"]:
        with lock:
            # Check if we have data
            if not members_data:
                bot.add_response("No Frys-IX member data available yet. Please try again later.")
                return

        if event["command"] == "member":
            handle_member_command(bot, event)
        elif event["command"] == "frysix":
            handle_frysix_command(bot, event)

def handle_member_command(bot, event):
    """Handle !member command to look up a specific ASN"""
    query = event["command_args"].strip()

    if not query:
        bot.add_response("Please provide an ASN number (e.g., !member 15169)")
        return

    # Remove 'AS' prefix if present
    if query.upper().startswith('AS'):
        query = query[2:]

    # Try to convert to integer
    try:
        asn = int(query)
    except ValueError:
        bot.add_response(f"Invalid ASN: {query}. Please provide a valid ASN number.")
        return

    # Look up the ASN in our data
    with lock:
        member = find_member_by_asn(asn)

    if member:
        # Format and display member information
        response = format_member_info(member)
        bot.add_response(response)
    else:
        bot.add_response(f"No member found with ASN {asn} at Frys-IX.")

def handle_frysix_command(bot, event):
    """Handle !frysix command with various subcommands"""
    args = event["command_args"].strip().split()
    subcommand = args[0].lower() if args else "help"

    if subcommand == "list":
        # List all members (limited to avoid flooding)
        with lock:
            if not members_data or "member_list" not in members_data:
                bot.add_response("No Frys-IX member data available.")
                return

            members = members_data.get("member_list", [])

        # Sort members by name
        sorted_members = sorted(members, key=lambda m: m.get("member_name", ""))

        # Limit to first 15 members to avoid flooding
        display_members = sorted_members[:15]

        response = "Frys-IX Members: "
        member_strings = []
        for member in display_members:
            asn = member.get("asnum")
            name = member.get("member_name")
            member_strings.append(f"{name} (AS{asn})")

        response += ", ".join(member_strings)

        if len(sorted_members) > 15:
            response += f" and {len(sorted_members) - 15} more. Use !member <ASN> for details."

        bot.add_response(response)

    elif subcommand == "stats":
        # Show statistics about Frys-IX
        with lock:
            if not members_data:
                bot.add_response("No Frys-IX member data available.")
                return

            members = members_data.get("member_list", [])

        total_members = len(members)
        total_connections = sum(len(member.get("connection_list", [])) for member in members)

        # Count IPv4 and IPv6 enabled members
        ipv4_members = sum(1 for member in members if any(
            conn.get("vlan_list", []) and any(
                vlan.get("ipv4", {}).get("address") for vlan in conn.get("vlan_list", [])
            ) for conn in member.get("connection_list", [])
        ))

        ipv6_members = sum(1 for member in members if any(
            conn.get("vlan_list", []) and any(
                vlan.get("ipv6", {}).get("address") for vlan in conn.get("vlan_list", [])
            ) for conn in member.get("connection_list", [])
        ))

        # Get last update time
        last_update = "Unknown"
        if last_check_time:
            last_update = last_check_time.strftime("%Y-%m-%d %H:%M:%S UTC")

        response = f"Frys-IX Stats: {total_members} members, {total_connections} connections, "
        response += f"{ipv4_members} with IPv4, {ipv6_members} with IPv6. Last updated: {last_update}"

        bot.add_response(response)

    else:
        # Show help
        bot.add_response("Frys-IX commands: !frysix list - List members, !frysix stats - Show statistics, !member <ASN> - Look up member")

def start_background_thread(bot):
    """Start a background thread to periodically check for updates"""
    bot.logger.info("Starting Frys-IX background update thread")

    def update_thread():
        while True:
            try:
                check_for_updates(bot)
                # Sleep for 5 minutes (300 seconds)
                time.sleep(300)
            except Exception as e:
                bot.logger.error(f"Error in Frys-IX update thread: {e}")
                # Sleep for 1 minute before retrying after an error
                time.sleep(60)

    # Create and start the thread
    thread = threading.Thread(target=update_thread, daemon=True)
    thread.start()
    bot.logger.info("Frys-IX update thread started")

def check_for_updates(bot):
    """Check for updates to the Frys-IX member list"""
    global members_data, last_check_time, member_asns

    bot.logger.info("Checking for Frys-IX member updates")

    try:
        # Fetch data from API
        response = requests.get(FRYSIX_API_URL, timeout=30)
        response.raise_for_status()
        new_data = response.json()

        # Update last check time
        current_time = datetime.utcnow()

        # Process the data
        with lock:
            # Check for new members if we already have data
            if members_data and "member_list" in members_data and "member_list" in new_data:
                old_members = members_data.get("member_list", [])
                new_members = new_data.get("member_list", [])

                # Get ASNs of current members
                old_asns = {member.get("asnum") for member in old_members if "asnum" in member}
                new_asns = {member.get("asnum") for member in new_members if "asnum" in member}

                # Find new members
                added_asns = new_asns - old_asns
                if added_asns:
                    # Announce new members in channels
                    for asn in added_asns:
                        member = next((m for m in new_members if m.get("asnum") == asn), None)
                        if member:
                            announce_new_member(bot, member)

            # Update stored data
            members_data = new_data
            last_check_time = current_time

            # Update member ASNs set
            if "member_list" in new_data:
                member_asns = {member.get("asnum") for member in new_data.get("member_list", []) if "asnum" in member}

        bot.logger.info(f"Frys-IX member data updated successfully. {len(member_asns)} members found.")

    except Exception as e:
        bot.logger.error(f"Error fetching Frys-IX member data: {e}")

def find_member_by_asn(asn):
    """Find a member by ASN in the stored data"""
    if not members_data or "member_list" not in members_data:
        return None

    for member in members_data.get("member_list", []):
        if member.get("asnum") == asn:
            return member

    return None

def format_member_info(member):
    """Format member information for display"""
    name = member.get("member_name", "Unknown")
    asn = member.get("asnum", "Unknown")
    url = member.get("url", "")

    # Get connection details
    connections = member.get("connection_list", [])
    connection_count = len(connections)

    # Check for IPv4 and IPv6 addresses
    has_ipv4 = False
    has_ipv6 = False
    speed = 0

    for conn in connections:
        if "state" in conn and conn["state"] != "active":
            continue

        # Sum up speeds
        if "if_list" in conn:
            for interface in conn.get("if_list", []):
                if "if_speed" in interface:
                    speed += interface.get("if_speed", 0)

        # Check for IP addresses
        for vlan in conn.get("vlan_list", []):
            if vlan.get("ipv4", {}).get("address"):
                has_ipv4 = True
            if vlan.get("ipv6", {}).get("address"):
                has_ipv6 = True

    # Format speed in appropriate units
    speed_str = "Unknown"
    if speed > 0:
        if speed >= 1000:
            speed_str = f"{speed/1000:.0f} Gbps"
        else:
            speed_str = f"{speed} Mbps"

    # Build response
    response = f"Frys-IX Member: {name} (AS{asn})"
    if url:
        response += f" | Website: {url}"

    response += f" | Connections: {connection_count}"
    response += f" | Speed: {speed_str}"
    response += f" | IPv4: {'Yes' if has_ipv4 else 'No'}"
    response += f" | IPv6: {'Yes' if has_ipv6 else 'No'}"

    return response

def announce_new_member(bot, member):
    """Announce a new member in all channels"""
    name = member.get("member_name", "Unknown")
    asn = member.get("asnum", "Unknown")

    announcement = f"New member at Frys-IX: {name} (AS{asn}). Use !member {asn} for details."

    # Send to all channels the bot is in
    for channel in bot.channels.keys():
        bot.say(channel, announcement)

    bot.logger.info(f"Announced new Frys-IX member: {name} (AS{asn})")
