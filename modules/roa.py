#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ROA validation module for PhreakBot
# Checks if an IP address or prefix has a valid ROA (Route Origin Authorization)

import ipaddress
import json
import re
import requests


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["rpki-old"],
        "permissions": ["user"],
        "help": "DEPRECATED: Use !roa or !irr instead.\n"
        "This module is deprecated and will be removed in a future version.",
    }


def run(bot, event):
    """Handle ROA validation commands"""
    # Parse command arguments
    args = event["command_args"].split() if event["command_args"] else []

    if not args:
        bot.add_response("Please specify an IP address or prefix to check.")
        return

    query = args[0]

    # Check if the input is a CIDR prefix
    is_prefix = "/" in query

    if is_prefix:
        # Validate prefix format
        if not _is_valid_prefix(query):
            bot.add_response(f"Invalid prefix format: {query}")
            return

        # Use the prefix directly
        prefix = query
        ip_address = query.split('/')[0]  # Extract the network address
    else:
        # Validate IP address format
        if not _is_valid_ip(query):
            bot.add_response(f"Invalid IP address format: {query}")
            return

        # Find the prefix that contains this IP
        ip_address = query
        prefix = _find_prefix_for_ip(bot, ip_address)

        if not prefix:
            bot.add_response(f"Could not find a prefix containing {ip_address}")
            return

    # Check ROA status
    try:
        result = _check_roa(ip_address, prefix)
        bot.add_response(result)
    except Exception as e:
        bot.logger.error(f"Error checking ROA for {prefix}: {str(e)}")
        bot.add_response(f"Error checking ROA for {prefix}: {str(e)}")


def _is_valid_ip(ip):
    """Check if the provided string is a valid IPv4 or IPv6 address"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def _is_valid_prefix(prefix):
    """Check if the provided string is a valid IPv4 or IPv6 prefix"""
    try:
        ipaddress.ip_network(prefix, strict=False)
        return True
    except ValueError:
        return False


def _find_prefix_for_ip(bot, ip_address):
    """Find the prefix that contains the given IP address"""
    try:
        # First try BGPView API
        bot.logger.info(f"Looking up prefix for IP {ip_address} using BGPView API")
        response = requests.get(f"https://api.bgpview.io/ip/{ip_address}", timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("status") == "ok" and "data" in data:
            prefixes = data["data"].get("prefixes", [])
            if prefixes:
                # Sort prefixes by prefix length (most specific first)
                prefixes.sort(key=lambda x: int(x.get("prefix", "0/0").split("/")[1]), reverse=True)

                # Get the most specific prefix
                prefix = prefixes[0].get("prefix")
                bot.logger.info(f"Found prefix {prefix} for IP {ip_address}")
                return prefix

        # If BGPView fails, try to use a default prefix
        ip_obj = ipaddress.ip_address(ip_address)
        default_prefix = f"{ip_address}/24" if ip_obj.version == 4 else f"{ip_address}/48"
        bot.logger.warning(f"Could not find prefix for {ip_address}, using default {default_prefix}")
        return default_prefix

    except Exception as e:
        bot.logger.error(f"Error finding prefix for {ip_address}: {str(e)}")

        # Use a default prefix as fallback
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            default_prefix = f"{ip_address}/24" if ip_obj.version == 4 else f"{ip_address}/48"
            bot.logger.warning(f"Using default prefix {default_prefix} for {ip_address} due to error")
            return default_prefix
        except:
            return None


def _check_roa(ip_address, prefix):
    """Check if a prefix has a valid ROA"""
    try:
        # Query RPKI validation API (using RIPE's API)
        api_url = f"https://rpki-validator.ripe.net/api/v1/validity/{prefix}"

        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors

        data = response.json()

        # Process the response
        if "validated_route" in data and "validity" in data:
            validity = data["validity"]["state"]
            validated_prefix = data["validated_route"]["route"]["prefix"]
            origin_asn = data["validated_route"]["route"]["origin_asn"]

            if validity == "valid":
                return f"✅ {ip_address} (in prefix {prefix}) has a valid ROA. Validated prefix: {validated_prefix}, Origin ASN: {origin_asn}"
            elif validity == "invalid":
                reason = data["validity"]["reason"] if "reason" in data["validity"] else "Unknown reason"
                return f"❌ {ip_address} (in prefix {prefix}) has an invalid ROA. Reason: {reason}, Validated prefix: {validated_prefix}, Origin ASN: {origin_asn}"
            elif validity == "unknown":
                return f"⚠️ {ip_address} (in prefix {prefix}) has no ROA (RPKI unknown). Validated prefix: {validated_prefix}, Origin ASN: {origin_asn}"
            else:
                return f"❓ {ip_address} (in prefix {prefix}) has an unknown ROA status: {validity}"
        else:
            # Try alternative API (CloudFlare's API)
            api_url = f"https://rpki.cloudflare.com/api/v1/validity/{prefix}"

            response = requests.get(api_url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "valid" in data:
                if data["valid"]:
                    return f"✅ {ip_address} (in prefix {prefix}) has a valid ROA according to CloudFlare RPKI Validator."
                else:
                    reason = data.get("reason", "Unknown reason")
                    return f"❌ {ip_address} (in prefix {prefix}) has an invalid ROA according to CloudFlare RPKI Validator. Reason: {reason}"
            else:
                return f"⚠️ {ip_address} (in prefix {prefix}) has no ROA information available."
    except requests.exceptions.RequestException as e:
        # If the first API fails, try the alternative API
        try:
            api_url = f"https://rpki.cloudflare.com/api/v1/validity/{prefix}"

            response = requests.get(api_url, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "valid" in data:
                if data["valid"]:
                    return f"✅ {ip_address} (in prefix {prefix}) has a valid ROA according to CloudFlare RPKI Validator."
                else:
                    reason = data.get("reason", "Unknown reason")
                    return f"❌ {ip_address} (in prefix {prefix}) has an invalid ROA according to CloudFlare RPKI Validator. Reason: {reason}"
            else:
                return f"⚠️ {ip_address} (in prefix {prefix}) has no ROA information available."
        except Exception as e2:
            raise Exception(f"Failed to check ROA status: {str(e)}, {str(e2)}")
    except Exception as e:
        raise Exception(f"Failed to check ROA status: {str(e)}")
