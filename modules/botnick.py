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
    bot.logger.info(f"Changing nickname from {bot.nickname} to {new_nick}")
    # Schedule nickname change asynchronously
    import asyncio

    try:

        async def change_nick():
            await bot.set_nickname(new_nick)

        asyncio.create_task(change_nick())
        bot.add_response(f"Changing nickname to {new_nick}")
    except Exception as e:
        bot.logger.error(f"Error changing nickname: {e}")
        bot.add_response(f"Error changing nickname: {str(e)}")
