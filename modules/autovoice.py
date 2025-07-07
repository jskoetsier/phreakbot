#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Autovoice module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": ["join"],
        "commands": ["autovoice", "deautovoice", "listautovoice"],
        "permissions": ["owner", "admin", "autovoice"],
        "help": "Automatically give voice status to users when they join.\n"
        "Usage: !autovoice <nickname> [channel] - Add a user to the autovoice list\n"
        "       !deautovoice <nickname> [channel] - Remove a user from the autovoice list\n"
        "       !listautovoice [channel] - List users in the autovoice list",
    }


def run(bot, event):
    """Handle autovoice events and commands"""
    # Handle join events
    if event["trigger"] == "event" and event["signal"] == "join":
        _check_autovoice(bot, event)
        return

    # Handle commands
    if event["command"] == "autovoice":
        _add_autovoice(bot, event)
    elif event["command"] == "deautovoice":
        _remove_autovoice(bot, event)
    elif event["command"] == "listautovoice":
        _list_autovoice(bot, event)


def _check_autovoice(bot, event):
    """Check if a user should be autovoiced when they join"""
    # Don't autovoice the bot itself
    if event["nick"] == bot.connection.get_nickname():
        return

    # Check if the database connection is available
    if not bot.db_connection:
        return

    try:
        channel = event["channel"]
        nick = event["nick"]
        hostmask = event["hostmask"]

        cur = bot.db_connection.cursor()

        # Check if the user is in the autovoice list for this channel
        cur.execute(
            "SELECT 1 FROM phreakbot_autovoice a "
            "JOIN phreakbot_users u ON a.users_id = u.id "
            "JOIN phreakbot_hostmasks h ON u.id = h.users_id "
            "WHERE h.hostmask = %s AND (a.channel = %s OR a.channel = '')",
            (hostmask.lower(), channel.lower()),
        )

        if cur.fetchone():
            # Give the user voice status
            bot.logger.info(f"Autovoicing {nick} in {channel}")
            bot.connection.mode(channel, f"+v {nick}")

        cur.close()

    except Exception as e:
        bot.logger.error(f"Error in autovoice check: {e}")


def _add_autovoice(bot, event):
    """Add a user to the autovoice list"""
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
        bot.add_response("Please specify a nickname to autovoice.")
        return

    nick = args[0]
    channel = args[1] if len(args) > 1 else event["channel"]

    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        # Find the user in the database
        cur.execute(
            "SELECT id FROM phreakbot_users WHERE username ILIKE %s", (nick.lower(),)
        )
        user = cur.fetchone()

        if not user:
            bot.add_response(
                f"User '{nick}' not found. They need to be registered first."
            )
            cur.close()
            return

        user_id = user[0]

        # Check if the user is already in the autovoice list for this channel
        cur.execute(
            "SELECT 1 FROM phreakbot_autovoice WHERE users_id = %s AND channel = %s",
            (user_id, channel.lower()),
        )

        if cur.fetchone():
            bot.add_response(
                f"User '{nick}' is already in the autovoice list for {channel}."
            )
            cur.close()
            return

        # Add the user to the autovoice list
        cur.execute(
            "INSERT INTO phreakbot_autovoice (users_id, channel) VALUES (%s, %s)",
            (user_id, channel.lower()),
        )

        bot.db_connection.commit()
        cur.close()

        bot.add_response(f"Added '{nick}' to the autovoice list for {channel}.")

    except Exception as e:
        bot.logger.error(f"Error adding autovoice: {e}")
        bot.add_response("Error updating autovoice settings.")


def _remove_autovoice(bot, event):
    """Remove a user from the autovoice list"""
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
        bot.add_response("Please specify a nickname to remove from autovoice.")
        return

    nick = args[0]
    channel = args[1] if len(args) > 1 else event["channel"]

    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        # Find the user in the database
        cur.execute(
            "SELECT id FROM phreakbot_users WHERE username ILIKE %s", (nick.lower(),)
        )
        user = cur.fetchone()

        if not user:
            bot.add_response(f"User '{nick}' not found.")
            cur.close()
            return

        user_id = user[0]

        # Remove the user from the autovoice list
        cur.execute(
            "DELETE FROM phreakbot_autovoice WHERE users_id = %s AND channel = %s",
            (user_id, channel.lower()),
        )

        if cur.rowcount > 0:
            bot.db_connection.commit()
            bot.add_response(f"Removed '{nick}' from the autovoice list for {channel}.")
        else:
            bot.add_response(f"User '{nick}' is not in the autovoice list for {channel}.")

        cur.close()

    except Exception as e:
        bot.logger.error(f"Error removing autovoice: {e}")
        bot.add_response("Error updating autovoice settings.")


def _list_autovoice(bot, event):
    """List users in the autovoice list"""
    channel = event["command_args"] if event["command_args"] else event["channel"]

    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        # Get users in the autovoice list for this channel
        cur.execute(
            "SELECT u.username FROM phreakbot_users u "
            "JOIN phreakbot_autovoice a ON u.id = a.users_id "
            "WHERE a.channel = %s "
            "ORDER BY u.username",
            (channel.lower(),),
        )

        users = [row[0] for row in cur.fetchall()]

        # Get users with global autovoice
        cur.execute(
            "SELECT u.username FROM phreakbot_users u "
            "JOIN phreakbot_autovoice a ON u.id = a.users_id "
            "WHERE a.channel = '' "
            "ORDER BY u.username"
        )

        global_users = [row[0] for row in cur.fetchall()]
        cur.close()

        if users or global_users:
            if users:
                bot.add_response(f"Users with autovoice in {channel}: {', '.join(users)}")
            if global_users:
                bot.add_response(
                    f"Users with global autovoice: {', '.join(global_users)}"
                )
        else:
            bot.add_response(f"No users in the autovoice list for {channel}.")

    except Exception as e:
        bot.logger.error(f"Error listing autovoice: {e}")
        bot.add_response("Error retrieving autovoice settings.")