#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Event handling and routing for PhreakBot."""

import re
import traceback


class EventsMixin:
    """Mixin for IRC event handling and module routing."""

    async def on_connect(self):
        """Called when bot has successfully connected to the server"""
        self.logger.info(f"Successfully connected to {self.network}")
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
        if message.source:
            hostmask = message.source
            nick = hostmask.split("!")[0] if "!" in hostmask else hostmask
            self.user_hostmasks[nick.lower()] = hostmask
            self.logger.info(f"Cached hostmask from raw JOIN: {hostmask}")
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
        output = []
        self._route_to_modules(event_obj, output)
        await self._process_output(event_obj, output)

    async def on_names(self, channel, names):
        """Called when the server sends a NAMES reply"""
        self.logger.info(f"Received NAMES reply for {channel}: {names}")
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
        output = []
        self._route_to_modules(event_obj, output)
        await self._process_output(event_obj, output)

    async def _handle_message(self, source, channel, message, is_private):
        """Process incoming messages and route to appropriate modules"""
        source = self._sanitize_nickname(source)
        channel = self._sanitize_channel_name(channel) if not is_private else source
        message = self._sanitize_input(message, max_length=500)

        user_host = self.user_hostmasks.get(source.lower())
        if not user_host:
            try:
                user_info = await self.whois(source)
                if user_info is None or not isinstance(user_info, dict):
                    self.logger.warning(
                        f"WHOIS returned None or invalid data for {source}, using fallback"
                    )
                    user_host = f"{source}!unknown@unknown"
                else:
                    user_host = f"{source}!{user_info.get('username', 'unknown')}@{user_info.get('hostname', 'unknown')}"
                    self.user_hostmasks[source.lower()] = user_host
            except Exception as e:
                self.logger.error(f"Error getting user info: {e}")
                user_host = f"{source}!unknown@unknown"
        else:
            self.logger.debug(f"Using cached hostmask for {source}: {user_host}")

        self.logger.debug(f"Formatted hostmask: {user_host}")
        self.logger.debug(f"Processing message from {source} in {channel}: '{message}'")

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

        trigger_re = self.trigger_re
        if trigger_re.match(message):
            self.logger.debug(f"RAW MESSAGE: '{message}'")

            if not self._check_rate_limit(user_host):
                self.logger.warning(
                    f"Rate limit exceeded for {user_host}, ignoring command"
                )
                if user_host not in self.rate_limit["banned_users"]:
                    await self.message(
                        channel,
                        f"{source}: Rate limit exceeded. Please slow down.",
                    )
                return

            command_re = re.compile(
                f'^{re.escape(self.config["trigger"])}([a-zA-Z0-9_][-a-zA-Z0-9_]*)(?:\\s(.*))?$'
            )
            match = command_re.match(message)
            self.logger.debug(f"Command match: {bool(match)}")

            if match:
                event_obj["command"] = match.group(1).lower()
                event_obj["command_args"] = self._sanitize_input(
                    match.group(2) or "", max_length=500
                )
                event_obj["trigger"] = "command"
                self.logger.debug(
                    f"Parsed command: '{event_obj['command']}' with args: '{event_obj['command_args']}'"
                )

                output = []
                self._route_to_modules(event_obj, output)
                await self._process_output(event_obj, output)
            else:
                self.logger.debug(
                    f"Message starts with trigger but doesn't match command pattern: '{message}'"
                )
                event_obj["trigger"] = "event"
                output = []
                self._route_to_modules(event_obj, output)
                await self._process_output(event_obj, output)
        else:
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

        self.user_hostmasks[user.lower()] = user_host

        if event_type == "join":
            self.logger.debug(f"JOIN: {user} ({user_host}) joined {channel}")
        elif event_type == "part":
            self.logger.debug(f"PART: {user} ({user_host}) left {channel}")
        elif event_type == "quit":
            self.logger.debug(f"QUIT: {user} ({user_host}) quit")
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
        handled = False

        self.logger.debug(
            f"Routing event: trigger={event['trigger']}, signal={event.get('signal', 'N/A')}, text={event.get('text', 'N/A')}"
        )

        # Check for custom infoitem commands first
        if not handled and "infoitems" in self.modules:
            try:
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

            self.logger.debug("Available modules and their commands:")
            for module_name, module in self.modules.items():
                self.logger.debug(
                    f"Module: {module_name}, Commands: {module['commands']}"
                )

            modules_copy = dict(self.modules)

            for module_name, module in modules_copy.items():
                if event["command"] in module["commands"]:
                    self.logger.debug(
                        f"Found module {module_name} to handle command {event['command']}"
                    )

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

            # If command not handled, try infoitems for custom patterns
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
