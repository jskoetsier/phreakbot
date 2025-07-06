#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Botnick module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["botnick"],
        "permissions": ["owner", "admin", "botnick"],
        "help": "Change the bot's nickname.\n"
        "Usage: !botnick <new_nickname> - Change the bot's nickname",
    }


def run(bot, event):
    """Handle botnick commands"""
    new_nick = event["command_args"]

    if not new_nick:
        bot.add_response("Please specify a new nickname.")
        return

    # Change the bot's nickname
    bot.logger.info(
        f"Changing nickname from {bot.connection.get_nickname()} to {new_nick}"
    )
    bot.connection.nick(new_nick)
    bot.add_response(f"Changing nickname to {new_nick}")
