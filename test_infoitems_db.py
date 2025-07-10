#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Test script to directly interact with the phreakbot_infoitems table
# This bypasses the bot entirely and just tests the database functionality

import os
import psycopg2
import sys

def main():
    print("PhreakBot InfoItems Database Test")
    print("================================")

    # Connect to the database
    try:
        print("Connecting to database...")
        db_connection = psycopg2.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=os.environ.get("DB_PORT", "5432"),
            user=os.environ.get("DB_USER", "phreakbot"),
            password=os.environ.get("DB_PASSWORD", "phreakbot"),
            dbname=os.environ.get("DB_NAME", "phreakbot"),
        )
        print("Connected to database successfully!")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Get user ID
    try:
        print("\nFinding user ID for 'phreak'...")
        cur = db_connection.cursor()
        cur.execute("SELECT id FROM phreakbot_users WHERE username = %s", ("phreak",))
        user_id = cur.fetchone()

        if not user_id:
            print("User 'phreak' not found in database!")
            sys.exit(1)

        user_id = user_id[0]
        print(f"Found user ID: {user_id}")
    except Exception as e:
        print(f"Error finding user ID: {e}")
        sys.exit(1)

    # Test inserting an info item
    try:
        print("\nInserting test info item 'phreak = gek' in channel '#test'...")
        cur = db_connection.cursor()

        # First check if it already exists
        cur.execute(
            "SELECT id FROM phreakbot_infoitems WHERE item = %s AND value = %s AND channel = %s",
            ("phreak", "gek", "#test")
        )

        if cur.fetchone():
            print("Info item already exists, skipping insert.")
        else:
            cur.execute(
                "INSERT INTO phreakbot_infoitems (users_id, item, value, channel) VALUES (%s, %s, %s, %s) RETURNING id",
                (user_id, "phreak", "gek", "#test")
            )
            item_id = cur.fetchone()[0]
            db_connection.commit()
            print(f"Inserted info item with ID: {item_id}")
    except Exception as e:
        print(f"Error inserting info item: {e}")
        db_connection.rollback()

    # Test retrieving info items
    try:
        print("\nRetrieving all 'phreak' info items from channel '#test'...")
        cur = db_connection.cursor()
        cur.execute(
            "SELECT i.id, i.value, u.username, i.insert_time FROM phreakbot_infoitems i "
            "JOIN phreakbot_users u ON i.users_id = u.id "
            "WHERE i.item = %s AND i.channel = %s "
            "ORDER BY i.insert_time",
            ("phreak", "#test")
        )

        items = cur.fetchall()

        if not items:
            print("No info items found for 'phreak' in channel '#test'.")
        else:
            print(f"Found {len(items)} info items:")
            for item_id, value, username, timestamp in items:
                print(f"• ID: {item_id}, Value: '{value}', Added by: {username}, Date: {timestamp.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error retrieving info items: {e}")

    # Test retrieving info items from all channels
    try:
        print("\nRetrieving all 'phreak' info items from all channels...")
        cur = db_connection.cursor()
        cur.execute(
            "SELECT i.id, i.value, i.channel, u.username, i.insert_time FROM phreakbot_infoitems i "
            "JOIN phreakbot_users u ON i.users_id = u.id "
            "WHERE i.item = %s "
            "ORDER BY i.channel, i.insert_time",
            ("phreak",)
        )

        items = cur.fetchall()

        if not items:
            print("No info items found for 'phreak' in any channel.")
        else:
            print(f"Found {len(items)} info items across all channels:")
            for item_id, value, channel, username, timestamp in items:
                print(f"• ID: {item_id}, Channel: {channel}, Value: '{value}', Added by: {username}, Date: {timestamp.strftime('%Y-%m-%d')}")
    except Exception as e:
        print(f"Error retrieving info items: {e}")

    # Close the database connection
    db_connection.close()
    print("\nTest completed.")

if __name__ == "__main__":
    main()
