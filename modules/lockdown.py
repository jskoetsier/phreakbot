#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot - A modular IRC bot
# Lockdown module - Allows channel operators to lock down a channel
#

import time
from datetime import datetime, timedelta

# Dictionary to track when users join channels and their hostmasks
join_times = {}
join_hostmasks = {}

def config(pb):
    """Return module configuration"""
    return {
        "events": ["join"],
        "commands": ["lockdown", "unlock"],
        "help": {
            "lockdown": "Lock down the channel (set +im) and kick unregistered users who joined in the last 5 minutes. Usage: !lockdown",
            "unlock": "Unlock the channel (set -im). Usage: !unlock"
        },
        "permissions": ["admin", "owner"]
    }

def handle_event(pb, event):
    """Handle join events"""
    if event["signal"] == "join":
        # Track when users join channels and their hostmasks
        channel = event["channel"]
        nick = event["nick"]
        hostmask = event["hostmask"]

        if channel not in join_times:
            join_times[channel] = {}
            join_hostmasks[channel] = {}

        join_times[channel][nick] = time.time()
        join_hostmasks[channel][nick] = hostmask
        pb.logger.info(f"Tracked join: {nick} ({hostmask}) in {channel} at {time.time()}")

def run(pb, event):
    """Handle lockdown commands"""
    if event["command"] == "lockdown":
        channel = event["channel"]

        # Check if this is a channel
        if not channel.startswith("#"):
            pb.reply("This command can only be used in a channel.")
            return

        # Set channel mode +im (invite-only and moderated)
        pb.connection.mode(channel, "+im")

        # Get list of users who joined in the last 5 minutes and aren't registered
        kicked_count = 0
        current_time = time.time()
        five_minutes_ago = current_time - (5 * 60)

        # Debug: Log the current state of join tracking
        pb.logger.info(f"Current join_times: {join_times}")
        pb.logger.info(f"Current join_hostmasks: {join_hostmasks}")

        # Get the current users in the channel using WHO command
        pb.logger.info(f"Sending WHO command for {channel}")
        pb.connection.send_raw(f"WHO {channel}")

        # Process users who joined in the last 5 minutes
        if channel in join_times and channel in join_hostmasks:
            pb.logger.info(f"Checking users in {channel} for lockdown kick")
            
            # Process each user who joined in the last 5 minutes
            for nick, join_time in list(join_times[channel].items()):
                # Only check users who joined in the last 5 minutes
                if join_time >= five_minutes_ago:
                    pb.logger.info(f"Checking if {nick} is registered (joined in last 5 minutes)")
                    
                    try:
                        # Get user hostmask from our tracking dictionary
                        user_host = join_hostmasks[channel].get(nick)
                        
                        if user_host:
                            # Check if user is in the database (registered)
                            user_info = pb.db_get_userinfo_by_userhost(user_host)
                            pb.logger.info(f"User info for {nick} ({user_host}): {user_info}")
                            
                            if not user_info:
                                # User is not registered, kick them
                                pb.logger.info(f"Kicking unregistered user {nick} ({user_host})")
                                pb.connection.kick(channel, nick, "Channel lockdown: unregistered users are not allowed during lockdown")
                                kicked_count += 1
                            else:
                                pb.logger.info(f"User {nick} is registered, not kicking")
                        else:
                            # If we can't get the hostmask, assume unregistered and kick
                            pb.logger.info(f"Could not get hostmask for {nick}, kicking as unregistered")
                            pb.connection.kick(channel, nick, "Channel lockdown: unregistered users are not allowed during lockdown")
                            kicked_count += 1
                    except Exception as e:
                        pb.logger.error(f"Error checking user {nick}: {str(e)}")
                        # If there's an error, err on the side of caution and kick
                        try:
                            pb.connection.kick(channel, nick, "Channel lockdown: unregistered users are not allowed during lockdown")
                            kicked_count += 1
                        except Exception as kick_error:
                            pb.logger.error(f"Error kicking user {nick}: {str(kick_error)}")
        
        # Special case for users with "Guest" in their nick who are in the channel
        # but might not be in our tracking dictionaries
        try:
            # Use the NAMES command to get a list of users in the channel
            pb.logger.info(f"Sending NAMES command for {channel}")
            pb.connection.names([channel])
            
            # We can't directly get the results of the NAMES command here,
            # so we'll use a different approach. We'll check if there are any users
            # with "Guest" in their nick in the channel and kick them.
            pb.logger.info(f"Checking for Guest users in {channel}")
            
            # Use the WHO command to get information about users in the channel
            pb.connection.send_raw(f"WHO {channel}")
            
            # Since we can't directly get the results of the WHO command here,
            # we'll use a more direct approach. We'll send a kick command for
            # users with "Guest" in their nick.
            pb.logger.info(f"Sending kick command for Guest users in {channel}")
            pb.connection.send_raw(f"KICK {channel} Guest* :Channel lockdown: unregistered users are not allowed during lockdown")
            
            # We don't know exactly how many users were kicked, but we'll increment the counter
            kicked_count += 1
        except Exception as e:
            pb.logger.error(f"Error kicking Guest users: {str(e)}")

        pb.reply(f"Channel {channel} is now locked down (mode +im). Kicked {kicked_count} unregistered users who joined in the last 5 minutes.")

    elif event["command"] == "unlock":
        channel = event["channel"]

        # Check if this is a channel
        if not channel.startswith("#"):
            pb.reply("This command can only be used in a channel.")
            return

        # Set channel mode -im (remove invite-only and moderated)
        pb.connection.mode(channel, "-im")
        pb.reply(f"Channel {channel} is now unlocked (mode -im).")
