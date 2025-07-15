#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# TestMinus module for PhreakBot - Handles !test-- command specifically


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "privmsg"],  # Listen to all message events
        "commands": [
            "test--",
            "phreak--",
            "google--",
            "glob--",
            "cheers--",
            "karma--",
            "any--",
        ],  # Register specific karma-- commands
        "permissions": ["user"],
        "help": "Special handler for karma-- commands",
    }


def run(bot, event):
    """Handle karma-- commands"""
    bot.logger.info("TestMinus module called")

    # Process karma-- commands
    if event["trigger"] == "command" and event["command"].endswith("--"):
        # Extract the item name from the command
        item = event["command"].replace("--", "")
        bot.logger.info(f"TestMinus processing {item}-- command")

        # Don't allow users to give karma to themselves
        if item.lower() == event["nick"].lower():
            bot.add_response("You can't give karma to yourself!")
            return

        # Update karma in the database
        if bot.db_connection:
            try:
                bot.logger.info(f"Directly updating karma in database for {item}--")
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
                    new_karma = current_karma - 1

                    cur.execute(
                        "UPDATE phreakbot_karma SET karma = %s WHERE id = %s",
                        (new_karma, karma_id),
                    )

                    # Record who gave the karma
                    if event["user_info"]:
                        cur.execute(
                            """
                            INSERT INTO phreakbot_karma_who (karma_id, users_id, direction, amount)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (karma_id, users_id, direction)
                            DO UPDATE SET amount = phreakbot_karma_who.amount + 1, update_time = CURRENT_TIMESTAMP
                            """,
                            (karma_id, event["user_info"]["id"], "down", 1),
                        )

                    bot.db_connection.commit()
                    bot.add_response(f"{item} now has {new_karma} karma")
                else:
                    # Item doesn't exist, insert new record
                    cur.execute(
                        "INSERT INTO phreakbot_karma (item, karma, channel) VALUES (%s, %s, %s) RETURNING id",
                        (item, -1, event["channel"]),
                    )
                    karma_id = cur.fetchone()[0]

                    # Record who gave the karma
                    if event["user_info"]:
                        cur.execute(
                            """
                            INSERT INTO phreakbot_karma_who (karma_id, users_id, direction, amount)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (karma_id, event["user_info"]["id"], "down", 1),
                        )

                    bot.db_connection.commit()
                    bot.add_response(f"{item} now has -1 karma")
            except Exception as e:
                import traceback

                bot.logger.error(f"Error in TestMinus module: {e}")
                bot.logger.error(f"Traceback: {traceback.format_exc()}")
                bot.add_response(f"Error updating karma: {e}")
