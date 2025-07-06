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
        "trigger": "!",
        "max_output_lines": 3,
        "log_file": "phreakbot.log",
        # Database configuration
        "db_host": args.db_host,
        "db_port": args.db_port,
        "db_user": args.db_user,
        "db_password": args.db_password,
        "db_name": args.db_name,
        # Remote deployment configuration
        "remote_ssh_command": args.remote_ssh,
        "remote_directory": args.remote_dir,
    }

    # Add owner to config for backward compatibility if specified
    if args.owner and args.owner != "*!user@host":
        config["owner"] = args.owner

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
    print(f"Bot owner: {args.owner}")
    print(
        "The owner is set in the configuration file and cannot be changed through commands."
    )


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


def check_docker_environment():
    """Check if running in Docker environment"""
    # Check for common Docker environment indicators
    if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
        return True

    # Check if running in the expected Docker path structure
    if os.path.exists("/app/phreakbot.py"):
        return True

    return False


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
    parser.add_argument(
        "-o", "--owner", default="*!user@host", help="Bot owner in format *!user@host"
    )
    # Database options
    parser.add_argument(
        "--db-host", default="postgres", help="PostgreSQL server address"
    )
    parser.add_argument("--db-port", default="5432", help="PostgreSQL server port")
    parser.add_argument("--db-user", default="phreakbot", help="PostgreSQL username")
    parser.add_argument(
        "--db-password", default="phreakbot", help="PostgreSQL password"
    )
    parser.add_argument(
        "--db-name", default="phreakbot", help="PostgreSQL database name"
    )
    # Remote deployment options
    parser.add_argument(
        "--remote-ssh",
        default="",
        help="SSH command for remote deployment (e.g., 'ssh user@server')",
    )
    parser.add_argument(
        "--remote-dir",
        default="/opt/phreakbot",
        help="Remote directory path for deployment",
    )
    # Docker option (kept for backward compatibility)
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Configure for Docker environment",
        default=True,
    )
    # Force non-Docker option (for testing only)
    parser.add_argument(
        "--force-non-docker", action="store_true", help=argparse.SUPPRESS
    )

    args = parser.parse_args()

    print("PhreakBot Installation")
    print("=====================")

    # Check if running in Docker environment
    if not check_docker_environment() and not args.force_non_docker:
        print("\n⚠️  WARNING: PhreakBot is designed to run exclusively in Docker.")
        print("This script should be run inside the Docker container.")
        print("Please use the install-docker.sh or install-docker.bat script instead.")
        print(
            "\nIf you want to continue anyway (not recommended), run with --force-non-docker"
        )
        sys.exit(1)

    # Set Docker-specific configuration
    args.db_host = "postgres"  # Use the service name from docker-compose
    if check_docker_environment():
        args.config = "/app/config/config.json"

    print("Configuring for Docker environment")

    # Create config file
    create_config(args)

    # Create example module
    create_example_module()

    print("\nInstallation complete!")


if __name__ == "__main__":
    main()
