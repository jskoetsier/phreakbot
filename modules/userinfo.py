#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Userinfo module for PhreakBot
# A more reliable alternative to the whois module

import threading
import time

# Dictionary to store WHOIS responses
whois_responses = {}
whois_events = {}

def config(bot):
    """Return module configuration"""
    return {
        "events": ["whoisuser", "whoisserver", "whoisoperator", "whoisidle", "whoischannels", "endofwhois"],
        "commands": ["userinfo"],
        "permissions": ["user"],
        "help": "Shows information about a user using IRC WHOIS.\n"
        "Usage: !userinfo <nickname> - Show information about a user",
    }


def run(bot, event):
    """Handle userinfo commands and WHOIS responses"""
    if event["trigger"] == "command" and event["command"] == "userinfo":
        _handle_userinfo_command(bot, event)
    elif event["trigger"] == "event" and event["signal"].startswith("whois"):
        _handle_whois_response(bot, event)
    elif event["trigger"] == "event" and event["signal"] == "endofwhois":
        _handle_end_of_whois(bot, event)


def _handle_userinfo_command(bot, event):
    """Handle the userinfo command"""
    tnick = event["command_args"].strip()

    if not tnick:
        bot.add_response("Please specify a nickname to look up.")
        return

    if tnick == bot.connection.get_nickname():
        bot.add_response(f"I am the channel bot, {bot.connection.get_nickname()}")
        return

    # Create an event to wait for the WHOIS response
    whois_event = threading.Event()
    whois_events[tnick.lower()] = whois_event
    whois_responses[tnick.lower()] = {}

    # Send WHOIS request
    bot.logger.info(f"Sending WHOIS request for {tnick}")
    bot.connection.whois(tnick)

    # Wait for the response with a timeout
    def process_whois_response():
        # Wait for the response with a timeout
        if whois_event.wait(5):  # 5 second timeout
            # Process the response
            response = whois_responses.get(tnick.lower(), {})
            bot.logger.info(f"WHOIS response for {tnick}: {response}")

            if not response:
                bot.add_response(f"No information found for {tnick}.")
                return

            # Format and send the response
            if "user" in response:
                user_info = response["user"]
                bot.add_response(f"{tnick} is {user_info['username']}@{user_info['host']} ({user_info['realname']})")

            if "server" in response:
                server_info = response["server"]
                bot.add_response(f"{tnick} is using {server_info['server']} ({server_info['serverinfo']})")

            if "channels" in response:
                channels = response["channels"]
                bot.add_response(f"{tnick} is on channels: {channels}")

            if "idle" in response:
                idle_info = response["idle"]
                idle_time = int(idle_info["idle"])
                if idle_time > 0:
                    minutes, seconds = divmod(idle_time, 60)
                    hours, minutes = divmod(minutes, 60)
                    days, hours = divmod(hours, 24)
                    
                    idle_str = ""
                    if days > 0:
                        idle_str += f"{days} days, "
                    if hours > 0:
                        idle_str += f"{hours} hours, "
                    if minutes > 0:
                        idle_str += f"{minutes} minutes, "
                    if seconds > 0:
                        idle_str += f"{seconds} seconds"
                    
                    bot.add_response(f"{tnick} has been idle for {idle_str}")

            if "operator" in response:
                bot.add_response(f"{tnick} is an IRC operator")

            # Check if the user exists in the database
            if bot.db_connection:
                try:
                    # Try to get user info from the database
                    if "user" in response:
                        user_info = response["user"]
                        hostmask = f"{tnick}!{user_info['username']}@{user_info['host']}"
                        
                        # Get user info from database
                        db_user = bot.db_get_userinfo_by_userhost(hostmask)
                        
                        if db_user:
                            bot.add_response(f"Recognized as user '{db_user['username']}'")
                            
                            # Show permissions
                            if db_user["permissions"]["global"]:
                                bot.add_response(f"Global permissions: {', '.join(db_user['permissions']['global'])}")
                            
                            channel = event["channel"]
                            if channel in db_user["permissions"]:
                                bot.add_response(f"Channel permissions for {channel}: {', '.join(db_user['permissions'][channel])}")
                            
                            # Show owner/admin status
                            if db_user.get("is_owner"):
                                bot.add_response("This user is the bot owner.")
                            elif db_user.get("is_admin"):
                                bot.add_response("This user is a bot admin.")
                        else:
                            bot.add_response("Unrecognized user (not in database).")
                except Exception as e:
                    bot.logger.error(f"Database error in userinfo module: {e}")
                    bot.add_response("Error retrieving user information from database.")
            
            # Clean up
            if tnick.lower() in whois_responses:
                del whois_responses[tnick.lower()]
            if tnick.lower() in whois_events:
                del whois_events[tnick.lower()]
        else:
            # Timeout occurred
            bot.add_response(f"Timeout waiting for WHOIS response for {tnick}.")
            
            # Clean up
            if tnick.lower() in whois_responses:
                del whois_responses[tnick.lower()]
            if tnick.lower() in whois_events:
                del whois_events[tnick.lower()]

    # Start a thread to process the response
    thread = threading.Thread(target=process_whois_response)
    thread.daemon = True
    thread.start()


def _handle_whois_response(bot, event):
    """Handle WHOIS response events"""
    # Extract the target nickname from the arguments
    if not event["raw_event"].arguments or len(event["raw_event"].arguments) < 2:
        return
    
    target_nick = event["raw_event"].arguments[0].lower()
    bot.logger.info(f"Received WHOIS response for {target_nick}: {event['signal']}")
    
    # Check if we're waiting for this response
    if target_nick not in whois_responses:
        return
    
    # Process different types of WHOIS responses
    if event["signal"] == "whoisuser":
        # RPL_WHOISUSER: "<nick> <user> <host> * :<real name>"
        if len(event["raw_event"].arguments) >= 5:
            whois_responses[target_nick]["user"] = {
                "username": event["raw_event"].arguments[1],
                "host": event["raw_event"].arguments[2],
                "realname": event["raw_event"].arguments[4]
            }
    
    elif event["signal"] == "whoisserver":
        # RPL_WHOISSERVER: "<nick> <server> :<server info>"
        if len(event["raw_event"].arguments) >= 3:
            whois_responses[target_nick]["server"] = {
                "server": event["raw_event"].arguments[1],
                "serverinfo": event["raw_event"].arguments[2]
            }
    
    elif event["signal"] == "whoisidle":
        # RPL_WHOISIDLE: "<nick> <idle> <signon> :seconds idle, signon time"
        if len(event["raw_event"].arguments) >= 3:
            whois_responses[target_nick]["idle"] = {
                "idle": event["raw_event"].arguments[1],
                "signon": event["raw_event"].arguments[2]
            }
    
    elif event["signal"] == "whoischannels":
        # RPL_WHOISCHANNELS: "<nick> :<channel list>"
        if len(event["raw_event"].arguments) >= 2:
            whois_responses[target_nick]["channels"] = event["raw_event"].arguments[1]
    
    elif event["signal"] == "whoisoperator":
        # RPL_WHOISOPERATOR: "<nick> :is an IRC operator"
        whois_responses[target_nick]["operator"] = True


def _handle_end_of_whois(bot, event):
    """Handle end of WHOIS response"""
    # Extract the target nickname from the arguments
    if not event["raw_event"].arguments or len(event["raw_event"].arguments) < 1:
        return
    
    target_nick = event["raw_event"].arguments[0].lower()
    bot.logger.info(f"End of WHOIS for {target_nick}")
    
    # Check if we're waiting for this response
    if target_nick in whois_events:
        # Signal that the WHOIS response is complete
        whois_events[target_nick].set()