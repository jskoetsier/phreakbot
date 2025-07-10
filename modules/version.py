#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Version module for PhreakBot

import os
import platform


def config(bot):
    """Return module configuration"""
    return {
        "events": ["ctcp"],
        "commands": ["version"],
        "permissions": ["user"],
        "help": "Display version information about the bot.",
    }


def run(bot, event):
    """Handle version command and CTCP VERSION requests"""
    try:
        # Get version from VERSION file
        version_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'VERSION')
        with open(version_path, 'r') as f:
            version = f.read().strip()

        version_info = f"PhreakBot v{version} running on Python {platform.python_version()} ({platform.system()} {platform.release()})"

        # Handle command
        if event["trigger"] == "command" and event["command"] == "version":
            bot.add_response(version_info)
            return

        # Handle CTCP VERSION
        if event["trigger"] == "event" and event["signal"] == "ctcp" and event.get("ctcp_command") == "VERSION":
            bot.connection.ctcp_reply(event["nick"], "VERSION", version_info)
            return

    except Exception as e:
        bot.logger.error(f"Error in version module: {e}")
        bot.add_response("Error retrieving version information.")
