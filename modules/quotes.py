#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Quotes module for PhreakBot

import random


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["quote", "q", "addquote", "aq", "delquote", "dq", "searchquote", "sq"],
        "permissions": ["user"],
        "help": "Quote management. Usage: !quote/!q [id] - Show a random quote or a specific quote by ID.\n"
                "       !addquote or !aq <text> - Add a new quote\n"
                "       !delquote or !dq <id> - Delete a quote (owner/admin only)\n"
                "       !searchquote or !sq <text> - Search for quotes containing text",
    }


def run(bot, event):
    """Handle quotes commands"""
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        if event["command"] in ["quote", "q"]:
            _show_quote(bot, event)
        elif event["command"] in ["addquote", "aq"]:
            _add_quote(bot, event)
        elif event["command"] in ["delquote", "dq"]:
            _delete_quote(bot, event)
        elif event["command"] in ["searchquote", "sq"]:
            _search_quotes(bot, event)
    except Exception as e:
        bot.logger.error(f"Error in quotes module: {e}")
        bot.add_response("Error processing quote command.")


def _show_quote(bot, event):
    """Show a quote from the database"""
    search_term = event["command_args"]

    cur = bot.db_connection.cursor()

    if not search_term:
        # Show a random quote
        cur.execute(
            "SELECT q.id, q.quote, u.username, q.channel, q.insert_time FROM phreakbot_quotes q "
            "JOIN phreakbot_users u ON q.users_id = u.id "
            "ORDER BY RANDOM() LIMIT 1"
        )
    elif search_term.isdigit():
        # Show a specific quote by ID
        cur.execute(
            "SELECT q.id, q.quote, u.username, q.channel, q.insert_time FROM phreakbot_quotes q "
            "JOIN phreakbot_users u ON q.users_id = u.id "
            "WHERE q.id = %s",
            (int(search_term),),
        )
    else:
        # Search for quotes containing the search term
        cur.execute(
            "SELECT q.id, q.quote, u.username, q.channel, q.insert_time FROM phreakbot_quotes q "
            "JOIN phreakbot_users u ON q.users_id = u.id "
            "WHERE q.quote ILIKE %s "
            "ORDER BY RANDOM() LIMIT 1",
            (f"%{search_term}%",),
        )

    quote = cur.fetchone()
    cur.close()

    if not quote:
        if search_term:
            bot.add_response(f"No quotes found matching '{search_term}'.")
        else:
            bot.add_response("No quotes found in the database.")
        return

    quote_id, quote_text, username, channel, timestamp = quote
    bot.add_response(
        f"Quote #{quote_id}: {quote_text} (added by {username} in {channel} on {timestamp.strftime('%Y-%m-%d')})"
    )


def _search_quotes(bot, event):
    """Search for quotes containing a specific string"""
    if not event["command_args"]:
        bot.add_response("Please provide a search term.")
        return
    
    bot.logger.info(f"Searching quotes for: {event['command_args']}")
    search_term = event["command_args"]

    cur = bot.db_connection.cursor()
    cur.execute(
        "SELECT q.id, q.quote, u.username, q.channel, q.insert_time FROM phreakbot_quotes q "
        "JOIN phreakbot_users u ON q.users_id = u.id "
        "WHERE q.quote ILIKE %s "
        "ORDER BY q.id LIMIT 5",
        (f"%{search_term}%",),
    )

    quotes = cur.fetchall()
    cur.close()

    if not quotes:
        bot.add_response(f"No quotes found matching '{search_term}'.")
        return

    bot.add_response(f"Found {len(quotes)} quotes matching '{search_term}':")
    for quote in quotes:
        quote_id, quote_text, username, channel, timestamp = quote
        bot.add_response(
            f"Quote #{quote_id}: {quote_text} (added by {username} in {channel} on {timestamp.strftime('%Y-%m-%d')})"
        )

def _add_quote(bot, event):
    """Add a new quote to the database"""
    quote_text = event["command_args"]
    
    if not quote_text:
        bot.add_response("Please provide a quote to add.")
        return

    # Get the user's ID
    user_info = event["user_info"]
    if not user_info:
        bot.add_response("You need to be a registered user to add quotes.")
        return

    cur = bot.db_connection.cursor()

    # Check if the quote already exists
    cur.execute(
        "SELECT id FROM phreakbot_quotes WHERE quote = %s AND channel = %s",
        (quote_text, event["channel"]),
    )

    if cur.fetchone():
        bot.add_response("This quote already exists in the database.")
        cur.close()
        return

    # Add the new quote
    cur.execute(
        "INSERT INTO phreakbot_quotes (users_id, quote, channel) VALUES (%s, %s, %s) RETURNING id",
        (user_info["id"], quote_text, event["channel"]),
    )

    quote_id = cur.fetchone()[0]
    bot.db_connection.commit()
    cur.close()

    bot.add_response(f"Quote #{quote_id} added successfully.")


def _delete_quote(bot, event):
    """Delete a quote from the database"""
    # Check if the user has permission to delete quotes
    if not bot._is_owner(event["source"]) and not (
        event["user_info"] and event["user_info"].get("is_admin")
    ):
        bot.add_response("Only the bot owner and admins can delete quotes.")
        return

    quote_id = event["command_args"]

    if not quote_id or not quote_id.isdigit():
        bot.add_response("Please provide a valid quote ID to delete.")
        return

    cur = bot.db_connection.cursor()

    # Check if the quote exists
    cur.execute("SELECT id FROM phreakbot_quotes WHERE id = %s", (int(quote_id),))

    if not cur.fetchone():
        bot.add_response(f"Quote #{quote_id} not found.")
        cur.close()
        return

    # Delete the quote
    cur.execute("DELETE FROM phreakbot_quotes WHERE id = %s", (int(quote_id),))
    bot.db_connection.commit()
    cur.close()

    bot.add_response(f"Quote #{quote_id} deleted successfully.")
