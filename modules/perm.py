#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Permission management module for PhreakBot


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["perm", "perms"],
        "permissions": ["owner", "admin", "perm"],
        "help": "Manage user permissions.\n"
        "Usage: !perm add <nick> <permission1> [..<permissionN>] [<channel>] - Add permissions\n"
        "       !perm remove <nick> <permission1> [..<permissionN>] [<channel>] - Remove permissions\n"
        "Note: Leave channel out for global permission.",
    }


def run(bot, event):
    """Handle permission management commands"""
    args_txt = event["command_args"]
    args_txt = bot.re.sub(r"\s{2,}", " ", args_txt)
    args_arr = args_txt.split(" ")

    if len(args_arr) < 3:
        bot.add_response(
            "Usage: !perm <add|remove> <nick> <permission1> [..<permissionN>] [<channel>]"
        )
        return

    mode = args_arr.pop(0)
    nick = args_arr.pop(0)
    channel = ""
    if bot.re.match(r"^[#&]", args_arr[-1]):
        channel = args_arr.pop(-1)

    # args_arr should now only hold permissions to set

    # Check if the user exists in the database
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        cur = bot.db_connection.cursor()

        # Find the user ID by nickname
        cur.execute(
            "SELECT id FROM phreakbot_users WHERE username ILIKE %s", (nick.lower(),)
        )
        user = cur.fetchone()

        if not user:
            bot.add_response(
                f"Could not match nick '{nick}' to a known user. Try using !meet first?"
            )
            cur.close()
            return

        user_id = user[0]

        if bot.re.match(r"(?:set|add)", mode):
            counter = 0
            for permission in args_arr:
                # Use ON CONFLICT to handle duplicate permissions
                cur.execute(
                    "INSERT INTO phreakbot_perms (users_id, permission, channel) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (user_id, permission, channel.lower()),
                )
                counter += 1

            bot.db_connection.commit()
            bot.add_response(f"Added {counter} permissions to '{nick}'")

        elif bot.re.match(r"(?:rem(?:ove)?|del(?:ete)?)", mode):
            counter = 0
            for permission in args_arr:
                cur.execute(
                    "DELETE FROM phreakbot_perms WHERE users_id = %s AND permission = %s AND channel = %s",
                    (user_id, permission, channel.lower()),
                )
                counter += 1

            bot.db_connection.commit()
            bot.add_response(f"Removed {counter} permissions from '{nick}'")

        else:
            bot.add_response(f"Unknown mode: {mode}. Use 'add' or 'remove'.")

        cur.close()

    except Exception as e:
        bot.logger.error(f"Database error in perm module: {e}")
        bot.add_response("Error managing permissions.")
