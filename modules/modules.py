#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Modules management module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["load", "reload", "unload", "avail"],
        "permissions": ["owner", "admin", "modules"],
        "help": "Provides module management functionality.\n"
        "Usage: !avail - List all available modules\n"
        "       !load <module_path> - Load a module\n"
        "       !reload <module_path> - Reload a module\n"
        "       !unload <module_name> - Unload a module",
    }


def run(bot, event):
    """Handle module management commands"""
    if event["command"] == "avail":
        mlist = ", ".join(sorted(bot.modules.keys()))
        bot.add_response(f"Modules loaded: {mlist}")
        return

    # Commands below require owner / modules permissions.
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"]
        and (
            "modules" in event["user_info"]["permissions"]["global"]
            or event["user_info"].get("is_admin")
        )
    ):
        bot.add_response("You don't have permission to manage modules.")
        return

    # Commands below require param to be set.
    if not event["command_args"]:
        bot.add_response("This command requires at least one argument (module name)")
        return

    if event["command"] == "load" or event["command"] == "reload":
        module_name = event["command_args"]

        # Add debug logging
        bot.logger.info(f"Starting module reload for {module_name}")

        try:
            # Send a message to the channel immediately
            bot.add_response(f"Starting reload of {module_name} module")

            # Try a simpler approach - use importlib directly
            import importlib
            import os
            import sys

            # Construct the full path to the module
            module_path = os.path.join(bot.bot_base, "modules", f"{module_name}.py")

            # Check if the file exists
            if not os.path.exists(module_path):
                bot.add_response(f"Module file not found: {module_path}")
                return

            bot.logger.info(f"Module file exists at {module_path}")

            # First, try to unload the module if it's already loaded
            if module_name in bot.modules:
                bot.logger.info(f"Unloading module {module_name}")
                try:
                    # Just unload the module directly
                    # Don't try to store or copy anything from it
                    bot.unload_module(module_name)
                    bot.logger.info(f"Module {module_name} unloaded")
                except Exception as unload_error:
                    # Log the error but continue with the reload process
                    bot.logger.error(
                        f"Error unloading module {module_name}: {unload_error}"
                    )
                    # Don't send the error to the channel to avoid confusion

            # Force a message to be sent before attempting to reload
            bot.add_response(f"Unloaded {module_name}, now reloading...")

            # Try to load the module
            bot.logger.info(f"Loading module {module_name} from {module_path}")
            success = False

            try:
                success = bot.load_module(module_path)
                bot.logger.info(f"Module {module_name} load result: {success}")
            except Exception as load_error:
                bot.logger.error(f"Error loading module {module_name}: {load_error}")
                bot.add_response(f"Error loading module: {str(load_error)[:100]}")
                return

            if success:
                bot.add_response(f"Successfully reloaded module: {module_name}")
            else:
                bot.add_response(f"Failed to reload module: {module_name}")

        except Exception as e:
            bot.logger.error(f"Error in module reload process: {e}")
            # Try to send a message even if there's an error
            try:
                bot.add_response(f"Error reloading {module_name}: {str(e)[:100]}")
            except:
                pass

        return

    if event["command"] == "unload":
        module_name = event["command_args"]
        if module_name in bot.modules:
            success = bot.unload_module(module_name)
            if success:
                bot.add_response(f"Unloaded module '{module_name}'")
            else:
                bot.add_response(f"Failed to unload module '{module_name}'")
        else:
            bot.add_response(f"Module '{module_name}' is not loaded")
        return
