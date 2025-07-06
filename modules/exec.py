#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Exec module for PhreakBot

import shlex
import subprocess


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["exec"],
        "permissions": ["owner", "admin", "exec"],
        "help": "Execute shell commands (restricted to authorized users).\n"
        "Usage: !exec <command> - Execute a shell command",
    }


def run(bot, event):
    """Handle exec commands"""
    # This is a potentially dangerous command, so restrict it to users with specific permissions
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"]
        and (
            "exec" in event["user_info"]["permissions"]["global"]
            or event["user_info"].get("is_admin")
        )
    ):
        bot.add_response("You don't have permission to execute commands.")
        return

    command = event["command_args"]
    if not command:
        bot.add_response("Please specify a command to execute.")
        return

    try:
        # Log the command execution
        bot.logger.warning(f"User {event['nick']} executing command: {command}")

        # Execute the command with a timeout
        process = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            bot.add_response("Command execution timed out after 10 seconds.")
            return

        # Get the return code
        return_code = process.returncode

        # Send the output
        if stdout:
            # Limit output to prevent flooding
            lines = stdout.strip().split("\n")
            if len(lines) > 5:
                bot.add_response(f"Output (first 5 of {len(lines)} lines):")
                for line in lines[:5]:
                    if line.strip():
                        bot.add_response(line[:300])
                bot.add_response(f"...{len(lines) - 5} more lines...")
            else:
                bot.add_response("Output:")
                for line in lines:
                    if line.strip():
                        bot.add_response(line[:300])

        if stderr:
            bot.add_response("Error output:")
            lines = stderr.strip().split("\n")
            for line in lines[:3]:  # Limit error output
                if line.strip():
                    bot.add_response(line[:300])

        bot.add_response(f"Command exited with code: {return_code}")

    except Exception as e:
        bot.logger.error(f"Error executing command: {e}")
        bot.add_response(f"Error executing command: {str(e)}")
