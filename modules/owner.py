#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Owner module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["owner"],
        "permissions": ["user"],
        "help": "Set or show the bot owner. Use !owner *!<user>@<hostname> to claim ownership.",
    }


def run(bot, event):
    """Handle owner commands"""
    # If no owner is set
    if not bot.config.get("owner"):
        # Check if someone is trying to claim ownership with the correct format
        if (
            event["command_args"]
            and event["command_args"].startswith("*!")
            and "@" in event["command_args"]
        ):
            # Set the owner to the specified hostmask
            bot.config["owner"] = event["command_args"]
            bot.save_config()
            bot.add_response(
                f"Ownership claimed by {event['nick']} with hostmask {event['command_args']}!"
            )
            bot.logger.info(
                f"Bot owner set to {event['command_args']} by {event['nick']}"
            )
            return
        elif event["command_args"]:
            # Invalid format
            bot.add_response(
                f"Invalid owner format. Use '!owner *!<user>@<hostname>' to claim ownership."
            )
            return

        # Display instructions for claiming ownership
        user_part = (
            event["hostmask"].split("@")[0] if "@" in event["hostmask"] else "user"
        )
        host_part = (
            event["hostmask"].split("@")[1] if "@" in event["hostmask"] else "hostname"
        )
        example = f"*!{user_part}@{host_part}"

        bot.add_response(
            f"This bot has no owner. Use '!owner {example}' to claim ownership."
        )
        return

    # If owner is already set
    # Check if the current user matches the owner pattern
    owner_pattern = bot.config["owner"]
    if owner_pattern.startswith("*!"):
        # Extract the user and host parts from the pattern
        pattern_parts = owner_pattern[2:].split("@")
        if len(pattern_parts) == 2:
            pattern_user = pattern_parts[0]
            pattern_host = pattern_parts[1]

            # Extract the user and host parts from the current user
            current_parts = event["hostmask"].split("@")
            if len(current_parts) == 2:
                current_user = current_parts[0]
                current_host = current_parts[1]

                # Check if the pattern matches
                is_owner = (pattern_user == "*" or pattern_user == current_user) and (
                    pattern_host == "*" or pattern_host == current_host
                )
            else:
                is_owner = False
        else:
            is_owner = False
    else:
        # Legacy format - exact match
        is_owner = event["hostmask"] == bot.config["owner"]

    if is_owner:
        # Owner can transfer ownership to another user
        if event["command_args"]:
            # Check if the argument is a valid hostmask format
            if event["command_args"].startswith("*!") and "@" in event["command_args"]:
                bot.config["owner"] = event["command_args"]
                bot.save_config()
                bot.add_response(f"Ownership transferred to {event['command_args']}")
                bot.logger.info(f"Bot owner changed to {event['command_args']}")
            else:
                bot.add_response("Invalid hostmask format. Use *!<user>@<host> format.")
        else:
            # Show current owner
            bot.add_response(f"I am owned by {bot.config['owner']}")
    else:
        # Non-owner trying to use owner command
        bot.add_response(f"I am already owned by {bot.config['owner']}")
