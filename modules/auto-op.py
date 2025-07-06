#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Auto-op module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": ["join"],
        "commands": ["autoop", "deautoop", "listautoop"],
        "permissions": ["owner", "admin", "autoop"],
        "help": "Automatically give operator status to users when they join.\n"
        "Usage: !autoop <nickname> [channel] - Add a user to the auto-op list\n"
        "       !deautoop <nickname> [channel] - Remove a user from the auto-op list\n"
        "       !listautoop [channel] - List users in the auto-op list",
    }


def run(bot, event):
    """Handle auto-op events and commands"""
    # Handle join events
    if event["trigger"] == "event" and event["signal"] == "join":
        _check_auto_op(bot, event)
        return

    # Handle commands
    if event["command"] == "autoop":
        _add_auto_op(bot, event)
    elif event["command"] == "deautoop":
        _remove_auto_op(bot, event)
    elif event["command"] == "listautoop":
        _list_auto_op(bot, event)


def _check_auto_op(bot, event):
    """Check if a user should be auto-opped when they join"""
    # Don't auto-op the bot itself
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

        # Check if the user is in the auto-op list for this channel
        cur.execute(
            "SELECT 1 FROM phreakbot_autoop a "
            "JOIN phreakbot_users u ON a.users_id = u.id "
            "JOIN phreakbot_hostmasks h ON u.id = h.users_id "
            "WHERE h.hostmask = %s AND (a.channel = %s OR a.channel = '')",
            (hostmask.lower(), channel.lower()),
        )

        if cur.fetchone():
            # Give the user operator status
            bot.logger.info(f"Auto-opping {nick} in {channel}")
            bot.connection.mode(channel, f"+o {nick}")

        cur.close()

    except Exception as e:
        bot.logger.error(f"Error in auto-op check: {e}")


def _add_auto_op(bot, event):
    """Add a user to the auto-op list"""
    # Check if the user has permission to manage auto-op
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"]
        and (
            "autoop" in event["user_info"]["permissions"]["global"]
            or event["user_info"].get("is_admin")
        )
    ):
        bot.add_response("You don't have permission to manage auto-op settings.")
        return

    args = event["command_args"].split() if event["command_args"] else []

    if not args:
        bot.add_response("Please specify a nickname to auto-op.")
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

        # Check if the user is already in the auto-op list for this channel
        cur.execute(
            "SELECT 1 FROM phreakbot_autoop WHERE users_id = %s AND channel = %s",
            (user_id, channel.lower()),
        )

        if cur.fetchone():
            bot.add_response(
                f"User '{nick}' is already in the auto-op list for {channel}."
            )
            cur.close()
            return

        # Add the user to the auto-op list
        cur.execute(
            "INSERT INTO phreakbot_autoop (users_id, channel) VALUES (%s, %s)",
            (user_id, channel.lower()),
        )

        bot.db_connection.commit()
        cur.close()

        bot.add_response(f"Added '{nick}' to the auto-op list for {channel}.")

    except Exception as e:
        bot.logger.error(f"Error adding auto-op: {e}")
        bot.add_response("Error updating auto-op settings.")


def _remove_auto_op(bot, event):
    """Remove a user from the auto-op list"""
    # Check if the user has permission to manage auto-op
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"]
        and (
            "autoop" in event["user_info"]["permissions"]["global"]
            or event["user_info"].get("is_admin")
        )
    ):
        bot.add_response("You don't have permission to manage auto-op settings.")
        return

    args = event["command_args"].split() if event["command_args"] else []

    if not args:
        bot.add_response("Please specify a nickname to remove from auto-op.")
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

        # Remove the user from the auto-op list
        cur.execute(
            "DELETE FROM phreakbot_autoop WHERE users_id = %s AND channel = %s",
            (user_id, channel.lower()),
        )

        if cur.rowcount > 0:
            bot.db_connection.commit()
            bot.add_response(f"Removed '{nick}' from the auto-op list for {channel}.")
        else:
            bot.add_response(f"User '{nick}' is not in the auto-op list for {channel}.")

        cur.close()

    except Exception as e:
        bot.logger.error(f"Error removing auto-op: {e}")
        bot.add_response("Error updating auto-op settings.")


def _list_auto_op(bot, event):
    """List users in the auto-op list"""
    channel = event["command_args"] if event["command_args"] else event["channel"]

    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        # Get users in the auto-op list for this channel
        cur.execute(
            "SELECT u.username FROM phreakbot_users u "
            "JOIN phreakbot_autoop a ON u.id = a.users_id "
            "WHERE a.channel = %s "
            "ORDER BY u.username",
            (channel.lower(),),
        )

        users = [row[0] for row in cur.fetchall()]

        # Get users with global auto-op
        cur.execute(
            "SELECT u.username FROM phreakbot_users u "
            "JOIN phreakbot_autoop a ON u.id = a.users_id "
            "WHERE a.channel = '' "
            "ORDER BY u.username"
        )

        global_users = [row[0] for row in cur.fetchall()]
        cur.close()

        if users or global_users:
            if users:
                bot.add_response(f"Users with auto-op in {channel}: {', '.join(users)}")
            if global_users:
                bot.add_response(
                    f"Users with global auto-op: {', '.join(global_users)}"
                )
        else:
            bot.add_response(f"No users in the auto-op list for {channel}.")

    except Exception as e:
        bot.logger.error(f"Error listing auto-op: {e}")
        bot.add_response("Error retrieving auto-op settings.")
