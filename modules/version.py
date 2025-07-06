#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Version module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["v", "version"],
        "permissions": ["user"],
        "help": "Shows information about the bot.\n"
        "Usage: !version - Display bot version and repository information",
    }


def run(bot, event):
    """Handle version commands"""
    bot.add_response("PhreakBot - https://github.com/jskoetsier/phreakbot/")
