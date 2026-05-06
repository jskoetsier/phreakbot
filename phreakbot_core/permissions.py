#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Permission checking for PhreakBot."""

import psycopg2


class PermissionMixin:
    """Mixin for owner detection and permission validation."""

    def _is_owner(self, hostmask):
        """Check if a hostmask matches an owner in the database"""
        if not self.db_pool:
            return False

        try:
            self.logger.debug(f"Checking owner status for hostmask: {hostmask}")
            nick = hostmask.split("!")[0] if "!" in hostmask else hostmask
            self.logger.debug(f"Extracted nick: {nick}")

            # First try the exact hostmask
            user_info = self.db_get_userinfo_by_userhost(hostmask)
            if user_info and user_info.get("is_owner"):
                self.logger.debug(f"User with hostmask {hostmask} is an owner in the database")
                return True

            # Try normalized hostmask (remove caret)
            normalized_hostmask = hostmask
            if "!" in hostmask:
                parts = hostmask.split("!")
                if len(parts) == 2 and parts[1].startswith("^"):
                    normalized_hostmask = f"{parts[0]}!{parts[1][1:]}"
                    self.logger.debug(f"Normalized hostmask: {normalized_hostmask}")
                    user_info = self.db_get_userinfo_by_userhost(normalized_hostmask)
                    if user_info and user_info.get("is_owner"):
                        self.logger.debug(f"User with normalized hostmask {normalized_hostmask} is an owner")
                        return True

            # Check by username
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
                        self.logger.debug(f"User with nick {nick} is an owner in the database")
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
        self.logger.debug(
            f"Checking permissions: {required_permissions} for user {event['nick']}"
        )

        # Validate event object has required fields
        required_fields = ["nick", "hostmask", "channel", "trigger"]
        for field in required_fields:
            if field not in event:
                self.logger.error(
                    f"Security: Invalid event object missing field '{field}'"
                )
                return False

        # Check if user is temporarily banned
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
            if not isinstance(event["user_info"]["permissions"], dict):
                self.logger.error("Security: Invalid permissions structure in user_info")
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

        # 'user' permission is granted to everyone
        if "user" in required_permissions:
            self.logger.debug("Granting 'user' permission to everyone")
            return True

        self.logger.debug(f"Permission denied for {event['nick']}")
        return False
