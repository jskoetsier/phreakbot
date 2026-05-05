#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Karma module for PhreakBot
"""
import re
import psycopg2.extras


def config(bot):
    return {
        "events": ["pubmsg"],
        "commands": ["karma", "topkarma"],
        "permissions": ["user"],
        "help": {
            "karma": "Show karma for an item. Usage: !karma <item>",
            "topkarma": "Show top karma items. Usage: !topkarma [limit]",
        },
    }


def run(bot, event):
    if event["trigger"] == "command":
        if event["command"] == "karma":
            return _cmd_karma(bot, event)
        elif event["command"] == "topkarma":
            return _cmd_topkarma(bot, event)

    elif event["trigger"] == "event" and event["signal"] == "pubmsg":
        return _handle_karma_pattern(bot, event)

    return False


KARMA_PATTERN = re.compile(r"^\!([a-zA-Z0-9_-]+)(\+\+|\-\-)(?:\s+#(.+))?$")


def _handle_karma_pattern(bot, event):
    text = event["text"]
    match = KARMA_PATTERN.match(text)
    if not match:
        return False

    item = match.group(1).lower()
    direction = "up" if match.group(2) == "++" else "down"
    reason = match.group(3)

    if item == event["nick"].lower():
        bot.reply("You can't give karma to yourself!")
        return True

    conn = bot.db_get()
    if not conn:
        bot.reply("Database connection is not available.")
        return True

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM karma WHERE LOWER(item) = LOWER(%s)", (item,))
        karma_item = cur.fetchone()

        if direction == "up":
            if karma_item:
                cur.execute("UPDATE karma SET karma = karma + 1 WHERE id = %s", (karma_item["id"],))
                karma_value = karma_item["karma"] + 1
            else:
                cur.execute("INSERT INTO karma (item, karma) VALUES (%s, 1) RETURNING id, karma", (item,))
                karma_value = cur.fetchone()["karma"]
        else:
            if karma_item:
                cur.execute("UPDATE karma SET karma = karma - 1 WHERE id = %s", (karma_item["id"],))
                karma_value = karma_item["karma"] - 1
            else:
                cur.execute("INSERT INTO karma (item, karma) VALUES (%s, -1) RETURNING id, karma", (item,))
                karma_value = cur.fetchone()["karma"]

        if reason:
            cur.execute(
                "INSERT INTO karma_reasons (karma_item, reason, direction) VALUES (%s, %s, %s)",
                (item, reason, direction),
            )

        conn.commit()
        cur.close()
        bot.db_return(conn)
        bot.reply(f"{item} now has {karma_value} karma")
        return True

    except Exception as e:
        bot.logger.error(f"Error in karma module: {e}")
        conn.rollback()
        cur.close()
        bot.db_return(conn)
        return True


def _cmd_karma(bot, event):
    args = event["command_args"].strip()
    if not args:
        bot.reply("Usage: !karma <item>")
        return True

    item = args.split()[0].lower()
    conn = bot.db_get()
    if not conn:
        bot.reply("Database connection is not available.")
        return True

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM karma WHERE LOWER(item) = LOWER(%s)", (item,))
        karma_item = cur.fetchone()

        if not karma_item:
            bot.reply(f"'{item}' has no karma.")
            cur.close()
            bot.db_return(conn)
            return True

        cur.execute(
            "SELECT * FROM karma_reasons WHERE LOWER(karma_item) = LOWER(%s) ORDER BY id DESC LIMIT 3",
            (item,),
        )
        reasons = cur.fetchall()

        response = f"{item} has {karma_item['karma']} karma"
        if reasons:
            response += " - Recent reasons: "
            reason_texts = []
            for reason in reasons:
                direction = "+" if reason["direction"] == "up" else "-"
                reason_texts.append(f"{direction}1 for {reason['reason']}")
            response += ", ".join(reason_texts)

        bot.reply(response)
        cur.close()
        bot.db_return(conn)
        return True

    except Exception as e:
        bot.logger.error(f"Error in karma module: {e}")
        bot.db_return(conn)
        return True


def _cmd_topkarma(bot, event):
    args = event["command_args"].strip()
    limit = 5
    if args and args.split()[0].isdigit():
        limit = int(args.split()[0])
        if limit > 10:
            limit = 10

    conn = bot.db_get()
    if not conn:
        bot.reply("Database connection is not available.")
        return True

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("SELECT * FROM karma WHERE karma > 0 ORDER BY karma DESC LIMIT %s", (limit,))
        top_positive = cur.fetchall()

        cur.execute("SELECT * FROM karma WHERE karma < 0 ORDER BY karma ASC LIMIT %s", (limit,))
        top_negative = cur.fetchall()

        if top_positive:
            bot.reply(f"Top {len(top_positive)} positive karma:")
            karma_texts = [f"{item['item']}: {item['karma']}" for item in top_positive]
            bot.reply(", ".join(karma_texts))
        else:
            bot.reply("No positive karma found.")

        if top_negative:
            bot.reply(f"Top {len(top_negative)} negative karma:")
            karma_texts = [f"{item['item']}: {item['karma']}" for item in top_negative]
            bot.reply(", ".join(karma_texts))
        else:
            bot.reply("No negative karma found.")

        cur.close()
        bot.db_return(conn)
        return True

    except Exception as e:
        bot.logger.error(f"Error in karma module: {e}")
        bot.db_return(conn)
        return True
