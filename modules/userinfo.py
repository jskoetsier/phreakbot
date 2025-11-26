#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Userinfo module for PhreakBot
# A simpler alternative to the whois module


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["userinfo"],
        "permissions": ["user"],
        "help": "Shows information about a user in the channel.\n"
        "Usage: !userinfo <nickname> - Show information about a user",
    }


async def run(bot, event):
    """Handle userinfo commands"""
    if event["trigger"] == "command" and event["command"] == "userinfo":
        tnick = event["command_args"].strip()

        if not tnick:
            bot.add_response("Please specify a nickname to look up.")
            return

        if tnick == bot.nickname:
            bot.add_response(f"I am the channel bot, {bot.nickname}")
            return

        # First check if the user is in any channel
        found_user = None
        found_channel = None

        # Debug: Log all channels and their users
        bot.logger.info(f"All channels: {list(bot.channels.keys())}")

        # Check current channel first
        current_channel = event["channel"]
        if current_channel in bot.channels:
            try:
                channel_data = bot.channels[current_channel]
                bot.logger.info(f"Channel data type: {type(channel_data)}")
                bot.logger.info(
                    f"Channel data keys: {list(channel_data.keys()) if isinstance(channel_data, dict) else 'Not a dict'}"
                )

                if "users" in channel_data:
                    # In pydle, channel['users'] is a set, not a dict
                    users = list(channel_data["users"])
                    bot.logger.info(f"Current channel {current_channel} users: {users}")

                # Check if the user is in this channel (case insensitive)
                for user in users:
                    if user.lower() == tnick.lower():
                        found_user = user
                        found_channel = current_channel
                        bot.logger.info(
                            f"Found user '{user}' in current channel '{current_channel}'"
                        )
                        break
            except Exception as e:
                bot.logger.error(
                    f"Error checking current channel {current_channel}: {e}"
                )
                import traceback

                bot.logger.error(f"Traceback: {traceback.format_exc()}")

        # If not found in current channel, check all other channels
        if not found_user:
            for channel_name in bot.channels:
                if channel_name == current_channel:
                    continue  # Skip current channel as we already checked it

                try:
                    channel_data = bot.channels[channel_name]
                    if "users" in channel_data:
                        # In pydle, channel['users'] is a set, not a dict
                        users = list(channel_data["users"])
                        bot.logger.info(f"Channel {channel_name} users: {users}")

                    # Check if the user is in this channel (case insensitive)
                    for user in users:
                        if user.lower() == tnick.lower():
                            found_user = user
                            found_channel = channel_name
                            bot.logger.info(
                                f"Found user '{user}' in channel '{channel_name}'"
                            )
                            break

                    if found_user:
                        break
                except Exception as e:
                    bot.logger.error(f"Error checking channel {channel_name}: {e}")
                    import traceback

                    bot.logger.error(f"Traceback: {traceback.format_exc()}")

        if not found_user:
            bot.add_response(f"{tnick} is not in any channel I'm in.")
            return

        # Use WHO command to get the user's real hostmask
        bot.logger.info(f"Sending WHO command for user '{found_user}'")
        await bot.rawmsg("WHO", found_user)

        # Wait briefly for WHO response (pydle handles this async)
        import asyncio

        await asyncio.sleep(0.5)

        # Try to get user info from pydle's user cache
        user_hostmask = None

        # Check if pydle has user info stored
        if hasattr(bot, "users") and found_user in bot.users:
            user_data = bot.users[found_user]
            username = user_data.get("username", found_user)
            hostname = user_data.get("hostname", "unknown")
            user_hostmask = f"{found_user}!{username}@{hostname}"
            bot.logger.info(f"Got hostmask from pydle users cache: {user_hostmask}")
        else:
            # Fallback: construct basic hostmask
            bot.logger.warning(
                f"Could not get real hostmask for '{found_user}', using placeholder"
            )
            user_hostmask = f"{found_user}!{found_user}@user.unknown"

        # User found, display information
        if user_hostmask:
            bot.add_response(
                f"{tnick} is on channel {found_channel} as {user_hostmask}."
            )
        else:
            bot.add_response(
                f"{tnick} is on channel {found_channel} (hostmask lookup failed)."
            )

        # Check if the user exists in the database
        if bot.db_connection:
            try:
                # Try to get user info from the database by username first
                cur = bot.db_connection.cursor()
                cur.execute(
                    "SELECT * FROM phreakbot_users WHERE username ILIKE %s",
                    (tnick.lower(),),
                )
                user_by_username = cur.fetchone()
                cur.close()

                if user_by_username:
                    # Get full user info by ID
                    cur = bot.db_connection.cursor()
                    cur.execute(
                        "SELECT * FROM phreakbot_users WHERE id = %s",
                        (user_by_username[0],),
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
                        bot.add_response(
                            f"Global permissions: {', '.join(global_perms)}"
                        )

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
                elif user_hostmask:
                    # Try by hostmask as a fallback (only if we got a valid hostmask)
                    user_by_hostmask = bot.db_get_userinfo_by_userhost(user_hostmask)

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
                        hostmasks_text = (
                            f"Hostmasks: {', '.join(user_by_hostmask['hostmasks'])}"
                        )
                        bot.add_response(hostmasks_text)
                    else:
                        bot.add_response("Unrecognized user (not in database).")
                else:
                    bot.add_response("Unrecognized user (not in database).")
            except Exception as e:
                bot.logger.error(f"Database error in userinfo module: {e}")
                bot.add_response("Error retrieving user information from database.")
