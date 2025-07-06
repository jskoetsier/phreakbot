# PhreakBot

PhreakBot is a modular IRC bot written in Python. It's designed to be easy to set up and extend with custom plugins.

This is a modular IRC bot that runs exclusively in Docker, providing a consistent and isolated environment across different operating systems.

## Features

- Standalone IRC connectivity using the `irc` Python library
- Modular plugin system
- Easy installation with Docker configuration wizard
- Simple permission system
- Customizable command trigger
- PostgreSQL database integration (included in Docker setup)
- Logging support
- Cross-platform compatibility through Docker

## Installation

### Requirements

- Docker (https://docs.docker.com/get-docker/)
- Docker Compose (https://docs.docker.com/compose/install/)

### Docker Installation

PhreakBot runs exclusively in Docker for consistent deployment across all platforms:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/phreakbot.git
   cd phreakbot
   ```

2. Run the installation script:

   **On Linux/macOS:**
   ```bash
   chmod +x install-docker.sh
   ./install-docker.sh
   ```

   **On Windows:**
   ```
   install-docker.bat
   ```

3. The installation script will:
   - Check if Docker and Docker Compose are installed
   - Prompt for IRC server, port, nickname, channel, and owner hostmask
   - Configure the database settings
   - Create the necessary configuration files
   - Build and start the Docker containers

4. The bot will connect to IRC with the owner already set in the configuration file.

5. To view logs:
   ```bash
   docker-compose logs -f phreakbot
   ```

6. To stop the bot:
   ```bash
   docker-compose down
   ```

7. To start the bot again:
   ```bash
   docker-compose up -d
   ```

## Configuration

The configuration is managed through environment variables in the `.env` file created during installation. You can edit this file directly to change the bot's settings:

```
# IRC Configuration
IRC_SERVER=irc.libera.chat
IRC_PORT=6667
IRC_NICKNAME=PhreakBot
IRC_CHANNEL=#phreakbot
OWNER_HOSTMASK=*!user@host

# Database Configuration
POSTGRES_USER=phreakbot
POSTGRES_PASSWORD=phreakbot
POSTGRES_DB=phreakbot
```

### Configuration Options

#### IRC Configuration
- `IRC_SERVER`: IRC server address
- `IRC_PORT`: IRC server port
- `IRC_NICKNAME`: Bot's nickname
- `IRC_CHANNEL`: Default channel to join
- `OWNER_HOSTMASK`: Owner's hostmask in format `*!<user>@<hostname>` (e.g., `*!john@example.com` or `*!*@192.168.1.100`)

#### Database Configuration
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `POSTGRES_DB`: PostgreSQL database name

After changing the configuration, restart the containers to apply the changes:
```bash
docker-compose down
docker-compose up -d
```

## Creating Plugins

Plugins (or modules) are Python files that define two functions:

1. `config(bot)`: Returns a dictionary with module configuration
2. `run(bot, event)`: Handles commands and events

### Example Plugin

```python
def config(bot):
    """Return module configuration"""
    return {
        'events': ['join'],  # Listen for join events
        'commands': ['hello', 'echo'],  # Respond to !hello and !echo commands
        'permissions': ['user'],  # Any user can use these commands
        'help': "Example module that demonstrates how to create plugins. Commands: !hello, !echo <text>"
    }

def run(bot, event):
    """Handle commands and events"""
    # Handle commands
    if event['trigger'] == 'command':
        if event['command'] == 'hello':
            bot.add_response(f"Hello, {event['nick']}!")
            return

        elif event['command'] == 'echo':
            if event['command_args']:
                bot.add_response(f"Echo: {event['command_args']}")
            else:
                bot.reply("Please provide some text to echo")
            return

    # Handle events
    elif event['trigger'] == 'event' and event['signal'] == 'join':
        # Someone joined the channel
        if event['nick'] != bot.connection.get_nickname():  # Don't greet ourselves
            bot.add_response(f"Welcome to {event['channel']}, {event['nick']}!")
            return
```

### Plugin Structure

- `config(bot)`: Returns a dictionary with the following keys:
  - `events`: List of IRC events to listen for (e.g., 'join', 'part', 'pubmsg', 'privmsg')
  - `commands`: List of commands this module handles (without the trigger character)
  - `permissions`: List of permissions required to use this module
  - `help`: Help text for this module

- `run(bot, event)`: Handles commands and events
  - `bot`: The bot instance
  - `event`: Dictionary containing event information

### Plugin API

The bot provides several methods for plugins to use:

- `bot.add_response(message, private=False)`: Add a message to the output queue
- `bot.reply(message)`: Add a reply message to the output queue (includes the user's nickname)
- `bot.say(target, message)`: Send a message directly to a channel or user

### Plugin Location

Plugins can be placed in two locations:

1. `modules/`: Core modules
2. `extra_modules/`: User-created modules

These directories are mounted as volumes in the Docker container, so you can add or modify plugins without rebuilding the container.

## Available Commands

The bot comes with several built-in commands:

- `!help [module]`: Show help for a module
- `!avail`: List all available modules
- `!owner`: Show the current bot owner (set in the configuration file)

## Updating PhreakBot

To update PhreakBot to the latest version:

1. Pull the latest changes from the repository:
   ```bash
   git pull
   ```

2. Rebuild and restart the Docker containers:
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

## License

This project is licensed under the GPL v3 License - see the LICENSE file for details.

## Acknowledgments

- Created by PhreakBot Team
