#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# InfoItems3 module for PhreakBot - Simplified version with hardcoded commands

def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "privmsg"],  # Listen for all messages
        "commands": [],  # No standard commands, only custom patterns
        "permissions": ["user"],
        "help": "InfoItems system. Usage:\n"
                "       !phreak = gek - Add the specific info item\n"
                "       !phreak? - Show the specific info item",
    }


def run(bot, event):
    """Handle specific infoitems patterns directly"""
    if not bot.db_connection:
        return

    # Only process event triggers
    if event["trigger"] != "event":
        return

    # Get the message text
    message = event["text"]
    
    # Always log the message for debugging
    bot.logger.info(f"InfoItems3 received message: '{message}'")
    
    # Check for specific commands
    if message == "!phreak = gek":
        bot.logger.info("InfoItems3: Matched !phreak = gek")
        bot.add_response("InfoItems3: Adding info item 'phreak' with value 'gek'")
        
        # Get the user's ID
        user_info = event["user_info"]
        if not user_info:
            bot.add_response("You need to be a registered user to add info items.")
            return True
            
        cur = bot.db_connection.cursor()
        try:
            # Add the new info item
            cur.execute(
                "INSERT INTO phreakbot_infoitems (users_id, item, value, channel) VALUES (%s, %s, %s, %s) RETURNING id",
                (user_info["id"], "phreak", "gek", event["channel"])
            )
            bot.db_connection.commit()
            bot.add_response("Info item 'phreak' added successfully.")
        except Exception as e:
            bot.logger.error(f"Error adding info item: {e}")
            bot.add_response("Error adding info item.")
            bot.db_connection.rollback()
        finally:
            cur.close()
        return True
    
    if message == "!phreak?":
        bot.logger.info("InfoItems3: Matched !phreak?")
        bot.add_response("InfoItems3: Getting info item 'phreak'")
        
        cur = bot.db_connection.cursor()
        try:
            # Get all values for this item in the current channel
            cur.execute(
                "SELECT i.value, u.username, i.insert_time FROM phreakbot_infoitems i "
                "JOIN phreakbot_users u ON i.users_id = u.id "
                "WHERE i.item = %s AND i.channel = %s "
                "ORDER BY i.insert_time",
                ("phreak", event["channel"])
            )
            
            items = cur.fetchall()
            
            if not items:
                bot.add_response("No info found for 'phreak'.")
            else:
                bot.add_response("Info for 'phreak':")
                for value, username, timestamp in items:
                    bot.add_response(f"• {value} (added by {username} on {timestamp.strftime('%Y-%m-%d')})")
        except Exception as e:
            bot.logger.error(f"Error retrieving info item: {e}")
            bot.add_response("Error retrieving info item.")
        finally:
            cur.close()
        return True
    
    return False