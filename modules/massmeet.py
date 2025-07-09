#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Mass Meet module for PhreakBot
# Registers all users in channels and merges hostmasks


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["massmeet"],
        "permissions": ["owner", "admin"],
        "help": "Register all users in channels and merge hostmasks.\n"
        "Usage: !massmeet - Register all unregistered users and merge hostmasks",
    }


def run(bot, event):
    """Handle massmeet command"""
    if event["command"] != "massmeet":
        return

    # Check if the database connection is available
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return

    bot.add_response("Starting mass meet process. This may take a moment...")
    
    # Statistics to track actions
    stats = {
        "total_users": 0,
        "registered_new": 0,
        "merged_hostmasks": 0,
        "already_registered": 0,
        "errors": 0,
        "skipped": 0  # For bot itself and users we can't process
    }
    
    try:
        # Get all users from all channels
        all_users = {}  # {nickname: hostmask}
        
        # Debug the channels
        bot.logger.info(f"Bot channels: {list(bot.channels.keys())}")
        bot.logger.info(f"Bot channels type: {type(bot.channels)}")
        
        # Debug the connection object
        bot.logger.info(f"Bot connection: {bot.connection}")
        bot.logger.info(f"Bot connection type: {type(bot.connection)}")
        
        # Try to get users directly from the connection
        for channel_name in bot.channels.keys():
            try:
                bot.logger.info(f"Trying to get users for channel: {channel_name}")
                
                # Try different methods to get users
                # Method 1: Using the channel object
                channel = bot.channels[channel_name]
                bot.logger.info(f"Channel object: {channel}")
                bot.logger.info(f"Channel object type: {type(channel)}")
                
                # Try to access users method if it exists
                if hasattr(channel, 'users'):
                    bot.logger.info("Channel has users() method")
                    try:
                        users_dict = channel.users()
                        bot.logger.info(f"Users dict: {users_dict}")
                        bot.logger.info(f"Users dict type: {type(users_dict)}")
                        bot.logger.info(f"Users in channel {channel_name}: {list(users_dict.keys()) if hasattr(users_dict, 'keys') else 'No keys method'}")
                    except Exception as e:
                        bot.logger.error(f"Error calling users() method: {e}")
                else:
                    bot.logger.info("Channel does not have users() method")
                
                # Method 2: Try to access users as an attribute
                if hasattr(channel, 'userdict'):
                    bot.logger.info("Channel has userdict attribute")
                    users_dict = channel.userdict
                    bot.logger.info(f"Users from userdict: {users_dict}")
                
                # Method 3: Try to get users from the connection
                try:
                    bot.logger.info("Trying to get users from connection.names")
                    if hasattr(bot.connection, 'names'):
                        names = bot.connection.names(channel_name)
                        bot.logger.info(f"Names from connection: {names}")
                except Exception as e:
                    bot.logger.error(f"Error getting names from connection: {e}")
                
                # Method 4: Try to use the raw event data
                try:
                    bot.logger.info("Trying to use raw event data")
                    if 'raw_event' in event and hasattr(event['raw_event'], 'arguments'):
                        bot.logger.info(f"Raw event arguments: {event['raw_event'].arguments}")
                except Exception as e:
                    bot.logger.error(f"Error accessing raw event data: {e}")
                
                # For now, let's try to get users from the channel object
                users_dict = {}
                try:
                    if hasattr(channel, 'users') and callable(channel.users):
                        users_dict = channel.users()
                    
                    # If we got a dictionary, process it
                    if hasattr(users_dict, 'items'):
                        bot.logger.info(f"Users in channel {channel_name}: {list(users_dict.keys())}")
                except Exception as e:
                    bot.logger.error(f"Error getting users from channel object: {e}")
                
                # Process users if we have any
                if hasattr(users_dict, 'items'):
                    for nick, hostmask in users_dict.items():
                        # Skip the bot itself
                        if nick.lower() == bot.connection.get_nickname().lower():
                            bot.logger.info(f"Skipping bot: {nick}")
                            continue
                        
                        # If hostmask is None or empty, generate one
                        if not hostmask:
                            hostmask = f"{nick}!{nick}@{bot.connection.server}"
                            bot.logger.info(f"Generated hostmask for {nick}: {hostmask}")
                        
                        bot.logger.info(f"Adding user {nick} with hostmask {hostmask}")
                        all_users[nick] = hostmask
            except Exception as e:
                bot.logger.error(f"Error getting users from channel {channel_name}: {e}")
                import traceback
                bot.logger.error(f"Traceback: {traceback.format_exc()}")
        
        stats["total_users"] = len(all_users)
        bot.logger.info(f"Found {len(all_users)} users across all channels")
        
        # Process each user
        cur = bot.db_connection.cursor()
        
        for nickname, hostmask in all_users.items():
            try:
                bot.logger.info(f"Processing user: {nickname} with hostmask: {hostmask}")
                
                # Check if the user exists in the database by nickname
                cur.execute(
                    "SELECT id, username FROM phreakbot_users WHERE username ILIKE %s",
                    (nickname.lower(),)
                )
                user_by_name = cur.fetchone()
                
                # Check if the hostmask is associated with any user
                cur.execute(
                    "SELECT u.id, u.username FROM phreakbot_users u JOIN phreakbot_hostmasks h ON u.id = h.users_id WHERE h.hostmask ILIKE %s",
                    (hostmask.lower(),)
                )
                user_by_hostmask = cur.fetchone()
                
                # Case 1: User exists by name and hostmask matches the same user
                if user_by_name and user_by_hostmask and user_by_name[0] == user_by_hostmask[0]:
                    bot.logger.info(f"User {nickname} already registered with matching hostmask")
                    stats["already_registered"] += 1
                    continue
                
                # Case 2: User exists by name but hostmask doesn't match or is not registered
                if user_by_name and (not user_by_hostmask or user_by_name[0] != user_by_hostmask[0]):
                    # Merge the hostmask to the existing user
                    if user_by_hostmask:
                        bot.logger.info(f"Hostmask {hostmask} already associated with user {user_by_hostmask[1]}, skipping")
                        stats["skipped"] += 1
                        continue
                    
                    bot.logger.info(f"Merging hostmask {hostmask} to user {user_by_name[1]}")
                    cur.execute(
                        "INSERT INTO phreakbot_hostmasks (users_id, hostmask) VALUES (%s, %s)",
                        (user_by_name[0], hostmask.lower())
                    )
                    stats["merged_hostmasks"] += 1
                    continue
                
                # Case 3: User doesn't exist by name but hostmask is registered
                if not user_by_name and user_by_hostmask:
                    bot.logger.info(f"Nickname {nickname} not in database but hostmask {hostmask} is registered to {user_by_hostmask[1]}, skipping")
                    stats["skipped"] += 1
                    continue
                
                # Case 4: User doesn't exist by name or hostmask - register new user
                if not user_by_name and not user_by_hostmask:
                    bot.logger.info(f"Registering new user {nickname} with hostmask {hostmask}")
                    
                    # Create new user
                    cur.execute(
                        "INSERT INTO phreakbot_users (username) VALUES (%s) RETURNING id",
                        (nickname.lower(),)
                    )
                    user_id = cur.fetchone()[0]
                    
                    # Add hostmask
                    cur.execute(
                        "INSERT INTO phreakbot_hostmasks (users_id, hostmask) VALUES (%s, %s)",
                        (user_id, hostmask.lower())
                    )
                    
                    # Add user permission
                    cur.execute(
                        "INSERT INTO phreakbot_perms (users_id, permission) VALUES (%s, %s)",
                        (user_id, "user")
                    )
                    
                    stats["registered_new"] += 1
            
            except Exception as e:
                bot.logger.error(f"Error processing user {nickname}: {e}")
                stats["errors"] += 1
        
        # Commit all changes
        bot.db_connection.commit()
        cur.close()
        
        # Report results
        summary = (
            f"Mass meet complete! "
            f"Processed {stats['total_users']} users: "
            f"{stats['registered_new']} new registrations, "
            f"{stats['merged_hostmasks']} hostmasks merged, "
            f"{stats['already_registered']} already registered, "
            f"{stats['skipped']} skipped, "
            f"{stats['errors']} errors."
        )
        bot.add_response(summary)
        
    except Exception as e:
        bot.logger.error(f"Error in massmeet module: {e}")
        import traceback
        bot.logger.error(f"Traceback: {traceback.format_exc()}")
        bot.add_response("Error during mass meet process.")