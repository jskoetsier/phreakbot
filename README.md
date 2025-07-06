# PhreakBot

PhreakBot is a modular IRC bot written in Python. It's designed to be easy to set up and extend with custom plugins.

This is a modular IRC bot that uses its own Python libraries for IRC connectivity.

## Features

- Standalone IRC connectivity using the `irc` Python library
- Modular plugin system
- Easy installation with configuration wizard
- Simple permission system
- Customizable command trigger
- PostgreSQL database integration
- Docker support for easy deployment
- Logging support

## Installation

### Requirements

- Python 3.6 or higher
- `irc` Python library
- `psycopg2-binary` Python library (for PostgreSQL support)
- Docker and Docker Compose (for Docker installation)

### Docker Installation (Recommended)

The easiest way to run PhreakBot is using Docker and Docker Compose:

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/phreakbot.git
   cd phreakbot
   ```

2. Create a `.env` file with your configuration or use the installation script:
   ```bash
   python install.py --docker
   ```

3. Start the bot using Docker Compose:
   ```bash
   docker-compose up -d
   ```

4. When the bot connects to IRC, claim ownership by typing in the IRC channel:
   ```
   !owner *!<user>@<hostname>
   ```
   (The bot will suggest an appropriate format based on your connection)

5. To view logs:
   ```bash
   docker-compose logs -f phreakbot
   ```

6. To stop the bot:
   ```bash
   docker-compose down
   ```

### Automatic Setup (Non-Docker)

If you prefer to run without Docker, you can use the provided setup scripts:

#### On Linux/macOS:
```bash
# Clone the repository
git clone https://github.com/yourusername/phreakbot.git
cd phreakbot

# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

#### On Windows:
```
# Clone the repository
git clone https://github.com/yourusername/phreakbot.git
cd phreakbot

# Run the setup script
setup.bat
```

These scripts will:
1. Check if Python is installed with the correct version
2. Install the required Python packages
3. Create necessary directories
4. Run the installation script to create a configuration file

### Manual Setup

If you prefer to set up manually:

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/phreakbot.git
   cd phreakbot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the installation script:
   ```
   python install.py
   ```

   This will create a default configuration file and set up the bot.

4. Start the bot:
   ```
   python phreakbot.py
   ```

5. When the bot connects to IRC, claim ownership by typing in the IRC channel:
   ```
   !owner *!<user>@<hostname>
   ```
   (The bot will suggest an appropriate format based on your connection)

### Custom Installation

You can customize the installation by providing arguments to the installation script:

```
python install.py --server irc.example.com --port 6667 --nickname MyBot --channel "#mychannel" --db-host localhost --db-user phreakbot --db-password secret
```

Run `python install.py --help` for a full list of options.

## Configuration

The configuration is stored in a JSON file (default: `config.json`). You can edit this file directly to change the bot's settings:

```json
{
    "server": "irc.libera.chat",
    "port": 6667,
    "nickname": "PhreakBot",
    "realname": "PhreakBot IRC Bot",
    "channels": ["#phreakbot"],
    "owner": "",
    "trigger": "!",
    "max_output_lines": 3,
    "log_file": "phreakbot.log",
    "db_host": "localhost",
    "db_port": "5432",
    "db_user": "phreakbot",
    "db_password": "phreakbot",
    "db_name": "phreakbot"
}
```

### IRC Configuration
- `server`: IRC server address
- `port`: IRC server port
- `nickname`: Bot's nickname
- `realname`: Bot's real name
- `channels`: List of channels to join
- `owner`: Owner's hostmask in format `*!<user>@<hostname>` (set when claiming ownership)
- `trigger`: Command trigger character (default: `!`)
- `max_output_lines`: Maximum number of lines to send to the channel
- `log_file`: Path to log file

### Database Configuration
- `db_host`: PostgreSQL server address
- `db_port`: PostgreSQL server port
- `db_user`: PostgreSQL username
- `db_password`: PostgreSQL password
- `db_name`: PostgreSQL database name

## Docker Configuration

When using Docker, you can configure the bot using environment variables in a `.env` file or by passing them to the `docker-compose up` command:

```
# IRC Configuration
IRC_SERVER=irc.libera.chat
IRC_PORT=6667
IRC_NICKNAME=PhreakBot
IRC_CHANNEL=#phreakbot

# Database Configuration
POSTGRES_USER=phreakbot
POSTGRES_PASSWORD=phreakbot
POSTGRES_DB=phreakbot
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

When using Docker, these directories are mounted as volumes, so you can add or modify plugins without rebuilding the container.

## Available Commands

The bot comes with several built-in commands:

- `!help [module]`: Show help for a module
- `!avail`: List all available modules
- `!owner *!<user>@<hostname>`: Claim ownership of the bot or show current owner

## License

This project is licensed under the GPL v3 License - see the LICENSE file for details.

## Acknowledgments

- Created by PhreakBot Team
