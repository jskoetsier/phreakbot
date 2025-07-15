#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Debug module for PhreakBot - Logs all events and messages

import re


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "privmsg", "event"],  # Listen to all event types
        "commands": ["debug"],
        "permissions": ["owner", "admin"],
        "help": "Debug module for PhreakBot. Usage:\n"
        "!debug on - Enable debug logging\n"
        "!debug off - Disable debug logging",
    }


def run(bot, event):
    """Handle debug commands and events"""
    # Log all events for debugging
    bot.logger.info(f"DEBUG MODULE - Event received: {event}")

    # Handle debug commands
    if event["trigger"] == "command" and event["command"] == "debug":
        if not event["command_args"]:
            bot.add_response("Debug module is active. Use !debug on or !debug off.")
            return

        if event["command_args"].lower() == "on":
            bot.state["debug_enabled"] = True
            bot.add_response("Debug logging enabled.")
        elif event["command_args"].lower() == "off":
            bot.state["debug_enabled"] = False
            bot.add_response("Debug logging disabled.")
        else:
            bot.add_response("Unknown debug command. Use !debug on or !debug off.")
        return

    # If debug is enabled, log all events
    if bot.state.get("debug_enabled", False):
        # Special handling for karma patterns
        if "text" in event and event["text"]:
            # Log all messages that start with ! for debugging
            if event["text"].startswith("!"):
                bot.logger.info(f"DEBUG MODULE - Message starts with !: '{event['text']}'")
                
            # Check for karma++ pattern
            karma_plus_pattern = re.compile(r"^\!([a-zA-Z0-9_-]+)\+\+(?:\s+#(.+))?$")
            match_plus = karma_plus_pattern.match(event["text"])
            if match_plus:
                bot.logger.info(f"DEBUG MODULE - Karma++ pattern detected: {match_plus.groups()}")
                bot.add_response(f"DEBUG: Karma++ pattern detected: {match_plus.groups()}")
                
            # Check for karma-- pattern
            karma_minus_pattern = re.compile(r"^\!([a-zA-Z0-9_-]+)\-\-(?:\s+#(.+))?$")
            match_minus = karma_minus_pattern.match(event["text"])
            if match_minus:
                bot.logger.info(f"DEBUG MODULE - Karma-- pattern detected: {match_minus.groups()}")
                bot.add_response(f"DEBUG: Karma-- pattern detected: {match_minus.groups()}")
