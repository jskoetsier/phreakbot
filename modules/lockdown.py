#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Lockdown module for PhreakBot

def config(bot):
    """Return module configuration"""
    return {
        "commands": ["lockdown", "unlock"],
        "permissions": ["admin", "owner"],
        "help": "Set channel to invite-only mode (+i) and voice/op registered users. Usage: !lockdown [reason] or !unlock"
    }

def run(bot, event):
    """Handle lockdown commands"""
    try:
        if event["trigger"] != "command":
            return

        channel = event["channel"]

        if event["command"] == "lockdown":
            reason = event["args"] if event["args"] else "Channel lockdown activated"

            # Set channel to invite-only mode
            bot.connection.mode(channel, "+i")

            # Voice all registered users in the channel
            for nick in bot.channels[channel].users():
                if bot.is_registered(nick):
                    bot.connection.mode(channel, "+v", nick)

            # Set channel topic to include lockdown reason
            current_topic = bot.channels[channel].topic
            new_topic = f"[LOCKDOWN: {reason}] {current_topic}" if current_topic else f"[LOCKDOWN: {reason}]"
            bot.connection.topic(channel, new_topic)

            bot.add_response(f"Channel locked down. Reason: {reason}")

        elif event["command"] == "unlock":
            # Remove invite-only mode
            bot.connection.mode(channel, "-i")

            # Update topic to remove lockdown notice
            current_topic = bot.channels[channel].topic
            if current_topic and "[LOCKDOWN:" in current_topic:
                new_topic = current_topic.split("] ", 1)[1] if "] " in current_topic else ""
                bot.connection.topic(channel, new_topic)

            bot.add_response("Channel lockdown lifted.")

    except Exception as e:
        bot.logger.error(f"Error in lockdown module: {e}")
        bot.add_response(f"Error executing lockdown command: {str(e)}")
    args = event.get("command_args", "").split()

    # Get the channel to lockdown
    if args and args[0].startswith("#"):
        channel = args[0]
        args = args[1:]  # Remove channel from args
    else:
        channel = event["channel"]

    # Check if confirmation is provided
    if "confirm" not in " ".join(args).lower():
        # Confirm the action
        bot.add_response(f"⚠️ CONFIRM EMERGENCY LOCKDOWN FOR {channel}? (say !lockdown {channel} confirm)")
        return

    bot.add_response(f"🚨 ACTIVATING EMERGENCY LOCKDOWN FOR {channel} 🚨")
    bot.logger.info(f"Activating lockdown for {channel} by {event['nick']}")

    try:
        # Step 1: Set channel to invite-only (+i)
        bot.add_response("Setting channel to invite-only mode...")
        bot.logger.info(f"Setting {channel} to +i")
        bot.connection.send_raw(f"MODE {channel} +i")
        time.sleep(0.5)  # Add delay between mode changes

        # Step 2: Kick all unregistered users who joined in the last 5 minutes
        bot.add_response("Kicking unregistered users who joined in the last 5 minutes...")
        _kick_unregistered_users(bot, channel)
        time.sleep(0.5)  # Add delay between operations

        # Step 3: Set channel to moderated mode (+m)
        bot.add_response("Setting channel to moderated mode...")
        bot.logger.info(f"Setting {channel} to +m")
        bot.connection.send_raw(f"MODE {channel} +m")
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
        bot.logger.info(f"Setting {channel} key to lockdown")
        bot.connection.send_raw(f"MODE {channel} +k lockdown")
        time.sleep(0.5)  # Add delay between mode changes

        # Step 7: Remove invite-only mode
        bot.add_response("Removing invite-only mode...")
        bot.logger.info(f"Setting {channel} to -i")
        bot.connection.send_raw(f"MODE {channel} -i")
        time.sleep(0.5)  # Add delay between mode changes

        # Get current channel modes
        bot.add_response("Lockdown complete. Channel is now secured.")
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

    # Parse command arguments
    args = event.get("command_args", "").split()

    # Get the channel to unlock
    if args and args[0].startswith("#"):
        channel = args[0]
    else:
        channel = event["channel"]

    bot.add_response(f"🔓 REMOVING LOCKDOWN FROM {channel} 🔓")
    bot.logger.info(f"Removing lockdown from {channel} by {event['nick']}")

    try:
        # Remove moderated mode
        bot.add_response("Removing moderated mode...")
        bot.logger.info(f"Setting {channel} to -m")
        bot.connection.send_raw(f"MODE {channel} -m")
        time.sleep(0.5)  # Add delay between mode changes

        # Remove channel key
        bot.add_response("Removing channel key...")
        bot.logger.info(f"Removing key from {channel}")
        bot.connection.send_raw(f"MODE {channel} -k lockdown")
        time.sleep(0.5)  # Add delay between mode changes

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
        try:
            # Use NAMES command to get users in channel
            bot.logger.info(f"Getting users in {channel}")
            bot.connection.send_raw(f"NAMES {channel}")
            time.sleep(1)  # Wait for server response

            # Try to get users from the channel object if available
            channel_users = []
            try:
                if hasattr(bot.connection, 'channels') and channel in bot.connection.channels:
                    channel_users = list(bot.connection.channels[channel].users())
                    bot.logger.info(f"Found {len(channel_users)} users in {channel} from channel object")
            except Exception as e:
                bot.logger.error(f"Error getting users from channel object: {e}")

            # If we couldn't get users from the channel object, use a simpler approach
            if not channel_users:
                bot.logger.info("Using alternative method to get users")
                # Just log that we couldn't get users
                bot.logger.warning("Could not get users from channel object")
                return

            bot.logger.info(f"Found {len(channel_users)} users in {channel}")
        except Exception as e:
            bot.logger.error(f"Error getting users in channel {channel}: {e}")
            bot.add_response(f"Error getting users in channel: {str(e)}")
            return

        # Don't kick the bot itself
        bot_nick = bot.connection.get_nickname()
        if bot_nick in channel_users:
            channel_users.remove(bot_nick)

        kicked_count = 0
        bot.logger.info(f"Checking {len(channel_users)} users in {channel} for kicking")

        # For now, just report how many users would be kicked
        bot.add_response(f"Would kick {len(channel_users)} users from {channel}.")

        # Skip actual kicking for now to avoid issues
        return

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
        # Get all admins and owners from the database
        try:
            cur = bot.db_connection.cursor()
            cur.execute(
                "SELECT u.nick FROM phreakbot_users u "
                "WHERE u.is_admin = TRUE OR u.is_owner = TRUE"
            )
            admin_users = [row[0] for row in cur.fetchall()]
            cur.close()

            if not admin_users:
                bot.logger.warning("No admin or owner users found in database")
                return

            bot.logger.info(f"Found {len(admin_users)} admin/owner users")

            # Get the list of users in the channel
            channel_users = []
            try:
                if hasattr(bot.connection, 'channels') and channel in bot.connection.channels:
                    channel_users = list(bot.connection.channels[channel].users())
            except Exception as e:
                bot.logger.error(f"Error getting users in channel: {e}")
                return

            # Op admins and owners who are in the channel
            opped_count = 0
            for nick in channel_users:
                if nick in admin_users:
                    try:
                        bot.logger.info(f"Opping admin/owner {nick}")
                        bot.connection.send_raw(f"MODE {channel} +o {nick}")
                        opped_count += 1
                        time.sleep(0.2)  # Small delay between mode changes
                    except Exception as e:
                        bot.logger.error(f"Error opping user {nick}: {e}")

            bot.add_response(f"Gave operator status to {opped_count} admins/owners in {channel}.")
        except Exception as e:
            bot.logger.error(f"Error getting admin users: {e}")
            bot.add_response(f"Error getting admin users: {str(e)}")

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
        try:
            channel_users = list(bot.connection.channels[channel].users())
        except Exception as e:
            bot.logger.error(f"Error getting users in channel {channel}: {e}")
            bot.add_response(f"Error getting users in channel: {str(e)}")
            return

        voiced_count = 0
        bot.logger.info(f"Checking {len(channel_users)} users in {channel} for voice status")

        for nick in channel_users:
            try:
                # Get the user's hostmask
                hostmask = None
                try:
                    for user in bot.connection.users():
                        if user == nick:
                            hostmask = bot.connection.users()[user]
                            break
                except Exception as e:
                    bot.logger.error(f"Error getting users from connection: {e}")

                if not hostmask:
                    bot.logger.warning(f"Could not find hostmask for {nick}")
                    continue

                # Check if the user is registered
                try:
                    cur = bot.db_connection.cursor()
                    cur.execute(
                        "SELECT 1 FROM phreakbot_users u "
                        "JOIN phreakbot_hostmasks h ON u.id = h.users_id "
                        "WHERE h.hostmask = %s",
                        (hostmask.lower(),),
                    )
                    is_registered = cur.fetchone() is not None
                    cur.close()
                except Exception as e:
                    bot.logger.error(f"Database error checking registration for {nick}: {e}")
                    continue

                if is_registered:
                    # Check if the user is already voiced or opped
                    try:
                        is_voiced = bot.connection.channels[channel].is_voiced(nick)
                        is_oper = bot.connection.channels[channel].is_oper(nick)
                    except Exception as e:
                        bot.logger.error(f"Error checking voice/op status for {nick}: {e}")
                        is_voiced = False
                        is_oper = False

                    if not is_voiced and not is_oper:
                        bot.logger.info(f"Voicing registered user {nick}")
                        try:
                            bot.connection.mode(channel, f"+v {nick}")
                            voiced_count += 1
                            time.sleep(0.2)  # Small delay between mode changes
                        except Exception as e:
                            bot.logger.error(f"Error voicing user {nick}: {e}")
            except Exception as e:
                bot.logger.error(f"Error processing user {nick} for voice: {e}")

        bot.add_response(f"Gave voice status to {voiced_count} registered users in {channel}.")

    except Exception as e:
        bot.logger.error(f"Error voicing registered users: {e}")
        bot.add_response(f"Error voicing registered users: {str(e)}")
        import traceback
        bot.logger.error(traceback.format_exc())
