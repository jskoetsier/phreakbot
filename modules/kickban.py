#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Kick/Ban module for PhreakBot
# Allows channel operators to kick and ban users

def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["kick", "kickban"],
        "permissions": ["owner", "admin", "op"],
        "help": "Kick and ban users from a channel.\n"
        "Usage: !kick <nickname> [reason] - Kick a user from the channel\n"
        "       !kickban <nickname> [reason] - Kick and ban a user from the channel",
    }


def run(bot, event):
    """Handle kick and kickban commands"""
    if event["command"] == "kick":
        _kick_user(bot, event)
    elif event["command"] == "kickban":
        _kickban_user(bot, event)


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
    """Kick and ban a user from a channel"""
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
    reason = " ".join(args[1:]) if len(args) > 1 else "Banned by operator"
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
        
        bot.add_response(f"Kicked and banned {nick} ({hostmask}) from {channel}: {reason}")
    except Exception as e:
        bot.logger.error(f"Error kicking and banning user {nick}: {str(e)}")
        bot.add_response(f"Error kicking and banning user {nick}: {str(e)}")


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
    """Get a user's hostmask for banning"""
    try:
        # Try to get the user's hostmask from the channel
        # This is a simplified approach - in a real implementation,
        # you might want to use the WHO command to get more accurate information
        for user in bot.channels[channel].users():
            if user.lower() == nick.lower():
                # Get the user's hostmask
                user_obj = bot.channels[channel].userdict[user]
                # Create a ban mask in the form *!*@host
                return f"*!*@{user_obj.host}"
        
        # If we couldn't find the user, return a simple nick-based mask
        return f"{nick}!*@*"
    except Exception as e:
        bot.logger.error(f"Error getting hostmask for {nick}: {str(e)}")
        # Return a simple nick-based mask as fallback
        return f"{nick}!*@*"