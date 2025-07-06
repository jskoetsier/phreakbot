#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Version module for PhreakBot

import os


def config(bot):
    """Return module configuration"""
    return {
        "events": ["irc_in2_VERSION"],
        "commands": ["version"],
        "permissions": ["user"],
        "help": "Display the bot version and GitHub URL",
    }


def run(bot, event):
    """Handle version commands and events"""
    try:
        # Get the bot version
        version = get_version()
        
        # Handle command
        if event["trigger"] == "command" and event["command"] == "version":
            bot.add_response(f"PhreakBot v{version} - https://github.com/jskoetsier/phreakbot")
            return
            
        # Handle CTCP VERSION requests
        if event["trigger"] == "event" and event["signal"] == "irc_in2_VERSION":
            # Override the default Python irc.bot VERSION reply with our own
            bot.connection.ctcp_reply(event["nick"], f"PhreakBot v{version} - https://github.com/jskoetsier/phreakbot")
            return
    except Exception as e:
        bot.logger.error(f"Error in version module: {e}")
        bot.add_response("Error retrieving version information.")


def get_version():
    """Get the bot version from the VERSION file."""
    version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "VERSION")
    try:
        with open(version_file, "r") as f:
            return f.read().strip()
    except Exception:
        return "unknown"
