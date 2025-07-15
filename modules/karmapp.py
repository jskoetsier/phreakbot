#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# KarmaPP module for PhreakBot - Handles !item++ and !item-- syntax
# This module is specifically designed to handle karma patterns before infoitems

import re


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "privmsg"],  # Listen to all message events
        "commands": [],  # No explicit commands, only event handling
        "permissions": ["user"],
        "help": "Karma tracking with ++ and -- syntax. Usage:\n"
        "!example++ - Increase karma for 'example'\n"
        "!example-- - Decrease karma for 'example'\n"
        "!example++ #reason - Increase karma with a reason\n"
        "!example-- #reason - Decrease karma with a reason",
    }


def run(bot, event):
    """Handle karma events (++ and --)"""
    # Only process event triggers with text
    if "text" not in event or not event["text"]:
        return False

    # Log every message for debugging
    bot.logger.info(f"KarmaPP checking message: {event['text']}")

    # Check for karma pattern
    karma_pattern = r"^\!([a-zA-Z0-9_-]+)(\+\+|\-\-)(?:\s+#(.+))?$"
    match = re.match(karma_pattern, event["text"])

    if not match:
        bot.logger.info(f"KarmaPP: No match for karma pattern")
        return False

    bot.logger.info(f"KarmaPP: Matched karma pattern: {match.groups()}")

    item = match.group(1).lower()
    direction = "up" if match.group(2) == "++" else "down"
    reason = match.group(3)

    # Process the karma
    _update_karma(bot, event, item, direction, reason)
    return True  # Signal that we've handled this event


def _update_karma(bot, event, item, direction, reason=None):
    """Update karma for an item"""
    bot.logger.info(
        f"KarmaPP: Updating karma for {item} in direction {direction} with reason {reason}"
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
