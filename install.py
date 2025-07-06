#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot Installation Script
# This script creates a default configuration file for PhreakBot

import argparse
import json
import os
import shutil
import sys


def create_config(args):
    """Create a default configuration file"""
    config = {
        "server": args.server,
        "port": args.port,
        "nickname": args.nickname,
        "realname": "PhreakBot IRC Bot",
        "channels": [args.channel],
        "owner": "",
        "trigger": "!",
        "max_output_lines": 3,
        "log_file": "phreakbot.log",
        # Database configuration
        "db_host": args.db_host,
        "db_port": args.db_port,
        "db_user": args.db_user,
        "db_password": args.db_password,
        "db_name": args.db_name,
    }

    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(args.config)), exist_ok=True)

    # Create the config file
    with open(args.config, "w") as f:
        json.dump(config, f, indent=4)

    print(f"Configuration file created: {args.config}")
    print(f"Server: {args.server}")
    print(f"Port: {args.port}")
    print(f"Nickname: {args.nickname}")
    print(f"Channel: {args.channel}")
    print(f"Command trigger: {config['trigger']}")
    print(f"Database: {args.db_host}:{args.db_port}/{args.db_name}")

    if args.docker:
        print("\nTo start the bot with Docker, run:")
        print("docker-compose up -d")
    else:
        print("\nTo start the bot, run:")
        print(f"python3 phreakbot.py -c {args.config}")

    print("\nWhen the bot connects, claim ownership by typing:")
    print("!owner *!<user>@<hostname>")
    print("(The bot will suggest an appropriate format based on your connection)")


def create_example_module():
    """Create an example module to demonstrate plugin development"""
    example_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "extra_modules"
    )
    os.makedirs(example_dir, exist_ok=True)

    example_path = os.path.join(example_dir, "example.py")
    with open(example_path, "w") as f:
        f.write(
            '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Example module for PhreakBot
# This demonstrates how to create a simple plugin

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
'''
        )
    print(f"Example module created: {example_path}")
    print("This module demonstrates how to create plugins for PhreakBot.")


def make_executable():
    """Make the main bot file executable"""
    bot_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phreakbot.py")
    if os.path.exists(bot_path):
        os.chmod(bot_path, 0o755)
        print(f"Made {bot_path} executable")


def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []

    try:
        import irc.bot

        print("IRC library found.")
    except ImportError:
        missing_deps.append("irc")

    try:
        import psycopg2

        print("PostgreSQL library found.")
    except ImportError:
        missing_deps.append("psycopg2-binary")

    if missing_deps:
        print("ERROR: Required libraries not found:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("Please install them with: pip install " + " ".join(missing_deps))
        print("or: pip install -r requirements.txt")
        return False

    return True


def create_requirements():
    """Create requirements.txt file"""
    with open("requirements.txt", "w") as f:
        f.write("irc>=20.0.0\n")
        f.write("psycopg2-binary>=2.9.3\n")
    print("Created requirements.txt file")


def create_docker_env_file(args):
    """Create .env file for Docker Compose"""
    env_content = f"""# PhreakBot Docker environment configuration
IRC_SERVER={args.server}
IRC_PORT={args.port}
IRC_NICKNAME={args.nickname}
IRC_CHANNEL={args.channel}

# Database configuration
POSTGRES_USER={args.db_user}
POSTGRES_PASSWORD={args.db_password}
POSTGRES_DB={args.db_name}
"""
    with open(".env", "w") as f:
        f.write(env_content)
    print("Created .env file for Docker Compose")


def main():
    parser = argparse.ArgumentParser(description="PhreakBot Installation Script")
    parser.add_argument(
        "-c", "--config", default="config.json", help="Path to config file"
    )
    parser.add_argument(
        "-s", "--server", default="irc.libera.chat", help="IRC server address"
    )
    parser.add_argument("-p", "--port", type=int, default=6667, help="IRC server port")
    parser.add_argument("-n", "--nickname", default="PhreakBot", help="Bot nickname")
    parser.add_argument(
        "-ch", "--channel", default="#phreakbot", help="Initial channel to join"
    )
    # Database options
    parser.add_argument(
        "--db-host", default="localhost", help="PostgreSQL server address"
    )
    parser.add_argument("--db-port", default="5432", help="PostgreSQL server port")
    parser.add_argument("--db-user", default="phreakbot", help="PostgreSQL username")
    parser.add_argument(
        "--db-password", default="phreakbot", help="PostgreSQL password"
    )
    parser.add_argument(
        "--db-name", default="phreakbot", help="PostgreSQL database name"
    )
    # Docker option
    parser.add_argument(
        "--docker", action="store_true", help="Configure for Docker environment"
    )

    args = parser.parse_args()

    print("PhreakBot Installation")
    print("=====================")

    # If Docker mode, adjust database host
    if args.docker:
        args.db_host = "postgres"  # Use the service name from docker-compose
        args.config = "/app/config/config.json"
        print("Configuring for Docker environment")
        create_docker_env_file(args)
    else:
        # Check dependencies only for non-Docker installation
        if not check_dependencies():
            create_requirements()
            print("Please install the required dependencies and run this script again.")
            sys.exit(1)

    # Create config file
    create_config(args)

    # Create example module
    create_example_module()

    # Make bot executable (not needed for Docker)
    if not args.docker:
        make_executable()

    print("\nInstallation complete!")


if __name__ == "__main__":
    main()
