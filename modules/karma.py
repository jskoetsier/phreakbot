#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Karma module for PhreakBot - Handles all karma functionality

import re


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "privmsg"],  # Listen to all message events
        "commands": ["karma", "topkarma"],
        "permissions": ["user"],
        "help": "Karma tracking system. Usage:\n"
        "!example++ - Increase karma for 'example'\n"
        "!example-- - Decrease karma for 'example'\n"
        "!example++ #reason - Increase karma with a reason\n"
        "!example-- #reason - Decrease karma with a reason\n"
        "!karma <item> - Show karma for a specific item\n"
        "!topkarma - Show items with highest and lowest karma",
    }


def run(bot, event):
    """Handle karma commands and events"""
    bot.logger.info(f"Karma module run called with event: {event}")

    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return False

    try:
        # Handle explicit commands
        if event["trigger"] == "command":
            bot.logger.info(f"Karma module processing command: {event['command']}")
            if event["command"] == "karma":
                _show_karma(bot, event)
                return True
            elif event["command"] == "topkarma":
                _show_top_karma(bot, event)
                return True
            
            # Special handling for commands that end with -- or ++
            if event["command"].endswith("--") or event["command"].endswith("++"):
                bot.logger.info(f"Karma module handling command with karma pattern: {event['command']}")
                item = event["command"][:-2]  # Remove -- or ++
                direction = "down" if event["command"].endswith("--") else "up"
                reason = event["command_args"].strip() if event["command_args"] else None
                
                # If reason starts with #, remove it
                if reason and reason.startswith("#"):
                    reason = reason[1:].strip()
                
                _update_karma(bot, event, item, direction, reason)
                return True
                
            return False

        # Only process event triggers with text
        if "text" not in event or not event["text"]:
            return False

        # Check for karma pattern (++ or --)
        karma_pattern = r"^\!([a-zA-Z0-9_-]+)(\+\+|\-\-)(?:\s+#(.+))?$"
        match = re.match(karma_pattern, event["text"])

        if match:
            bot.logger.info(f"Matched karma pattern: {match.groups()}")
            item = match.group(1).lower()
            direction = "up" if match.group(2) == "++" else "down"
            reason = match.group(3)

            _update_karma(bot, event, item, direction, reason)
            return True  # Signal that we've handled this event

        # Direct check for !item-- pattern
        if event["text"].startswith("!") and event["text"].endswith("--"):
            bot.logger.info(f"Direct karma minus pattern detected: {event['text']}")
            item = event["text"][1:-2]  # Remove ! and --
            
            # Check if there's a reason (format: !item-- #reason)
            parts = event["text"].split("#", 1)
            reason = parts[1].strip() if len(parts) > 1 else None
            
            _update_karma(bot, event, item, "down", reason)
            return True

        return False  # We didn't handle this event

    except Exception as e:
        bot.logger.error(f"Error in karma module: {e}")
        import traceback
        bot.logger.error(f"Traceback: {traceback.format_exc()}")
        bot.add_response("Error processing karma command.")
        return False


def _process_karma_up(bot, event):
    """Process karma up command"""
    if not event["command_args"]:
        bot.add_response(
            "Please specify an item to give karma to. Usage: !kup <item> [#reason]"
        )
        return

    # Split the command args to get the item and optional reason
    args = event["command_args"].split("#", 1)
    item = args[0].strip().lower()
    reason = args[1].strip() if len(args) > 1 else None

    _update_karma(bot, event, item, "up", reason)


def _process_karma_down(bot, event):
    """Process karma down command"""
    if not event["command_args"]:
        bot.add_response(
            "Please specify an item to give karma to. Usage: !kdown <item> [#reason]"
        )
        return

    # Split the command args to get the item and optional reason
    args = event["command_args"].split("#", 1)
    item = args[0].strip().lower()
    reason = args[1].strip() if len(args) > 1 else None

    _update_karma(bot, event, item, "down", reason)


def _process_karma_event(bot, event):
    """Process messages for karma events (++ and --)"""
    text = event["text"]
    bot.logger.info(f"Processing karma event: {text}")

    # Pattern for !item++ or !item-- with optional #reason
    karma_pattern = (
        r"^"
        + re.escape(bot.config["trigger"])
        + r"([a-zA-Z0-9_-]+)(\+\+|\-\-)(?:\s+#(.+))?$"
    )

    bot.logger.info(f"Karma pattern: {karma_pattern}")
    match = re.match(karma_pattern, text)
    bot.logger.info(f"Karma match: {bool(match)}")

    if not match:
        bot.logger.info(f"No match for karma pattern in text: {text}")
        return

    bot.logger.info(f"Matched karma pattern: {match.groups()}")

    item = match.group(1).lower()
    direction = "up" if match.group(2) == "++" else "down"
    reason = match.group(3)

    _update_karma(bot, event, item, direction, reason)


def _update_karma(bot, event, item, direction, reason=None):
    """Update karma for an item"""
    bot.logger.info(
        f"Updating karma for {item} in direction {direction} with reason {reason}"
    )

    # Get the user's ID
    user_info = event["user_info"]
    if not user_info:
        bot.add_response("You need to be a registered user to give karma.")
        return

    # Don't allow users to give karma to themselves
    if item.lower() == event["nick"].lower():
        bot.add_response("You can't give karma to yourself!")
        return

    # Update or insert karma
    cur = bot.db_connection.cursor()

    # First, check if the item exists
    cur.execute(
        "SELECT id, karma FROM phreakbot_karma WHERE item = %s AND channel = %s",
        (item, event["channel"]),
    )

    karma_row = cur.fetchone()

    if karma_row:
        # Item exists, update karma
        karma_id, current_karma = karma_row
        new_karma = current_karma + (1 if direction == "up" else -1)

        cur.execute(
            "UPDATE phreakbot_karma SET karma = %s WHERE id = %s", (new_karma, karma_id)
        )
    else:
        # Item doesn't exist, insert new record
        initial_karma = 1 if direction == "up" else -1
        cur.execute(
            "INSERT INTO phreakbot_karma (item, karma, channel) VALUES (%s, %s, %s) RETURNING id",
            (item, initial_karma, event["channel"]),
        )
        karma_id = cur.fetchone()[0]
        new_karma = initial_karma

    # Record who gave the karma
    cur.execute(
        """
        INSERT INTO phreakbot_karma_who (karma_id, users_id, direction, amount)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (karma_id, users_id, direction)
        DO UPDATE SET amount = phreakbot_karma_who.amount + 1, update_time = CURRENT_TIMESTAMP
        """,
        (karma_id, user_info["id"], direction, 1),
    )

    # If a reason was provided, record it
    if reason:
        cur.execute(
            """
            INSERT INTO phreakbot_karma_why (karma_id, direction, reason, channel)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (karma_id, direction, reason, channel) DO NOTHING
            """,
            (karma_id, direction, reason, event["channel"]),
        )

    bot.db_connection.commit()
    cur.close()

    # Respond with the new karma value
    bot.add_response(f"{item} now has {new_karma} karma")


def _show_karma(bot, event):
    """Show karma for a specific item"""
    item = event["command_args"]

    if not item:
        bot.add_response("Please specify an item to check karma for.")
        return

    item = item.lower()
    cur = bot.db_connection.cursor()

    # Get karma for the item
    cur.execute(
        "SELECT id, karma FROM phreakbot_karma WHERE item = %s AND channel = %s",
        (item, event["channel"]),
    )

    karma_row = cur.fetchone()

    if not karma_row:
        bot.add_response(f"{item} has no karma yet.")
        cur.close()
        return

    karma_id, karma_value = karma_row

    # Get reasons for karma
    cur.execute(
        "SELECT direction, reason FROM phreakbot_karma_why WHERE karma_id = %s ORDER BY id DESC LIMIT 5",
        (karma_id,),
    )

    reasons = cur.fetchall()
    cur.close()

    # Display karma and reasons on a single line
    response = f"{item} has {karma_value} karma"

    if reasons:
        reason_texts = []
        for direction, reason in reasons:
            direction_symbol = "+" if direction == "up" else "-"
            reason_texts.append(f"{direction_symbol} {reason}")

        if reason_texts:
            response += f" (Recent reasons: {', '.join(reason_texts)})"

    bot.add_response(response)


def _show_top_karma(bot, event):
    """Show items with highest and lowest karma"""
    cur = bot.db_connection.cursor()

    # Get top 5 positive karma
    cur.execute(
        "SELECT item, karma FROM phreakbot_karma WHERE channel = %s AND karma > 0 ORDER BY karma DESC LIMIT 5",
        (event["channel"],),
    )

    top_positive = cur.fetchall()

    # Get top 5 negative karma
    cur.execute(
        "SELECT item, karma FROM phreakbot_karma WHERE channel = %s AND karma < 0 ORDER BY karma ASC LIMIT 5",
        (event["channel"],),
    )

    top_negative = cur.fetchall()

    cur.close()

    # Format results in a single line for each category
    positive_items = []
    negative_items = []
    
    if top_positive:
        for item, karma in top_positive:
            positive_items.append(f"{item}: {karma}")
    
    if top_negative:
        for item, karma in top_negative:
            negative_items.append(f"{item}: {karma}")
    
    # Display results in a single line for each category
    if positive_items:
        bot.add_response(f"Top positive karma: {', '.join(positive_items)}")
    else:
        bot.add_response("No items with positive karma found.")
        
    if negative_items:
        bot.add_response(f"Top negative karma: {', '.join(negative_items)}")
    else:
        bot.add_response("No items with negative karma found.")
