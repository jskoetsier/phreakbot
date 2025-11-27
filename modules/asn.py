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
        # Use ip-api.com for IP to ASN lookup
        response = requests.get(
            f"http://ip-api.com/json/{ip}?fields=as,asname,country,regionName,city,org",
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "fail":
            bot.add_response(
                f"Failed to look up ASN for IP {ip}: {data.get('message', 'Unknown error')}"
            )
            return

        # Extract ASN number from the AS field (format: "AS15169 Google LLC")
        as_info = data.get("as", "")
        asn = "Unknown"
        if as_info:
            as_match = re.match(r"^AS(\d+)\s", as_info)
            if as_match:
                asn = as_match.group(1)

        company = data.get("org", data.get("asname", "Unknown"))
        location = format_location(
            data.get("country"), data.get("regionName"), data.get("city")
        )

        # Combine all information into a single line
        result = f"ASN Lookup for {ip}: AS{asn} | Organization: {company} | Location: {location}"
        bot.add_response(result)

    except Exception as e:
        bot.logger.error(f"Error looking up ASN for IP {ip}: {e}")
        bot.add_response(f"Error looking up ASN information: {str(e)}")


def lookup_asn_by_number(bot, asn):
    """Look up ASN information for an AS number"""
    try:
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

        country_code = ""
        announced = asn_data.get("announced", False)

        prefix_count = 0
        if announced:
            response2 = requests.get(
                f"https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS{asn}",
                timeout=10,
            )
            if response2.status_code == 200:
                prefix_data = response2.json()
                if prefix_data.get("status") == "ok":
                    prefixes = prefix_data.get("data", {}).get("prefixes", [])
                    prefix_count = len(prefixes)

                    if prefixes and len(prefixes) > 0:
                        sample_prefixes = [p.get("prefix", "") for p in prefixes[:3]]
                        prefix_info = f" | Prefixes: {prefix_count} total (e.g., {', '.join(sample_prefixes)})"
                    else:
                        prefix_info = f" | Prefixes: {prefix_count}"
                else:
                    prefix_info = ""
            else:
                prefix_info = ""
        else:
            prefix_info = " | Status: Not currently announced"

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
