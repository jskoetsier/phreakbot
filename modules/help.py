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
        bot.add_response(
            f"A module named '{module}' was not found! Try the !avail command!"
        )
        return

    try:
        # Display module help information
        helptxt = bot.modules[module]["help"]
        
        # Handle help text that could be a string or a dictionary
        if isinstance(helptxt, dict):
            # If it's a dictionary, send each command-specific help text as a separate message
            for cmd, txt in helptxt.items():
                bot.add_response(f"{cmd}: {txt}")
        else:
            # If it's a string, split by newlines and send each line as a separate message
            for line in helptxt.split("\n"):
                if line.strip():  # Only send non-empty lines
                    bot.add_response(line)
        
        # Display commands and permissions
        if "commands" in bot.modules[module] and bot.modules[module]["commands"]:
            helpcmds = ", ".join(bot.modules[module]["commands"])
            bot.add_response(f"Provides commands: {helpcmds}")
        
        if "permissions" in bot.modules[module] and bot.modules[module]["permissions"]:
            helpperm = ", ".join(bot.modules[module]["permissions"])
            bot.add_response(f"Needs permissions: {helpperm}")
    except Exception as e:
        bot.logger.error(f"Error displaying help for module {module}: {e}")
        import traceback
        bot.logger.error(f"Traceback: {traceback.format_exc()}")
        bot.add_response(
            f"Error displaying help for module {module}. Please check the logs."
        )
