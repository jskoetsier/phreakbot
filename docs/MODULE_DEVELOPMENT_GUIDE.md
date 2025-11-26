# PhreakBot Module Development Guide

PhreakBot is designed with a modular architecture that makes it easy to add new functionality. This guide explains how to create your own modules.

## Basic Module Structure

Modules are stored in the `modules` directory. Each module is a Python file with at least two functions:

1. `config(bot)` - Returns configuration information about the module
2. `run(bot, event)` - Handles events and commands

Here's a minimal module template:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Example module for PhreakBot

def config(bot):
    """Return module configuration"""
    return {
        "events": [],                # IRC events to listen for
        "commands": ["example"],     # Commands this module provides
        "permissions": ["user"],     # Permissions required to use this module
        "help": "An example module.\n"
                "Usage: !example - Shows an example message",
    }

def run(bot, event):
    """Handle events and commands"""
    # This function is called when a command or event is triggered
    bot.add_response("This is an example module!")
```

## The `config` Function

The `config` function returns a dictionary with the following keys:

- `events`: List of IRC events to listen for (e.g., "join", "part", "quit", "pubmsg", "privmsg")
- `commands`: List of commands the module provides (without the command prefix)
- `permissions`: List of permissions required to use the module (e.g., "user", "admin", "owner")
- `help`: Help text for the module, displayed when users type `!help <module>`

## The `run` Function

The `run` function handles events and commands. It receives two parameters:

- `bot`: The PhreakBot instance, providing access to the bot's API
- `event`: A dictionary containing information about the event or command

The `event` dictionary contains:

- `trigger`: Either "command" or "event"
- `command`: The command name (if trigger is "command")
- `command_args`: The command arguments (if trigger is "command")
- `signal`: The event type (if trigger is "event")
- `nick`: The nickname of the user who triggered the event
- `hostmask`: The hostmask of the user
- `channel`: The channel where the event occurred
- `text`: The full message text
- `user_info`: User information from the database (if available)

## Interacting with the Bot

The `bot` parameter provides access to the bot's API:

- `bot.add_response(message, private=False)`: Add a message to the output queue
- `bot.say(target, message)`: Send a message directly to a channel or user
- `bot.logger`: Logger for debugging and error messages
- `bot.db_connection`: Database connection for SQL queries
- `bot.channels`: Dictionary of IRC channels the bot is in
- `bot.connection`: IRC connection object
- `bot.config`: Bot configuration dictionary

## Example Modules

### 1. Simple Command Module

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Hello module for PhreakBot

def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["hello"],
        "permissions": ["user"],
        "help": "A friendly greeting module.\n"
                "Usage: !hello [name] - Greets you or the specified name",
    }

def run(bot, event):
    """Handle hello command"""
    if event["command_args"]:
        name = event["command_args"]
    else:
        name = event["nick"]

    bot.add_response(f"Hello, {name}!")
```

### 2. Event Handler Module

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Join greeter module for PhreakBot

def config(bot):
    """Return module configuration"""
    return {
        "events": ["join"],
        "commands": [],
        "permissions": ["user"],
        "help": "Automatically greets users when they join a channel",
    }

def run(bot, event):
    """Handle join events"""
    # Don't greet the bot itself
    if event["nick"] == bot.connection.get_nickname():
        return

    bot.add_response(f"Welcome to {event['channel']}, {event['nick']}!")
```

### 3. Database Module

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Last seen module for PhreakBot

import time

def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg", "join", "part", "quit"],
        "commands": ["seen"],
        "permissions": ["user"],
        "help": "Tracks when users were last seen.\n"
                "Usage: !seen <nickname> - Shows when a user was last seen",
    }

def run(bot, event):
    """Handle seen command and track user activity"""
    # Update last seen information for all events
    if bot.db_connection:
        try:
            cur = bot.db_connection.cursor()

            # Record the user's activity
            cur.execute(
                "INSERT INTO last_seen (nickname, channel, action, timestamp) "
                "VALUES (%s, %s, %s, %s)",
                (event["nick"], event["channel"], event["signal"], int(time.time()))
            )
            bot.db_connection.commit()
            cur.close()
        except Exception as e:
            bot.logger.error(f"Database error in last_seen module: {e}")

    # Handle the seen command
    if event["trigger"] == "command" and event["command"] == "seen":
        if not event["command_args"]:
            bot.add_response("Please specify a nickname to look up.")
            return

        nickname = event["command_args"].strip()

        if not bot.db_connection:
            bot.add_response("Database connection is not available.")
            return

        try:
            cur = bot.db_connection.cursor()
            cur.execute(
                "SELECT action, channel, timestamp FROM last_seen "
                "WHERE nickname = %s ORDER BY timestamp DESC LIMIT 1",
                (nickname.lower(),)
            )
            result = cur.fetchone()
            cur.close()

            if result:
                action, channel, timestamp = result
                time_ago = int(time.time()) - timestamp
                hours, remainder = divmod(time_ago, 3600)
                minutes, seconds = divmod(remainder, 60)

                if hours > 0:
                    time_str = f"{hours}h {minutes}m ago"
                elif minutes > 0:
                    time_str = f"{minutes}m {seconds}s ago"
                else:
                    time_str = f"{seconds}s ago"

                bot.add_response(f"{nickname} was last seen {action} in {channel} {time_str}")
            else:
                bot.add_response(f"I haven't seen {nickname}")
        except Exception as e:
            bot.logger.error(f"Database error in seen command: {e}")
            bot.add_response("Error retrieving last seen information.")
```

## Best Practices

1. **Error Handling**: Always use try-except blocks for database operations and other code that might fail.
2. **Logging**: Use `bot.logger` for debugging and error messages.
3. **Permissions**: Set appropriate permissions for your module.
4. **Help Text**: Provide clear and concise help text with usage examples.
5. **Code Organization**: Keep your module focused on a single responsibility.
6. **Input Validation**: Always validate user input before processing it.
7. **Resource Management**: Close database cursors and other resources when done.

## Testing Your Module

1. Place your module in the `modules` directory
2. Restart the bot or use the `!reload <module>` command
3. Test your module's functionality
4. Check the logs for any errors

## Advanced Features

- **State Management**: Use `bot.state` dictionary to store module-specific state
- **Regular Expressions**: Use `bot.re` for regex operations
- **Configuration**: Access bot configuration via `bot.config`
- **IRC Operations**: Use `bot.connection` for IRC operations like mode changes
