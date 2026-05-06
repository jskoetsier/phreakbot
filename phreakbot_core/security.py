#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Security utilities for PhreakBot: sanitization and rate limiting."""

import time
from collections import defaultdict


class SecurityMixin:
    """Mixin for input sanitization and rate limiting."""

    def _sanitize_input(self, input_str, max_length=500):
        """Sanitize user input: truncate, remove null bytes and control chars.

        SQL injection is prevented by using parameterized queries throughout
        the codebase, so we do not filter SQL-specific patterns here.
        Shell injection is prevented by not executing user input as shell
        commands (the !exec module has been removed).
        """
        if not isinstance(input_str, str):
            return ""

        sanitized = input_str[:max_length]
        sanitized = sanitized.replace("\x00", "")
        sanitized = "".join(
            char for char in sanitized if char.isprintable() or char in "\n\t"
        )
        return sanitized.strip()

    def _sanitize_channel_name(self, channel):
        """Sanitize channel name to prevent injection"""
        if not isinstance(channel, str):
            return "#unknown"

        if not channel or channel[0] not in "#&":
            return "#unknown"

        sanitized = channel[:50]
        sanitized = "".join(
            c for c in sanitized if c.isalnum() or c in "#&-_"
        )
        return sanitized or "#unknown"

    def _sanitize_nickname(self, nickname):
        """Sanitize nickname to prevent injection"""
        if not isinstance(nickname, str):
            return "unknown"

        sanitized = nickname[:30]
        sanitized = "".join(
            c for c in sanitized if c.isalnum() or c in "-_[]{}\\`|^"
        )
        return sanitized or "unknown"

    def _check_rate_limit(self, hostmask):
        """Check if user is within rate limits. Returns True if allowed, False if blocked."""
        current_time = time.time()

        # Check if user is banned
        if hostmask in self.rate_limit["banned_users"]:
            ban_time = self.rate_limit["banned_users"][hostmask]
            if current_time < ban_time:
                return False
            else:
                del self.rate_limit["banned_users"][hostmask]

        # Clean up old timestamps
        cutoff_minute = current_time - 60
        cutoff_10sec = current_time - 10
        cutoff_second = current_time - 1

        user_commands = self.rate_limit["user_commands"][hostmask]
        user_commands = [t for t in user_commands if t > cutoff_minute]
        self.rate_limit["user_commands"][hostmask] = user_commands

        global_commands = self.rate_limit["global_commands"]
        self.rate_limit["global_commands"] = [t for t in global_commands if t > cutoff_second]

        # Check per-10-seconds limit
        recent_10sec = [t for t in user_commands if t > cutoff_10sec]
        if len(recent_10sec) >= self.rate_limit["max_commands_per_10_seconds"]:
            return False

        # Check per-minute limit
        if len(user_commands) >= self.rate_limit["max_commands_per_minute"]:
            self.rate_limit["banned_users"][hostmask] = current_time + self.rate_limit["ban_duration"]
            return False

        # Check global limit
        if len(self.rate_limit["global_commands"]) >= self.rate_limit["max_global_commands_per_second"]:
            return False

        # Record command timestamp
        user_commands.append(current_time)
        self.rate_limit["global_commands"].append(current_time)
        return True
