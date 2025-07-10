#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Factoids module for PhreakBot
#
# This module implements the factoid system that allows users to store and retrieve
# information using the syntax !factoid = value and !factoid?

import re


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "privmsg"],  # Listen for all messages
        "commands": ["factoid"],  # Standard command for management
        "permissions": ["user"],
        "help": "Factoid system. Usage:\n"
                "       !<factoid> = <value> - Add a new factoid\n"
                "       !<factoid>? - Show all values for a factoid\n"
                "       !factoid list - List all available factoids\n"
                "       !factoid delete <factoid> <value> - Delete a specific factoid value (owner/admin only)",
    }


def run(bot, event):
    """Handle factoid commands and events"""
    # Log every call to the run method
    bot.logger.info(f"Factoids module run() called with trigger: {event['trigger']}, signal: {event.get('signal', 'N/A')}")
    bot.logger.info(f"Event text: '{event.get('text', 'N/A')}'")

    try:
        # Handle event-based factoid commands
        if event["trigger"] == "event" and event["signal"] in ["pubmsg", "privmsg"]:
            message = event["text"]
            bot.logger.info(f"Factoids module checking message: '{message}'")

            # Always add a response to see if the module is being called
            bot.add_response(f"DEBUG: Factoids module received message: {message}")

            # Check for factoid set command (!factoid = value)
            set_match = re.match(r'^\!([a-zA-Z0-9_-]+)\s*=\s*(.+)$', message)
            if set_match:
                bot.logger.info(f"Matched factoid set command: {message}")
                factoid_name = set_match.group(1).lower()
                value = set_match.group(2).strip()

                # Skip if the factoid name is a known command
                registered_commands = []
                for module in bot.modules.values():
                    registered_commands.extend(module.get('commands', []))

                if factoid_name not in registered_commands:
                    bot.logger.info(f"Processing factoid set command: {factoid_name} = {value}")
                    _add_factoid(bot, event, factoid_name, value)
                    return

            # Check for factoid get command (!factoid?)
            get_match = re.match(r'^\!([a-zA-Z0-9_-]+)\?$', message)
            if get_match:
                bot.logger.info(f"Matched factoid get command: {message}")
                factoid_name = get_match.group(1).lower()

                # Skip if the factoid name is a known command
                registered_commands = []
                for module in bot.modules.values():
                    registered_commands.extend(module.get('commands', []))

                if factoid_name not in registered_commands:
                    bot.logger.info(f"Processing factoid get command: {factoid_name}?")
                    _get_factoid(bot, event, factoid_name)
                    return

        # Handle standard factoid management commands
        if event["trigger"] == "command" and event["command"] == "factoid":
            if not event["command_args"]:
                bot.add_response("Please specify a subcommand. Try !help factoid for usage information.")
                return

            args = event["command_args"].split()
            subcommand = args[0].lower()

            if subcommand == "list":
                _list_factoids(bot, event)
            elif subcommand == "delete" and len(args) >= 3:
                factoid_name = args[1]
                value = " ".join(args[2:])
                _delete_factoid(bot, event, factoid_name, value)
            else:
                bot.add_response("Unknown subcommand. Try !help factoid for usage information.")

    except Exception as e:
        bot.logger.error(f"Error in factoids module: {e}")
        import traceback
        bot.logger.error(f"Traceback: {traceback.format_exc()}")
        bot.add_response("Error processing factoid command.")


def _add_factoid(bot, event, factoid_name, value):
    """Add a new factoid to the database"""
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    # Get the user's ID
    user_info = event["user_info"]
    if not user_info:
        bot.add_response("You need to be a registered user to add factoids.")
        return

    cur = bot.db_connection.cursor()

    try:
        # Check if this exact factoid/value combination already exists
        cur.execute(
            "SELECT id FROM phreakbot_infoitems WHERE item = %s AND value = %s AND channel = %s",
            (factoid_name, value, event["channel"])
        )

        if cur.fetchone():
            bot.add_response(f"This factoid already exists.")
            cur.close()
            return

        # Add the new factoid
        cur.execute(
            "INSERT INTO phreakbot_infoitems (users_id, item, value, channel) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_info["id"], factoid_name, value, event["channel"])
        )

        item_id = cur.fetchone()[0]
        bot.db_connection.commit()
        bot.add_response(f"Factoid '{factoid_name}' added successfully.")

    except Exception as e:
        bot.logger.error(f"Error adding factoid: {e}")
        bot.add_response("Error adding factoid.")
        bot.db_connection.rollback()
    finally:
        cur.close()


def _get_factoid(bot, event, factoid_name):
    """Get all values for a factoid"""
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    cur = bot.db_connection.cursor()

    try:
        # Get all values for this factoid in the current channel
        cur.execute(
            "SELECT i.value, u.username, i.insert_time FROM phreakbot_infoitems i "
            "JOIN phreakbot_users u ON i.users_id = u.id "
            "WHERE i.item = %s AND i.channel = %s "
            "ORDER BY i.insert_time",
            (factoid_name, event["channel"])
        )

        items = cur.fetchall()

        if not items:
            bot.add_response(f"No factoid found for '{factoid_name}'.")
            return

        bot.add_response(f"Factoid '{factoid_name}':")
        for value, username, timestamp in items:
            bot.add_response(f"• {value} (added by {username} on {timestamp.strftime('%Y-%m-%d')})")

    except Exception as e:
        bot.logger.error(f"Error retrieving factoid: {e}")
        bot.add_response("Error retrieving factoid.")
    finally:
        cur.close()


def _list_factoids(bot, event):
    """List all available factoids in the current channel"""
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    cur = bot.db_connection.cursor()

    try:
        # Get distinct factoid names and count of values
        cur.execute(
            "SELECT item, COUNT(*) as count FROM phreakbot_infoitems "
            "WHERE channel = %s "
            "GROUP BY item "
            "ORDER BY item",
            (event["channel"],)
        )

        items = cur.fetchall()

        if not items:
            bot.add_response("No factoids found in this channel.")
            return

        bot.add_response("Available factoids in this channel:")
        for item, count in items:
            bot.add_response(f"• !{item}? - {count} value(s)")

    except Exception as e:
        bot.logger.error(f"Error listing factoids: {e}")
        bot.add_response("Error listing factoids.")
    finally:
        cur.close()


def _delete_factoid(bot, event, factoid_name, value):
    """Delete a specific factoid value"""
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    # Check if the user has permission to delete factoids
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"] and event["user_info"].get("is_admin")
    ):
        bot.add_response("Only the bot owner and admins can delete factoids.")
        return

    cur = bot.db_connection.cursor()

    try:
        # Check if the factoid exists
        cur.execute(
            "SELECT id FROM phreakbot_infoitems WHERE item = %s AND value = %s AND channel = %s",
            (factoid_name, value, event["channel"])
        )

        if not cur.fetchone():
            bot.add_response(f"Factoid '{factoid_name}' with that value not found.")
            cur.close()
            return

        # Delete the factoid
        cur.execute(
            "DELETE FROM phreakbot_infoitems WHERE item = %s AND value = %s AND channel = %s",
            (factoid_name, value, event["channel"])
        )

        bot.db_connection.commit()
        bot.add_response(f"Factoid '{factoid_name}' with value '{value}' deleted successfully.")

    except Exception as e:
        bot.logger.error(f"Error deleting factoid: {e}")
        bot.add_response("Error deleting factoid.")
        bot.db_connection.rollback()
    finally:
        cur.close()
