#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Whoami module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["whoami", "test"],
        "permissions": ["user"],
        "help": "Tells you who the bot thinks you are.",
    }


def run(bot, event):
    """Handle whoami commands"""
    if "test =" in event["text"]:  # ignore '!test = bla' events.
        return

    rtxt = f"You are {event['nick']} at {event['hostmask']}"

    if bot._is_owner(event["hostmask"]):
        rtxt += ", and YOU are my owner!"
    elif event["user_info"] and event["user_info"].get("is_admin"):
        rtxt += (
            f", registered user {event['user_info']['username']} and you are an admin!"
        )
    else:
        if event["user_info"] and event["user_info"].get("username"):
            rtxt += f", registered user {event['user_info']['username']}"

            if event["user_info"]["permissions"]["global"]:
                rtxt += f", with global perms ({', '.join(event['user_info']['permissions']['global'])})"

            channel = event["channel"]
            if channel in event["user_info"]["permissions"]:
                rtxt += f", with {channel} perms ({', '.join(event['user_info']['permissions'][channel])})"

        else:
            rtxt += ", unrecognized user"

            if bot.db_connection:
                try:
                    cur = bot.db_connection.cursor()
                    sql = "SELECT * FROM phreakbot_users WHERE username ILIKE %s"
                    cur.execute(sql, (event["nick"].lower(),))
                    res = cur.fetchone()
                    if res:
                        rtxt += ", but a user was found in the DB, perhaps you need a merge?"
                    cur.close()
                except Exception as e:
                    bot.logger.error(f"Database error in whoami module: {e}")

    bot.add_response(rtxt)
