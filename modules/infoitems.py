#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# InfoItems module for PhreakBot

import re


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "privmsg"],  # Handle all messages to check for custom patterns
        "commands": ["infoitem", "info"],  # Standard commands
        "permissions": ["user"],
        "help": "InfoItems management. Usage:\n"
                "       !<item> = <value> - Add a new info item\n"
                "       !<item>? - Show all values for an info item\n"
                "       !infoitem add <item> <value> - Add a new info item\n"
                "       !infoitem list - List all available info items\n"
                "       !infoitem delete <item> <value> - Delete a specific info item value (owner/admin only)",
    }


def run(bot, event):
    """Handle infoitems commands and custom patterns"""
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        # First check for custom patterns in all messages
        if event["trigger"] == "event" and event["signal"] in ["pubmsg", "privmsg"]:
            message = event["text"]
            bot.logger.info(f"Checking message for infoitem patterns: '{message}'")

            # Check for set patterns with multiple syntaxes
            # Try !item = value
            set_match1 = re.match(r'^\!([a-zA-Z0-9_-]+)\s*=\s*(.+)$', message)
            # Try !item:value
            set_match2 = re.match(r'^\!([a-zA-Z0-9_-]+)\s*:\s*(.+)$', message)
            # Try !item+value
            set_match3 = re.match(r'^\!([a-zA-Z0-9_-]+)\s*\+\s*(.+)$', message)

            set_match = set_match1 or set_match2 or set_match3

            if set_match:
                bot.logger.info(f"Matched set pattern: {message}")
                item_name = set_match.group(1).lower()
                value = set_match.group(2).strip()

                # Skip if the item name is a known command
                if item_name not in ['infoitem', 'info', 'help', 'avail']:
                    bot.logger.info(f"Processing set command for item: {item_name}")
                    _add_infoitem(bot, event, item_name, value)
                    return

            # Also check for direct syntax !item value (without any separator)
            direct_match = re.match(r'^\!([a-zA-Z0-9_-]+)\s+(.+)$', message)
            if direct_match:
                bot.logger.info(f"Matched direct pattern: {message}")
                item_name = direct_match.group(1).lower()
                value = direct_match.group(2).strip()

                # Skip if the item name is a known command or a registered command
                if (item_name not in ['infoitem', 'info', 'help', 'avail'] and
                    item_name not in [cmd for mod in bot.modules.values() for cmd in mod.get('commands', [])]):
                    bot.logger.info(f"Processing direct command for item: {item_name}")
                    _add_infoitem(bot, event, item_name, value)
                    return

            # Check for get pattern (!item?)
            get_match = re.match(r'^\!([a-zA-Z0-9_-]+)\?$', message)
            if get_match:
                bot.logger.info(f"Matched get pattern: {message}")
                item_name = get_match.group(1).lower()

                # Skip if the item name is a known command
                if item_name not in ['infoitem', 'info', 'help', 'avail']:
                    bot.logger.info(f"Processing get command for item: {item_name}")
                    _get_infoitem(bot, event, item_name)
                    return

        # Handle standard commands
        if event["trigger"] == "command":
            # Handle infoitem/info commands
            if event["command"] in ["infoitem", "info"]:
                if not event["command_args"]:
                    bot.add_response("Please specify a subcommand. Try !help infoitem for usage information.")
                    return

                args = event["command_args"].split()
                subcommand = args[0].lower()

                if subcommand == "list":
                    _list_infoitems(bot, event)
                elif subcommand == "add" and len(args) >= 3:
                    item_name = args[1]
                    value = " ".join(args[2:])
                    _add_infoitem(bot, event, item_name, value)
                elif subcommand == "delete" and len(args) >= 3:
                    item_name = args[1]
                    value = " ".join(args[2:])
                    _delete_infoitem(bot, event, item_name, value)
                else:
                    bot.add_response("Unknown subcommand. Try !help infoitem for usage information.")

            # Handle commands that might be infoitem commands with special syntax
            else:
                # Check if the command is not a registered command in any module
                registered_commands = [cmd for mod in bot.modules.values() for cmd in mod.get('commands', [])]
                if event["command"] not in registered_commands:
                    bot.logger.info(f"Checking unregistered command: {event['command']} with args: {event['command_args']}")

                    # Check if args start with special characters
                    args = event["command_args"]
                    if args and args.startswith(('=', ':', '+')):
                        bot.logger.info(f"Detected special character at start of args: {args}")

                        # Extract the value (skip the special character and any whitespace)
                        value = args[1:].strip()
                        if value:
                            bot.logger.info(f"Processing as infoitem: {event['command']} with value: {value}")
                            _add_infoitem(bot, event, event["command"], value)
                            return

                    # Also check for direct syntax where args don't start with special chars
                    elif args and not args.startswith(('=', ':', '+')):
                        # Check if this command is not handled by any other module
                        bot.logger.info(f"Processing as direct infoitem: {event['command']} with value: {args}")
                        _add_infoitem(bot, event, event["command"], args)
                        return
    except Exception as e:
        bot.logger.error(f"Error in infoitems module: {e}")
        bot.add_response("Error processing infoitem command.")


def handle_custom_command(bot, event):
    """Handle custom infoitem commands (!item = value and !item?)"""
    if not bot.db_connection:
        bot.logger.info("Infoitems: Database connection not available")
        return False

    message = event["text"]

    # Log the message and event details for debugging
    bot.logger.info(f"Infoitems module checking message: '{message}'")
    bot.logger.info(f"Event trigger: {event['trigger']}")
    bot.logger.info(f"Event type: {event.get('signal', 'unknown')}")

    # Check if this is an infoitem set command (!item = value)
    set_match = re.match(r'^\!([a-zA-Z0-9_-]+)\s*=\s*(.+)$', message)
    if set_match:
        bot.logger.info(f"Matched infoitem set command: {message}")
        item_name = set_match.group(1).lower()
        value = set_match.group(2).strip()

        # Skip if the item name is a known command
        if item_name in ['infoitem', 'help', 'avail']:
            bot.logger.info(f"Skipping reserved command name: {item_name}")
            return False

        return _add_infoitem(bot, event, item_name, value)

    # Check if this is an infoitem get command (!item?)
    get_match = re.match(r'^\!([a-zA-Z0-9_-]+)\?$', message)
    if get_match:
        bot.logger.info(f"Matched infoitem get command: {message}")
        item_name = get_match.group(1).lower()

        # Skip if the item name is a known command
        if item_name in ['infoitem', 'help', 'avail']:
            bot.logger.info(f"Skipping reserved command name: {item_name}")
            return False

        return _get_infoitem(bot, event, item_name)

    bot.logger.info("No match for infoitem command patterns")
    return False


def _add_infoitem(bot, event, item_name, value):
    """Add a new info item to the database"""
    # Get the user's ID
    user_info = event["user_info"]
    if not user_info:
        bot.add_response("You need to be a registered user to add info items.")
        return True

    cur = bot.db_connection.cursor()

    try:
        # Add the new info item with ON CONFLICT DO NOTHING to handle duplicates gracefully
        cur.execute(
            """
            INSERT INTO phreakbot_infoitems (users_id, item, value, channel)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (item, value, channel) DO NOTHING
            RETURNING id
            """,
            (user_info["id"], item_name, value, event["channel"])
        )

        result = cur.fetchone()
        bot.db_connection.commit()

        if result:
            bot.add_response(f"Info item '{item_name}' added successfully.")
        else:
            bot.add_response(f"This info item already exists.")

    except Exception as e:
        bot.logger.error(f"Error adding info item: {str(e).replace('\r', '').replace('\n', ' ')}")
        bot.add_response("Error adding info item. Please try again.")
        bot.db_connection.rollback()
    finally:
        cur.close()

    return True


def _get_infoitem(bot, event, item_name):
    """Get all values for an info item"""
    cur = bot.db_connection.cursor()

    try:
        # Get all values for this item in the current channel
        cur.execute(
            "SELECT i.value, u.username, i.insert_time FROM phreakbot_infoitems i "
            "JOIN phreakbot_users u ON i.users_id = u.id "
            "WHERE i.item = %s AND i.channel = %s "
            "ORDER BY i.insert_time",
            (item_name, event["channel"])
        )

        items = cur.fetchall()

        if not items:
            bot.add_response(f"No info found for '{item_name}'.")
            return True

        bot.add_response(f"Info for '{item_name}':")
        for value, username, timestamp in items:
            bot.add_response(f"• {value} (added by {username} on {timestamp.strftime('%Y-%m-%d')})")

    except Exception as e:
        bot.logger.error(f"Error retrieving info item: {e}")
        bot.add_response("Error retrieving info item.")
    finally:
        cur.close()

    return True


def _list_infoitems(bot, event):
    """List all available info items in the current channel"""
    cur = bot.db_connection.cursor()

    try:
        # Get distinct item names and count of values
        cur.execute(
            "SELECT item, COUNT(*) as count FROM phreakbot_infoitems "
            "WHERE channel = %s "
            "GROUP BY item "
            "ORDER BY item",
            (event["channel"],)
        )

        items = cur.fetchall()

        if not items:
            bot.add_response("No info items found in this channel.")
            return

        bot.add_response("Available info items in this channel:")
        for item, count in items:
            bot.add_response(f"• !{item}? - {count} value(s)")

    except Exception as e:
        bot.logger.error(f"Error listing info items: {e}")
        bot.add_response("Error listing info items.")
    finally:
        cur.close()


def _delete_infoitem(bot, event, item_name, value):
    """Delete a specific info item value"""
    # Check if the user has permission to delete info items
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"] and event["user_info"].get("is_admin")
    ):
        bot.add_response("Only the bot owner and admins can delete info items.")
        return

    cur = bot.db_connection.cursor()

    try:
        # Check if the item exists
        cur.execute(
            "SELECT id FROM phreakbot_infoitems WHERE item = %s AND value = %s AND channel = %s",
            (item_name, value, event["channel"])
        )

        if not cur.fetchone():
            bot.add_response(f"Info item '{item_name}' with that value not found.")
            cur.close()
            return

        # Delete the info item
        cur.execute(
            "DELETE FROM phreakbot_infoitems WHERE item = %s AND value = %s AND channel = %s",
            (item_name, value, event["channel"])
        )

        bot.db_connection.commit()
        bot.add_response(f"Info item '{item_name}' with value '{value}' deleted successfully.")

    except Exception as e:
        bot.logger.error(f"Error deleting info item: {e}")
        bot.add_response("Error deleting info item.")
        bot.db_connection.rollback()
    finally:
        cur.close()
