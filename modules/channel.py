#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Channel management module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": ["irc_in2_INVITE"],
        "commands": ["join", "part"],
        "permissions": ["owner", "admin", "join", "part"],
        "help": "Manage channel membership - !join <channel> to join a channel, !part [channel] to leave a channel",
    }


def run(bot, event):
    """Handle channel management commands"""
    # Handle invite events
    if event["trigger"] == "event" and event["signal"] == "irc_in2_INVITE":
        bot.logger.info(f"Received invite to {event['args'][1]} from {event['source']}")
        # Auto-join on invite if from owner or admin
        if bot._is_owner(event["hostmask"]) or (
            event["user_info"] and event["user_info"].get("is_admin")
        ):
            import asyncio

            try:

                async def join_channel():
                    await bot.join(event["args"][1])

                asyncio.create_task(join_channel())
                bot.add_response(f"Joining {event['args'][1]}")
            except Exception as e:
                bot.logger.error(f"Error joining channel: {e}")
                bot.add_response(f"Error joining channel: {str(e)}")

    # Handle join command
    if event["command"] == "join":
        # Check permissions - owner, admin, or users with join permission
        if not bot._check_permissions(event, ["owner", "admin", "join"]):
            bot.logger.info(
                f"Permission denied for {event['nick']} to use join command"
            )
            bot.add_response("You don't have permission to make the bot join channels.")
            return

        chan = event["command_args"]
        if not chan:
            bot.add_response("Please specify a channel to join.")
            return

        bot.logger.info(f"Joining channel '{chan}' on command from '{event['nick']}'")
        import asyncio

        try:

            async def join_channel():
                await bot.join(chan)

            asyncio.create_task(join_channel())
            bot.add_response(f"Joining {chan}")
        except Exception as e:
            bot.logger.error(f"Error joining channel: {e}")
            bot.add_response(f"Error joining channel: {str(e)}")
        return

    # Handle part command
    if event["command"] == "part":
        # Check permissions - owner, admin, or users with part permission
        if not bot._check_permissions(event, ["owner", "admin", "part"]):
            bot.logger.info(
                f"Permission denied for {event['nick']} to use part command"
            )
            bot.add_response(
                "You don't have permission to make the bot leave channels."
            )
            return

        chan = event["command_args"]
        if not chan:
            chan = event["channel"]

        bot.logger.info(f"Leaving channel '{chan}' on command from '{event['nick']}'")
        import asyncio

        try:

            async def part_channel():
                await bot.part(chan, f"Requested by {event['nick']}")

            asyncio.create_task(part_channel())
            bot.add_response(f"Leaving {chan}")
        except Exception as e:
            bot.logger.error(f"Error parting channel: {e}")
            bot.add_response(f"Error parting channel: {str(e)}")
        if chan != event["channel"]:
            bot.add_response(f"Left channel {chan}")
        return
