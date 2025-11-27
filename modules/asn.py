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
        # Use ipinfo.io API for IP to ASN lookup (free tier, no auth needed)
        response = requests.get(
            f"https://ipinfo.io/{ip}/json",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        # Extract ASN and network information
        org = data.get("org", "Unknown")
        asn = "Unknown"
        name = org

        # Parse ASN from org field (format: "AS15169 Google LLC")
        if org and org.startswith("AS"):
            parts = org.split(" ", 1)
            asn = parts[0].replace("AS", "")
            if len(parts) > 1:
                name = parts[1]

        city = data.get("city", "")
        region = data.get("region", "")
        country = data.get("country", "Unknown")

        location = ", ".join(filter(None, [city, region, country]))

        # Combine all information into a single line
        result = f"ASN Lookup for {ip}: AS{asn} ({name}) | Location: {location}"
        bot.add_response(result)

    except Exception as e:
        bot.logger.error(f"Error looking up ASN for IP {ip}: {e}")
        bot.add_response(f"Error looking up ASN information: {str(e)}")


def lookup_asn_by_number(bot, asn):
    """Look up ASN information for an AS number"""
    try:
        # Use RIPE NCC API - more reliable and open
        response = requests.get(
            f"https://stat.ripe.net/data/as-overview/data.json?resource=AS{asn}",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            bot.add_response(f"Failed to look up information for AS{asn}")
            return

        asn_data = data.get("data", {})
        holder = asn_data.get("holder", "Unknown")
        announced = asn_data.get("announced", False)

        # Try to get prefix information
        prefix_info = ""
        if announced:
            try:
                response2 = requests.get(
                    f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{asn}",
                    timeout=10,
                )
                if response2.status_code == 200:
                    prefix_data = response2.json()
                    if prefix_data.get("status") == "ok":
                        prefixes = prefix_data.get("data", {}).get("prefixes", [])

                        # Count IPv4 and IPv6 prefixes
                        ipv4_count = sum(
                            1 for p in prefixes if ":" not in p.get("prefix", "")
                        )
                        ipv6_count = sum(
                            1 for p in prefixes if ":" in p.get("prefix", "")
                        )
                        total = len(prefixes)

                        prefix_info = f" | Prefixes: {total} total (IPv4: {ipv4_count}, IPv6: {ipv6_count})"
            except:
                pass

        if not prefix_info:
            status = "Announced" if announced else "Not announced"
            prefix_info = f" | Status: {status}"

        result = f"ASN Lookup for AS{asn}: {holder}{prefix_info}"
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
