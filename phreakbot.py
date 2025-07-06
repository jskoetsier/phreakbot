#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot - A modular IRC bot
#
import argparse
import importlib.util
import json
import logging
import os
import random
import re
import sys
from datetime import datetime

# IRC library
import irc.bot
import irc.client
import irc.strings

# Database library
import psycopg2
import psycopg2.extras


class PhreakBot(irc.bot.SingleServerIRCBot):
    def __init__(self, config_path):
        self.config_path = config_path
        self.load_config()

        # Initialize bot state
        self.modules = {}
        self.output = []
        self.db_connection = None
        self.re = re  # Expose re module for modules to use
        self.state = {}  # State dictionary for modules to use

        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.config.get("log_file", "phreakbot.log")),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("PhreakBot")

        # Connect to database
        self.db_connect()

        # Connect to IRC server
        self.logger.info(f"Connecting to {self.config['server']}:{self.config['port']}")
        irc.bot.SingleServerIRCBot.__init__(
            self,
            [(self.config["server"], self.config["port"])],
            self.config["nickname"],
            self.config["realname"],
        )

        # Load modules
        self.bot_base = os.path.dirname(os.path.abspath(__file__))
        self.modules_dir = os.path.join(self.bot_base, "phreakbot_core", "modules")
        self.extra_modules_dir = os.path.join(
            self.bot_base, "phreakbot_core", "extra_modules"
        )

        # Create directories if they don't exist
        for path in [self.modules_dir, self.extra_modules_dir]:
            if not os.path.exists(path):
                os.makedirs(path)
                self.logger.info(f"Created directory: {path}")

        # Load all modules
        self.load_all_modules()

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)

            # Set default values for missing config options
            if "server" not in self.config:
                self.config["server"] = "irc.libera.chat"
            if "port" not in self.config:
                self.config["port"] = 6667
            if "nickname" not in self.config:
                self.config["nickname"] = "PhreakBot"
            if "realname" not in self.config:
                self.config["realname"] = "PhreakBot IRC Bot"
            if "channels" not in self.config:
                self.config["channels"] = ["#phreakbot"]
            if "owner" not in self.config:
                self.config["owner"] = ""
            if "trigger" not in self.config:
                self.config["trigger"] = "!"
            if "max_output_lines" not in self.config:
                self.config["max_output_lines"] = 3

            # Database configuration - use environment variables if available
            if "db_host" not in self.config:
                self.config["db_host"] = os.environ.get("DB_HOST", "localhost")
            if "db_port" not in self.config:
                self.config["db_port"] = os.environ.get("DB_PORT", "5432")
            if "db_user" not in self.config:
                self.config["db_user"] = os.environ.get("DB_USER", "phreakbot")
            if "db_password" not in self.config:
                self.config["db_password"] = os.environ.get("DB_PASSWORD", "phreakbot")
            if "db_name" not in self.config:
                self.config["db_name"] = os.environ.get("DB_NAME", "phreakbot")

        except FileNotFoundError:
            self.logger.error(f"Config file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError:
            self.logger.error(f"Invalid JSON in config file: {self.config_path}")
            sys.exit(1)

    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")

    def db_connect(self):
        """Connect to the PostgreSQL database"""
        try:
            self.logger.info(
                f"Connecting to database at {self.config['db_host']}:{self.config['db_port']}"
            )
            self.db_connection = psycopg2.connect(
                host=self.config["db_host"],
                port=self.config["db_port"],
                user=self.config["db_user"],
                password=self.config["db_password"],
                dbname=self.config["db_name"],
            )
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            # Don't exit, allow the bot to run without database functionality
            self.db_connection = None

    def db_get_userinfo_by_userhost(self, host):
        """Get user information from the database by hostmask"""
        if not self.db_connection:
            return None

        ret = {}
        host = host.lower()

        try:
            cur = self.db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Get user info
            sql = "SELECT h.hostmask AS current_hostmask, u.* FROM phreakbot_hostmasks h, phreakbot_users u WHERE h.users_id = u.id AND h.hostmask = %s"
            cur.execute(sql, (host,))
            db_res = cur.fetchall()
            if not db_res:
                return None

            db_res = db_res[0]
            for key in db_res.keys():
                ret[key] = db_res[key]

            # Get permissions
            ret["permissions"] = {"global": []}

            sql = "SELECT permission, channel FROM phreakbot_perms WHERE users_id = %s"
            cur.execute(sql, (ret["id"],))
            db_res = cur.fetchall()
            for row in db_res:
                if row["channel"] and row["channel"] != "":
                    if row["channel"] not in ret["permissions"]:
                        ret["permissions"][row["channel"]] = []
                    ret["permissions"][row["channel"]].append(row["permission"])
                else:
                    ret["permissions"]["global"].append(row["permission"])

            # Get hostmasks
            ret["hostmasks"] = []
            sql = "SELECT hostmask FROM phreakbot_hostmasks WHERE users_id = %s"
            cur.execute(sql, (ret["id"],))
            db_res = cur.fetchall()
            for row in db_res:
                for k in row.keys():
                    ret["hostmasks"].append(row[k])

            cur.close()
            return ret
        except Exception as e:
            self.logger.error(f"Database error in db_get_userinfo_by_userhost: {e}")
            return None

    def load_all_modules(self):
        """Load all modules from the modules directory"""
        self.logger.info("Loading modules...")

        # Load core modules
        for filename in os.listdir(self.modules_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                self.load_module(os.path.join(self.modules_dir, filename))

        # Load extra modules
        if os.path.exists(self.extra_modules_dir):
            for filename in os.listdir(self.extra_modules_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    self.load_module(os.path.join(self.extra_modules_dir, filename))

        self.logger.info(f"Loaded modules: {', '.join(self.modules.keys())}")

    def load_module(self, module_path):
        """Load a module from file"""
        module_name = os.path.basename(module_path)[:-3]  # Remove .py extension

        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module_object = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module_object
            spec.loader.exec_module(module_object)

            # Check if module has required functions
            if not hasattr(module_object, "config"):
                self.logger.error(
                    f"Module {module_name} does not have a config() function"
                )
                return False

            # Get module configuration
            module_config = module_object.config(self)

            # Check if module has required configuration keys
            for key in ["events", "commands", "help"]:
                if key not in module_config:
                    self.logger.error(
                        f"Module {module_name} config does not provide '{key}' key"
                    )
                    return False

            # Add module object to config
            module_config["object"] = module_object
            self.modules[module_name] = module_config

            self.logger.info(f"Loaded module: {module_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load module {module_name}: {e}")
            return False

    def unload_module(self, module_name):
        """Unload a module"""
        if module_name in self.modules:
            del self.modules[module_name]
            self.logger.info(f"Unloaded module: {module_name}")
            return True
        else:
            self.logger.error(f"Module not found: {module_name}")
            return False

    def on_welcome(self, connection, event):
        """Called when bot has successfully connected to the server"""
        self.logger.info(f"Connected to {self.config['server']}")

        # Join channels
        for channel in self.config["channels"]:
            connection.join(channel)
            self.logger.info(f"Joined channel: {channel}")

    def on_pubmsg(self, connection, event):
        """Called when a message is received in a channel"""
        self._handle_message(connection, event, is_private=False)

    def on_privmsg(self, connection, event):
        """Called when a private message is received"""
        self._handle_message(connection, event, is_private=True)

    def on_join(self, connection, event):
        """Called when someone joins a channel"""
        self._handle_event(connection, event, "join")

    def on_part(self, connection, event):
        """Called when someone leaves a channel"""
        self._handle_event(connection, event, "part")

    def on_quit(self, connection, event):
        """Called when someone quits IRC"""
        self._handle_event(connection, event, "quit")

    def _handle_message(self, connection, event, is_private):
        """Process incoming messages and route to appropriate modules"""
        nick = event.source.nick
        user_host = event.source.userhost
        channel = event.target if not is_private else nick
        message = event.arguments[0]

        # Create event object similar to the original bot
        event_obj = {
            "server": self.connection.get_server_name(),
            "signal": "privmsg" if is_private else "pubmsg",
            "nick": nick,
            "hostmask": user_host,
            "channel": channel,
            "text": message,
            "is_privmsg": is_private,
            "connection": connection,
            "raw_event": event,
            "bot_nick": self.connection.get_nickname(),
            "command": "",
            "command_args": "",
            "trigger": "",
            "user_info": (
                self.db_get_userinfo_by_userhost(user_host)
                if self.db_connection
                else None
            ),
        }

        # Check if message starts with trigger
        trigger_re = re.compile(f'^{re.escape(self.config["trigger"])}')
        command_re = re.compile(
            f'^{re.escape(self.config["trigger"])}([-a-zA-Z0-9]+)(?:\\s(.*))?$'
        )

        if trigger_re.match(message):
            match = command_re.match(message)
            if match:
                event_obj["command"] = match.group(1).lower()
                event_obj["command_args"] = match.group(2) or ""
                event_obj["trigger"] = "command"

                # Find modules that handle this command
                self._route_to_modules(event_obj)
        else:
            # Handle non-command events
            event_obj["trigger"] = "event"
            self._route_to_modules(event_obj)

    def _handle_event(self, connection, event, event_type):
        """Handle non-message events like joins, parts, quits"""
        nick = event.source.nick
        user_host = event.source.userhost
        channel = event.target if hasattr(event, "target") else None

        event_obj = {
            "server": self.connection.get_server_name(),
            "signal": event_type,
            "nick": nick,
            "hostmask": user_host,
            "channel": channel,
            "text": "",
            "is_privmsg": False,
            "connection": connection,
            "raw_event": event,
            "bot_nick": self.connection.get_nickname(),
            "command": "",
            "command_args": "",
            "trigger": "event",
            "user_info": (
                self.db_get_userinfo_by_userhost(user_host)
                if self.db_connection
                else None
            ),
        }

        self._route_to_modules(event_obj)

    def _route_to_modules(self, event):
        """Route an event to the appropriate modules"""
        self.output = []  # Clear output buffer

        # Find modules to handle this event
        handled = False

        # First try modules that handle commands
        if event["trigger"] == "command":
            for module_name, module in self.modules.items():
                if event["command"] in module["commands"]:
                    if self._check_permissions(event, module["permissions"]):
                        try:
                            module["object"].run(self, event)
                            handled = True
                        except Exception as e:
                            import traceback

                            self.logger.error(f"Error in module {module_name}: {e}")
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

        # Then try modules that handle events
        if not handled and event["trigger"] == "event":
            for module_name, module in self.modules.items():
                if event["signal"] in module["events"]:
                    if self._check_permissions(event, module["permissions"]):
                        try:
                            module["object"].run(self, event)
                            handled = True
                        except Exception as e:
                            self.logger.error(f"Error in module {module_name}: {e}")

        # Process output
        self._process_output(event)

    def _is_owner(self, hostmask):
        """Check if a hostmask matches the owner pattern"""
        if not self.config["owner"]:
            return False

        owner_pattern = self.config["owner"]
        if owner_pattern.startswith("*!"):
            # Extract the user and host parts from the pattern
            pattern_parts = owner_pattern[2:].split("@")
            if len(pattern_parts) == 2:
                pattern_user = pattern_parts[0]
                pattern_host = pattern_parts[1]

                # Extract the user and host parts from the hostmask
                hostmask_parts = hostmask.split("@")
                if len(hostmask_parts) == 2:
                    current_user = hostmask_parts[0]
                    current_host = hostmask_parts[1]

                    # Check if the pattern matches
                    return (pattern_user == "*" or pattern_user == current_user) and (
                        pattern_host == "*" or pattern_host == current_host
                    )

        # Legacy format - exact match
        return hostmask == self.config["owner"]

    def _check_permissions(self, event, required_permissions):
        """Check if the user has the required permissions"""
        # Owner always has all permissions
        if self.config["owner"] and self._is_owner(event["hostmask"]):
            return True

        # Check database permissions if available
        if event["user_info"] and "permissions" in event["user_info"]:
            # Check global permissions
            for perm in required_permissions:
                if perm in event["user_info"]["permissions"]["global"]:
                    return True

            # Check channel-specific permissions
            if event["channel"] in event["user_info"]["permissions"]:
                for perm in required_permissions:
                    if perm in event["user_info"]["permissions"][event["channel"]]:
                        return True

        # For now, simple permission system - 'user' permission is granted to everyone
        if "user" in required_permissions:
            return True

        return False

    def _process_output(self, event):
        """Process and send output messages"""
        if not self.output:
            return

        # Limit number of output lines
        if len(self.output) > self.config["max_output_lines"]:
            self.say(
                event["channel"],
                f"There's more than {self.config['max_output_lines']} lines of output, I'll message you privately.",
            )
            for line in self.output:
                self.connection.privmsg(event["nick"], line["msg"])
        else:
            for line in self.output:
                if line["type"] == "say":
                    self.say(event["channel"], line["msg"])
                elif line["type"] == "reply":
                    self.say(event["channel"], f"{event['nick']}, {line['msg']}")
                elif line["type"] == "private":
                    self.connection.privmsg(event["nick"], line["msg"])

        self.output = []

    # Helper methods for modules to use
    def say(self, target, message):
        """Send a message to a channel or user"""
        self.connection.privmsg(target, message)

    def reply(self, message):
        """Add a reply message to the output queue"""
        self.output.append({"type": "reply", "msg": message})

    def add_response(self, message, private=False):
        """Add a message to the output queue"""
        if private:
            self.output.append({"type": "private", "msg": message})
        else:
            self.output.append({"type": "say", "msg": message})


def main():
    parser = argparse.ArgumentParser(description="PhreakBot IRC Bot")
    parser.add_argument(
        "-c", "--config", default="config.json", help="Path to config file"
    )
    args = parser.parse_args()

    bot = PhreakBot(args.config)
    bot.start()


if __name__ == "__main__":
    main()
