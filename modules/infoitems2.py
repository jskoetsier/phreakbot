#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# InfoItems2 module for PhreakBot - Simplified version

import re


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "privmsg"],  # Listen for all messages
        "commands": [],  # No standard commands, only custom patterns
        "permissions": ["user"],
        "help": "InfoItems system. Usage:\n"
                "       !<item> = <value> - Add a new info item\n"
                "       !<item>? - Show all values for an info item",
    }


def run(bot, event):
    """Handle infoitems patterns directly"""
    if not bot.db_connection:
        return

    # Only process event triggers
    if event["trigger"] != "event":
        return

    # Get the message text
    message = event["text"]
    
    # Always log the message for debugging
    bot.logger.info(f"InfoItems2 received message: '{message}'")
    
    # Check for set pattern (!item = value)
    set_match = re.match(r'^\!([a-zA-Z0-9_-]+)\s*=\s*(.+)$', message)
    if set_match:
        bot.logger.info(f"InfoItems2 matched set pattern: {message}")
        item_name = set_match.group(1).lower()
        value = set_match.group(2).strip()
        
        # Skip if the item name is a known command
        registered_commands = []
        for module in bot.modules.values():
            registered_commands.extend(module.get('commands', []))
        
        if item_name not in registered_commands:
            bot.logger.info(f"InfoItems2 processing set command: {item_name} = {value}")
            # Add a debug response
            bot.add_response(f"DEBUG: InfoItems2 processing set command: {item_name} = {value}")
            _add_infoitem(bot, event, item_name, value)
            return True
    
    # Check for get pattern (!item?)
    get_match = re.match(r'^\!([a-zA-Z0-9_-]+)\?$', message)
    if get_match:
        bot.logger.info(f"InfoItems2 matched get pattern: {message}")
        item_name = get_match.group(1).lower()
        
        # Skip if the item name is a known command
        registered_commands = []
        for module in bot.modules.values():
            registered_commands.extend(module.get('commands', []))
        
        if item_name not in registered_commands:
            bot.logger.info(f"InfoItems2 processing get command: {item_name}?")
            # Add a debug response
            bot.add_response(f"DEBUG: InfoItems2 processing get command: {item_name}?")
            _get_infoitem(bot, event, item_name)
            return True
    
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