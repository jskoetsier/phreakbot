#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Help module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["help", "avail"],
        "permissions": ["user"],
        "help": "Shows help information for modules. Use !help <module> or !avail to list all modules.",
    }


def run(bot, event):
    """Handle help commands"""
    if event["command"] == "avail":
        # List all available modules
        module_list = list(bot.modules.keys())
        module_list.sort()
        bot.add_response(f"Available modules: {', '.join(module_list)}")
        bot.add_response(
            "Use !help <module> for more information on a specific module."
        )
        return

    # Handle help for a specific module
    module = event["command_args"]
    if not module:
        bot.add_response(
            "Use !help <module> to get help for a specific module, or !avail to list all modules."
        )
        return

    if module not in bot.modules:
        bot.reply(f"A module named '{module}' was not found! Try the !avail command!")
        return

    # Display module help information
    helptxt = bot.modules[module]["help"]
    helpcmds = ", ".join(bot.modules[module]["commands"])
    helpperm = ", ".join(bot.modules[module]["permissions"])

    bot.add_response(f"{helptxt}")
    bot.add_response(f"Provides commands: {helpcmds}")
    bot.add_response(f"Needs permissions: {helpperm}")
