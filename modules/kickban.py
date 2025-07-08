#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Kick/Ban module for PhreakBot
# Allows channel operators to kick and ban users

import threading
import time

# Dictionary to track scheduled unbans
scheduled_unbans = {}

def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["kick", "kickban", "unban"],
        "permissions": ["owner", "admin", "op"],
        "help": "Kick and ban users from a channel.\n"
        "Usage: !kick <nickname> [reason] - Kick a user from the channel\n"
        "       !kickban <nickname> [minutes] [reason] - Kick and ban a user from the channel with optional auto-unban timer\n"
        "       !unban <hostmask> - Manually unban a hostmask from the channel",
    }


def run(bot, event):
    """Handle kick and kickban commands"""
    if event["command"] == "kick":
        _kick_user(bot, event)
    elif event["command"] == "kickban":
        _kickban_user(bot, event)
    elif event["command"] == "unban":
        _unban_user(bot, event)


def _kick_user(bot, event):
    """Kick a user from a channel"""
    # Check if the user has permission to kick users
    if not _has_permission(bot, event):
        bot.add_response("You don't have permission to kick users.")
        return

    # Parse command arguments
    args = event["command_args"].split() if event["command_args"] else []

    if not args:
        bot.add_response("Please specify a nickname to kick.")
        return

    nick = args[0]
    reason = " ".join(args[1:]) if len(args) > 1 else "Kicked by operator"
    channel = event["channel"]

    # Check if this is a channel
    if not channel.startswith("#"):
        bot.add_response("This command can only be used in a channel.")
        return

    # Don't allow kicking the bot itself
    if nick.lower() == bot.connection.get_nickname().lower():
        bot.add_response("I won't kick myself.")
        return

    try:
        # Kick the user
        bot.logger.info(f"Kicking {nick} from {channel} with reason: {reason}")
        bot.connection.kick(channel, nick, reason)
        bot.add_response(f"Kicked {nick} from {channel}: {reason}")
    except Exception as e:
        bot.logger.error(f"Error kicking user {nick}: {str(e)}")
        bot.add_response(f"Error kicking user {nick}: {str(e)}")


def _kickban_user(bot, event):
    """Kick and ban a user from a channel with optional unban timer"""
    # Check if the user has permission to ban users
    if not _has_permission(bot, event):
        bot.add_response("You don't have permission to kick and ban users.")
        return

    # Parse command arguments
    args = event["command_args"].split() if event["command_args"] else []

    if not args:
        bot.add_response("Please specify a nickname to kick and ban.")
        return

    nick = args[0]
    
    # Check if the second argument is a number (minutes for unban)
    unban_minutes = None
    reason_start_index = 1
    
    if len(args) > 1 and args[1].isdigit():
        unban_minutes = int(args[1])
        reason_start_index = 2
    
    reason = " ".join(args[reason_start_index:]) if len(args) > reason_start_index else "Banned by operator"
    channel = event["channel"]

    # Check if this is a channel
    if not channel.startswith("#"):
        bot.add_response("This command can only be used in a channel.")
        return

    # Don't allow banning the bot itself
    if nick.lower() == bot.connection.get_nickname().lower():
        bot.add_response("I won't ban myself.")
        return

    try:
        # Get the user's hostmask
        hostmask = _get_hostmask(bot, nick, channel)

        if not hostmask:
            bot.add_response(f"Could not find user {nick} in {channel}.")
            return

        # Set ban on the user
        bot.logger.info(f"Setting ban on {hostmask} in {channel}")
        bot.connection.mode(channel, f"+b {hostmask}")

        # Kick the user
        bot.logger.info(f"Kicking {nick} from {channel} with reason: {reason}")
        bot.connection.kick(channel, nick, reason)

        # Schedule unban if minutes are specified
        if unban_minutes:
            _schedule_unban(bot, channel, hostmask, unban_minutes)
            bot.add_response(f"Kicked and banned {nick} ({hostmask}) from {channel} for {unban_minutes} minutes: {reason}")
        else:
            bot.add_response(f"Kicked and banned {nick} ({hostmask}) from {channel}: {reason}")
    except Exception as e:
        bot.logger.error(f"Error kicking and banning user {nick}: {str(e)}")
        bot.add_response(f"Error kicking and banning user {nick}: {str(e)}")


def _unban_user(bot, event):
    """Manually unban a hostmask from a channel"""
    # Check if the user has permission to unban users
    if not _has_permission(bot, event):
        bot.add_response("You don't have permission to unban users.")
        return

    # Parse command arguments
    args = event["command_args"].split() if event["command_args"] else []

    if not args:
        bot.add_response("Please specify a hostmask to unban.")
        return

    hostmask = args[0]
    channel = event["channel"]

    # Check if this is a channel
    if not channel.startswith("#"):
        bot.add_response("This command can only be used in a channel.")
        return

    try:
        # Remove the ban
        bot.logger.info(f"Removing ban on {hostmask} in {channel}")
        bot.connection.mode(channel, f"-b {hostmask}")
        bot.add_response(f"Unbanned {hostmask} from {channel}")
    except Exception as e:
        bot.logger.error(f"Error unbanning {hostmask}: {str(e)}")
        bot.add_response(f"Error unbanning {hostmask}: {str(e)}")


def _schedule_unban(bot, channel, hostmask, minutes):
    """Schedule an unban after the specified number of minutes"""
    key = f"{channel}:{hostmask}"
    
    # Cancel any existing scheduled unban for this hostmask in this channel
    if key in scheduled_unbans:
        scheduled_unbans[key].cancel()
    
    # Schedule the unban
    bot.logger.info(f"Scheduling unban for {hostmask} in {channel} in {minutes} minutes")
    
    def unban_task():
        try:
            bot.logger.info(f"Auto-unbanning {hostmask} in {channel}")
            bot.connection.mode(channel, f"-b {hostmask}")
            bot.say(channel, f"Auto-unban: {hostmask} has been unbanned")
            # Remove from scheduled unbans
            if key in scheduled_unbans:
                del scheduled_unbans[key]
        except Exception as e:
            bot.logger.error(f"Error in scheduled unban for {hostmask}: {str(e)}")
    
    # Create and start the timer
    timer = threading.Timer(minutes * 60, unban_task)
    timer.daemon = True  # Make sure the timer doesn't prevent the bot from shutting down
    timer.start()
    
    # Store the timer
    scheduled_unbans[key] = timer


def _has_permission(bot, event):
    """Check if the user has permission to use kick/ban commands"""
    # Owner always has permission
    if bot._is_owner(event["hostmask"]):
        return True

    # Check if the user has the required permissions
    if event["user_info"]:
        # Check global permissions
        if "op" in event["user_info"]["permissions"]["global"] or event["user_info"].get("is_admin"):
            return True

        # Check channel-specific permissions
        channel = event["channel"]
        if channel in event["user_info"]["permissions"]:
            if "op" in event["user_info"]["permissions"][channel]:
                return True

    # Check if the user is a channel operator
    try:
        # This is a simplified check - in a real implementation,
        # you might want to use the IRC protocol to check if the user is an operator
        if event["nick"] in bot.channels[event["channel"]].opers():
            return True
    except Exception:
        pass

    return False


def _get_hostmask(bot, nick, channel):
    """Get a user's hostmask for banning, using only the hostname"""
    try:
        # Try to get the user's hostmask from the channel
        for user in bot.channels[channel].users():
            if user.lower() == nick.lower():
                # Get the user's hostmask
                user_obj = bot.channels[channel].userdict[user]
                # Create a ban mask in the form *!*@host
                # This focuses on the hostname part, not the nickname
                return f"*!*@{user_obj.host}"

        # If we couldn't find the user, try to use WHO command
        bot.logger.info(f"User {nick} not found in channel users, trying WHO command")
        bot.connection.who(nick)
        
        # Since we can't directly get the result of the WHO command here,
        # we'll return a simple nick-based mask as fallback
        return f"{nick}!*@*"
    except Exception as e:
        bot.logger.error(f"Error getting hostmask for {nick}: {str(e)}")
        # Return a simple nick-based mask as fallback
        return f"{nick}!*@*"
