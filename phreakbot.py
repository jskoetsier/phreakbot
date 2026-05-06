#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot - A modular IRC bot using pydle
#
# This file re-exports the PhreakBot class from phreakbot_core for backward
# compatibility. The core implementation has been split into focused modules
# under the phreakbot_core/ package.
#
# Core modules:
#   phreakbot_core/config.py    - Configuration management
#   phreakbot_core/database.py  - Database connection pooling
#   phreakbot_core/security.py  - Input sanitization and rate limiting
#   phreakbot_core/cache.py     - TTL-based caching
#   phreakbot_core/permissions.py - Owner detection and permission checks
#   phreakbot_core/events.py    - IRC event handling and module routing
#   phreakbot_core/bot.py       - PhreakBot class combining all mixins
#

# Keep these imports for backward compatibility with tests that patch them
import psycopg2
import psycopg2.extras
import psycopg2.pool

# Re-export PhreakBot and main from phreakbot_core
from phreakbot_core.bot import PhreakBot, main

__all__ = ["PhreakBot", "main"]
