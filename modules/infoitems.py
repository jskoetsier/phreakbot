#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot - InfoItems module for pydle version
#
import re
from datetime import datetime


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "privmsg", "ctcp"],
        "commands": ["infoitem", "info", "forget"],
        "help": {
            "infoitem": "Manage info items. Usage: !infoitem add <item> <value> | !infoitem del <id> | !infoitem list [<item>]",
            "info": "Alias for infoitem",
            "forget": "Delete an info item by name and value. Usage: !forget <item> <value>",
        },
        "permissions": ["user"],
    }


def run(bot, event):
    """Handle infoitem commands"""
    if event["trigger"] != "command":
        return False

    # Handle forget command
    if event["command"] == "forget":
        if not event["command_args"]:
            bot.reply("Usage: !forget <item> <value>")
            return True

        args = event["command_args"].split()
        if len(args) < 2:
            bot.reply("Usage: !forget <item> <value>")
            return True

        item = args[0].lower()
        value = " ".join(args[1:])
        _forget_infoitem(bot, event, item, value)
        return True

    if event["command"] not in ["infoitem", "info"]:
        return False

    args = event["command_args"].split()
    if not args:
        bot.reply(
            "Usage: !infoitem add <item> <value> | !infoitem del <id> | !infoitem list [<item>]"
        )
        return True

    action = args[0].lower()

    if action == "add" and len(args) >= 3:
        item = args[1].lower()
        value = " ".join(args[2:])
        _add_infoitem(bot, event, item, value)
        return True
    elif action == "del" and len(args) == 2:
        try:
            item_id = int(args[1])
            _delete_infoitem(bot, event, item_id)
            return True
        except ValueError:
            bot.reply("Invalid item ID. Usage: !infoitem del <id>")
            return True
    elif action == "list":
        if len(args) >= 2:
            item = args[1].lower()
            _get_infoitem(bot, event, item)
        else:
            _list_infoitems(bot, event)
        return True
    else:
        bot.reply(
            "Usage: !infoitem add <item> <value> | !infoitem del <id> | !infoitem list [<item>]"
        )
        return True


def handle_custom_command(bot, event):
    """Handle custom infoitem commands like !item = value or !item?"""
    if event["trigger"] == "event" and event["text"].startswith(bot.config["trigger"]):
        # Check for karma patterns (!item++ or !item--) and skip them
        karma_pattern = re.compile(r"^\!([a-zA-Z0-9_-]+)(\+\+|\-\-)(?:\s+#(.+))?$")
        if karma_pattern.match(event["text"]):
            bot.logger.info(f"Skipping karma command: {event['text']}")
            return False

        # Check for !item? pattern
        get_pattern = re.compile(r"^\!([a-zA-Z0-9_-]+)\?$")
        get_match = get_pattern.match(event["text"])
        if get_match:
            item = get_match.group(1).lower()
            bot.logger.info(f"Custom infoitem get command: {item}")
            _get_infoitem(bot, event, item)
            return True

        # Check for !item = value pattern
        set_pattern = re.compile(r"^\!([a-zA-Z0-9_-]+)(?:\s*[=:+]\s*|\s+)(.+)$")
        set_match = set_pattern.match(event["text"])
        if set_match:
            item = set_match.group(1).lower()
            value = set_match.group(2).strip()

            # Skip if the item is a registered command
            registered_commands = []
            for module in bot.modules.values():
                registered_commands.extend(module.get("commands", []))

            if item not in registered_commands:
                bot.logger.info(f"Custom infoitem set command: {item} = {value}")
                _add_infoitem(bot, event, item, value)
                return True

    return False


def _add_infoitem(bot, event, item, value):
    """Add a new info item"""
    # Check if user is registered
    if not event["user_info"]:
        bot.reply("You need to be a registered user to add info items.")
        return

    if bot.db_connection:
        try:
            cur = bot.db_connection.cursor()
            cur.execute(
                "INSERT INTO phreakbot_infoitems (users_id, item, value, channel) VALUES (%s, %s, %s, %s) RETURNING id",
                (event["user_info"]["id"], item, value, event["channel"]),
            )
            item_id = cur.fetchone()[0]
            bot.db_connection.commit()
            bot.reply(f"Info item '{item}' added successfully with ID {item_id}.")
            bot.logger.info(f"Added info item '{item}' with ID {item_id}")
        except Exception as e:
            bot.logger.error(f"Error adding info item: {e}")
            bot.reply(f"Error adding info item: {e}")
            bot.db_connection.rollback()
        finally:
            cur.close()
    else:
        bot.reply("Database connection not available.")


def _delete_infoitem(bot, event, item_id):
    """Delete an info item by ID"""
    # Check if user is registered
    if not event["user_info"]:
        bot.reply("You need to be a registered user to delete info items.")
        return

    if bot.db_connection:
        try:
            cur = bot.db_connection.cursor()

            # First check if the item exists and belongs to the user or if user is admin
            cur.execute(
                "SELECT i.id, i.item, i.users_id FROM phreakbot_infoitems i WHERE i.id = %s",
                (item_id,),
            )
            item = cur.fetchone()

            if not item:
                bot.reply(f"Info item with ID {item_id} not found.")
                return

            # Check if user is owner or the item belongs to the user
            is_owner = False
            for perm in event["user_info"]["permissions"]["global"]:
                if perm == "owner":
                    is_owner = True
                    break

            if not is_owner and item[2] != event["user_info"]["id"]:
                bot.reply("You can only delete your own info items.")
                return

            # Delete the item
            cur.execute("DELETE FROM phreakbot_infoitems WHERE id = %s", (item_id,))
            bot.db_connection.commit()
            bot.reply(f"Info item '{item[1]}' with ID {item_id} deleted successfully.")
            bot.logger.info(f"Deleted info item '{item[1]}' with ID {item_id}")
        except Exception as e:
            bot.logger.error(f"Error deleting info item: {e}")
            bot.reply(f"Error deleting info item: {e}")
            bot.db_connection.rollback()
        finally:
            cur.close()
    else:
        bot.reply("Database connection not available.")


def _get_infoitem(bot, event, item):
    """Get all values for an info item"""
    if bot.db_connection:
        try:
            cur = bot.db_connection.cursor()
            cur.execute(
                "SELECT i.id, i.value, u.username, i.insert_time FROM phreakbot_infoitems i "
                "JOIN phreakbot_users u ON i.users_id = u.id "
                "WHERE i.item = %s AND i.channel = %s "
                "ORDER BY i.insert_time",
                (item, event["channel"]),
            )

            items = cur.fetchall()

            if not items:
                bot.reply(f"No info found for '{item}'.")
            else:
                bot.reply(f"Info for '{item}' ({len(items)} entries):")
                for item_id, value, username, timestamp in items:
                    bot.reply(
                        f"• [{item_id}] {value} (added by {username} on {timestamp.strftime('%Y-%m-%d')})"
                    )
        except Exception as e:
            bot.logger.error(f"Error retrieving info item: {e}")
            bot.reply(f"Error retrieving info item: {e}")
        finally:
            cur.close()
    else:
        bot.reply("Database connection not available.")


def _forget_infoitem(bot, event, item, value):
    """Delete an info item by name and value"""
    # Check if user is registered
    if not event["user_info"]:
        bot.reply("You need to be a registered user to delete info items.")
        return

    if bot.db_connection:
        try:
            cur = bot.db_connection.cursor()

            # First check if the item exists with the specified value
            cur.execute(
                "SELECT i.id, i.item, i.value, i.users_id FROM phreakbot_infoitems i WHERE i.item = %s AND i.value = %s AND i.channel = %s",
                (item, value, event["channel"]),
            )
            items = cur.fetchall()

            if not items:
                bot.reply(f"No info item '{item}' with value '{value}' found.")
                return

            # If there are multiple matches, we need to be more specific
            if len(items) > 1:
                bot.reply(
                    f"Multiple matches found for '{item}' with value '{value}'. Please use !infoitem del <id> with one of these IDs:"
                )
                for item_id, item_name, item_value, _ in items:
                    bot.reply(f"• [{item_id}] {item_value}")
                return

            # We have exactly one match
            item_id, item_name, item_value, user_id = items[0]

            # Check if user is owner or the item belongs to the user
            is_owner = False
            for perm in event["user_info"]["permissions"]["global"]:
                if perm == "owner":
                    is_owner = True
                    break

            if not is_owner and user_id != event["user_info"]["id"]:
                bot.reply("You can only delete your own info items.")
                return

            # Delete the item
            cur.execute("DELETE FROM phreakbot_infoitems WHERE id = %s", (item_id,))
            bot.db_connection.commit()
            bot.reply(f"Info item '{item}' with value '{value}' deleted successfully.")
            bot.logger.info(f"Deleted info item '{item}' with ID {item_id}")
        except Exception as e:
            bot.logger.error(f"Error deleting info item: {e}")
            bot.reply(f"Error deleting info item: {e}")
            bot.db_connection.rollback()
        finally:
            cur.close()
    else:
        bot.reply("Database connection not available.")


def _list_infoitems(bot, event):
    """List all info items in the current channel"""
    if bot.db_connection:
        try:
            cur = bot.db_connection.cursor()
            cur.execute(
                "SELECT DISTINCT item FROM phreakbot_infoitems WHERE channel = %s ORDER BY item",
                (event["channel"],),
            )

            items = cur.fetchall()

            if not items:
                bot.reply("No info items found in this channel.")
            else:
                bot.reply(f"Info items in this channel ({len(items)} items):")
                item_list = ", ".join([item[0] for item in items])
                bot.reply(f"• {item_list}")
        except Exception as e:
            bot.logger.error(f"Error listing info items: {e}")
            bot.reply(f"Error listing info items: {e}")
        finally:
            cur.close()
    else:
        bot.reply("Database connection not available.")
