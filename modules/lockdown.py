#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot - A modular IRC bot
# Lockdown module - Allows channel operators to lock down a channel
#

import time

def config(pb):
    """Return module configuration"""
    return {
        "events": ["join"],
        "commands": ["lockdown", "unlock"],
        "help": {
            "lockdown": "Lock down the channel (set +im) and kick unregistered users. Usage: !lockdown",
            "unlock": "Unlock the channel (set -im). Usage: !unlock"
        },
        "permissions": ["admin", "owner"]
    }

def run(pb, event):
    """Handle lockdown commands"""
    if event["command"] == "lockdown":
        channel = event["channel"]

        # Check if this is a channel
        if not channel.startswith("#"):
            pb.reply("This command can only be used in a channel.")
            return

        # Set channel mode +im (invite-only and moderated)
        pb.connection.mode(channel, "+im")

        # Get list of users who aren't registered
        kicked_count = 0

        # Check if the channel exists in the bot's channels dictionary
        if channel in pb.channels:
            pb.logger.info(f"Checking users in {channel} for lockdown kick")

            try:
                # Get all users in the channel
                users = list(pb.channels[channel].users())
                pb.logger.info(f"Users in {channel}: {users}")

                # Process each user in the channel
                for nick in users:
                    # Skip the bot itself
                    if nick == pb.connection.get_nickname():
                        continue

                    pb.logger.info(f"Checking if {nick} is registered")

                    try:
                        # Create a hostmask for the user (this is an approximation)
                        user_hostmask = f"{nick}!{nick}@{pb.connection.server}"

                        # Check if user is in the database (registered)
                        user_info = pb.db_get_userinfo_by_userhost(user_hostmask)

                        # Also try by username directly as a fallback
                        if not user_info:
                            # Try to get user info from the database by username
                            cur = pb.db_connection.cursor()
                            cur.execute(
                                "SELECT * FROM phreakbot_users WHERE username ILIKE %s", (nick.lower(),)
                            )
                            user_by_username = cur.fetchone()
                            cur.close()

                            if user_by_username:
                                user_info = True  # Just need to know they exist

                        pb.logger.info(f"User info for {nick} ({user_hostmask}): {user_info is not None}")

                        if not user_info:
                            # User is not registered, kick them
                            pb.logger.info(f"Kicking unregistered user {nick}")
                            pb.connection.kick(channel, nick, "Channel lockdown: unregistered users are not allowed during lockdown")
                            kicked_count += 1
                        else:
                            pb.logger.info(f"User {nick} is registered, not kicking")
                    except Exception as e:
                        pb.logger.error(f"Error checking user {nick}: {str(e)}")
                        import traceback
                        pb.logger.error(f"Traceback: {traceback.format_exc()}")
            except Exception as e:
                pb.logger.error(f"Error processing users in {channel}: {str(e)}")
                import traceback
                pb.logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            pb.logger.warning(f"Channel {channel} not found in bot's channels dictionary")

        pb.reply(f"Channel {channel} is now locked down (mode +im). Kicked {kicked_count} unregistered users.")

    elif event["command"] == "unlock":
        channel = event["channel"]

        # Check if this is a channel
        if not channel.startswith("#"):
            pb.reply("This command can only be used in a channel.")
            return

        # Set channel mode -im (remove invite-only and moderated)
        pb.connection.mode(channel, "-im")
        pb.reply(f"Channel {channel} is now unlocked (mode -im).")
