#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot - A modular IRC bot
#
# Module: topic
# Set and retrieve channel topics
#


def config(wcb):
    return {
        "events": [
            "irc_in2_332",
            "irc_in2_TOPIC",
        ],  # Add event handlers for topic responses
        "commands": ["topic", "settopic", "addtopic"],
        "permissions": ["topic"],
        "help": {
            "topic": "Retrieve the current topic for a channel",
            "settopic": "Set the topic for a channel",
            "addtopic": "Add text to the current topic",
        },
    }


def run(wcb, event):
    # Handle topic response events
    if event["trigger"] == "event":
        if event["signal"] == "irc_in2_332":  # RPL_TOPIC response
            # This is the response to a TOPIC request
            channel = event["raw_event"].arguments[0]
            topic = event["raw_event"].arguments[1]
            wcb.say(channel, f"Current topic: {topic}")
        elif event["signal"] == "irc_in2_TOPIC":  # TOPIC change notification
            channel = event["raw_event"].target
            topic = event["raw_event"].arguments[0]
            wcb.say(channel, f"Topic changed to: {topic}")
        return

    # Handle commands
    if event["command"] == "topic":
        # Get the current topic
        channel = event["channel"]
        if event["command_args"]:
            channel = event["command_args"].strip()

        # Check if the channel is in the config
        if channel not in wcb.config["channels"]:
            wcb.reply(f"I'm not in channel {channel}")
            return

        # Get the topic
        wcb.logger.info(f"Getting topic for channel: {channel}")
        wcb.connection.topic(channel)
        wcb.reply(f"Retrieving topic for {channel}...")

    elif event["command"] == "settopic":
        # Set the topic
        if not event["command_args"]:
            wcb.reply("Please provide a topic")
            return

        channel = event["channel"]
        topic = event["command_args"]

        # Check if the user has permission to set topics
        has_permission = wcb._check_permissions(event, ["topic"])
        wcb.logger.info(
            f"User {event['nick']} permission to set topic: {has_permission}"
        )

        if not has_permission:
            wcb.reply("You don't have permission to set topics.")
            return

        # Check if the channel is in the config
        if channel not in wcb.config["channels"]:
            wcb.reply(f"I'm not in channel {channel}")
            return

        # Set the topic
        wcb.logger.info(f"Setting topic in {channel} to: {topic}")
        wcb.connection.topic(channel, topic)
        wcb.reply(f"Setting topic for {channel} to: {topic}")

    elif event["command"] == "addtopic":
        # Add to the topic
        if not event["command_args"]:
            wcb.reply("Please specify text to add to the topic.")
            return

        channel = event["channel"]
        addition = event["command_args"]

        # Check if the user has permission to set topics
        has_permission = wcb._check_permissions(event, ["topic"])
        wcb.logger.info(
            f"User {event['nick']} permission to modify topic: {has_permission}"
        )

        if not has_permission:
            wcb.reply("You don't have permission to modify topics.")
            return

        # Check if the channel is in the config
        if channel not in wcb.config["channels"]:
            wcb.reply(f"I'm not in channel {channel}")
            return

        # For now, just set the new topic to the addition
        # In a future update, we could implement a callback to get the current topic first
        wcb.connection.topic(channel, addition)
        wcb.reply(f"Setting topic to: {addition}")
    # This comment is already handled in the code above
