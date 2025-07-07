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
        "commands": ["lockdown", "unlock"],
        "permissions": ["owner", "admin"],
        "help": "Emergency lockdown for a channel during incidents or attacks.\n"
        "Usage: !lockdown [channel] - Activate lockdown mode\n"
        "       !unlock [channel] - Remove lockdown mode\n"
        "Lockdown will:\n"
        "1. Set the channel to invite-only (+i)\n"
        "2. Kick all unregistered users who joined in the last 5 minutes\n"
        "3. Set the channel to moderated mode (+m)\n"
        "4. Auto-op all admins and owners\n"
        "5. Voice all registered users\n"
        "6. Set channel key to 'lockdown'\n"
        "7. Remove invite-only mode (-i)",
    }


def run(bot, event):
    """Handle lockdown command"""
    if event["command"] == "lockdown":
        _activate_lockdown(bot, event)
    elif event["command"] == "unlock":
        _deactivate_lockdown(bot, event)


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

    # Confirm the action
    bot.add_response(f"⚠️ CONFIRM EMERGENCY LOCKDOWN FOR {channel}? (say !lockdown {channel} confirm)")
    
    # Check if confirmation is provided
    if "confirm" not in event.get("command_args", "").lower():
        return
    
    bot.add_response(f"🚨 ACTIVATING EMERGENCY LOCKDOWN FOR {channel} 🚨")
    bot.logger.info(f"Activating lockdown for {channel} by {event['nick']}")

    try:
        # Step 1: Set channel to invite-only (+i)
        bot.add_response("Setting channel to invite-only mode...")
        bot.connection.mode(channel, "+i")
        time.sleep(0.5)  # Add delay between mode changes

        # Step 2: Kick all unregistered users who joined in the last 5 minutes
        bot.add_response("Kicking unregistered users who joined in the last 5 minutes...")
        _kick_unregistered_users(bot, channel)
        time.sleep(0.5)  # Add delay between operations

        # Step 3: Set channel to moderated mode (+m)
        bot.add_response("Setting channel to moderated mode...")
        bot.connection.mode(channel, "+m")
        time.sleep(0.5)  # Add delay between mode changes

        # Step 4: Auto-op all admins and owners
        bot.add_response("Giving operator status to all admins and owners...")
        _op_admins_and_owners(bot, channel)
        time.sleep(0.5)  # Add delay between operations

        # Step 5: Voice all registered users
        bot.add_response("Giving voice to all registered users...")
        _voice_registered_users(bot, channel)
        time.sleep(0.5)  # Add delay between operations

        # Step 6: Set channel key to 'lockdown'
        bot.add_response("Setting channel key to 'lockdown'...")
        bot.connection.mode(channel, "+k lockdown")
        time.sleep(0.5)  # Add delay between mode changes

        # Step 7: Remove invite-only mode
        bot.add_response("Removing invite-only mode...")
        bot.connection.mode(channel, "-i")
        time.sleep(0.5)  # Add delay between mode changes

        # Get current channel modes
        try:
            current_modes = bot.connection.channels[channel].modes
            bot.add_response(f"Current channel modes: {current_modes}")
        except:
            bot.add_response("Unable to retrieve current channel modes.")

        bot.add_response(f"🔒 LOCKDOWN COMPLETE FOR {channel} 🔒")
        bot.add_response("Channel is now secured with key 'lockdown' and in moderated mode.")
        bot.add_response("Only voiced users can speak. All admins and owners have operator status.")
        bot.add_response("Use !unlock to remove the lockdown.")

    except Exception as e:
        bot.logger.error(f"Error during lockdown: {e}")
        bot.add_response(f"Error during lockdown: {str(e)}")
        import traceback
        bot.logger.error(traceback.format_exc())


def _deactivate_lockdown(bot, event):
    """Remove lockdown mode from a channel"""
    # Check if the user has permission to use unlock
    if not bot._is_owner(event["hostmask"]) and not (
        event["user_info"] and event["user_info"].get("is_admin")
    ):
        bot.add_response("You don't have permission to use the unlock command.")
        return

    # Get the channel to unlock
    channel = event["command_args"] if event["command_args"] else event["channel"]

    bot.add_response(f"🔓 REMOVING LOCKDOWN FROM {channel} 🔓")
    bot.logger.info(f"Removing lockdown from {channel} by {event['nick']}")

    try:
        # Remove moderated mode
        bot.add_response("Removing moderated mode...")
        bot.connection.mode(channel, "-m")
        time.sleep(0.5)  # Add delay between mode changes

        # Remove channel key
        bot.add_response("Removing channel key...")
        bot.connection.mode(channel, "-k lockdown")
        time.sleep(0.5)  # Add delay between mode changes

        # Get current channel modes
        try:
            current_modes = bot.connection.channels[channel].modes
            bot.add_response(f"Current channel modes: {current_modes}")
        except:
            bot.add_response("Unable to retrieve current channel modes.")

        bot.add_response(f"🔓 LOCKDOWN REMOVED FROM {channel} 🔓")

    except Exception as e:
        bot.logger.error(f"Error during unlock: {e}")
        bot.add_response(f"Error during unlock: {str(e)}")
        import traceback
        bot.logger.error(traceback.format_exc())


def _kick_unregistered_users(bot, channel):
    """Kick all unregistered users who joined in the last 5 minutes"""
    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        # Get the list of users in the channel
        channel_users = list(bot.connection.channels[channel].users())
        
        # Don't kick the bot itself
        bot_nick = bot.connection.get_nickname()
        if bot_nick in channel_users:
            channel_users.remove(bot_nick)

        kicked_count = 0
        bot.logger.info(f"Checking {len(channel_users)} users in {channel} for kicking")

        for nick in channel_users:
            try:
                # Get the user's hostmask
                hostmask = None
                for user in bot.connection.users():
                    if user == nick:
                        hostmask = bot.connection.users()[user]
                        break

                if not hostmask:
                    bot.logger.warning(f"Could not find hostmask for {nick}")
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

                # If the user is not registered, kick them
                if not is_registered:
                    bot.logger.info(f"Kicking unregistered user {nick} ({hostmask})")
                    bot.connection.kick(channel, nick, "Channel lockdown in effect - Unregistered user")
                    kicked_count += 1
                    time.sleep(0.2)  # Small delay between kicks to avoid flood
            except Exception as e:
                bot.logger.error(f"Error processing user {nick}: {e}")

        bot.add_response(f"Kicked {kicked_count} unregistered users from {channel}.")

    except Exception as e:
        bot.logger.error(f"Error kicking unregistered users: {e}")
        bot.add_response(f"Error kicking unregistered users: {str(e)}")
        import traceback
        bot.logger.error(traceback.format_exc())


def _op_admins_and_owners(bot, channel):
    """Give operator status to all admins and owners in the channel"""
    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        # Get the list of users in the channel
        channel_users = list(bot.connection.channels[channel].users())
        
        opped_count = 0
        bot.logger.info(f"Checking {len(channel_users)} users in {channel} for op status")

        for nick in channel_users:
            try:
                # Get the user's hostmask
                hostmask = None
                for user in bot.connection.users():
                    if user == nick:
                        hostmask = bot.connection.users()[user]
                        break

                if not hostmask:
                    bot.logger.warning(f"Could not find hostmask for {nick}")
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
                    try:
                        is_oper = bot.connection.channels[channel].is_oper(nick)
                    except:
                        is_oper = False
                        
                    if not is_oper:
                        bot.logger.info(f"Opping admin/owner {nick}")
                        bot.connection.mode(channel, f"+o {nick}")
                        opped_count += 1
                        time.sleep(0.2)  # Small delay between mode changes
            except Exception as e:
                bot.logger.error(f"Error processing user {nick} for op: {e}")

        bot.add_response(f"Gave operator status to {opped_count} admins and owners in {channel}.")

    except Exception as e:
        bot.logger.error(f"Error opping admins and owners: {e}")
        bot.add_response(f"Error opping admins and owners: {str(e)}")
        import traceback
        bot.logger.error(traceback.format_exc())


def _voice_registered_users(bot, channel):
    """Give voice status to all registered users in the channel"""
    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    try:
        # Get the list of users in the channel
        channel_users = list(bot.connection.channels[channel].users())
        
        voiced_count = 0
        bot.logger.info(f"Checking {len(channel_users)} users in {channel} for voice status")

        for nick in channel_users:
            try:
                # Get the user's hostmask
                hostmask = None
                for user in bot.connection.users():
                    if user == nick:
                        hostmask = bot.connection.users()[user]
                        break

                if not hostmask:
                    bot.logger.warning(f"Could not find hostmask for {nick}")
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

                if is_registered:
                    # Check if the user is already voiced or opped
                    try:
                        is_voiced = bot.connection.channels[channel].is_voiced(nick)
                        is_oper = bot.connection.channels[channel].is_oper(nick)
                    except:
                        is_voiced = False
                        is_oper = False
                        
                    if not is_voiced and not is_oper:
                        bot.logger.info(f"Voicing registered user {nick}")
                        bot.connection.mode(channel, f"+v {nick}")
                        voiced_count += 1
                        time.sleep(0.2)  # Small delay between mode changes
            except Exception as e:
                bot.logger.error(f"Error processing user {nick} for voice: {e}")

        bot.add_response(f"Gave voice status to {voiced_count} registered users in {channel}.")

    except Exception as e:
        bot.logger.error(f"Error voicing registered users: {e}")
        bot.add_response(f"Error voicing registered users: {str(e)}")
        import traceback
        bot.logger.error(traceback.format_exc())
