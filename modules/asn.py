#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ASN lookup module for PhreakBot

import ipaddress
import json
import re
import sys

import requests

# Check if this module is being reloaded
if "asn" in sys.modules:
    # This is a reload, not a fresh import
    print("ASN module is being reloaded, not restarting the bot")


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["asn"],
        "permissions": ["user"],
        "help": "Look up ASN information for an IP address or AS number.\n"
        "Usage: !asn <IP address> - Look up ASN info for an IP address\n"
        "       !asn AS<number> - Look up ASN info for an AS number (e.g., AS15169)",
    }


def run(bot, event):
    """Handle ASN lookup command"""
    if event["command"] != "asn":
        return

    query = event["command_args"].strip()

    if not query:
        bot.add_response(
            "Please provide an IP address or AS number (e.g., !asn 8.8.8.8 or !asn AS15169)"
        )
        return

    # Check if the query is an AS number
    as_match = re.match(r"^(?:AS)?(\d+)$", query, re.IGNORECASE)
    if as_match:
        asn = as_match.group(1)
        lookup_asn_by_number(bot, asn)
        return

    # Check if the query is an IP address
    try:
        ip = ipaddress.ip_address(query)
        lookup_asn_by_ip(bot, query)
        return
    except ValueError:
        bot.add_response(
            f"Invalid input: {query}. Please provide a valid IP address or AS number."
        )
        return


def lookup_asn_by_ip(bot, ip):
    """Look up ASN information for an IP address"""
    try:
        # Use bgp.tools API for IP to ASN lookup
        response = requests.get(
            f"https://bgp.tools/prefix/{ip}",
            headers={"Accept": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Extract ASN and network information
        asn = data.get("asn", "Unknown")
        name = data.get("name", "Unknown")
        prefix = data.get("prefix", ip)
        country = data.get("country_code", "Unknown")

        # Combine all information into a single line
        result = f"ASN Lookup for {ip}: AS{asn} ({name}) | Prefix: {prefix} | Country: {country}"
        bot.add_response(result)

    except Exception as e:
        bot.logger.error(f"Error looking up ASN for IP {ip}: {e}")
        bot.add_response(f"Error looking up ASN information: {str(e)}")


def lookup_asn_by_number(bot, asn):
    """Look up ASN information for an AS number"""
    try:
        # Use bgp.tools API for ASN lookup
        response = requests.get(
            f"https://bgp.tools/as/{asn}",
            headers={"Accept": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Extract ASN information
        name = data.get("name", "Unknown")
        description = data.get("description", name)
        country = data.get("country_code", "Unknown")

        # Get prefix counts
        prefix_v4 = data.get("ipv4_prefixes", 0)
        prefix_v6 = data.get("ipv6_prefixes", 0)
        total_prefixes = prefix_v4 + prefix_v6

        prefix_info = f" | Prefixes: {total_prefixes} total (IPv4: {prefix_v4}, IPv6: {prefix_v6})"

        result = (
            f"ASN Lookup for AS{asn}: {description} | Country: {country}{prefix_info}"
        )
        bot.add_response(result)

    except Exception as e:
        bot.logger.error(f"Error looking up ASN {asn}: {e}")
        bot.add_response(f"Error looking up ASN information: {str(e)}")


def format_location(country, region, city):
    """Format location information"""
    parts = []
    if city:
        parts.append(city)
    if region and region != city:  # Avoid duplication if city and region are the same
        parts.append(region)
    if country:
        parts.append(country)

    return ", ".join(parts) if parts else "Unknown"
