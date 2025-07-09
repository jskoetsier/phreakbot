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
        
        # Use exec module to reload the module in a separate process
        import subprocess
        import os
        
        # Construct the full path to the module
        module_path = os.path.join(bot.bot_base, "modules", f"{module_name}.py")
        
        # Check if the file exists
        if not os.path.exists(module_path):
            bot.add_response(f"Module file not found: {module_path}")
            return
            
        # Send a message to the channel
        bot.add_response(f"Reloading module: {module_name}")
        
        # Create a Python script to reload the module
        reload_script = f"""
import importlib.util
import sys

# Load the module
spec = importlib.util.spec_from_file_location("{module_name}", "{module_path}")
module = importlib.util.module_from_spec(spec)
sys.modules["{module_name}"] = module
spec.loader.exec_module(module)

# Print success message
print("Module {module_name} reloaded successfully")
"""
        
        # Write the script to a temporary file
        temp_script_path = os.path.join(bot.bot_base, "temp_reload.py")
        with open(temp_script_path, "w") as f:
            f.write(reload_script)
            
        try:
            # Execute the script in a separate process
            result = subprocess.run(
                ["python", temp_script_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Check if the script executed successfully
            if result.returncode == 0:
                # Unload the module if it's already loaded
                if module_name in bot.modules:
                    bot.unload_module(module_name)
                
                # Load the module
                success = bot.load_module(module_path)
                if success:
                    bot.add_response(f"Successfully reloaded module: {module_name}")
                else:
                    bot.add_response(f"Failed to reload module: {module_name}")
            else:
                bot.add_response(f"Failed to reload module: {module_name}")
                bot.add_response(f"Error: {result.stderr}")
                
        except Exception as e:
            bot.logger.error(f"Error reloading {module_name}: {e}")
            bot.add_response(f"Error reloading {module_name}: {e}")
        finally:
            # Clean up the temporary script
            if os.path.exists(temp_script_path):
                os.remove(temp_script_path)
                
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
