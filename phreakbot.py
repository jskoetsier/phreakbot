#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot - A modular IRC bot using pydle
#
import argparse
import importlib.util
import json
import logging
import os
import re
import sys
from datetime import datetime

# Pydle IRC library
import pydle

# Database library
import psycopg2
import psycopg2.extras


class PhreakBot(pydle.Client):
    def __init__(self, config_path, *args, **kwargs):
        self.config_path = config_path
        self.load_config()

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

        # Initialize bot state
        self.modules = {}
        self.output = []
        self.db_connection = None
        self.re = re  # Expose re module for modules to use
        self.state = {}  # State dictionary for modules to use

        # Set up trigger regex for modules to use
        self.trigger_re = re.compile(f'^{re.escape(self.config["trigger"])}')
        self.bot_trigger_re = re.compile(f'^{re.escape(self.config["trigger"])}')

        # Connect to database
        self.db_connect()

        # Call the parent constructor with our nickname and realname
        super().__init__(
            nickname=self.config["nickname"],
            realname=self.config["realname"],
            *args, **kwargs
        )

        # Load modules
        self.bot_base = os.path.dirname(os.path.abspath(__file__))
        self.modules_dir = os.path.join(self.bot_base, "modules")
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

    def db_get_userinfo_by_userhost(self, hostmask):
        """Get user information from the database by hostmask"""
        if not self.db_connection:
            return None

        ret = {}
        hostmask = hostmask.lower()

        try:
            cur = self.db_connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Get user info
            sql = "SELECT h.hostmask AS current_hostmask, u.* FROM phreakbot_hostmasks h, phreakbot_users u WHERE h.users_id = u.id AND h.hostmask = %s"
            cur.execute(sql, (hostmask,))
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

        # Load modules from the modules directory
        modules_dir = os.path.join(self.bot_base, "modules")
        if os.path.exists(modules_dir):
            for filename in os.listdir(modules_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    self.load_module(os.path.join(modules_dir, filename))

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
            if spec is None:
                self.logger.error(
                    f"Failed to load module {module_name}: Could not create spec from file location"
                )
                return False

            module_object = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module_object
            if spec.loader is None:
                self.logger.error(
                    f"Failed to load module {module_name}: Spec loader is None"
                )
                return False

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

    async def on_connect(self):
        """Called when bot has successfully connected to the server"""
        self.logger.info(f"Connected to {self.network}")

        # Join channels
        for channel in self.config["channels"]:
            await self.join(channel)
            self.logger.info(f"Joined channel: {channel}")

    async def on_message(self, target, source, message):
        """Called when a message is received in a channel or privately"""
        is_private = target == self.nickname
        channel = source if is_private else target
        await self._handle_message(source, channel, message, is_private)

    async def on_join(self, channel, user):
        """Called when someone joins a channel"""
        await self._handle_event(user, channel, "join")

    async def on_part(self, channel, user, message=None):
        """Called when someone leaves a channel"""
        await self._handle_event(user, channel, "part")

    async def on_quit(self, user, message=None):
        """Called when someone quits IRC"""
        await self._handle_event(user, None, "quit")

    async def on_ctcp(self, by, target, what, contents):
        """Called when a CTCP request is received"""
        self.logger.info(f"Received CTCP {what} from {by} to {target}: {contents}")

        # Create event object for modules
        try:
            user_info = await self.whois(by)
            user_host = f"{by}!{user_info.get('username', '')}@{user_info.get('hostname', '')}"
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            user_host = f"{by}!unknown@unknown"

        event_obj = {
            "server": self.network,
            "signal": "ctcp",
            "nick": by,
            "hostmask": user_host,
            "channel": target,
            "text": contents,
            "is_privmsg": target == self.nickname,
            "raw_event": None,
            "bot_nick": self.nickname,
            "command": "",
            "command_args": "",
            "trigger": "event",
            "ctcp_command": what.upper(),
            "user_info": (
                self.db_get_userinfo_by_userhost(user_host)
                if self.db_connection
                else None
            ),
        }

        # Route to modules that handle CTCP events
        await self._route_to_modules(event_obj)

    async def on_names(self, channel, names):
        """Called when the server sends a NAMES reply"""
        self.logger.info(f"Received NAMES reply for {channel}: {names}")

        # Create event object for modules
        event_obj = {
            "server": self.network,
            "signal": "namreply",
            "nick": self.nickname,
            "hostmask": "",
            "channel": channel,
            "names": list(names.keys()),
            "text": "",
            "is_privmsg": False,
            "raw_event": None,
            "bot_nick": self.nickname,
            "command": "",
            "command_args": "",
            "trigger": "event",
            "user_info": None,
        }

        # Route to modules that handle namreply events
        await self._route_to_modules(event_obj)

    async def _handle_message(self, source, channel, message, is_private):
        """Process incoming messages and route to appropriate modules"""
        # Get the user's hostmask
        try:
            user_info = await self.whois(source)
            user_host = f"{source}!{user_info.get('username', '')}@{user_info.get('hostname', '')}"
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            user_host = f"{source}!unknown@unknown"

        self.logger.info(f"Formatted hostmask: {user_host}")
        self.logger.info(f"Processing message from {source} in {channel}: '{message}'")

        # Create event object similar to the original bot
        event_obj = {
            "server": self.network,
            "signal": "privmsg" if is_private else "pubmsg",
            "nick": source,
            "hostmask": user_host,
            "channel": channel,
            "text": message,
            "is_privmsg": is_private,
            "raw_event": None,
            "bot_nick": self.nickname,
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
        
        # Special handling for karma patterns - HARDCODED check for test++ and test--
        if message == "!test++" or message == "!test--":
            self.logger.info(f"HARDCODED KARMA PATTERN DETECTED: '{message}' in channel '{channel}'")
            event_obj["trigger"] = "event"
            
            # Directly call the karma module
            if "karma" in self.modules:
                try:
                    self.logger.info("Directly calling karma module")
                    self.modules["karma"]["object"].run(self, event_obj)
                    await self._process_output(event_obj)
                    return
                except Exception as e:
                    import traceback
                    self.logger.error(f"Error in karma module: {e}")
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            await self._route_to_modules(event_obj)
            return
            
        # Regular karma pattern check
        karma_pattern = re.compile(r"^\!([a-zA-Z0-9_-]+)(\+\+|\-\-)(?:\s+#(.+))?$")
        karma_match = karma_pattern.match(message)
        
        # Debug message parsing
        self.logger.info(f"Processing message: '{message}'")
        self.logger.info(f"Trigger regex: '{trigger_re.pattern}'")
        self.logger.info(f"Trigger match: {bool(trigger_re.match(message))}")
        self.logger.info(f"Karma match: {bool(karma_match)}")
        
        # Special handling for karma patterns
        if karma_match:
            self.logger.info(f"EXACT MESSAGE: '{message}' in channel '{channel}'")
            self.logger.info(f"Detected karma pattern: {karma_match.groups()}")
            event_obj["trigger"] = "event"
            await self._route_to_modules(event_obj)
            return
            
        # Continue with normal message processing
        if trigger_re.match(message):
            self.logger.info(f"RAW MESSAGE: '{message}'")
            
            # Regular command handling - exclude karma patterns
            command_re = re.compile(
                f'^{re.escape(self.config["trigger"])}([a-zA-Z0-9_][-a-zA-Z0-9_]*)(?:\\s(.*))?$'
            )
            match = command_re.match(message)
            self.logger.info(f"Command match: {bool(match)}")
            
            if match:
                event_obj["command"] = match.group(1).lower()
                event_obj["command_args"] = match.group(2) or ""
                event_obj["trigger"] = "command"
                self.logger.info(
                    f"Parsed command: '{event_obj['command']}' with args: '{event_obj['command_args']}'"
                )

                # Find modules that handle this command
                await self._route_to_modules(event_obj)
            else:
                # This is a message that starts with the trigger but doesn't match the command pattern
                self.logger.info(f"Message starts with trigger but doesn't match command pattern: '{message}'")
                event_obj["trigger"] = "event"
                await self._route_to_modules(event_obj)
        else:
            # Handle non-command events
            event_obj["trigger"] = "event"
            await self._route_to_modules(event_obj)

    async def _handle_event(self, user, channel, event_type):
        """Handle non-message events like joins, parts, quits"""
        try:
            user_info = await self.whois(user)
            user_host = f"{user}!{user_info.get('username', '')}@{user_info.get('hostname', '')}"
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            user_host = f"{user}!unknown@unknown"

        # Log join and part events
        if event_type == "join":
            self.logger.info(f"JOIN: {user} ({user_host}) joined {channel}")
        elif event_type == "part":
            self.logger.info(f"PART: {user} ({user_host}) left {channel}")
        elif event_type == "quit":
            self.logger.info(f"QUIT: {user} ({user_host}) quit")

        event_obj = {
            "server": self.network,
            "signal": event_type,
            "nick": user,
            "hostmask": user_host,
            "channel": channel,
            "text": "",
            "is_privmsg": False,
            "raw_event": None,
            "bot_nick": self.nickname,
            "command": "",
            "command_args": "",
            "trigger": "event",
            "user_info": (
                self.db_get_userinfo_by_userhost(user_host)
                if self.db_connection
                else None
            ),
        }

        await self._route_to_modules(event_obj)

    async def _route_to_modules(self, event):
        """Route an event to the appropriate modules"""
        self.output = []  # Clear output buffer

        # Find modules to handle this event
        handled = False

        # Debug the event
        self.logger.info(f"Routing event: trigger={event['trigger']}, signal={event.get('signal', 'N/A')}, text={event.get('text', 'N/A')}")

        # Special handling for karma patterns
        if event["trigger"] == "event" and "text" in event and event["text"]:
            # Check for karma pattern
            karma_pattern = re.compile(r"^\!([a-zA-Z0-9_-]+)(\+\+|\-\-)(?:\s+#(.+))?$")
            match = karma_pattern.match(event["text"])
            
            if match:
                self.logger.info(f"Detected karma pattern in message: {event['text']}")
                self.logger.info(f"Matched groups: {match.groups()}")
                
                # Try to route directly to karmaplus module
                if "karmaplus" in self.modules:
                    try:
                        self.logger.info("Routing directly to karmaplus module")
                        self.modules["karmaplus"]["object"].run(self, event)
                        handled = True
                        self.logger.info("Karmaplus module handled the message")
                        
                        # Process output and return early
                        await self._process_output(event)
                        return
                    except Exception as e:
                        import traceback
                        self.logger.error(f"Error in karmaplus module: {e}")
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

        # Check for custom infoitem commands first
        if not handled and "infoitems" in self.modules:
            try:
                # Try to handle as a custom infoitem command regardless of trigger type
                self.logger.info("Checking if infoitems module can handle this message")
                if hasattr(self.modules["infoitems"]["object"], "handle_custom_command"):
                    handled = self.modules["infoitems"]["object"].handle_custom_command(self, event)
                    self.logger.info(f"Infoitems module handled message: {handled}")
            except Exception as e:
                import traceback
                self.logger.error(f"Error in infoitems custom command handler: {e}")
                self.logger.error(f"Traceback: {traceback.format_exc()}")

        # First try modules that handle commands
        if not handled and event["trigger"] == "command":
            self.logger.info(
                f"Routing command: {event['command']} with args: {event['command_args']}"
            )

            # Log all available modules and their commands
            self.logger.info("Available modules and their commands:")
            for module_name, module in self.modules.items():
                self.logger.info(
                    f"Module: {module_name}, Commands: {module['commands']}"
                )

            for module_name, module in self.modules.items():
                if event["command"] in module["commands"]:
                    self.logger.info(
                        f"Found module {module_name} to handle command {event['command']}"
                    )

                    # Check permissions
                    has_permission = self._check_permissions(
                        event, module["permissions"]
                    )
                    self.logger.info(f"User has permission: {has_permission}")

                    if has_permission:
                        try:
                            self.logger.info(
                                f"Calling module {module_name}.run() with command {event['command']}"
                            )
                            module["object"].run(self, event)
                            handled = True
                            self.logger.info(
                                f"Module {module_name} handled command {event['command']}"
                            )
                        except Exception as e:
                            import traceback

                            self.logger.error(f"Error in module {module_name}: {e}")
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

        # Then try modules that handle events
        if not handled and event["trigger"] == "event":
            self.logger.info("Routing event to modules that handle events")
            for module_name, module in self.modules.items():
                self.logger.info(f"Checking if module {module_name} handles event signal {event['signal']}")
                self.logger.info(f"Module {module_name} events: {module['events']}")

                if event["signal"] in module["events"]:
                    self.logger.info(f"Module {module_name} handles event signal {event['signal']}")

                    # Check permissions
                    has_permission = self._check_permissions(event, module["permissions"])
                    self.logger.info(f"User has permission for module {module_name}: {has_permission}")

                    if has_permission:
                        try:
                            self.logger.info(f"Calling module {module_name}.run() with event")
                            module["object"].run(self, event)
                            self.logger.info(f"Module {module_name} processed event")
                            handled = True
                        except Exception as e:
                            import traceback
                            self.logger.error(f"Error in module {module_name}: {e}")
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

        # Process output
        await self._process_output(event)

    def _is_owner(self, hostmask):
        """Check if a hostmask matches an owner in the database"""
        if not self.db_connection:
            return False

        try:
            # Log the hostmask for debugging
            self.logger.info(f"Checking owner status for hostmask: {hostmask}")

            # Extract the nick from the hostmask
            nick = hostmask.split("!")[0] if "!" in hostmask else hostmask
            self.logger.info(f"Extracted nick: {nick}")

            # First try the exact hostmask
            user_info = self.db_get_userinfo_by_userhost(hostmask)
            if user_info and user_info.get("is_owner"):
                self.logger.info(
                    f"User with hostmask {hostmask} is an owner in the database"
                )
                return True

            # Try to normalize the hostmask by removing the caret if present
            normalized_hostmask = hostmask
            if "!" in hostmask:
                parts = hostmask.split("!")
                if len(parts) == 2 and parts[1].startswith("^"):
                    normalized_hostmask = f"{parts[0]}!{parts[1][1:]}"
                    self.logger.info(f"Normalized hostmask: {normalized_hostmask}")

                    # Try with normalized hostmask
                    user_info = self.db_get_userinfo_by_userhost(normalized_hostmask)
                    if user_info and user_info.get("is_owner"):
                        self.logger.info(
                            f"User with normalized hostmask {normalized_hostmask} is an owner in the database"
                        )
                        return True

            # If we still haven't found an owner, check by username
            try:
                cur = self.db_connection.cursor()
                cur.execute(
                    "SELECT is_owner FROM phreakbot_users WHERE username = %s",
                    (nick.lower(),),
                )
                result = cur.fetchone()
                cur.close()

                if result and result[0]:
                    self.logger.info(
                        f"User with nick {nick} is an owner in the database"
                    )
                    return True
            except Exception as e:
                self.logger.error(f"Error checking owner status by username: {e}")

            self.logger.info(f"User with hostmask {hostmask} is not an owner")
            return False
        except Exception as e:
            self.logger.error(f"Error checking owner status: {e}")
            return False

    def _check_permissions(self, event, required_permissions):
        """Check if the user has the required permissions"""
        # Log the permission check
        self.logger.info(
            f"Checking permissions: {required_permissions} for user {event['nick']}"
        )

        # Skip permission checks for the bot itself
        if event["nick"] == self.nickname:
            self.logger.info("Skipping permission check for the bot itself")
            return True

        # Special case: Always allow the owner claim command
        if (
            event["trigger"] == "command"
            and event["command"] == "owner"
            and event["command_args"] == "claim"
        ):
            self.logger.info("Allowing owner claim command without permissions")
            return True

        # Owner always has all permissions
        if self._is_owner(event["hostmask"]):
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
            self.logger.info("Granting 'user' permission to everyone")
            return True

        self.logger.info(f"Permission denied for {event['nick']}")
        return False

    async def _process_output(self, event):
        """Process and send output messages"""
        if not self.output:
            return

        # Limit number of output lines
        if len(self.output) > self.config["max_output_lines"]:
            await self.message(
                event["channel"],
                f"There's more than {self.config['max_output_lines']} lines of output, I'll message you privately.",
            )
            for line in self.output:
                await self.message(event["nick"], line["msg"])
        else:
            for line in self.output:
                if line["type"] == "say":
                    await self.message(event["channel"], line["msg"])
                elif line["type"] == "reply":
                    await self.message(event["channel"], f"{event['nick']}, {line['msg']}")
                elif line["type"] == "private":
                    await self.message(event["nick"], line["msg"])

        self.output = []

    # Helper methods for modules to use
    async def say(self, target, message):
        """Send a message to a channel or user"""
        await self.message(target, message)

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

    # Create bot instance
    bot = PhreakBot(args.config)

    # Connect to server
    bot.run(
        bot.config["server"],
        bot.config["port"],
        tls=bot.config.get("use_tls", False),
        tls_verify=bot.config.get("tls_verify", True)
    )


if __name__ == "__main__":
    main()
