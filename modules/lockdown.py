#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# PhreakBot - A modular IRC bot
# Lockdown module - Allows channel operators to lock down a channel
#

def config(pb):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["lockdown", "unlock"],
        "help": {
            "lockdown": "Lock down the channel (set +im). Usage: !lockdown",
            "unlock": "Unlock the channel (set -im). Usage: !unlock"
        },
        "permissions": ["admin", "owner"]
    }

def run(pb, event):
    """Handle lockdown commands"""
    if event["command"] == "lockdown":
        channel = event["channel"]
        
        # Check if this is a channel
        if not channel.startswith("#"):
            pb.reply("This command can only be used in a channel.")
            return
        
        # Set channel mode +im (invite-only and moderated)
        pb.connection.mode(channel, "+im")
        pb.reply(f"Channel {channel} is now locked down (mode +im).")
        
    elif event["command"] == "unlock":
        channel = event["channel"]
        
        # Check if this is a channel
        if not channel.startswith("#"):
            pb.reply("This command can only be used in a channel.")
            return
        
        # Set channel mode -im (remove invite-only and moderated)
        pb.connection.mode(channel, "-im")
        pb.reply(f"Channel {channel} is now unlocked (mode -im).")