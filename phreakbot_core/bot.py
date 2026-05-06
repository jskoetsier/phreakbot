#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PhreakBot main class combining all mixins."""

import argparse
import importlib.util
import logging
import os
import re
import sys

import pydle

from .cache import CacheMixin
from .config import ConfigMixin
from .database import DatabaseMixin
from .events import EventsMixin
from .permissions import PermissionMixin
from .security import SecurityMixin


class PhreakBot(
    SecurityMixin,
    CacheMixin,
    DatabaseMixin,
    PermissionMixin,
    EventsMixin,
    ConfigMixin,
    pydle.Client,
):
    """Modular IRC bot using pydle."""

    def __init__(self, config_path, *args, **kwargs):
        self.config_path = config_path
        self.load_config()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(self.config.get("log_file", "phreakbot.log")),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("PhreakBot")

        self.modules = {}
        self.db_pool = None
        self.re = re
        self.state = {}
        self.user_hostmasks = {}

        self.rate_limit = {
            "user_commands": __import__("collections").defaultdict(list),
            "max_commands_per_minute": 10,
            "max_commands_per_10_seconds": 5,
            "global_commands": [],
            "max_global_commands_per_second": 20,
            "banned_users": {},
            "ban_duration": 300,
        }

        self.cache = {
            "user_permissions": {},
            "user_info": {},
            "cache_ttl": 300,
            "cache_timestamps": {},
        }

        self.trigger_re = re.compile(f'^{re.escape(self.config["trigger"])}')
        self.bot_trigger_re = re.compile(f'^{re.escape(self.config["trigger"])}')

        self.db_connect()

        super().__init__(
            nickname=self.config["nickname"],
            realname=self.config["realname"],
            *args,
            **kwargs,
        )

        self.bot_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.modules_dir = os.path.join(self.bot_base, "modules")
        self.extra_modules_dir = os.path.join(
            self.bot_base, "phreakbot_core", "extra_modules"
        )

        for path in [self.modules_dir, self.extra_modules_dir]:
            if not os.path.exists(path):
                os.makedirs(path)
                self.logger.info(f"Created directory: {path}")

        self.load_all_modules()

    def load_all_modules(self):
        """Load all modules from the modules directory"""
        self.logger.info("Loading modules...")

        modules_dir = os.path.join(self.bot_base, "modules")
        if os.path.exists(modules_dir):
            for filename in os.listdir(modules_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    self.load_module(os.path.join(modules_dir, filename))

        if os.path.exists(self.extra_modules_dir):
            for filename in os.listdir(self.extra_modules_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    self.load_module(os.path.join(self.extra_modules_dir, filename))

        self.logger.info(f"Loaded modules: {', '.join(self.modules.keys())}")

    def load_module(self, module_path):
        """Load a module from file"""
        module_name = os.path.basename(module_path)[:-3]

        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None:
                self.logger.error(
                    f"Failed to load module {module_name}: Could not create spec"
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

            if not hasattr(module_object, "config"):
                self.logger.error(
                    f"Module {module_name} does not have a config() function"
                )
                return False

            module_config = module_object.config(self)

            for key in ["events", "commands", "help"]:
                if key not in module_config:
                    self.logger.error(
                        f"Module {module_name} config does not provide '{key}' key"
                    )
                    return False

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


def main():
    parser = argparse.ArgumentParser(description="PhreakBot IRC Bot")
    parser.add_argument(
        "-c", "--config", default="config.json", help="Path to config file"
    )
    args = parser.parse_args()

    bot = PhreakBot(args.config)
    bot.run(
        bot.config["server"],
        bot.config["port"],
        tls=bot.config.get("use_tls", False),
        tls_verify=bot.config.get("tls_verify", True),
    )


if __name__ == "__main__":
    main()
