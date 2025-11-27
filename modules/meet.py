#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Meet module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["meet"],
        "permissions": ["owner", "admin", "meet"],
        "help": "Introduce new users to the bot.\n"
        "Usage: !meet <nickname> - Register a new user in the database",
    }


def run(bot, event):
    """Handle meet commands"""
    # Strip whitespace from the nickname
    tnick = event["command_args"].strip() if event["command_args"] else ""

    bot.logger.info(f"Meet command called with nickname: '{tnick}'")

    if not tnick:
        bot.add_response("Please specify who you want me to meet.")
        return

    if tnick == bot.nickname:
        bot.add_response("I know who I am.")
        return

    # Check if the user exists in the database
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        # Get the user's hostmask from cache
        tuserhost = bot.user_hostmasks.get(tnick.lower())

        if not tuserhost:
            bot.add_response(
                f"Can't find hostmask for '{tnick}'. They need to join a channel or speak first."
            )
            bot.logger.info(f"No cached hostmask found for '{tnick}'")
            return

        bot.logger.info(f"Using cached hostmask for '{tnick}': {tuserhost}")

        # Check if the user already exists in the database
        cur = bot.db_connection.cursor()

        # Check by nickname
        cur.execute(
            "SELECT * FROM phreakbot_users WHERE username ILIKE %s", (tnick.lower(),)
        )
        if cur.fetchone():
            bot.add_response(
                f"A user with the name '{tnick}' already exists in the database."
            )
            cur.close()
            return

        # Check by hostmask
        cur.execute(
            "SELECT u.* FROM phreakbot_users u JOIN phreakbot_hostmasks h ON u.id = h.users_id WHERE h.hostmask ILIKE %s",
            (tuserhost.lower(),),
        )
        user_info = cur.fetchone()
        if user_info:
            bot.add_response(
                f"An existing user '{user_info[1]}' was found matching the hostmask for '{tnick}'."
            )
            cur.close()
            return

        # Create new user
        cur.execute(
            "INSERT INTO phreakbot_users (username) VALUES (%s) RETURNING id",
            (tnick.lower(),),
        )
        user_id = cur.fetchone()[0]

        # Add hostmask
        cur.execute(
            "INSERT INTO phreakbot_hostmasks (users_id, hostmask) VALUES (%s, %s)",
            (user_id, tuserhost.lower()),
        )

        # Add user permission
        cur.execute(
            "INSERT INTO phreakbot_perms (users_id, permission) VALUES (%s, %s)",
            (user_id, "user"),
        )

        bot.db_connection.commit()
        cur.close()

        bot.add_response(
            f"Added user '{tnick}' to the database with hostmask '{tuserhost}'."
        )

        # Invalidate user cache
        bot._cache_invalidate("user_info", tuserhost.lower())

    except Exception as e:
        bot.logger.error(f"Database error in meet module: {e}")
        import traceback

        bot.logger.error(f"Traceback: {traceback.format_exc()}")
        bot.add_response("Error adding user to the database.")
