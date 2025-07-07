#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ASN lookup module for PhreakBot

import re
import requests
import json
import ipaddress


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
        bot.add_response("Please provide an IP address or AS number (e.g., !asn 8.8.8.8 or !asn AS15169)")
        return

    # Check if the query is an AS number
    as_match = re.match(r'^(?:AS)?(\d+)$', query, re.IGNORECASE)
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
        bot.add_response(f"Invalid input: {query}. Please provide a valid IP address or AS number.")
        return


def lookup_asn_by_ip(bot, ip):
    """Look up ASN information for an IP address"""
    try:
        # Use ip-api.com for IP to ASN lookup
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=as,asname,country,regionName,city,org", timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "fail":
            bot.add_response(f"Failed to look up ASN for IP {ip}: {data.get('message', 'Unknown error')}")
            return

        # Extract ASN number from the AS field (format: "AS15169 Google LLC")
        as_info = data.get("as", "")
        asn = "Unknown"
        if as_info:
            as_match = re.match(r'^AS(\d+)\s', as_info)
            if as_match:
                asn = as_match.group(1)

        company = data.get("org", data.get("asname", "Unknown"))
        location = format_location(data.get("country"), data.get("regionName"), data.get("city"))

        # Combine all information into a single line
        result = f"ASN Lookup for {ip}: AS{asn} | Organization: {company} | Location: {location}"
        bot.add_response(result)

    except Exception as e:
        bot.logger.error(f"Error looking up ASN for IP {ip}: {e}")
        bot.add_response(f"Error looking up ASN information: {str(e)}")


def lookup_asn_by_number(bot, asn):
    """Look up ASN information for an AS number"""
    try:
        # Use ASN.cymru.com for ASN lookup
        # This is a whois-based lookup that returns ASN information
        response = requests.get(f"https://api.bgpview.io/asn/{asn}", timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("status") == "ok":
            bot.add_response(f"Failed to look up information for AS{asn}")
            return

        asn_data = data.get("data", {})
        name = asn_data.get("name", "Unknown")
        description = asn_data.get("description_short", asn_data.get("description", "Unknown"))

        # Get country information
        country_code = asn_data.get("country_code", "")
        country = asn_data.get("rir_allocation", {}).get("country_name", "Unknown")
        
        # Get some prefixes if available
        prefix_info = ""
        prefixes = asn_data.get("prefixes", [])
        if prefixes and len(prefixes) > 0:
            prefix_count = len(prefixes)
            sample_prefixes = [p.get("prefix", "") for p in prefixes[:3]]
            if sample_prefixes:
                prefix_info = f" | Sample Prefixes ({prefix_count} total): {', '.join(sample_prefixes)}"
        
        # Combine all information into a single line
        result = f"ASN Lookup for AS{asn}: {name} | Description: {description} | Country: {country} ({country_code}){prefix_info}"
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
