#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Snarf module for PhreakBot
#
# This module implements functionality similar to gozerbot's snarf function,
# allowing the bot to respond to specific patterns in chat messages without
# requiring a command prefix.

import re
import json
import os


def config(pb):
    """Return module configuration"""
    return {
        "events": ["pubmsg"],  # Listen for public messages
        "commands": ["snarf", "addsnarf", "delsnarf", "listsnarf"],
        "permissions": ["user", "snarf"],
        "help": "Respond to specific patterns in chat messages.\n"
                "Usage: !snarf - Show snarf status\n"
                "       !addsnarf <pattern> <response> - Add a new snarf pattern (admin/snarf permission)\n"
                "       !delsnarf <pattern> - Delete a snarf pattern (admin/snarf permission)\n"
                "       !listsnarf - List all snarf patterns",
    }


def run(pb, event):
    """Handle snarf events and commands"""
    # Handle commands
    if event["trigger"] == "command":
        if event["command"] == "snarf":
            _show_snarf_status(pb, event)
        elif event["command"] == "addsnarf":
            _add_snarf(pb, event)
        elif event["command"] == "delsnarf":
            _delete_snarf(pb, event)
        elif event["command"] == "listsnarf":
            _list_snarfs(pb, event)
        return

    # Handle chat messages (snarf functionality)
    if event["trigger"] == "event" and event["signal"] == "pubmsg":
        _process_message(pb, event)


def _show_snarf_status(pb, event):
    """Show the current status of the snarf module"""
    snarfs = _load_snarfs(pb)
    pb.add_response(f"Snarf module is active with {len(snarfs)} patterns.")
    pb.add_response("Use !listsnarf to see all patterns, !addsnarf to add a new pattern, or !delsnarf to remove a pattern.")


def _add_snarf(pb, event):
    """Add a new snarf pattern"""
    # Check if the user has permission to add snarfs
    has_permission = _check_snarf_permission(pb, event)
    if not has_permission:
        pb.add_response("You don't have permission to add snarf patterns.")
        return

    # Parse the command arguments
    args = event["command_args"]
    if not args:
        pb.add_response("Usage: !addsnarf <pattern> <response>")
        return

    # Split the first word as the pattern and the rest as the response
    parts = args.split(None, 1)
    if len(parts) < 2:
        pb.add_response("Usage: !addsnarf <pattern> <response>")
        return

    pattern, response = parts

    # Validate the pattern (try to compile it as a regex)
    try:
        re.compile(pattern)
    except re.error:
        pb.add_response(f"Invalid regex pattern: {pattern}")
        return

    # Load existing snarfs
    snarfs = _load_snarfs(pb)

    # Check if the pattern already exists
    if pattern in snarfs:
        pb.add_response(f"Pattern '{pattern}' already exists with response: {snarfs[pattern]}")
        return

    # Add the new pattern
    snarfs[pattern] = response
    _save_snarfs(pb, snarfs)

    pb.add_response(f"Added snarf pattern: '{pattern}' -> '{response}'")


def _delete_snarf(pb, event):
    """Delete a snarf pattern"""
    # Check if the user has permission to delete snarfs
    has_permission = _check_snarf_permission(pb, event)
    if not has_permission:
        pb.add_response("You don't have permission to delete snarf patterns.")
        return

    # Parse the command arguments
    pattern = event["command_args"]
    if not pattern:
        pb.add_response("Usage: !delsnarf <pattern>")
        return

    # Load existing snarfs
    snarfs = _load_snarfs(pb)

    # Check if the pattern exists
    if pattern not in snarfs:
        pb.add_response(f"Pattern '{pattern}' not found.")
        return

    # Delete the pattern
    response = snarfs.pop(pattern)
    _save_snarfs(pb, snarfs)

    pb.add_response(f"Deleted snarf pattern: '{pattern}' -> '{response}'")


def _list_snarfs(pb, event):
    """List all snarf patterns"""
    snarfs = _load_snarfs(pb)

    if not snarfs:
        pb.add_response("No snarf patterns defined.")
        return

    pb.add_response(f"Found {len(snarfs)} snarf patterns:")
    for pattern, response in snarfs.items():
        pb.add_response(f"'{pattern}' -> '{response}'")


def _process_message(pb, event):
    """Process a chat message and check for snarf patterns"""
    # Don't process messages from the bot itself
    if event["nick"] == pb.connection.get_nickname():
        return

    # Get the message text
    message = event["text"]

    # Load snarfs
    snarfs = _load_snarfs(pb)

    # Check each pattern
    for pattern, response in snarfs.items():
        try:
            # Try to match the pattern
            if re.search(pattern, message, re.IGNORECASE):
                # Send the response
                pb.say(event["channel"], response)
                # Only match one pattern per message
                break
        except re.error:
            # Log invalid patterns but don't crash
            pb.logger.error(f"Invalid regex pattern in snarf: {pattern}")


def _check_snarf_permission(pb, event):
    """Check if the user has permission to manage snarfs"""
    # Owner and admins always have permission
    if pb._is_owner(event["hostmask"]):
        return True

    # Check for snarf permission
    if event["user_info"] and (
        "snarf" in event["user_info"]["permissions"]["global"]
        or event["user_info"].get("is_admin")
    ):
        return True

    return False


def _load_snarfs(pb):
    """Load snarf patterns from the database or file"""
    # Try to load from database first
    if pb.db_connection:
        try:
            cur = pb.db_connection.cursor()
            cur.execute("SELECT pattern, response FROM phreakbot_snarfs")
            snarfs = {row[0]: row[1] for row in cur.fetchall()}
            cur.close()
            return snarfs
        except Exception as e:
            pb.logger.error(f"Error loading snarfs from database: {e}")
            # Fall back to file-based storage

    # File-based storage as fallback
    snarf_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "snarfs.json")

    # Create the data directory if it doesn't exist
    os.makedirs(os.path.dirname(snarf_file), exist_ok=True)

    try:
        if os.path.exists(snarf_file):
            with open(snarf_file, "r") as f:
                return json.load(f)
    except Exception as e:
        pb.logger.error(f"Error loading snarfs from file: {e}")

    return {}


def _save_snarfs(pb, snarfs):
    """Save snarf patterns to the database or file"""
    # Try to save to database first
    if pb.db_connection:
        try:
            cur = pb.db_connection.cursor()

            # Check if the table exists
            try:
                cur.execute("SELECT 1 FROM phreakbot_snarfs LIMIT 1")
            except Exception:
                # Create the table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS phreakbot_snarfs (
                        id SERIAL PRIMARY KEY,
                        pattern TEXT NOT NULL UNIQUE,
                        response TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                pb.db_connection.commit()

            # Clear existing snarfs
            cur.execute("DELETE FROM phreakbot_snarfs")

            # Insert new snarfs
            for pattern, response in snarfs.items():
                cur.execute(
                    "INSERT INTO phreakbot_snarfs (pattern, response) VALUES (%s, %s)",
                    (pattern, response)
                )

            pb.db_connection.commit()
            cur.close()
            return
        except Exception as e:
            pb.logger.error(f"Error saving snarfs to database: {e}")
            # Fall back to file-based storage

    # File-based storage as fallback
    snarf_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "snarfs.json")

    # Create the data directory if it doesn't exist
    os.makedirs(os.path.dirname(snarf_file), exist_ok=True)

    try:
        with open(snarf_file, "w") as f:
            json.dump(snarfs, f, indent=2)
    except Exception as e:
        pb.logger.error(f"Error saving snarfs to file: {e}")
