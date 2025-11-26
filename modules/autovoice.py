#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Autovoice module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": ["join"],
        "commands": ["autovoice"],
        "permissions": ["owner", "admin", "autovoice"],
        "help": "Automatically give voice status to all registered users when they join.\n"
        "Usage: !autovoice on|off [channel] - Enable or disable autovoice for a channel\n"
        "       !autovoice status [channel] - Check if autovoice is enabled for a channel\n"
        "When autovoice is enabled, the channel is set to moderated mode (+m).",
    }


def run(bot, event):
    """Handle autovoice events and commands"""
    # Handle join events
    if event["trigger"] == "event" and event["signal"] == "join":
        _check_autovoice(bot, event)
        return

    # Handle commands
    if event["command"] == "autovoice":
        _manage_autovoice(bot, event)


def _check_autovoice(bot, event):
    """Check if a user should be autovoiced when they join"""
    # Don't autovoice the bot itself
    if event["nick"] == bot.nickname:
        return

    # Check if the database connection is available
    if not bot.db_connection:
        return

    try:
        channel = event["channel"]
        nick = event["nick"]
        hostmask = event["hostmask"]

        cur = bot.db_connection.cursor()

        # Check if autovoice is enabled for this channel
        cur.execute(
            "SELECT 1 FROM phreakbot_autovoice WHERE channel = %s AND enabled = TRUE",
            (channel.lower(),),
        )

        if not cur.fetchone():
            # Autovoice is not enabled for this channel
            cur.close()
            return

        # Check if the user is registered
        cur.execute(
            "SELECT 1 FROM phreakbot_users u "
            "JOIN phreakbot_hostmasks h ON u.id = h.users_id "
            "WHERE h.hostmask = %s",
            (hostmask.lower(),),
        )

        if cur.fetchone():
            # Give the user voice status
            bot.logger.info(f"Auto-voicing {nick} in {channel}")
            # Schedule mode change asynchronously
            import asyncio

            try:

                async def set_voice():
                    await bot.set_mode(channel, f"+v {nick}")

                asyncio.create_task(set_voice())
            except Exception as e:
                bot.logger.error(f"Error setting voice mode: {e}")

        cur.close()

    except Exception as e:
        bot.logger.error(f"Error in autovoice check: {e}")


def _manage_autovoice(bot, event):
    """Manage autovoice settings for a channel"""
    # Check if the user has permission to manage autovoice
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"]
        and (
            "autovoice" in event["user_info"]["permissions"]["global"]
            or event["user_info"].get("is_admin")
        )
    ):
        bot.add_response("You don't have permission to manage autovoice settings.")
        return

    args = event["command_args"].split() if event["command_args"] else []

    if not args:
        bot.add_response("Please specify 'on', 'off', or 'status' for autovoice.")
        return

    action = args[0].lower()
    channel = args[1] if len(args) > 1 else event["channel"]

    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        if action == "on":
            # Enable autovoice for the channel
            cur.execute(
                "INSERT INTO phreakbot_autovoice (channel, enabled) VALUES (%s, TRUE) "
                "ON CONFLICT (channel) DO UPDATE SET enabled = TRUE",
                (channel.lower(),),
            )
            bot.db_connection.commit()

            # Set moderated mode on the channel
            bot.logger.info(f"Setting moderated mode on {channel}")
            import asyncio

            try:

                async def set_moderated():
                    await bot.set_mode(channel, "+m")

                asyncio.create_task(set_moderated())
            except Exception as e:
                bot.logger.error(f"Error setting moderated mode: {e}")

            bot.add_response(
                f"Autovoice enabled for {channel}. Channel set to moderated mode (+m)."
            )

        elif action == "off":
            # Disable autovoice for the channel
            cur.execute(
                "INSERT INTO phreakbot_autovoice (channel, enabled) VALUES (%s, FALSE) "
                "ON CONFLICT (channel) DO UPDATE SET enabled = FALSE",
                (channel.lower(),),
            )
            bot.db_connection.commit()

            # Remove moderated mode from the channel
            bot.logger.info(f"Removing moderated mode from {channel}")
            import asyncio

            try:

                async def unset_moderated():
                    await bot.set_mode(channel, "-m")

                asyncio.create_task(unset_moderated())
            except Exception as e:
                bot.logger.error(f"Error removing moderated mode: {e}")

            bot.add_response(
                f"Autovoice disabled for {channel}. Channel moderated mode removed (-m)."
            )

        elif action == "status":
            # Check if autovoice is enabled for the channel
            cur.execute(
                "SELECT enabled FROM phreakbot_autovoice WHERE channel = %s",
                (channel.lower(),),
            )
            result = cur.fetchone()
            if result:
                status = "enabled" if result[0] else "disabled"
                bot.add_response(f"Autovoice is {status} for {channel}.")
            else:
                bot.add_response(f"Autovoice is not configured for {channel}.")

        else:
            bot.add_response("Invalid option. Use 'on', 'off', or 'status'.")

        cur.close()

    except Exception as e:
        bot.logger.error(f"Error managing autovoice: {e}")
        bot.add_response("Error updating autovoice settings.")
