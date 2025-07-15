#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Karma module for PhreakBot
"""

import re

import psycopg2.extras


def config(wcb):
    return {
        "events": [
            ("pubmsg", "handle_pubmsg"),
        ],
        "commands": [
            "karma",
            "topkarma",
        ],
    }


def handle_pubmsg(wcb, event):
    """Handle public messages to check for karma patterns"""
    text = event.arguments[0]

    # Check for !item++ pattern
    plus_match = re.match(r"^!(\S+)\+\+(?:\s+#(.+))?$", text)
    if plus_match:
        item = plus_match.group(1)
        reason = plus_match.group(2) if plus_match.group(2) else None
        wcb.logger.info(f"Karma++ detected for item: {item}, reason: {reason}")
        return add_karma(wcb, event, item, reason)

    # Check for !item-- pattern
    minus_match = re.match(r"^!(\S+)--(?:\s+#(.+))?$", text)
    if minus_match:
        item = minus_match.group(1)
        reason = minus_match.group(2) if minus_match.group(2) else None
        wcb.logger.info(f"Karma-- detected for item: {item}, reason: {reason}")
        return remove_karma(wcb, event, item, reason)

    return False


def add_karma(wcb, event, item, reason=None):
    """Add karma to an item"""
    nick = event.source.nick

    # Don't allow users to give karma to themselves
    if item.lower() == nick.lower():
        wcb.reply("You can't give karma to yourself!")
        return True

    conn = wcb.db_connect()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if the item exists in the karma table
    cur.execute("SELECT * FROM karma WHERE LOWER(item) = LOWER(%s)", (item,))
    karma_item = cur.fetchone()

    if karma_item:
        # Update existing karma
        cur.execute(
            "UPDATE karma SET karma = karma + 1 WHERE id = %s", (karma_item["id"],)
        )
        karma_value = karma_item["karma"] + 1
    else:
        # Insert new karma item
        cur.execute(
            "INSERT INTO karma (item, karma) VALUES (%s, 1) RETURNING id, karma",
            (item,),
        )
        result = cur.fetchone()
        karma_value = result["karma"]

    # Add reason if provided
    if reason:
        cur.execute(
            "INSERT INTO karma_reasons (karma_item, reason, direction) VALUES (%s, %s, 'up')",
            (item, reason),
        )

    conn.commit()
    cur.close()
    conn.close()

    wcb.reply(f"{item} now has {karma_value} karma")
    return True


def remove_karma(wcb, event, item, reason=None):
    """Remove karma from an item"""
    nick = event.source.nick

    # Don't allow users to remove karma from themselves
    if item.lower() == nick.lower():
        wcb.reply("You can't remove karma from yourself!")
        return True

    conn = wcb.db_connect()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Check if the item exists in the karma table
    cur.execute("SELECT * FROM karma WHERE LOWER(item) = LOWER(%s)", (item,))
    karma_item = cur.fetchone()

    if karma_item:
        # Update existing karma
        cur.execute(
            "UPDATE karma SET karma = karma - 1 WHERE id = %s", (karma_item["id"],)
        )
        karma_value = karma_item["karma"] - 1
    else:
        # Insert new karma item with negative value
        cur.execute(
            "INSERT INTO karma (item, karma) VALUES (%s, -1) RETURNING id, karma",
            (item,),
        )
        result = cur.fetchone()
        karma_value = result["karma"]

    # Add reason if provided
    if reason:
        cur.execute(
            "INSERT INTO karma_reasons (karma_item, reason, direction) VALUES (%s, %s, 'down')",
            (item, reason),
        )

    conn.commit()
    cur.close()
    conn.close()

    wcb.reply(f"{item} now has {karma_value} karma")
    return True


def karma(wcb, event, args):
    """Show karma for an item"""
    if not args:
        wcb.reply("Usage: !karma <item>")
        return

    item = args[0]
    conn = wcb.db_connect()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Get karma for the item
    cur.execute("SELECT * FROM karma WHERE LOWER(item) = LOWER(%s)", (item,))
    karma_item = cur.fetchone()

    if not karma_item:
        wcb.reply(f"'{item}' has no karma.")
        cur.close()
        conn.close()
        return

    # Get recent reasons
    cur.execute(
        "SELECT * FROM karma_reasons WHERE LOWER(karma_item) = LOWER(%s) ORDER BY id DESC LIMIT 3",
        (item,),
    )
    reasons = cur.fetchall()

    # Format response
    response = f"{item} has {karma_item['karma']} karma"

    if reasons:
        response += " - Recent reasons: "
        reason_texts = []
        for reason in reasons:
            direction = "+" if reason["direction"] == "up" else "-"
            reason_texts.append(f"{direction}1 for {reason['reason']}")
        response += ", ".join(reason_texts)

    wcb.reply(response)
    cur.close()
    conn.close()


def topkarma(wcb, event, args):
    """Show top karma items"""
    conn = wcb.db_connect()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Default to showing top 5 positive and negative
    limit = 5
    if args and args[0].isdigit():
        limit = int(args[0])
        if limit > 10:  # Cap at 10 to prevent spam
            limit = 10

    # Get top positive karma
    cur.execute(
        "SELECT * FROM karma WHERE karma > 0 ORDER BY karma DESC LIMIT %s", (limit,)
    )
    top_positive = cur.fetchall()

    # Get top negative karma
    cur.execute(
        "SELECT * FROM karma WHERE karma < 0 ORDER BY karma ASC LIMIT %s", (limit,)
    )
    top_negative = cur.fetchall()

    # Format response
    if top_positive:
        wcb.reply(f"Top {len(top_positive)} positive karma:")
        karma_texts = []
        for item in top_positive:
            karma_texts.append(f"{item['item']}: {item['karma']}")
        wcb.reply(", ".join(karma_texts))
    else:
        wcb.reply("No positive karma found.")

    if top_negative:
        wcb.reply(f"Top {len(top_negative)} negative karma:")
        karma_texts = []
        for item in top_negative:
            karma_texts.append(f"{item['item']}: {item['karma']}")
        wcb.reply(", ".join(karma_texts))
    else:
        wcb.reply("No negative karma found.")

    cur.close()
    conn.close()
