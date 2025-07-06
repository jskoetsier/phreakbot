#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Channel management module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": ["irc_in2_INVITE"],
        "commands": ["join", "part"],
        "permissions": ["owner", "admin", "join", "part"],
        "help": "Manage channel membership - !join <channel> to join a channel, !part [channel] to leave a channel",
    }


def run(bot, event):
    """Handle channel management commands"""
    # Handle invite events
    if event["trigger"] == "event" and event["signal"] == "irc_in2_INVITE":
        bot.logger.info(f"Received invite to {event['args'][1]} from {event['source']}")
        # Auto-join on invite if from owner or admin
        if bot.check_permission(event, "owner") or bot.check_permission(event, "admin"):
            bot.connection.join(event["args"][1])
        return

    # Handle join command
    if event["command"] == "join":
        # Check permissions
        if not bot.check_permission(event, "join"):
            bot.logger.info(
                f"Permission denied for {event['nick']} to use join command"
            )
            bot.add_response("You don't have permission to make the bot join channels.")
            return

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
        # Check permissions
        if not bot.check_permission(event, "part"):
            bot.logger.info(
                f"Permission denied for {event['nick']} to use part command"
            )
            bot.add_response(
                "You don't have permission to make the bot leave channels."
            )
            return

        chan = event["command_args"]
        if not chan:
            chan = event["channel"]

        bot.logger.info(f"Leaving channel '{chan}' on command from '{event['nick']}'")
        bot.connection.part(chan, f"Requested by {event['nick']}")

        # Only add a response if we're not leaving the current channel
        if chan != event["channel"]:
            bot.add_response(f"Left channel {chan}")
        return
