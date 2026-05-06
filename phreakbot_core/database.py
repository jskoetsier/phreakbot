#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database connection management for PhreakBot."""

import time

import psycopg2
import psycopg2.pool


class DatabaseMixin:
    """Mixin for database connection pooling and queries."""

    def db_connect(self, max_retries=3, retry_delay=5):
        """Connect to the PostgreSQL database with connection pooling"""
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    f"Creating database connection pool at {self.config['db_host']}:{self.config['db_port']} (attempt {attempt + 1}/{max_retries})"
                )
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

    def db_get_userinfo_by_userhost(self, hostmask):
        """Get user info by hostmask from database"""
        if not self.db_pool:
            return None

        # Check cache first
        cached = self._cache_get("user_info", hostmask)
        if cached:
            return cached

        conn = self.db_get()
        if not conn:
            return None

        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "SELECT u.id, u.username, u.is_admin, u.is_owner, "
                "array_agg(DISTINCT h.hostmask) as hostmasks, "
                "array_agg(DISTINCT p.permission) FILTER (WHERE p.channel = '') as global_perms, "
                "array_agg(DISTINCT p.permission || ':' || p.channel) FILTER (WHERE p.channel != '') as channel_perms "
                "FROM phreakbot_users u "
                "LEFT JOIN phreakbot_hostmasks h ON h.users_id = u.id "
                "LEFT JOIN phreakbot_perms p ON p.users_id = u.id "
                "WHERE h.hostmask = %s OR u.username = %s "
                "GROUP BY u.id",
                (hostmask, hostmask.split("!")[0] if "!" in hostmask else hostmask),
            )
            user = cur.fetchone()
            cur.close()
            self.db_return(conn)

            if user:
                user_info = {
                    "id": user["id"],
                    "username": user["username"],
                    "is_admin": user["is_admin"],
                    "is_owner": user["is_owner"],
                    "hostmasks": user["hostmasks"] or [],
                    "permissions": {
                        "global": user["global_perms"] or [],
                    },
                }
                # Parse channel-specific permissions
                if user["channel_perms"]:
                    for perm_channel in user["channel_perms"]:
                        if ":" in perm_channel:
                            perm, channel = perm_channel.rsplit(":", 1)
                            if channel not in user_info["permissions"]:
                                user_info["permissions"][channel] = []
                            user_info["permissions"][channel].append(perm)

                self._cache_set("user_info", hostmask, user_info)
                return user_info
        except Exception as e:
            self.logger.error(f"Error getting user info: {e}")
            self.db_return(conn)

        return None
