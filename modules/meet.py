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
        # Get the user's hostmask
        tuserhost = None
        found_user = None

        # Log all channels and users for debugging
        bot.logger.info(f"Looking for user '{tnick}' in channels:")
        for channel_name in bot.channels:
            # Get the users in the channel
            try:
                # In pydle, bot.channels[channel_name] is a dict with a 'users' key
                channel_data = bot.channels[channel_name]

                # The 'users' key contains a set of users
                if "users" in channel_data:
                    users = list(channel_data["users"])
                    bot.logger.info(f"Channel {channel_name} users: {users}")

                    # Check if the user is in this channel (case insensitive)
                    for user in users:
                        bot.logger.info(f"Checking user: {user}")
                        if user.lower() == tnick.lower():
                            found_user = user
                            bot.logger.info(
                                f"Found user '{user}' in channel {channel_name}"
                            )
                            break

                if found_user:
                    break
            except Exception as e:
                bot.logger.error(f"Error accessing channel users: {e}")
                import traceback

                bot.logger.error(f"Traceback: {traceback.format_exc()}")

        if not found_user:
            bot.add_response(f"Can't find user '{tnick}' on any channel.")
            bot.logger.info(f"User '{tnick}' not found in any channel")
            return

        # Get the actual hostmask - pydle's whois() doesn't work on IRCnet, so we'll construct a basic one
        # The real hostmask will be captured when the user sends a message
        tuserhost = f"{found_user}!{found_user}@user.unknown"
        bot.logger.info(f"Using constructed hostmask for '{found_user}': {tuserhost}")

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

    except Exception as e:
        bot.logger.error(f"Database error in meet module: {e}")
        bot.add_response("Error adding user to the database.")
