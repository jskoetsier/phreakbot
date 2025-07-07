#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Whois module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["whois"],
        "permissions": ["user"],
        "help": "Tells you who the bot thinks someone is.\n"
        "Usage: !whois <nickname> - Show information about a user",
    }


def run(bot, event):
    """Handle whois commands"""
    tnick = event["command_args"]

    if not tnick:
        bot.add_response("Please specify a nickname to look up.")
        return

    if tnick == bot.connection.get_nickname():
        bot.add_response(f"I am the channel bot, {bot.connection.get_nickname()}")
        return

    # Get the user's hostmask
    tuserhost = None
    for channel_name, channel in bot.channels.items():
        try:
            # Get the users in the channel
            users = channel.users()
            bot.logger.info(f"Channel {channel_name} users: {list(users)}")
            
            # Check if the user is in this channel (case insensitive)
            for user in users:
                if user.lower() == tnick.lower():
                    # Since we can't get the hostmask directly, we'll create a generic one
                    # Format: nickname!username@hostname
                    # We'll use the nickname for both the nickname and username parts
                    tuserhost = f"{user}!{user}@{bot.connection.server}"
                    bot.logger.info(f"Found user '{user}' with generated hostmask '{tuserhost}'")
                    break
            
            if tuserhost:
                break
        except Exception as e:
            bot.logger.error(f"Error accessing channel users: {e}")
            import traceback
            bot.logger.error(f"Traceback: {traceback.format_exc()}")

    if not tuserhost:
        bot.add_response(f"{tnick} is not in any channel I'm in.")
        return
    else:
        bot.add_response(f"{tnick} is on channel {event['channel']} as {tuserhost}.")

    # Check if the user exists in the database
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        # Check by hostmask
        user_by_hostmask = bot.db_get_userinfo_by_userhost(tuserhost)

        # Check by username
        cur = bot.db_connection.cursor()
        cur.execute(
            "SELECT * FROM phreakbot_users WHERE username ILIKE %s", (tnick.lower(),)
        )
        user_by_username = cur.fetchone()
        cur.close()

        if user_by_hostmask:
            bot.add_response(
                f"Recognized by hostmask as user '{user_by_hostmask['username']}'"
            )

            # Show permissions
            perms_text = "With "
            if user_by_hostmask["permissions"]["global"]:
                perms_text += f"global perms ({', '.join(user_by_hostmask['permissions']['global'])})"

                channel = event["channel"]
                if channel in user_by_hostmask["permissions"]:
                    perms_text += f" and '{channel}' perms ({', '.join(user_by_hostmask['permissions'][channel])})"

            bot.add_response(perms_text)

            # Show hostmasks
            hostmasks_text = f"Hostmasks: {', '.join(user_by_hostmask['hostmasks'])}"
            bot.add_response(hostmasks_text)

        elif not user_by_hostmask and user_by_username:
            bot.add_response(
                f"Unrecognized user. But a user named '{tnick}' exists. Perhaps use !merge?"
            )
        else:
            bot.add_response("Unrecognized user.")

    except Exception as e:
        bot.logger.error(f"Database error in whois module: {e}")
        bot.add_response("Error retrieving user information.")
