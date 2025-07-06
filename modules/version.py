#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

def config(wcb):
    return {
        'events': ['irc_in2_VERSION'],
        'commands': ['version'],
        'help': {
            'version': 'Shows the version of the bot'
        }
    }

def get_version():
    version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VERSION')
    try:
        with open(version_file, 'r') as f:
            version = f.read().strip()
        return version
    except Exception:
        return "unknown"

def version(wcb, event):
    version = get_version()
    wcb.reply(event, f"PhreakBot v{version} - https://github.com/jskoetsier/phreakbot")

def irc_in2_VERSION(wcb, event):
    version = get_version()
    wcb.connection.ctcp_reply(event.source.nick, f"VERSION PhreakBot v{version} - https://github.com/jskoetsier/phreakbot")
