#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Country module for PhreakBot

import re
import socket


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["country"],
        "permissions": ["user"],
        "help": "Look up country information for a hostname or IP address.\n"
        "Usage: !country <hostname|ip> - Show country information for a host",
    }


def run(bot, event):
    """Handle country commands"""
    host = event["command_args"]

    if not host:
        bot.add_response("Please specify a hostname or IP address.")
        return

    try:
        # Try to resolve the hostname to an IP address
        try:
            ip = socket.gethostbyname(host)
        except socket.gaierror:
            bot.add_response(f"Could not resolve hostname: {host}")
            return

        # Use a simple regex to validate the IP address
        if not re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip):
            bot.add_response(f"Invalid IP address: {ip}")
            return

        # In a real implementation, we would use a GeoIP database to look up the country
        # For this example, we'll just return a placeholder message
        bot.add_response(
            f"IP address {ip} is located in [Country information would be displayed here]"
        )

    except Exception as e:
        bot.logger.error(f"Error in country module: {e}")
        bot.add_response(f"Error looking up country information for {host}")
