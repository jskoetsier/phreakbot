#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

def config(pb):
    return {
        'events': ['irc_in2_VERSION'],
        'commands': ['version'],
        'help': {
            'version': 'Display the bot version'
        }
    }

def get_version():
    """Get the bot version from the VERSION file."""
    version_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'VERSION')
    try:
        with open(version_file, 'r') as f:
            return f.read().strip()
    except Exception:
        return "unknown"

def version(pb, event):
    """Display the bot version."""
    version = get_version()
    pb.reply(event, f"PhreakBot v{version} - https://github.com/jskoetsier/phreakbot")

def irc_in2_VERSION(pb, event):
    """Handle CTCP VERSION requests."""
    version = get_version()
    # Override the default Python irc.bot VERSION reply with our own
    pb.connection.ctcp_reply(event.source.nick, f"PhreakBot v{version} - https://github.com/jskoetsier/phreakbot")
