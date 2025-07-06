#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Channel management module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": ["join"],
        "commands": ["join", "part"],
        "permissions": ["owner", "admin", "join", "part"],
        "help": "Manage channel membership.\n"
        "Usage: !join <channel> - Join a channel\n"
        "       !part [channel] - Leave a channel (current channel if not specified)\n"
        "The bot also automatically joins channels when invited.",
    }


def run(bot, event):
    """Handle channel management commands"""
    # Handle join events (invites)
    if event["trigger"] == "event" and event["signal"] == "join":
        # Only respond to join events that aren't our own
        if event["nick"] != bot.connection.get_nickname():
            bot.logger.info(f"Detected {event['nick']} joining {event['channel']}")
            return

    # Handle join command
    if event["command"] == "join":
        chan = event["command_args"]
        if not chan:
            bot.add_response("Please specify a channel to join.")
            return

        bot.logger.info(f"Joining channel '{chan}' on command from '{event['nick']}'")
        bot.connection.join(chan)
        bot.add_response(f"Joining channel {chan}")
        return

    # Handle part command
    if event["command"] == "part":
        chan = event["command_args"]
        if not chan:
            chan = event["channel"]

        bot.logger.info(f"Leaving channel '{chan}' on command from '{event['nick']}'")
        bot.connection.part(chan, f"Requested by {event['nick']}")

        # Only add a response if we're not leaving the current channel
        if chan != event["channel"]:
            bot.add_response(f"Left channel {chan}")
        return
