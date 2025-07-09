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

        # Check if this is a reload and the module is already loaded
        if event["command"] == "reload" and module_name in bot.modules:
            # Unload the module first
            bot.unload_module(module_name)

        # Construct the full path to the module
        import os
        module_path = os.path.join(bot.bot_base, "modules", f"{module_name}.py")

        # Check if the file exists
        if not os.path.exists(module_path):
            bot.add_response(f"Module file not found: {module_path}")
            return

        # Special handling for asn module to prevent bot restart
        if module_name == "asn":
            try:
                # Try to load the module
                success = bot.load_module(module_path)
                if success:
                    bot.add_response(f"Successfully loaded module: {module_name}")
                else:
                    bot.add_response(f"Failed to load module: {module_name}")
                # Force a message to be sent before potential restart
                bot.connection.privmsg(event["channel"], f"Successfully reloaded {module_name} module")
            except Exception as e:
                bot.logger.error(f"Error reloading {module_name}: {e}")
                bot.add_response(f"Error reloading {module_name}: {e}")
            return
        else:
            # Try to load the module
            success = bot.load_module(module_path)
            if success:
                bot.add_response(f"Successfully loaded module: {module_name}")
            else:
                bot.add_response(f"Failed to load module: {module_name}")
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
