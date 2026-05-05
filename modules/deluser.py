#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Deluser module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["deluser"],
        "permissions": ["owner", "admin", "deluser"],
        "help": "Delete a user from the database.\n"
        "Usage: !deluser <nickname> - Remove a user from the database",
    }


def run(bot, event):
    """Handle deluser commands"""
    tnick = event["command_args"]
    if not tnick:
        bot.add_response("Please specify a nickname to delete.")
        return

    if tnick == bot.nickname:
        bot.add_response("Why are you so mean? :(")
        return

    # Check if the database connection is available
    conn = bot.db_get()
    if not conn:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = conn.cursor()

        # Check by username
        cur.execute(
            "SELECT id FROM phreakbot_users WHERE username ILIKE %s", (tnick.lower(),)
        )
        user = cur.fetchone()

        if not user:
            bot.add_response(f"No user named '{tnick}' was found.")
            cur.close()
            bot.db_return(conn)
            return

        user_id = user[0]

        # Delete the user's hostmasks
        cur.execute("DELETE FROM phreakbot_hostmasks WHERE users_id = %s", (user_id,))

        # Delete the user's permissions
        cur.execute("DELETE FROM phreakbot_perms WHERE users_id = %s", (user_id,))

        # Delete the user
        cur.execute("DELETE FROM phreakbot_users WHERE id = %s", (user_id,))

        conn.commit()
        cur.close()
        bot.db_return(conn)

        bot.add_response(f"Obliterated user '{tnick}' from existence.")

    except Exception as e:
        conn.rollback()
        bot.db_return(conn)
        bot.logger.error(f"Database error in deluser module: {e}")
        bot.add_response("Error deleting user.")
