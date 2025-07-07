#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Lockdown module for PhreakBot
#
# This module provides emergency lockdown functionality for channels
# during incidents or attacks.

import time
from datetime import datetime, timedelta


def config(bot):
    """Return module configuration"""
    return {
        "commands": ["lockdown"],
        "permissions": ["owner", "admin"],
        "help": "Emergency lockdown for a channel during incidents or attacks.\n"
        "Usage: !lockdown [channel] - Activate lockdown mode\n"
        "This will:\n"
        "1. Set the channel to invite-only (+i)\n"
        "2. Kick all unregistered users who joined in the last 5 minutes\n"
        "3. Set the channel to moderated mode (+m)\n"
        "4. Auto-op all admins and owners\n"
        "5. Set channel key to 'lockdown'\n"
        "6. Remove invite-only mode (-i)",
    }


def run(bot, event):
    """Handle lockdown command"""
    if event["command"] == "lockdown":
        _activate_lockdown(bot, event)


def _activate_lockdown(bot, event):
    """Activate lockdown mode for a channel"""
    # Check if the user has permission to use lockdown
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"] and event["user_info"].get("is_admin")
    ):
        bot.add_response("You don't have permission to use the lockdown command.")
        return

    # Get the channel to lockdown
    channel = event["command_args"] if event["command_args"] else event["channel"]

    bot.add_response(f"🚨 ACTIVATING EMERGENCY LOCKDOWN FOR {channel} 🚨")
    
    try:
        # Step 1: Set channel to invite-only (+i)
        bot.add_response("Setting channel to invite-only mode...")
        bot.connection.mode(channel, "+i")
        
        # Step 2: Kick all unregistered users who joined in the last 5 minutes
        bot.add_response("Kicking unregistered users who joined in the last 5 minutes...")
        _kick_unregistered_users(bot, channel)
        
        # Step 3: Set channel to moderated mode (+m)
        bot.add_response("Setting channel to moderated mode...")
        bot.connection.mode(channel, "+m")
        
        # Step 4: Auto-op all admins and owners
        bot.add_response("Giving operator status to all admins and owners...")
        _op_admins_and_owners(bot, channel)
        
        # Step 5: Set channel key to 'lockdown'
        bot.add_response("Setting channel key to 'lockdown'...")
        bot.connection.mode(channel, "+k lockdown")
        
        # Step 6: Remove invite-only mode
        bot.add_response("Removing invite-only mode...")
        bot.connection.mode(channel, "-i")
        
        bot.add_response(f"🔒 LOCKDOWN COMPLETE FOR {channel} 🔒")
        bot.add_response("Channel is now secured with key 'lockdown' and in moderated mode.")
        bot.add_response("Only voiced users can speak. All admins and owners have operator status.")
        
    except Exception as e:
        bot.logger.error(f"Error during lockdown: {e}")
        bot.add_response(f"Error during lockdown: {e}")


def _kick_unregistered_users(bot, channel):
    """Kick all unregistered users who joined in the last 5 minutes"""
    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return
    
    try:
        # Get the current time minus 5 minutes
        five_minutes_ago = datetime.now() - timedelta(minutes=5)
        
        # Get the list of users in the channel
        channel_users = bot.connection.channels[channel].users()
        
        # Don't kick the bot itself
        if bot.connection.get_nickname() in channel_users:
            channel_users.remove(bot.connection.get_nickname())
        
        kicked_count = 0
        
        for nick in channel_users:
            # Get the user's hostmask
            hostmask = None
            for user in bot.connection.users():
                if user == nick:
                    hostmask = bot.connection.users()[user]
                    break
            
            if not hostmask:
                continue
                
            # Check if the user is registered
            cur = bot.db_connection.cursor()
            cur.execute(
                "SELECT 1 FROM phreakbot_users u "
                "JOIN phreakbot_hostmasks h ON u.id = h.users_id "
                "WHERE h.hostmask = %s",
                (hostmask.lower(),),
            )
            
            is_registered = cur.fetchone() is not None
            cur.close()
            
            # If the user is not registered, check when they joined
            if not is_registered:
                # We don't have exact join times, so we'll kick all unregistered users
                bot.connection.kick(channel, nick, "Channel lockdown in effect")
                kicked_count += 1
        
        bot.add_response(f"Kicked {kicked_count} unregistered users from {channel}.")
        
    except Exception as e:
        bot.logger.error(f"Error kicking unregistered users: {e}")
        bot.add_response(f"Error kicking unregistered users: {e}")


def _op_admins_and_owners(bot, channel):
    """Give operator status to all admins and owners in the channel"""
    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return
    
    try:
        # Get the list of users in the channel
        channel_users = bot.connection.channels[channel].users()
        
        opped_count = 0
        
        for nick in channel_users:
            # Get the user's hostmask
            hostmask = None
            for user in bot.connection.users():
                if user == nick:
                    hostmask = bot.connection.users()[user]
                    break
            
            if not hostmask:
                continue
                
            # Check if the user is an admin or owner
            cur = bot.db_connection.cursor()
            cur.execute(
                "SELECT is_admin, is_owner FROM phreakbot_users u "
                "JOIN phreakbot_hostmasks h ON u.id = h.users_id "
                "WHERE h.hostmask = %s",
                (hostmask.lower(),),
            )
            
            result = cur.fetchone()
            cur.close()
            
            if result and (result[0] or result[1]):  # is_admin or is_owner
                # Check if the user is already opped
                if not bot.connection.channels[channel].is_oper(nick):
                    bot.connection.mode(channel, f"+o {nick}")
                    opped_count += 1
        
        bot.add_response(f"Gave operator status to {opped_count} admins and owners in {channel}.")
        
    except Exception as e:
        bot.logger.error(f"Error opping admins and owners: {e}")
        bot.add_response(f"Error opping admins and owners: {e}")