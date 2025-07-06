#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Topic module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["topic", "settopic", "addtopic"],
        "permissions": ["user", "topic"],
        "help": "Manage channel topics.\n"
        "Usage: !topic - Show the current topic\n"
        "       !settopic <text> - Set a new topic (requires topic permission)\n"
        "       !addtopic <text> - Add text to the current topic (requires topic permission)",
    }


def run(bot, event):
    """Handle topic commands"""
    if event["command"] == "topic":
        _show_topic(bot, event)
    elif event["command"] == "settopic":
        _set_topic(bot, event)
    elif event["command"] == "addtopic":
        _add_topic(bot, event)


def _show_topic(bot, event):
    """Show the current topic"""
    channel = event["channel"]

    # Check if the channel is in the bot's configured channels
    if channel not in bot.config["channels"]:
        bot.add_response(f"I'm not in channel {channel}")
        return

    # Get the topic using the connection object
    bot.connection.topic(channel)
    bot.add_response("Retrieving topic information...")


def _set_topic(bot, event):
    """Set a new topic"""
    # Check if the user has permission to set topics
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"]
        and (
            "topic" in event["user_info"]["permissions"]["global"]
            or (
                event["channel"] in event["user_info"]["permissions"]
                and "topic" in event["user_info"]["permissions"][event["channel"]]
            )
        )
    ):
        bot.add_response("You don't have permission to set topics.")
        return

    new_topic = event["command_args"]
    if not new_topic:
        bot.add_response("Please specify a topic.")
        return

    channel = event["channel"]
    # Check if the channel is in the bot's configured channels
    if channel not in bot.config["channels"]:
        bot.add_response(f"I'm not in channel {channel}")
        return

    bot.connection.topic(channel, new_topic)
    bot.add_response(f"Setting topic to: {new_topic}")


def _add_topic(bot, event):
    """Add text to the current topic"""
    # Check if the user has permission to set topics
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"]
        and (
            "topic" in event["user_info"]["permissions"]["global"]
            or (
                event["channel"] in event["user_info"]["permissions"]
                and "topic" in event["user_info"]["permissions"][event["channel"]]
            )
        )
    ):
        bot.add_response("You don't have permission to modify topics.")
        return

    addition = event["command_args"]
    if not addition:
        bot.add_response("Please specify text to add to the topic.")
        return

    channel = event["channel"]
    # Check if the channel is in the bot's configured channels
    if channel not in bot.config["channels"]:
        bot.add_response(f"I'm not in channel {channel}")
        return

    # We need to request the current topic first
    # For now, just set the new topic to the addition
    # In a future update, we could implement a callback to get the current topic first
    bot.connection.topic(channel, addition)
    bot.add_response(f"Setting topic to: {addition}")
