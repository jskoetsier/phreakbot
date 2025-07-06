#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Merge module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["merge"],
        "permissions": ["owner", "admin", "merge"],
        "help": "Merge the hostmask of an IRC user to a database user.\n"
        "Usage: !merge <irc_nick> <db_username> - Associate a hostmask with an existing user",
    }


def run(bot, event):
    """Handle merge commands"""
    try:
        merge_irc_nick, merge_db_user = event["command_args"].split(" ", 1)
    except ValueError:
        bot.add_response("Usage: !merge <irc_nick> <db_username>")
        return

    merge_db_user = merge_db_user.lower()

    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        # Check if the database user exists
        cur.execute(
            "SELECT id, username FROM phreakbot_users WHERE username = %s",
            (merge_db_user,),
        )
        db_userinfo = cur.fetchone()
        if not db_userinfo:
            bot.add_response(f"User '{merge_db_user}' was not found in the database.")
            cur.close()
            return

        # Get the IRC user's hostmask
        merge_userhost = None
        for channel in bot.channels.values():
            if merge_irc_nick in channel.users():
                merge_userhost = channel.users()[merge_irc_nick]
                break

        if not merge_userhost:
            bot.add_response(f"Nick '{merge_irc_nick}' was not found in any channel.")
            cur.close()
            return

        # Check if the hostmask is already associated with a user
        cur.execute(
            "SELECT u.* FROM phreakbot_users u JOIN phreakbot_hostmasks h ON u.id = h.users_id WHERE h.hostmask = %s",
            (merge_userhost.lower(),),
        )
        existing_user = cur.fetchone()
        if existing_user:
            bot.add_response(
                f"Hostmask '{merge_userhost}' for nick '{merge_irc_nick}' already matches registered user '{existing_user[1]}'."
            )
            cur.close()
            return

        # Add the hostmask to the database user
        cur.execute(
            "INSERT INTO phreakbot_hostmasks (users_id, hostmask) VALUES (%s, %s)",
            (db_userinfo[0], merge_userhost.lower()),
        )

        bot.db_connection.commit()
        cur.close()

        bot.add_response(
            f"Hostmask '{merge_userhost}' added to '{db_userinfo[1]}', '{merge_irc_nick}' is now identified."
        )

    except Exception as e:
        bot.logger.error(f"Database error in merge module: {e}")
        bot.add_response("Error merging hostmask.")
