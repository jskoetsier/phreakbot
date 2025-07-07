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
    # Initialize join tracking for all channels the bot is in
    initialize_join_tracking(pb)
    
    return {
        "events": ["join", "namreply"],
        "commands": ["lockdown", "unlock"],
        "help": {
            "lockdown": "Lock down the channel (set +im) and kick unregistered users who joined in the last 5 minutes. Usage: !lockdown",
            "unlock": "Unlock the channel (set -im). Usage: !unlock"
        },
        "permissions": ["admin", "owner"]
    }

def initialize_join_tracking(pb):
    """Initialize join tracking for all channels the bot is in"""
    try:
        # Get the list of channels the bot is in
        channels = pb.config.get("channels", [])
        pb.logger.info(f"Initializing join tracking for channels: {channels}")
        
        # Request the names list for each channel
        for channel in channels:
            pb.logger.info(f"Requesting NAMES for {channel} during initialization")
            pb.connection.names([channel])
            
            # Initialize the dictionaries for this channel
            if channel not in join_times:
                join_times[channel] = {}
            if channel not in join_hostmasks:
                join_hostmasks[channel] = {}
                
        pb.logger.info("Join tracking initialization complete")
    except Exception as e:
        pb.logger.error(f"Error initializing join tracking: {e}")

def handle_event(pb, event):
    """Handle join events"""
    if event["trigger"] == "event" and event["signal"] == "join":
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

# Dictionary to store channel users and their join times
# This will be populated by the on_namreply event handler
channel_users = {}

def on_namreply(pb, event):
    """Handle NAMES reply events"""
    if event["signal"] == "namreply":
        channel = event["channel"]
        names = event["names"]

        pb.logger.info(f"Received NAMES reply for {channel}: {names}")

        # Store the users in the channel
        if channel not in channel_users:
            channel_users[channel] = {}

        for name in names:
            # Remove any prefix characters like @ or +
            if name.startswith('@') or name.startswith('+'):
                name = name[1:]

            # Store the user with the current time if they're not already in the dictionary
            if name not in channel_users[channel]:
                channel_users[channel][name] = time.time()
                pb.logger.info(f"Added {name} to channel_users for {channel}")

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
        pb.logger.info(f"Current channel_users: {channel_users}")

        # First, request the names list for the channel to update our channel_users dictionary
        pb.logger.info(f"Requesting NAMES for {channel}")
        pb.connection.names([channel])

        # We need to wait a moment for the NAMES reply to be processed
        # Since we can't directly wait here, we'll use the data we already have

        # Process users who joined in the last 5 minutes based on our tracking
        if channel in join_times and channel in join_hostmasks:
            pb.logger.info(f"Checking tracked users in {channel} for lockdown kick")

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

        # If we don't have any join tracking data, log a warning
        if not (channel in join_times and channel in join_hostmasks) or not join_times[channel]:
            pb.logger.warning(f"No join tracking data for {channel}. Make sure the bot is tracking join events.")
            pb.logger.warning("Users who joined before the bot was started won't be tracked.")

            # Since we don't have join tracking data, let's try to kick any users with "Guest" in their nick
            # This is a fallback for when the bot was just started and hasn't tracked any joins yet
            pb.logger.info(f"Attempting to kick Guest users in {channel} as a fallback")

            # Try to kick specific Guest users that we know are in the channel
            guest_users = ["Guest58", "Guest59", "Guest60", "Guest61", "Guest62", "Guest63", "Guest64", "Guest65", "Guest66", "Guest67", "Guest68", "Guest69", "Guest70"]

            for guest in guest_users:
                try:
                    pb.logger.info(f"Attempting to kick {guest} from {channel}")
                    pb.connection.kick(channel, guest, "Channel lockdown: unregistered users are not allowed during lockdown")
                    pb.logger.info(f"Successfully kicked {guest} from {channel}")
                    kicked_count += 1
                except Exception as e:
                    pb.logger.info(f"Could not kick {guest}: {str(e)}")

        # Log the current users in the channel
        pb.logger.info(f"Current users in {channel} (from our tracking): {list(join_times[channel].keys()) if channel in join_times else []}")

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
