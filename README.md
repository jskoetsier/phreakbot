# PhreakBot (v0.1.6)

PhreakBot is a modular IRC bot written in Python.

## Features

- Modular design with easy-to-add modules
- Permission system with owner, admin, and user levels
- Quote database with search functionality
- URL title and description fetching
- Channel management (join, part, topic)
- User registration and management
- Auto-op functionality
- CTCP version support
- Robust error handling and logging
- And more!

## Installation

### Docker (Recommended)

1. Clone the repository
2. Run `docker-compose up -d`

### Manual Installation

1. Clone the repository
2. Install the required dependencies: `pip install -r requirements.txt`
3. Set up a PostgreSQL database
4. Run the SQL in `dbschema.psql` to create the necessary tables
5. Configure the bot by editing `config.json`
6. Run the bot: `python phreakbot.py`

## Configuration

Edit `config.json` to configure the bot:

```json
{
    "server": "irc.example.com",
    "port": 6667,
    "nickname": "PhreakBot",
    "realname": "PhreakBot",
    "channels": ["#channel1", "#channel2"],
    "command_trigger": "!"
}
```

## Setting Up Ownership

When the bot first starts, use the `!owner claim` command to claim ownership of the bot. This will grant you admin privileges and allow you to manage the bot.

## Module Development

Modules are stored in the `modules` directory. Each module should have a `config` function that returns a dictionary with the following keys:

- `events`: List of IRC events to listen for
- `commands`: List of commands the module provides
- `permissions`: List of permissions required to use the module
- `help`: Help text for the module

For detailed information on how to create your own modules, see the [Module Development Guide](MODULE_DEVELOPMENT_GUIDE.md).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
