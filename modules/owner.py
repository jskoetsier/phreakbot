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
        "help": "Show the bot owner. The owner is set in the configuration file.",
    }


def run(bot, event):
    """Handle owner commands"""
    # If no owner is set
    if not bot.config.get("owner"):
        bot.add_response(
            "This bot has no owner. The owner must be set in the configuration file."
        )
        return

    # Show current owner
    bot.add_response(f"I am owned by {bot.config['owner']}")
