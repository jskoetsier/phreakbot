#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Mass Meet module for PhreakBot
# Registers all users in channels and merges hostmasks


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["massmeet"],
        "permissions": ["owner", "admin"],
        "help": "Register all users in channels and merge hostmasks.\n"
        "Usage: !massmeet - Register all unregistered users and merge hostmasks",
    }


async def run(bot, event):
    """Handle massmeet command"""
    if event["command"] != "massmeet":
        return

    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    bot.add_response("Starting mass meet process. This may take a moment...")

    # Statistics to track actions
    stats = {
        "total_users": 0,
        "registered_new": 0,
        "merged_hostmasks": 0,
        "already_registered": 0,
        "errors": 0,
        "skipped": 0,
    }

    try:
        # Get all users from all channels
        all_users = {}

        # Get the current channel from the event
        current_channel = event["channel"]
        bot.logger.info(f"Processing channel: {current_channel}")

        # Get users from the channel
        if current_channel in bot.channels:
            channel_users = bot.channels[current_channel].get("users", {})
            bot.logger.info(f"Found {len(channel_users)} users in {current_channel}")

            for nick in channel_users:
                if nick.lower() == bot.nickname.lower():
                    continue

                try:
                    # Try to get hostmask from cache first
                    if nick.lower() in bot.user_hostmasks:
                        hostmask = bot.user_hostmasks[nick.lower()]
                        bot.logger.info(f"Using cached hostmask for {nick}: {hostmask}")
                    else:
                        # Get hostmask via WHOIS
                        user_info = await bot.whois(nick)
                        if user_info and isinstance(user_info, dict):
                            hostmask = f"{nick}!{user_info.get('username', 'unknown')}@{user_info.get('hostname', 'unknown')}"
                            bot.user_hostmasks[nick.lower()] = hostmask
                            bot.logger.info(f"Got hostmask via WHOIS for {nick}: {hostmask}")
                        else:
                            bot.logger.warning(f"Could not get hostmask for {nick}, skipping")
                            stats["skipped"] += 1
                            continue

                    all_users[nick] = hostmask
                except Exception as e:
                    bot.logger.error(f"Error getting hostmask for {nick}: {e}")
                    stats["errors"] += 1
                    continue
        else:
            bot.logger.warning(f"Channel {current_channel} not in bot.channels")
            bot.add_response(f"Could not access channel {current_channel}")
            return

        stats["total_users"] = len(all_users)
        bot.logger.info(f"Found {len(all_users)} users to process")

        # Process each user
        cur = bot.db_connection.cursor()

        for nickname, hostmask in all_users.items():
            try:
                bot.logger.info(
                    f"Processing user: {nickname} with hostmask: {hostmask}"
                )

                # Check if the user exists in the database by nickname
                cur.execute(
                    "SELECT id, username FROM phreakbot_users WHERE username ILIKE %s",
                    (nickname.lower(),),
                )
                user_by_name = cur.fetchone()

                # Check if the hostmask is associated with any user
                cur.execute(
                    "SELECT u.id, u.username FROM phreakbot_users u JOIN phreakbot_hostmasks h ON u.id = h.users_id WHERE h.hostmask ILIKE %s",
                    (hostmask.lower(),),
                )
                user_by_hostmask = cur.fetchone()

                # Case 1: User exists by name and hostmask matches the same user
                if (
                    user_by_name
                    and user_by_hostmask
                    and user_by_name[0] == user_by_hostmask[0]
                ):
                    bot.logger.info(
                        f"User {nickname} already registered with matching hostmask"
                    )
                    stats["already_registered"] += 1
                    continue

                # Case 2: User exists by name but hostmask doesn't match or is not registered
                if user_by_name and (
                    not user_by_hostmask or user_by_name[0] != user_by_hostmask[0]
                ):
                    # Merge the hostmask to the existing user
                    if user_by_hostmask:
                        bot.logger.info(
                            f"Hostmask {hostmask} already associated with user {user_by_hostmask[1]}, skipping"
                        )
                        stats["skipped"] += 1
                        continue

                    bot.logger.info(
                        f"Merging hostmask {hostmask} to user {user_by_name[1]}"
                    )
                    cur.execute(
                        "INSERT INTO phreakbot_hostmasks (users_id, hostmask) VALUES (%s, %s)",
                        (user_by_name[0], hostmask.lower()),
                    )
                    stats["merged_hostmasks"] += 1
                    continue

                # Case 3: User doesn't exist by name but hostmask is registered
                if not user_by_name and user_by_hostmask:
                    bot.logger.info(
                        f"Nickname {nickname} not in database but hostmask {hostmask} is registered to {user_by_hostmask[1]}, skipping"
                    )
                    stats["skipped"] += 1
                    continue

                # Case 4: User doesn't exist by name or hostmask - register new user
                if not user_by_name and not user_by_hostmask:
                    bot.logger.info(
                        f"Registering new user {nickname} with hostmask {hostmask}"
                    )

                    # Create new user
                    cur.execute(
                        "INSERT INTO phreakbot_users (username) VALUES (%s) RETURNING id",
                        (nickname.lower(),),
                    )
                    user_id = cur.fetchone()[0]

                    # Add hostmask
                    cur.execute(
                        "INSERT INTO phreakbot_hostmasks (users_id, hostmask) VALUES (%s, %s)",
                        (user_id, hostmask.lower()),
                    )

                    # Add user permission
                    cur.execute(
                        "INSERT INTO phreakbot_perms (users_id, permission) VALUES (%s, %s)",
                        (user_id, "user"),
                    )

                    stats["registered_new"] += 1

            except Exception as e:
                bot.logger.error(f"Error processing user {nickname}: {e}")
                stats["errors"] += 1

        # Commit all changes
        bot.db_connection.commit()
        cur.close()

        # Report results
        summary = (
            f"Mass meet complete! "
            f"Processed {stats['total_users']} users: "
            f"{stats['registered_new']} new registrations, "
            f"{stats['merged_hostmasks']} hostmasks merged, "
            f"{stats['already_registered']} already registered, "
            f"{stats['skipped']} skipped, "
            f"{stats['errors']} errors."
        )
        bot.add_response(summary)

    except Exception as e:
        bot.logger.error(f"Error in massmeet module: {e}")
        import traceback

        bot.logger.error(f"Traceback: {traceback.format_exc()}")
        bot.add_response("Error during mass meet process.")
