#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot IRC Bot
# https://github.com/johansebastiaan/phreakbot
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import platform
import irc.client

def config(pb):
    pb.register_command('version', version_command)
    pb.register_ctcp_handler('VERSION', ctcp_version_handler)

def version_command(pb, event, args):
    """Display version information about the bot."""
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'VERSION'), 'r') as f:
        version = f.read().strip()

    pb.privmsg(event.target, f"PhreakBot v{version} running on Python {platform.python_version()} ({platform.system()} {platform.release()})")

def ctcp_version_handler(pb, event):
    """Handle CTCP VERSION requests."""
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'VERSION'), 'r') as f:
        version = f.read().strip()

    pb.ctcp_reply(event.source.nick, 'VERSION', f"PhreakBot v{version} running on Python {platform.python_version()} ({platform.system()} {platform.release()})")
