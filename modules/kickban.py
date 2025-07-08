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
        "events": ["namreply"],  # Add namreply event to track users in channels
        "commands": ["kick", "kickban", "unban"],
        "permissions": ["owner", "admin", "op"],
        "help": "Kick and ban users from a channel.\n"
        "Usage: !kick <nickname> [reason] - Kick a user from the channel\n"
        "       !kickban <nickname> [minutes] [reason] - Kick and ban a user from the channel with optional auto-unban timer\n"
        "       !unban <hostmask> - Manually unban a hostmask from the channel",
    }

# Dictionary to track users and their hostmasks in each channel
channel_users = {}


def run(bot, event):
    """Handle kick and kickban commands"""
    if event["trigger"] == "event" and event["signal"] == "namreply":
        _handle_namreply(bot, event)
        return
        
    if event["command"] == "kick":
        _kick_user(bot, event)
    elif event["command"] == "kickban":
        _kickban_user(bot, event)
    elif event["command"] == "unban":
        _unban_user(bot, event)

def _handle_namreply(bot, event):
    """Handle NAMES reply events to track users in channels"""
    try:
        channel = event["channel"]
        names = event["names"]
        
        bot.logger.info(f"Received NAMES reply for {channel}: {names}")
        
        # Initialize the channel in our tracking dictionary if needed
        if channel not in channel_users:
            channel_users[channel] = {}
            
        # Process each name in the list
        for name in names:
            # Remove any prefix characters like @ or +
            clean_name = name
            if name.startswith('@') or name.startswith('+'):
                clean_name = name[1:]
                
            # Store the user in our tracking dictionary
            # We'll update the hostmask when we get more information
            if clean_name not in channel_users[channel]:
                channel_users[channel][clean_name] = {"joined": time.time(), "hostmask": None}
                bot.logger.info(f"Added {clean_name} to channel_users for {channel}")
                
        bot.logger.info(f"Updated channel_users for {channel}: {channel_users[channel]}")
    except Exception as e:
        bot.logger.error(f"Error handling namreply event: {str(e)}")


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
        hostmask = None
        
        # First, check if the user is in our tracking dictionary
        if channel in channel_users and nick.lower() in [n.lower() for n in channel_users[channel]]:
            # Find the exact nick with correct case
            for tracked_nick in channel_users[channel]:
                if tracked_nick.lower() == nick.lower():
                    user_data = channel_users[channel][tracked_nick]
                    if user_data.get("hostmask"):
                        # Extract the hostname part (after the @)
                        if "@" in user_data["hostmask"]:
                            hostname = user_data["hostmask"].split("@")[1]
                            hostmask = f"*!*@{hostname}"
                            bot.logger.info(f"Using hostmask from tracking: {hostmask}")
                        break
        
        # If we couldn't find the user in our tracking, check if they're the one executing the command
        if not hostmask and event["nick"].lower() == nick.lower():
            # Use the hostmask from the event
            user_host = event["hostmask"]
            # Extract the hostname part (after the @)
            if "@" in user_host:
                hostname = user_host.split("@")[1]
                hostmask = f"*!*@{hostname}"
                bot.logger.info(f"Using hostmask from event: {hostmask}")
                
                # Also update our tracking dictionary
                if channel in channel_users and nick in channel_users[channel]:
                    channel_users[channel][nick]["hostmask"] = user_host
                    bot.logger.info(f"Updated hostmask for {nick} in {channel}: {user_host}")
        
        # If we still don't have a hostmask, try to get it from the server
        if not hostmask:
            # Send a WHO command to get more information
            bot.logger.info(f"Sending WHO command for {nick}")
            bot.connection.who(nick)
            
            # Since we can't directly get the result of the WHO command here,
            # we'll use a fallback based on the nickname
            
            # For Guest users, use a common pattern
            if nick.lower().startswith("guest"):
                hostmask = "*!*@gateway/web/*"
                bot.logger.info(f"Using web gateway mask for Guest user: {hostmask}")
            else:
                # As a last resort, use a nick-based mask
                hostmask = f"{nick}!*@*"
                bot.logger.warning(f"Could not determine hostname for {nick}, using nick-based mask")
                bot.add_response(f"Warning: Using nick-based ban mask for {nick}. This may not be as effective as a hostname-based mask.")

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


# Remove the _get_hostmask function since we've integrated its functionality directly into _kickban_user
