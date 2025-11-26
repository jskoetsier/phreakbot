#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Channel Operator module for PhreakBot
# Allows operators to manage channel modes (op/deop/voice/devoice)


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["op", "deop", "voice", "devoice"],
        "permissions": ["owner", "admin", "op"],
        "help": "Manage channel operator and voice modes.\n"
        "Usage: !op <nickname> - Give operator status (+o) to a user\n"
        "       !deop <nickname> - Remove operator status (-o) from a user\n"
        "       !voice <nickname> - Give voice (+v) to a user\n"
        "       !devoice <nickname> - Remove voice (-v) from a user",
    }


async def run(bot, event):
    """Handle channel operator commands"""
    if event["command"] == "op":
        await _op_user(bot, event)
    elif event["command"] == "deop":
        await _deop_user(bot, event)
    elif event["command"] == "voice":
        await _voice_user(bot, event)
    elif event["command"] == "devoice":
        await _devoice_user(bot, event)


async def _op_user(bot, event):
    """Give operator status to a user"""
    # Check if the user has permission
    if not _has_permission(bot, event):
        bot.add_response("You don't have permission to give operator status.")
        return

    # Parse command arguments
    args = event["command_args"].strip() if event["command_args"] else ""

    if not args:
        bot.add_response("Please specify a nickname to op.")
        return

    nick = args
    channel = event["channel"]

    # Check if this is a channel
    if not channel.startswith("#"):
        bot.add_response("This command can only be used in a channel.")
        return

    # Check if the bot has operator status
    if not _bot_is_op(bot, channel):
        bot.add_response("I need to be a channel operator to give op to others.")
        return

    # Check if the user is in the channel
    if channel in bot.channels and "users" in bot.channels[channel]:
        users = list(bot.channels[channel]["users"])
        if nick not in users:
            bot.add_response(f"{nick} is not in {channel}.")
            return

    try:
        # Give operator status
        await bot.set_mode(channel, "+o", nick)
        bot.add_response(f"Gave operator status to {nick} in {channel}")
        bot.logger.info(f"Gave +o to {nick} in {channel} by {event['nick']}")
    except Exception as e:
        bot.logger.error(f"Error giving +o to {nick}: {str(e)}")
        bot.add_response(f"Error giving operator status to {nick}: {str(e)}")


async def _deop_user(bot, event):
    """Remove operator status from a user"""
    # Check if the user has permission
    if not _has_permission(bot, event):
        bot.add_response("You don't have permission to remove operator status.")
        return

    # Parse command arguments
    args = event["command_args"].strip() if event["command_args"] else ""

    if not args:
        bot.add_response("Please specify a nickname to deop.")
        return

    nick = args
    channel = event["channel"]

    # Check if this is a channel
    if not channel.startswith("#"):
        bot.add_response("This command can only be used in a channel.")
        return

    # Don't allow deopping the bot itself
    if nick.lower() == bot.nickname.lower():
        bot.add_response("I won't deop myself.")
        return

    # Check if the user is in the channel
    if channel in bot.channels and "users" in bot.channels[channel]:
        users = list(bot.channels[channel]["users"])
        if nick not in users:
            bot.add_response(f"{nick} is not in {channel}.")
            return

    try:
        # Remove operator status
        await bot.set_mode(channel, "-o", nick)
        bot.add_response(f"Removed operator status from {nick} in {channel}")
        bot.logger.info(f"Removed -o from {nick} in {channel} by {event['nick']}")
    except Exception as e:
        bot.logger.error(f"Error removing -o from {nick}: {str(e)}")
        bot.add_response(f"Error removing operator status from {nick}: {str(e)}")


async def _voice_user(bot, event):
    """Give voice to a user"""
    # Check if the user has permission
    if not _has_permission(bot, event):
        bot.add_response("You don't have permission to give voice.")
        return

    # Parse command arguments
    args = event["command_args"].strip() if event["command_args"] else ""

    if not args:
        bot.add_response("Please specify a nickname to voice.")
        return

    nick = args
    channel = event["channel"]

    # Check if this is a channel
    if not channel.startswith("#"):
        bot.add_response("This command can only be used in a channel.")
        return

    # Check if the user is in the channel
    if channel in bot.channels and "users" in bot.channels[channel]:
        users = list(bot.channels[channel]["users"])
        if nick not in users:
            bot.add_response(f"{nick} is not in {channel}.")
            return

    try:
        # Give voice
        await bot.set_mode(channel, "+v", nick)
        bot.add_response(f"Gave voice to {nick} in {channel}")
        bot.logger.info(f"Gave +v to {nick} in {channel} by {event['nick']}")
    except Exception as e:
        bot.logger.error(f"Error giving +v to {nick}: {str(e)}")
        bot.add_response(f"Error giving voice to {nick}: {str(e)}")


async def _devoice_user(bot, event):
    """Remove voice from a user"""
    # Check if the user has permission
    if not _has_permission(bot, event):
        bot.add_response("You don't have permission to remove voice.")
        return

    # Parse command arguments
    args = event["command_args"].strip() if event["command_args"] else ""

    if not args:
        bot.add_response("Please specify a nickname to devoice.")
        return

    nick = args
    channel = event["channel"]

    # Check if this is a channel
    if not channel.startswith("#"):
        bot.add_response("This command can only be used in a channel.")
        return

    # Check if the user is in the channel
    if channel in bot.channels and "users" in bot.channels[channel]:
        users = list(bot.channels[channel]["users"])
        if nick not in users:
            bot.add_response(f"{nick} is not in {channel}.")
            return

    try:
        # Remove voice
        await bot.set_mode(channel, "-v", nick)
        bot.add_response(f"Removed voice from {nick} in {channel}")
        bot.logger.info(f"Removed -v from {nick} in {channel} by {event['nick']}")
    except Exception as e:
        bot.logger.error(f"Error removing -v from {nick}: {str(e)}")
        bot.add_response(f"Error removing voice from {nick}: {str(e)}")


def _has_permission(bot, event):
    """Check if the user has permission to use channel operator commands"""
    # Owner always has permission
    if bot._is_owner(event["hostmask"]):
        return True

    # Check if the user has the required permissions
    if event["user_info"]:
        # Check global permissions
        if "op" in event["user_info"]["permissions"]["global"] or event[
            "user_info"
        ].get("is_admin"):
            return True

        # Check channel-specific permissions
        channel = event["channel"]
        if channel in event["user_info"]["permissions"]:
            if "op" in event["user_info"]["permissions"][channel]:
                return True

    return False


def _bot_is_op(bot, channel):
    """Check if the bot has operator status in the channel"""
    try:
        # Check if the bot is in the channel
        if channel not in bot.channels:
            return False

        # In pydle, we can check if bot's nickname is in the channel
        # But pydle doesn't track individual user modes easily
        # For now, we'll just return True and let IRC reject the command
        # A better implementation would check bot.channels[channel] for operator info

        # Try to check if we have channel info
        channel_data = bot.channels.get(channel)
        if not channel_data:
            return False

        # Pydle doesn't easily expose individual user modes
        # So we'll just return True and rely on IRC to reject if bot isn't op
        # This prevents the error message but IRC will silently ignore
        return True
    except Exception as e:
        bot.logger.error(f"Error checking if bot is op in {channel}: {e}")
        return False
