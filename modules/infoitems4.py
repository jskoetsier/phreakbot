#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# InfoItems4 module for PhreakBot - Based on weechatbot implementation

import re


def config(bot):
    """Return module configuration"""
    return {
        'events': ['pubmsg', 'privmsg'],  # Listen for all messages
        'commands': ['infoitem', 'info'],  # Standard commands
        'permissions': ['user'],
        'help': "InfoItems system. Usage:\n"
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

    # Process 'non command' triggers here
    txt = event['text']
    bot.logger.info(f"InfoItems4 processing message: '{txt}'")

    # See if it is an attempt to define a thing?
    define_re = re.compile(r'^\!(.+?) = (.*)$')
    define_match = define_re.match(txt)
    if define_match:
        bot.logger.info(f"InfoItems4 matched define pattern: {txt}")
        item_name = define_match.group(1).lower()
        value = define_match.group(2).strip()

        # Skip if the item name is a known command
        registered_commands = []
        for module in bot.modules.values():
            registered_commands.extend(module.get('commands', []))

        if item_name not in registered_commands:
            bot.logger.info(f"InfoItems4 processing define command: {item_name} = {value}")
            _add_infoitem(bot, event, item_name, value)
            return True

    # See if it is an attempt to get the definition of a thing?
    query_re = re.compile(r'^\!(.+?)\?\s*$')
    query_match = query_re.match(txt)
    if query_match:
        bot.logger.info(f"InfoItems4 matched query pattern: {txt}")
        item_name = query_match.group(1).lower()

        # Skip if the item name is a known command
        registered_commands = []
        for module in bot.modules.values():
            registered_commands.extend(module.get('commands', []))

        if item_name not in registered_commands:
            bot.logger.info(f"InfoItems4 processing query command: {item_name}?")
            _get_infoitem(bot, event, item_name)
            return True

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

    return False


def _add_infoitem(bot, event, item_name, value):
    """Add a new info item to the database"""
    # Get the user's ID
    user_info = event["user_info"]
    if not user_info:
        bot.add_response("You need to be a registered user to add info items.")
        return

    cur = bot.db_connection.cursor()

    try:
        # Check if this exact item/value combination already exists
        cur.execute(
            "SELECT id FROM phreakbot_infoitems WHERE item = %s AND value = %s AND channel = %s",
            (item_name, value, event["channel"])
        )

        if cur.fetchone():
            bot.add_response(f"This info item already exists.")
            cur.close()
            return

        # Add the new info item
        cur.execute(
            "INSERT INTO phreakbot_infoitems (users_id, item, value, channel) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_info["id"], item_name, value, event["channel"])
        )

        item_id = cur.fetchone()[0]
        bot.db_connection.commit()
        bot.add_response(f"Info item '{item_name}' added successfully.")

    except Exception as e:
        bot.logger.error(f"Error adding info item: {e}")
        bot.add_response("Error adding info item.")
        bot.db_connection.rollback()
    finally:
        cur.close()


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
            return

        bot.add_response(f"Info for '{item_name}':")
        for value, username, timestamp in items:
            bot.add_response(f"• {value} (added by {username} on {timestamp.strftime('%Y-%m-%d')})")

    except Exception as e:
        bot.logger.error(f"Error retrieving info item: {e}")
        bot.add_response("Error retrieving info item.")
    finally:
        cur.close()


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
