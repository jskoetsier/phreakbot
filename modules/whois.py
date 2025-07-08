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
    found_channel = None
    
    # Debug: Log all channels and their users
    bot.logger.info(f"All channels: {list(bot.channels.keys())}")
    for channel_name, channel in bot.channels.items():
        try:
            # Get the users in the channel
            users = list(channel.users())
            bot.logger.info(f"Channel {channel_name} users: {users}")
        except Exception as e:
            bot.logger.error(f"Error listing users in {channel_name}: {e}")
    
    # First check the current channel
    current_channel = event['channel']
    if current_channel in bot.channels:
        try:
            users = list(bot.channels[current_channel].users())
            bot.logger.info(f"Current channel {current_channel} users: {users}")
            
            # Check if the user is in this channel (case insensitive)
            for user in users:
                if user.lower() == tnick.lower():
                    tuserhost = f"{user}!{user}@{bot.connection.server}"
                    found_channel = current_channel
                    bot.logger.info(f"Found user '{user}' in current channel '{current_channel}' with generated hostmask '{tuserhost}'")
                    break
        except Exception as e:
            bot.logger.error(f"Error checking current channel {current_channel}: {e}")
            import traceback
            bot.logger.error(f"Traceback: {traceback.format_exc()}")
    
    # If not found in current channel, check all other channels
    if not tuserhost:
        for channel_name, channel in bot.channels.items():
            if channel_name == current_channel:
                continue  # Skip current channel as we already checked it
                
            try:
                # Get the users in the channel
                users = list(channel.users())
                
                # Check if the user is in this channel (case insensitive)
                for user in users:
                    if user.lower() == tnick.lower():
                        tuserhost = f"{user}!{user}@{bot.connection.server}"
                        found_channel = channel_name
                        bot.logger.info(f"Found user '{user}' in channel '{channel_name}' with generated hostmask '{tuserhost}'")
                        break
                
                if tuserhost:
                    break
            except Exception as e:
                bot.logger.error(f"Error checking channel {channel_name}: {e}")
                import traceback
                bot.logger.error(f"Traceback: {traceback.format_exc()}")

    if not tuserhost:
        bot.add_response(f"{tnick} is not in any channel I'm in.")
        return
    else:
        bot.add_response(f"{tnick} is on channel {found_channel} as {tuserhost}.")

    # Check if the user exists in the database
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        # First check by username since we know the generated hostmask might not match
        cur = bot.db_connection.cursor()
        cur.execute(
            "SELECT * FROM phreakbot_users WHERE username ILIKE %s", (tnick.lower(),)
        )
        user_by_username = cur.fetchone()
        cur.close()

        if user_by_username:
            # Get full user info by ID
            cur = bot.db_connection.cursor()
            cur.execute(
                "SELECT * FROM phreakbot_users WHERE id = %s", (user_by_username[0],)
            )
            user_info = cur.fetchone()
            cur.close()

            # Get user permissions
            cur = bot.db_connection.cursor()
            cur.execute(
                "SELECT permission, channel FROM phreakbot_perms WHERE users_id = %s",
                (user_info[0],),
            )
            permissions = cur.fetchall()
            cur.close()

            # Get user hostmasks
            cur = bot.db_connection.cursor()
            cur.execute(
                "SELECT hostmask FROM phreakbot_hostmasks WHERE users_id = %s",
                (user_info[0],),
            )
            hostmasks = [row[0] for row in cur.fetchall()]
            cur.close()

            # Display user info
            bot.add_response(f"Recognized as user '{user_info[1]}'")

            # Show permissions
            global_perms = []
            channel_perms = {}
            for perm in permissions:
                if not perm[1] or perm[1] == "":
                    global_perms.append(perm[0])
                else:
                    if perm[1] not in channel_perms:
                        channel_perms[perm[1]] = []
                    channel_perms[perm[1]].append(perm[0])

            if global_perms:
                bot.add_response(f"Global permissions: {', '.join(global_perms)}")

            channel = event["channel"]
            if channel in channel_perms:
                bot.add_response(
                    f"Channel permissions for {channel}: {', '.join(channel_perms[channel])}"
                )

            # Show hostmasks
            if hostmasks:
                bot.add_response(f"Hostmasks: {', '.join(hostmasks)}")

            # Show owner/admin status
            if user_info[4]:  # is_owner
                bot.add_response("This user is the bot owner.")
            elif user_info[3]:  # is_admin
                bot.add_response("This user is a bot admin.")

        else:
            # Try by hostmask as a fallback
            user_by_hostmask = bot.db_get_userinfo_by_userhost(tuserhost)

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
            else:
                bot.add_response("Unrecognized user.")

    except Exception as e:
        bot.logger.error(f"Database error in whois module: {e}")
        bot.add_response("Error retrieving user information.")
