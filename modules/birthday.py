#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Birthday module for PhreakBot

import datetime
import re


def config(bot):
    """Return module configuration"""
    return {
        "events": ["join"],  # Check birthdays when users join
        "commands": ["bd", "bd-set"],
        "permissions": ["user"],
        "help": "Birthday management and notifications.\n"
        "Usage: !bd - List upcoming birthdays\n"
        "       !bd <nickname> - Show a specific user's birthday\n"
        "       !bd-set DD-MM-YYYY - Set your own birthday\n"
        "       !bd-today - Show today's birthdays",
    }


def run(bot, event):
    """Handle birthday commands and events"""
    # Handle commands
    if event["trigger"] == "command":
        if event["command"] == "bd-set":
            _set_birthday(bot, event)
        elif event["command"] == "bd":
            _show_birthdays(bot, event)
    
    # Handle events - check for birthdays when users join
    elif event["trigger"] == "event" and event["signal"] == "join":
        # Only check once per day per channel when the bot joins
        if event["nick"] == bot.connection.get_nickname():
            _check_todays_birthdays(bot, event["channel"])


def _set_birthday(bot, event):
    """Set a user's birthday"""
    # Check if the user is registered
    if not event["user_info"]:
        bot.add_response("You need to be a registered user to set your birthday. Use !meet to register.")
        return

    # Get the date from the command arguments
    date_str = event["command_args"].strip()
    
    # Validate the date format (DD-MM-YYYY)
    if not re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
        bot.add_response("Invalid date format. Please use DD-MM-YYYY format (e.g., 31-12-1990).")
        return
    
    try:
        # Parse the date
        day, month, year = map(int, date_str.split("-"))
        dob = datetime.date(year, month, day)
        
        # Check if the date is valid and not in the future
        today = datetime.date.today()
        if dob > today:
            bot.add_response("Birthday cannot be in the future.")
            return
        
        # Update the user's birthday in the database
        if bot.db_connection:
            try:
                cur = bot.db_connection.cursor()
                cur.execute(
                    "UPDATE phreakbot_users SET dob = %s WHERE id = %s",
                    (dob, event["user_info"]["id"])
                )
                bot.db_connection.commit()
                cur.close()
                
                bot.add_response(f"Your birthday has been set to {dob.strftime('%d-%m-%Y')}.")
            except Exception as e:
                bot.logger.error(f"Database error in birthday module: {e}")
                bot.add_response("Error updating your birthday in the database.")
        else:
            bot.add_response("Database connection is not available.")
    except ValueError:
        bot.add_response("Invalid date. Please provide a valid date in DD-MM-YYYY format.")


def _show_birthdays(bot, event):
    """Show birthdays"""
    if not bot.db_connection:
        bot.add_response("Database connection is not available.")
        return
    
    args = event["command_args"].strip()
    
    try:
        cur = bot.db_connection.cursor()
        
        # If a nickname is provided, show that user's birthday
        if args:
            cur.execute(
                "SELECT username, dob FROM phreakbot_users WHERE username ILIKE %s AND dob IS NOT NULL",
                (args,)
            )
            user = cur.fetchone()
            
            if user:
                username, dob = user
                bot.add_response(f"{username}'s birthday is on {dob.strftime('%d-%m-%Y')}.")
            else:
                bot.add_response(f"No birthday information found for '{args}'.")
        
        # Otherwise, show upcoming birthdays
        else:
            today = datetime.date.today()
            
            # Get users with birthdays in the next 30 days
            cur.execute(
                """
                SELECT username, dob,
                       EXTRACT(DAY FROM dob) as day,
                       EXTRACT(MONTH FROM dob) as month
                FROM phreakbot_users
                WHERE dob IS NOT NULL
                ORDER BY 
                    EXTRACT(MONTH FROM dob),
                    EXTRACT(DAY FROM dob)
                """
            )
            
            users = cur.fetchall()
            
            if users:
                upcoming = []
                today_month = today.month
                today_day = today.day
                
                for username, dob, day, month in users:
                    # Calculate days until next birthday
                    next_birthday = datetime.date(today.year, int(month), int(day))
                    if next_birthday < today:
                        next_birthday = datetime.date(today.year + 1, int(month), int(day))
                    
                    days_until = (next_birthday - today).days
                    
                    if days_until <= 30:
                        age = today.year - dob.year
                        if today < datetime.date(today.year, dob.month, dob.day):
                            age -= 1
                        
                        upcoming.append((username, dob, days_until, age + 1))
                
                if upcoming:
                    # Sort by days until birthday
                    upcoming.sort(key=lambda x: x[2])
                    
                    bot.add_response("Upcoming birthdays in the next 30 days:")
                    for username, dob, days, next_age in upcoming:
                        if days == 0:
                            bot.add_response(f"🎂 TODAY: {username} turns {next_age} today! 🎉")
                        else:
                            bot.add_response(f"In {days} days: {username} will turn {next_age} on {dob.strftime('%d-%m')}.")
                else:
                    bot.add_response("No upcoming birthdays in the next 30 days.")
            else:
                bot.add_response("No birthdays have been set yet.")
        
        cur.close()
    
    except Exception as e:
        bot.logger.error(f"Database error in birthday module: {e}")
        bot.add_response("Error retrieving birthday information.")


def _check_todays_birthdays(bot, channel):
    """Check for birthdays today and send congratulations"""
    if not bot.db_connection:
        return
    
    try:
        today = datetime.date.today()
        
        cur = bot.db_connection.cursor()
        cur.execute(
            """
            SELECT username, dob
            FROM phreakbot_users
            WHERE 
                dob IS NOT NULL AND
                EXTRACT(DAY FROM dob) = %s AND
                EXTRACT(MONTH FROM dob) = %s
            """,
            (today.day, today.month)
        )
        
        birthday_users = cur.fetchall()
        cur.close()
        
        if birthday_users:
            bot.add_response(f"🎂 Today's Birthdays 🎂", private=False)
            
            for username, dob in birthday_users:
                age = today.year - dob.year
                bot.add_response(f"Happy {age}th Birthday to {username}! 🎉🎈🎁", private=False)
    
    except Exception as e:
        bot.logger.error(f"Error checking today's birthdays: {e}")
