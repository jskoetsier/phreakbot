#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot - A modular IRC bot using pydle
#
import argparse
import asyncio
import importlib.util
import json
import logging
import os
import re
import sys
import time
import traceback
from collections import defaultdict
from datetime import datetime

# Database library
import psycopg2
import psycopg2.extras
import psycopg2.pool

# Pydle IRC library
import pydle


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
        self.db_pool = None  # Connection pool (use db_get()/db_return())
        self.re = re  # Expose re module for modules to use
        self.state = {}  # State dictionary for modules to use
        self.user_hostmasks = {}  # Cache of user hostmasks from JOIN/PRIVMSG events

        # Security: Rate limiting tracking
        self.rate_limit = {
            "user_commands": defaultdict(list),  # Track command timestamps per user
            "max_commands_per_minute": 10,  # Max commands per user per minute
            "max_commands_per_10_seconds": 5,  # Max commands per user per 10 seconds
            "global_commands": [],  # Track all command timestamps
            "max_global_commands_per_second": 20,  # Max commands globally per second
            "banned_users": {},  # Temporarily banned users {hostmask: unban_time}
            "ban_duration": 300,  # Ban duration in seconds (5 minutes)
        }

        # Performance optimization: Add caching
        self.cache = {
            "user_permissions": {},  # Cache user permissions by hostmask
            "user_info": {},  # Cache full user info by hostmask
            "cache_ttl": 300,  # Cache time-to-live in seconds (5 minutes)
            "cache_timestamps": {},  # Track when items were cached
        }

        # Set up trigger regex for modules to use
        self.trigger_re = re.compile(f'^{re.escape(self.config["trigger"])}')
        self.bot_trigger_re = re.compile(f'^{re.escape(self.config["trigger"])}')

        # Connect to database
        self.db_connect()

        # Call the parent constructor with our nickname and realname
        super().__init__(
            nickname=self.config["nickname"],
            realname=self.config["realname"],
            *args,
            **kwargs,
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

    def db_connect(self, max_retries=3, retry_delay=5):
        """Connect to the PostgreSQL database with connection pooling"""
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Creating database connection pool at {self.config['db_host']}:{self.config['db_port']} (attempt {attempt + 1}/{max_retries})"
                )
                # Create connection pool with 5 min connections and 20 max connections
                self.db_pool = psycopg2.pool.ThreadedConnectionPool(
                    5,  # minconn
                    20,  # maxconn
                    host=self.config["db_host"],
                    port=self.config["db_port"],
                    user=self.config["db_user"],
                    password=self.config["db_password"],
                    dbname=self.config["db_name"],
                    connect_timeout=10,
                )
                self.logger.info("Database connection pool created successfully")
                return True
            except Exception as e:
                self.logger.error(
                    f"Database connection attempt {attempt + 1} failed: {e}"
                )
                if attempt < max_retries - 1:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    self.logger.warning(
                        "All database connection attempts failed. Bot will run with limited functionality."
                    )
                    self.db_pool = None
                    return False

    def db_get(self):
        """Get a database connection from the pool."""
        if self.db_pool is not None:
            return self.db_pool.getconn()
        return None

    def db_return(self, conn):
        """Return a database connection to the pool."""
        if conn is None:
            return
        if self.db_pool is not None:
            self.db_pool.putconn(conn)

    def ensure_db_connection(self):
        """Ensure database connection pool is alive, reconnect if needed"""
        if self.db_pool is None:
            self.logger.warning("No database connection pool, attempting to reconnect...")
            return self.db_connect(max_retries=2, retry_delay=3)

        try:
            conn = self.db_pool.getconn()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            self.db_pool.putconn(conn)
            return True
        except Exception as e:
            self.logger.warning(f"Database connection pool unhealthy: {e}. Reconnecting...")
            return self.db_connect(max_retries=2, retry_delay=3)

    def _is_cache_valid(self, cache_key):
        """Check if a cached item is still valid based on TTL"""
        if cache_key not in self.cache["cache_timestamps"]:
            return False

        age = time.time() - self.cache["cache_timestamps"][cache_key]
        return age < self.cache["cache_ttl"]

    def _cache_set(self, cache_type, key, value):
        """Set a value in the cache with timestamp"""
        cache_key = f"{cache_type}:{key}"
        self.cache[cache_type][key] = value
        self.cache["cache_timestamps"][cache_key] = time.time()
        self.logger.debug(f"Cached {cache_key}")

    def _cache_get(self, cache_type, key):
        """Get a value from cache if it exists and is valid"""
        cache_key = f"{cache_type}:{key}"

        if not self._is_cache_valid(cache_key):
            # Cache expired or doesn't exist
            if key in self.cache[cache_type]:
                del self.cache[cache_type][key]
            if cache_key in self.cache["cache_timestamps"]:
                del self.cache["cache_timestamps"][cache_key]
            return None

        return self.cache[cache_type].get(key)

    def _cache_invalidate(self, cache_type, key=None):
        """Invalidate cache entries. If key is None, invalidate all entries of that type"""
        if key is None:
            # Clear all entries of this type
            self.cache[cache_type] = {}
            # Remove timestamps for this cache type
            keys_to_remove = [
                k
                for k in self.cache["cache_timestamps"].keys()
                if k.startswith(f"{cache_type}:")
            ]
            for k in keys_to_remove:
                del self.cache["cache_timestamps"][k]
            self.logger.debug(f"Invalidated all {cache_type} cache")
        else:
            # Clear specific entry
            cache_key = f"{cache_type}:{key}"
            if key in self.cache[cache_type]:
                del self.cache[cache_type][key]
            if cache_key in self.cache["cache_timestamps"]:
                del self.cache["cache_timestamps"][cache_key]
            self.logger.debug(f"Invalidated cache for {cache_key}")

    def _sanitize_input(self, input_str, max_length=500):
        """Sanitize user input: truncate, remove null bytes and control chars.

        SQL injection is prevented by using parameterized queries throughout
        the codebase, so we do not filter SQL-specific patterns here.
        Shell injection is prevented by not executing user input as shell
        commands (the !exec module has been removed).
        """
        if not isinstance(input_str, str):
            return ""

        # Truncate to max length
        sanitized = input_str[:max_length]

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Remove control characters except newlines and tabs
        sanitized = "".join(
            char for char in sanitized if char.isprintable() or char in "\n\t"
        )

        return sanitized.strip()

    def _sanitize_channel_name(self, channel):
        """Sanitize channel name to prevent injection"""
        if not isinstance(channel, str):
            return "#unknown"

        # Channel names should start with # or & and contain only safe characters
        if not channel or channel[0] not in "#&":
            return "#unknown"

        # Only allow alphanumeric, hyphen, underscore, and the channel prefix
        sanitized = channel[0] + "".join(
            char for char in channel[1:] if char.isalnum() or char in "-_"
        )

        return sanitized[:50]  # Max length 50

    def _sanitize_nickname(self, nickname):
        """Sanitize nickname to prevent injection"""
        if not isinstance(nickname, str):
            return "unknown"

        # Nicknames should only contain safe characters
        # IRC allows: a-z A-Z 0-9 - [ ] \ ` ^ { } | _
        # We'll be more restrictive
        sanitized = "".join(
            char for char in nickname if char.isalnum() or char in "-_[]\\`^{}|"
        )

        return sanitized[:30]  # Max length 30

    def _check_rate_limit(self, hostmask):
        """Check if user is within rate limits"""
        current_time = time.time()

        # Check if user is temporarily banned
        if hostmask in self.rate_limit["banned_users"]:
            unban_time = self.rate_limit["banned_users"][hostmask]
            if current_time < unban_time:
                remaining = int(unban_time - current_time)
                self.logger.warning(
                    f"Rate limit: User {hostmask} is banned for {remaining} more seconds"
                )
                return False
            else:
                # Unban the user
                del self.rate_limit["banned_users"][hostmask]
                self.logger.info(f"Rate limit: User {hostmask} has been unbanned")

        # Clean up old timestamps (older than 1 minute)
        cutoff_time = current_time - 60
        self.rate_limit["user_commands"][hostmask] = [
            ts for ts in self.rate_limit["user_commands"][hostmask] if ts > cutoff_time
        ]

        # Check rate limits
        user_commands = self.rate_limit["user_commands"][hostmask]

        # Check commands per minute
        if len(user_commands) >= self.rate_limit["max_commands_per_minute"]:
            self.logger.warning(
                f"Rate limit exceeded: {hostmask} has sent {len(user_commands)} commands in the last minute"
            )
            # Ban the user temporarily
            self.rate_limit["banned_users"][hostmask] = (
                current_time + self.rate_limit["ban_duration"]
            )
            return False

        # Check commands per 10 seconds
        recent_cutoff = current_time - 10
        recent_commands = [ts for ts in user_commands if ts > recent_cutoff]
        if len(recent_commands) >= self.rate_limit["max_commands_per_10_seconds"]:
            self.logger.warning(
                f"Rate limit exceeded: {hostmask} has sent {len(recent_commands)} commands in the last 10 seconds"
            )
            return False

        # Check global rate limit
        global_cutoff = current_time - 1
        self.rate_limit["global_commands"] = [
            ts for ts in self.rate_limit["global_commands"] if ts > global_cutoff
        ]
        if (
            len(self.rate_limit["global_commands"])
            >= self.rate_limit["max_global_commands_per_second"]
        ):
            self.logger.warning(
                f"Global rate limit exceeded: {len(self.rate_limit['global_commands'])} commands in the last second"
            )
            return False

        # Record this command
        self.rate_limit["user_commands"][hostmask].append(current_time)
        self.rate_limit["global_commands"].append(current_time)

        return True

    def db_get_userinfo_by_userhost(self, hostmask):
        """Get user information from the database by hostmask with caching"""
        hostmask = hostmask.lower()

        # Check cache first
        cached_info = self._cache_get("user_info", hostmask)
        if cached_info is not None:
            self.logger.debug(f"Cache hit for user info: {hostmask}")
            return cached_info

        if not self.ensure_db_connection():
            self.logger.debug("Database unavailable, returning None for user info")
            return None

        conn = self.db_get()
        if not conn:
            return None

        ret = {}

        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Optimized query using index on hostmask
            sql = "SELECT h.hostmask AS current_hostmask, u.* FROM phreakbot_hostmasks h, phreakbot_users u WHERE h.users_id = u.id AND h.hostmask = %s"
            cur.execute(sql, (hostmask,))
            db_res = cur.fetchall()
            if not db_res:
                # Cache negative result too (short TTL)
                self._cache_set("user_info", hostmask, None)
                cur.close()
                self.db_return(conn)
                return None

            db_res = db_res[0]
            for key in db_res.keys():
                ret[key] = db_res[key]

            # Get permissions (using optimized index)
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

            # Get hostmasks (using optimized index)
            ret["hostmasks"] = []
            sql = "SELECT hostmask FROM phreakbot_hostmasks WHERE users_id = %s"
            cur.execute(sql, (ret["id"],))
            db_res = cur.fetchall()
            for row in db_res:
                for k in row.keys():
                    ret["hostmasks"].append(row[k])

            cur.close()
            self.db_return(conn)

            # Cache the result
            self._cache_set("user_info", hostmask, ret)
            self.logger.debug(f"Cached user info for {hostmask}")

            return ret
        except psycopg2.OperationalError as e:
            self.logger.error(
                f"Database connection lost in db_get_userinfo_by_userhost: {e}"
            )
            self.db_return(conn)
            return None
        except Exception as e:
            self.logger.error(f"Database error in db_get_userinfo_by_userhost: {e}")
            self.db_return(conn)
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
            sys.modules[f"phreakbot.modules.{module_name}"] = module_object
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
        self.logger.info(f"Successfully connected to {self.network}")

        # Join channels with error handling
        for channel in self.config["channels"]:
            try:
                await self.join(channel)
                self.logger.info(f"Joined channel: {channel}")
            except Exception as e:
                self.logger.error(f"Failed to join channel {channel}: {e}")

    async def on_disconnect(self, expected):
        """Called when disconnected from server"""
        if expected:
            self.logger.info("Disconnected from server as expected")
        else:
            self.logger.warning("Unexpectedly disconnected from server")
            self.logger.info("Automatic reconnection will be attempted by pydle")

    async def on_message(self, target, source, message):
        """Called when a message is received in a channel or privately"""
        is_private = target == self.nickname
        channel = source if is_private else target
        try:
            await self._handle_message(source, channel, message, is_private)
        except Exception as e:
            self.logger.error(f"Error handling message from {source}: {e}")
            if is_private or message.startswith(self.config["trigger"]):
                await self.message(
                    channel,
                    f"Error processing command: {type(e).__name__}. Please try again or contact bot administrator.",
                )

    async def on_raw_join(self, message):
        """Capture hostmask from raw JOIN message"""
        # message.source contains the full hostmask: nick!user@host
        if message.source:
            # The source is already the full hostmask
            hostmask = message.source
            nick = hostmask.split("!")[0] if "!" in hostmask else hostmask

            # Cache the full hostmask for the meet command
            self.user_hostmasks[nick.lower()] = hostmask
            self.logger.info(f"Cached hostmask from raw JOIN: {hostmask}")

        # Call the parent handler to continue normal processing
        await super().on_raw_join(message)

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
            user_host = (
                f"{by}!{user_info.get('username', '')}@{user_info.get('hostname', '')}"
            )
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
            "user_info": self.db_get_userinfo_by_userhost(user_host),
        }

        # Route to modules that handle CTCP events
        output = []
        self._route_to_modules(event_obj, output)
        await self._process_output(event_obj, output)

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
        output = []
        self._route_to_modules(event_obj, output)
        await self._process_output(event_obj, output)

    async def _handle_message(self, source, channel, message, is_private):
        """Process incoming messages and route to appropriate modules"""
        # Security: Sanitize inputs
        source = self._sanitize_nickname(source)
        channel = self._sanitize_channel_name(channel) if not is_private else source
        message = self._sanitize_input(message, max_length=500)

        # Check if we have cached hostmask first (performance optimization)
        user_host = self.user_hostmasks.get(source.lower())

        if not user_host:
            # Only do WHOIS if we don't have a cached hostmask
            try:
                user_info = await self.whois(source)
                if user_info is None or not isinstance(user_info, dict):
                    self.logger.warning(
                        f"WHOIS returned None or invalid data for {source}, using fallback"
                    )
                    user_host = f"{source}!unknown@unknown"
                else:
                    user_host = f"{source}!{user_info.get('username', 'unknown')}@{user_info.get('hostname', 'unknown')}"
                    # Cache the hostmask for future use
                    self.user_hostmasks[source.lower()] = user_host
            except Exception as e:
                self.logger.error(f"Error getting user info: {e}")
                user_host = f"{source}!unknown@unknown"
        else:
            self.logger.debug(f"Using cached hostmask for {source}: {user_host}")

        self.logger.debug(f"Formatted hostmask: {user_host}")
        self.logger.debug(f"Processing message from {source} in {channel}: '{message}'")

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
            "user_info": self.db_get_userinfo_by_userhost(user_host),
        }

        # Continue with normal message processing
        trigger_re = self.trigger_re
        if trigger_re.match(message):
            self.logger.debug(f"RAW MESSAGE: '{message}'")

            # Security: Check rate limit before processing commands
            if not self._check_rate_limit(user_host):
                self.logger.warning(
                    f"Rate limit exceeded for {user_host}, ignoring command"
                )
                # Optionally notify the user (but don't spam them)
                if user_host not in self.rate_limit["banned_users"]:
                    await self.message(
                        channel,
                        f"{source}: Rate limit exceeded. Please slow down.",
                    )
                return

            # Regular command handling
            command_re = re.compile(
                f'^{re.escape(self.config["trigger"])}([a-zA-Z0-9_][-a-zA-Z0-9_]*)(?:\\s(.*))?$'
            )
            match = command_re.match(message)
            self.logger.debug(f"Command match: {bool(match)}")

            if match:
                event_obj["command"] = match.group(1).lower()
                # Security: Sanitize command arguments
                event_obj["command_args"] = self._sanitize_input(
                    match.group(2) or "", max_length=500
                )
                event_obj["trigger"] = "command"
                self.logger.debug(
                    f"Parsed command: '{event_obj['command']}' with args: '{event_obj['command_args']}'"
                )

                # Find modules that handle this command
                output = []
                self._route_to_modules(event_obj, output)
                await self._process_output(event_obj, output)
            else:
                # This is a message that starts with the trigger but doesn't match the command pattern
                self.logger.debug(
                    f"Message starts with trigger but doesn't match command pattern: '{message}'"
                )
                event_obj["trigger"] = "event"
                output = []
                self._route_to_modules(event_obj, output)
                await self._process_output(event_obj, output)
        else:
            # Handle non-command events
            event_obj["trigger"] = "event"
            output = []
            self._route_to_modules(event_obj, output)
            await self._process_output(event_obj, output)

    async def _handle_event(self, user, channel, event_type):
        """Handle non-message events like joins, parts, quits"""
        try:
            user_info = await self.whois(user)
            user_host = f"{user}!{user_info.get('username', '')}@{user_info.get('hostname', '')}"
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            user_host = f"{user}!unknown@unknown"

        # Cache the hostmask for later use
        self.user_hostmasks[user.lower()] = user_host

        # Log join and part events
        if event_type == "join":
            self.logger.debug(f"JOIN: {user} ({user_host}) joined {channel}")
        elif event_type == "part":
            self.logger.debug(f"PART: {user} ({user_host}) left {channel}")
        elif event_type == "quit":
            self.logger.debug(f"QUIT: {user} ({user_host}) quit")
            # Remove from cache on quit
            if user.lower() in self.user_hostmasks:
                del self.user_hostmasks[user.lower()]

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
            "user_info": self.db_get_userinfo_by_userhost(user_host),
        }

        output = []
        self._route_to_modules(event_obj, output)
        await self._process_output(event_obj, output)

    def _route_to_modules(self, event, output):
        """Route an event to the appropriate modules."""
        self._active_output = output

        try:
            self._dispatch_event(event)
        finally:
            self._active_output = None

    def _dispatch_event(self, event):
        """Internal event dispatch logic."""
        # Find modules to handle this event
        handled = False

        # Debug the event
        self.logger.debug(
            f"Routing event: trigger={event['trigger']}, signal={event.get('signal', 'N/A')}, text={event.get('text', 'N/A')}"
        )

        # Check for custom infoitem commands first
        if not handled and "infoitems" in self.modules:
            try:
                # Try to handle as a custom infoitem command regardless of trigger type
                self.logger.debug("Checking if infoitems module can handle this message")
                if hasattr(
                    self.modules["infoitems"]["object"], "handle_custom_command"
                ):
                    handled = self.modules["infoitems"]["object"].handle_custom_command(
                        self, event
                    )
                    self.logger.debug(f"Infoitems module handled message: {handled}")
            except Exception as e:
                self.logger.error(f"Error in infoitems custom command handler: {e}")
                self.logger.error(f"Traceback: {traceback.format_exc()}")

        # First try modules that handle commands
        if not handled and event["trigger"] == "command":
            self.logger.debug(
                f"Routing command: {event['command']} with args: {event['command_args']}"
            )

            # Log all available modules and their commands
            self.logger.debug("Available modules and their commands:")
            for module_name, module in self.modules.items():
                self.logger.debug(
                    f"Module: {module_name}, Commands: {module['commands']}"
                )

            # Create a copy of the modules dict to avoid "dictionary changed during iteration" errors
            modules_copy = dict(self.modules)

            for module_name, module in modules_copy.items():
                if event["command"] in module["commands"]:
                    self.logger.debug(
                        f"Found module {module_name} to handle command {event['command']}"
                    )

                    # Check permissions
                    has_permission = self._check_permissions(
                        event, module["permissions"]
                    )
                    self.logger.debug(f"User has permission: {has_permission}")

                    if has_permission:
                        try:
                            self.logger.debug(
                                f"Calling module {module_name}.run() with command {event['command']}"
                            )
                            module["object"].run(self, event)
                            handled = True
                            self.logger.debug(
                                f"Module {module_name} handled command {event['command']}"
                            )
                        except Exception as e:
        
                            self.logger.error(f"Error in module {module_name}: {e}")
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

            # If command not handled and it looks like an infoitem pattern, try infoitems module
            if not handled and "infoitems" in self.modules:
                if event["command_args"] and (
                    "=" in event["command_args"] or event["command_args"].strip() == "?"
                ):
                    self.logger.debug(
                        f"Trying infoitems module for unhandled command pattern"
                    )
                    has_permission = self._check_permissions(
                        event, self.modules["infoitems"]["permissions"]
                    )
                    if has_permission:
                        try:
                            result = self.modules["infoitems"]["object"].run(
                                self, event
                            )
                            if result:
                                handled = True
                                self.logger.debug("Infoitems module handled the command")
                        except Exception as e:
        
                            self.logger.error(f"Error in infoitems module: {e}")
                            self.logger.error(f"Traceback: {traceback.format_exc()}")

        # Then try modules that handle events
        if not handled and event["trigger"] == "event":
            self.logger.debug("Routing event to modules that handle events")
            for module_name, module in self.modules.items():
                self.logger.debug(
                    f"Checking if module {module_name} handles event signal {event['signal']}"
                )
                self.logger.debug(f"Module {module_name} events: {module['events']}")

                if event["signal"] in module["events"]:
                    self.logger.debug(
                        f"Module {module_name} handles event signal {event['signal']}"
                    )

                    # Don't check permissions for passive events like join, part, quit
                    # These events should be processed by all modules that listen for them
                    # The module itself will handle any permission or validation logic
                    try:
                        self.logger.debug(
                            f"Calling module {module_name}.run() with event"
                        )
                        module["object"].run(self, event)
                        self.logger.debug(f"Module {module_name} processed event")
                        handled = True
                    except Exception as e:
    
                        self.logger.error(f"Error in module {module_name}: {e}")
                        self.logger.error(f"Traceback: {traceback.format_exc()}")

    def _is_owner(self, hostmask):
        """Check if a hostmask matches an owner in the database"""
        if not self.db_pool:
            return False

        try:
            # Log the hostmask for debugging
            self.logger.debug(f"Checking owner status for hostmask: {hostmask}")

            # Extract the nick from the hostmask
            nick = hostmask.split("!")[0] if "!" in hostmask else hostmask
            self.logger.debug(f"Extracted nick: {nick}")

            # First try the exact hostmask
            user_info = self.db_get_userinfo_by_userhost(hostmask)
            if user_info and user_info.get("is_owner"):
                self.logger.debug(
                    f"User with hostmask {hostmask} is an owner in the database"
                )
                return True

            # Try to normalize the hostmask by removing the caret if present
            normalized_hostmask = hostmask
            if "!" in hostmask:
                parts = hostmask.split("!")
                if len(parts) == 2 and parts[1].startswith("^"):
                    normalized_hostmask = f"{parts[0]}!{parts[1][1:]}"
                    self.logger.debug(f"Normalized hostmask: {normalized_hostmask}")

                    # Try with normalized hostmask
                    user_info = self.db_get_userinfo_by_userhost(normalized_hostmask)
                    if user_info and user_info.get("is_owner"):
                        self.logger.debug(
                            f"User with normalized hostmask {normalized_hostmask} is an owner in the database"
                        )
                        return True

            # If we still haven't found an owner, check by username
            try:
                conn = self.db_get()
                if conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT is_owner FROM phreakbot_users WHERE username = %s",
                        (nick.lower(),),
                    )
                    result = cur.fetchone()
                    cur.close()
                    self.db_return(conn)

                    if result and result[0]:
                        self.logger.debug(
                            f"User with nick {nick} is an owner in the database"
                        )
                        return True
            except Exception as e:
                self.logger.error(f"Error checking owner status by username: {e}")

            self.logger.debug(f"User with hostmask {hostmask} is not an owner")
            return False
        except Exception as e:
            self.logger.error(f"Error checking owner status: {e}")
            return False

    def _check_permissions(self, event, required_permissions):
        """Check if the user has the required permissions with enhanced security"""
        # Log the permission check
        self.logger.debug(
            f"Checking permissions: {required_permissions} for user {event['nick']}"
        )

        # Security: Validate event object has required fields
        required_fields = ["nick", "hostmask", "channel", "trigger"]
        for field in required_fields:
            if field not in event:
                self.logger.error(
                    f"Security: Invalid event object missing field '{field}'"
                )
                return False

        # Security: Check if user is temporarily banned
        if event["hostmask"] in self.rate_limit["banned_users"]:
            self.logger.warning(
                f"Security: Banned user {event['hostmask']} attempted to execute command"
            )
            return False

        # Skip permission checks for the bot itself
        if event["nick"] == self.nickname:
            self.logger.debug("Skipping permission check for the bot itself")
            return True

        # Special case: Always allow the owner claim command
        if (
            event["trigger"] == "command"
            and event["command"] == "owner"
            and event["command_args"] == "claim"
        ):
            self.logger.debug("Allowing owner claim command without permissions")
            return True

        # Owner always has all permissions
        if self._is_owner(event["hostmask"]):
            return True

        # Check database permissions if available
        if event["user_info"] and "permissions" in event["user_info"]:
            # Security: Validate permissions structure
            if not isinstance(event["user_info"]["permissions"], dict):
                self.logger.error(
                    "Security: Invalid permissions structure in user_info"
                )
                return False

            # Check global permissions
            if "global" in event["user_info"]["permissions"]:
                for perm in required_permissions:
                    if perm in event["user_info"]["permissions"]["global"]:
                        self.logger.debug(
                            f"Permission granted via global permission: {perm}"
                        )
                        return True

            # Check channel-specific permissions
            if event["channel"] in event["user_info"]["permissions"]:
                for perm in required_permissions:
                    if perm in event["user_info"]["permissions"][event["channel"]]:
                        self.logger.debug(
                            f"Permission granted via channel permission: {perm} in {event['channel']}"
                        )
                        return True

        # For now, simple permission system - 'user' permission is granted to everyone
        if "user" in required_permissions:
            self.logger.debug("Granting 'user' permission to everyone")
            return True

        self.logger.debug(f"Permission denied for {event['nick']}")
        return False

    async def _process_output(self, event, output):
        """Process and send output messages."""
        if not output:
            return

        if len(output) > self.config["max_output_lines"]:
            self.logger.debug(
                f"Output has {len(output)} lines, combining into single line"
            )
            combined_message = " | ".join([line["msg"] for line in output])
            await self.message(event["channel"], combined_message)
        else:
            for line in output:
                if line["type"] == "say":
                    await self.message(event["channel"], line["msg"])
                elif line["type"] == "reply":
                    await self.message(
                        event["channel"], f"{event['nick']}, {line['msg']}"
                    )
                elif line["type"] == "private":
                    await self.message(event["nick"], line["msg"])

    # Helper methods for modules to use
    async def say(self, target, message):
        """Send a message to a channel or user"""
        await self.message(target, message)

    def reply(self, message):
        """Add a reply message to the output queue."""
        if self._active_output is not None:
            self._active_output.append({"type": "reply", "msg": message})

    def add_response(self, message, private=False):
        """Add a message to the output queue."""
        if self._active_output is not None:
            if private:
                self._active_output.append({"type": "private", "msg": message})
            else:
                self._active_output.append({"type": "say", "msg": message})


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
        tls_verify=bot.config.get("tls_verify", True),
    )


if __name__ == "__main__":
    main()
