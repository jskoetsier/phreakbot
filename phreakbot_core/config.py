#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Configuration management for PhreakBot."""

import json
import os
import sys


class ConfigMixin:
    """Mixin for configuration loading and saving."""

    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, "r") as f:
                self.config = json.load(f)

            # Set default values for missing config options
            defaults = {
                "server": "irc.libera.chat",
                "port": 6667,
                "nickname": "PhreakBot",
                "realname": "PhreakBot IRC Bot",
                "channels": ["#phreakbot"],
                "owner": "",
                "trigger": "!",
                "max_output_lines": 3,
            }
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value

            # Database configuration - use environment variables if available
            db_defaults = {
                "db_host": ("DB_HOST", "localhost"),
                "db_port": ("DB_PORT", "5432"),
                "db_user": ("DB_USER", "phreakbot"),
                "db_password": ("DB_PASSWORD", "phreakbot"),
                "db_name": ("DB_NAME", "phreakbot"),
            }
            for key, (env_var, default) in db_defaults.items():
                if key not in self.config:
                    self.config[key] = os.environ.get(env_var, default)

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
