#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Owner module for PhreakBot

import random


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["owner", "admin"],
        "permissions": ["user"],
        "help": "Manage bot ownership and admin privileges.\n"
        "Usage: !owner - Show current owner\n"
        "       !owner claim - Claim ownership of the bot (if no owner exists)\n"
        "       !admin list - List all admins\n"
        "       !admin add <username> - Add a user as admin (owner only)\n"
        "       !admin remove <username> - Remove admin privileges (owner only)",
    }


def run(bot, event):
    """Handle owner and admin commands"""
    command = event["command"]
    args = event["command_args"].split() if event["command_args"] else []

    # Log the command for debugging
    bot.logger.info(f"Owner module received command: {command} with args: {args}")
    bot.logger.info(f"User: {event['nick']} with hostmask: {event['hostmask']}")

    # Handle owner commands
    if command == "owner":
        bot.logger.info("Processing owner command")
        if not args:
            # Show current owner
            bot.logger.info("Showing current owner")
            _show_owner(bot, event)
        elif args[0] == "claim":
            # Claim ownership
            bot.logger.info(f"User {event['nick']} is attempting to claim ownership")
            _claim_ownership(bot, event)

    # Handle admin commands
    elif command == "admin":
        if not args:
            bot.add_response("Please specify an admin command: list, add, or remove")
            return

        if args[0] == "list":
            _list_admins(bot, event)
        elif args[0] == "add" and len(args) > 1:
            _add_admin(bot, event, args[1])
        elif args[0] == "remove" and len(args) > 1:
            _remove_admin(bot, event, args[1])
        else:
            bot.add_response("Unknown admin command. Use: list, add, or remove")


def _show_owner(bot, event):
    """Show the current bot owner"""
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()
        cur.execute("SELECT username FROM phreakbot_users WHERE is_owner = TRUE")
        owner = cur.fetchone()
        cur.close()

        if owner:
            bot.add_response(f"I am owned by {owner[0]}")
        else:
            # Fallback to config file
            if bot.config.get("owner"):
                bot.add_response(f"I am owned by {bot.config['owner']} (legacy config)")
            else:
                bot.add_response(
                    "This bot has no owner. Use !owner claim to claim ownership."
                )
    except Exception as e:
        bot.logger.error(f"Database error in _show_owner: {e}")
        bot.add_response("Error retrieving owner information.")


def _claim_ownership(bot, event):
    """Claim ownership of the bot"""
    # Check if there's already an owner in the database
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        # Log the hostmask for debugging
        bot.logger.info(
            f"Claim ownership attempt from: {event['nick']} with hostmask: {event['hostmask']}"
        )

        cur = bot.db_connection.cursor()
        cur.execute("SELECT COUNT(*) FROM phreakbot_users WHERE is_owner = TRUE")
        owner_count = cur.fetchone()[0]
        bot.logger.info(f"Current owner count in database: {owner_count}")

        # Check if the user is already the owner
        if bot._is_owner(event["hostmask"]):
            bot.add_response(f"You are already the owner, {event['nick']}!")
            cur.close()
            return

        # If there's already an owner and the current user is not the owner, reject the claim
        if owner_count > 0:
            bot.add_response("This bot already has an owner.")
            cur.close()
            return

        # Get user info or create new user
        user_info = event["user_info"]
        bot.logger.info(f"User info from event: {user_info}")

        if not user_info:
            bot.logger.info(
                f"Creating new user for {event['nick']} with hostmask {event['hostmask']}"
            )
            # Create new user
            cur.execute(
                "INSERT INTO phreakbot_users (username, is_owner) VALUES (%s, TRUE) RETURNING id",
                (event["nick"].lower(),),
            )
            user_id = cur.fetchone()[0]
            bot.logger.info(f"Created new user with ID: {user_id}")

            # Add hostmask
            bot.logger.info(
                f"Adding hostmask {event['hostmask']} for user ID {user_id}"
            )
            cur.execute(
                "INSERT INTO phreakbot_hostmasks (users_id, hostmask) VALUES (%s, %s)",
                (user_id, event["hostmask"].lower()),
            )

            # Add owner and other essential permissions
            bot.logger.info(
                f"Adding owner and essential permissions for user ID {user_id}"
            )
            essential_permissions = [
                "owner",
                "admin",
                "topic",
                "perm",
                "join",
                "part",
                "autoop",
            ]
            for permission in essential_permissions:
                cur.execute(
                    "INSERT INTO phreakbot_perms (users_id, permission) VALUES (%s, %s)",
                    (user_id, permission),
                )
        else:
            # Update existing user
            cur.execute(
                "UPDATE phreakbot_users SET is_owner = TRUE WHERE id = %s",
                (user_info["id"],),
            )

            # Check if user has owner permission
            has_owner_perm = False
            if (
                "global" in user_info["permissions"]
                and "owner" in user_info["permissions"]["global"]
            ):
                has_owner_perm = True

            if not has_owner_perm:
                cur.execute(
                    "INSERT INTO phreakbot_perms (users_id, permission) VALUES (%s, %s)",
                    (user_info["id"], "owner"),
                )

        # If there was a previous owner in the config, remove it
        if "owner" in bot.config:
            del bot.config["owner"]
            bot.save_config()

        bot.db_connection.commit()
        cur.close()
        bot.add_response(f"Congratulations! You are now my owner, {event['nick']}!")

    except Exception as e:
        bot.logger.error(f"Database error in _claim_ownership: {e}")
        bot.add_response("Error setting ownership.")


def _list_admins(bot, event):
    """List all admins"""
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()
        cur.execute("SELECT username FROM phreakbot_users WHERE is_admin = TRUE")
        admins = cur.fetchall()
        cur.close()

        if admins:
            admin_list = ", ".join([admin[0] for admin in admins])
            bot.add_response(f"Admins: {admin_list}")
        else:
            bot.add_response("There are no admins configured.")
    except Exception as e:
        bot.logger.error(f"Database error in _list_admins: {e}")
        bot.add_response("Error retrieving admin information.")


def _add_admin(bot, event, username):
    """Add a user as admin"""
    # Only owner can add admins
    if not bot._is_owner(event["hostmask"]):
        bot.add_response("Only the bot owner can add admins.")
        return

    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        # Check if user exists
        cur.execute(
            "SELECT id FROM phreakbot_users WHERE username = %s", (username.lower(),)
        )
        user = cur.fetchone()

        if not user:
            bot.add_response(f"User {username} not found.")
            cur.close()
            return

        # Set admin flag
        cur.execute(
            "UPDATE phreakbot_users SET is_admin = TRUE WHERE id = %s", (user[0],)
        )

        # Add admin permission if it doesn't exist
        cur.execute(
            "INSERT INTO phreakbot_perms (users_id, permission) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user[0], "admin"),
        )

        bot.db_connection.commit()
        cur.close()
        bot.add_response(f"{username} is now an admin.")
    except Exception as e:
        bot.logger.error(f"Database error in _add_admin: {e}")
        bot.add_response("Error adding admin.")


def _remove_admin(bot, event, username):
    """Remove admin privileges"""
    # Only owner can remove admins
    if not bot._is_owner(event["hostmask"]):
        bot.add_response("Only the bot owner can remove admins.")
        return

    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        # Check if user exists
        cur.execute(
            "SELECT id FROM phreakbot_users WHERE username = %s", (username.lower(),)
        )
        user = cur.fetchone()

        if not user:
            bot.add_response(f"User {username} not found.")
            cur.close()
            return

        # Remove admin flag
        cur.execute(
            "UPDATE phreakbot_users SET is_admin = FALSE WHERE id = %s", (user[0],)
        )

        # Remove admin permission
        cur.execute(
            "DELETE FROM phreakbot_perms WHERE users_id = %s AND permission = %s",
            (user[0], "admin"),
        )

        bot.db_connection.commit()
        cur.close()
        bot.add_response(f"{username} is no longer an admin.")
    except Exception as e:
        bot.logger.error(f"Database error in _remove_admin: {e}")
        bot.add_response("Error removing admin.")
