#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Whocan module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["whocan"],
        "permissions": ["user"],
        "help": "List users with a specific permission.\n"
        "Usage: !whocan <permission> [channel] - Show users with the specified permission",
    }


def run(bot, event):
    """Handle whocan commands"""
    args = event["command_args"].split() if event["command_args"] else []

    if not args:
        bot.add_response("Please specify a permission to look up.")
        return

    permission = args[0]
    channel = args[1] if len(args) > 1 else ""

    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        # Find users with the specified permission
        if channel:
            # Channel-specific permission
            cur.execute(
                "SELECT u.username FROM phreakbot_users u "
                "JOIN phreakbot_perms p ON u.id = p.users_id "
                "WHERE p.permission = %s AND p.channel = %s "
                "ORDER BY u.username",
                (permission, channel.lower()),
            )
        else:
            # Global permission
            cur.execute(
                "SELECT u.username FROM phreakbot_users u "
                "JOIN phreakbot_perms p ON u.id = p.users_id "
                "WHERE p.permission = %s AND (p.channel = '' OR p.channel IS NULL) "
                "ORDER BY u.username",
                (permission,),
            )

        users = [row[0] for row in cur.fetchall()]
        cur.close()

        if users:
            if channel:
                bot.add_response(
                    f"Users with '{permission}' permission in {channel}: {', '.join(users)}"
                )
            else:
                bot.add_response(
                    f"Users with global '{permission}' permission: {', '.join(users)}"
                )
        else:
            if channel:
                bot.add_response(
                    f"No users found with '{permission}' permission in {channel}."
                )
            else:
                bot.add_response(
                    f"No users found with global '{permission}' permission."
                )

    except Exception as e:
        bot.logger.error(f"Database error in whocan module: {e}")
        bot.add_response("Error retrieving permission information.")
