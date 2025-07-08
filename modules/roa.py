#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ROA validation module for PhreakBot
# Checks if an IP address has a valid ROA (Route Origin Authorization)

import ipaddress
import json
import re
import requests


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["roa", "rpki"],
        "permissions": ["user"],
        "help": "Check if an IP address has a valid ROA (Route Origin Authorization).\n"
        "Usage: !roa <ip_address> - Check ROA status for an IP address\n"
        "       !rpki <ip_address> - Alias for !roa",
    }


def run(bot, event):
    """Handle ROA validation commands"""
    # Parse command arguments
    args = event["command_args"].split() if event["command_args"] else []

    if not args:
        bot.add_response("Please specify an IP address to check.")
        return

    ip_address = args[0]

    # Validate IP address format
    if not _is_valid_ip(ip_address):
        bot.add_response(f"Invalid IP address format: {ip_address}")
        return

    # Check ROA status
    try:
        result = _check_roa(ip_address)
        bot.add_response(result)
    except Exception as e:
        bot.logger.error(f"Error checking ROA for {ip_address}: {str(e)}")
        bot.add_response(f"Error checking ROA for {ip_address}: {str(e)}")


def _is_valid_ip(ip):
    """Check if the provided string is a valid IPv4 or IPv6 address"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def _check_roa(ip_address):
    """Check if an IP address has a valid ROA"""
    # Convert IP address to network prefix for API query
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        
        # Use /32 for IPv4 and /128 for IPv6 to represent a single IP
        prefix = f"{ip_address}/32" if ip_obj.version == 4 else f"{ip_address}/128"
        
        # Query RPKI validation API (using RIPE's API)
        api_url = f"https://rpki-validator.ripe.net/api/v1/validity/{prefix}"
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        
        # Process the response
        if "validated_route" in data and "validity" in data:
            validity = data["validity"]["state"]
            prefix = data["validated_route"]["route"]["prefix"]
            origin_asn = data["validated_route"]["route"]["origin_asn"]
            
            if validity == "valid":
                return f"✅ {ip_address} has a valid ROA. Prefix: {prefix}, Origin ASN: {origin_asn}"
            elif validity == "invalid":
                reason = data["validity"]["reason"] if "reason" in data["validity"] else "Unknown reason"
                return f"❌ {ip_address} has an invalid ROA. Reason: {reason}, Prefix: {prefix}, Origin ASN: {origin_asn}"
            elif validity == "unknown":
                return f"⚠️ {ip_address} has no ROA (RPKI unknown). Prefix: {prefix}, Origin ASN: {origin_asn}"
            else:
                return f"❓ {ip_address} has an unknown ROA status: {validity}"
        else:
            # Try alternative API (CloudFlare's API)
            api_url = f"https://rpki.cloudflare.com/api/v1/validity/{prefix}"
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "valid" in data:
                if data["valid"]:
                    return f"✅ {ip_address} has a valid ROA according to CloudFlare RPKI Validator."
                else:
                    reason = data.get("reason", "Unknown reason")
                    return f"❌ {ip_address} has an invalid ROA according to CloudFlare RPKI Validator. Reason: {reason}"
            else:
                return f"⚠️ {ip_address} has no ROA information available."
    except requests.exceptions.RequestException as e:
        # If the first API fails, try the alternative API
        try:
            api_url = f"https://rpki.cloudflare.com/api/v1/validity/{prefix}"
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if "valid" in data:
                if data["valid"]:
                    return f"✅ {ip_address} has a valid ROA according to CloudFlare RPKI Validator."
                else:
                    reason = data.get("reason", "Unknown reason")
                    return f"❌ {ip_address} has an invalid ROA according to CloudFlare RPKI Validator. Reason: {reason}"
            else:
                return f"⚠️ {ip_address} has no ROA information available."
        except Exception as e2:
            raise Exception(f"Failed to check ROA status: {str(e)}, {str(e2)}")
    except Exception as e:
        raise Exception(f"Failed to check ROA status: {str(e)}")