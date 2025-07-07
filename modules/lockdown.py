#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lockdown module for PhreakBot
Allows channel operators to quickly set the channel to invite-only mode (+i)
"""

import logging

def config(pb):
    """Configure the lockdown module"""
    return {
        'commands': ['lockdown', 'unlock'],
        'help': {
            'lockdown': 'Set the channel to invite-only mode (+i)',
            'unlock': 'Remove invite-only mode (-i) from the channel'
        }
    }

def lockdown(pb, event, args):
    """Set the channel to invite-only mode (+i)"""
    channel = event.target
    nick = event.source.nick
    
    # Check if the user has permission (is op or higher)
    if not pb.is_op_or_higher(channel, nick):
        pb.msg(channel, f"{nick}: You don't have permission to use this command.")
        return
    
    try:
        pb.connection.mode(channel, '+i')
        pb.msg(channel, f"Channel {channel} is now in lockdown mode (invite-only).")
        logging.info(f"User {nick} set {channel} to invite-only mode")
    except Exception as e:
        pb.msg(channel, f"Error setting channel mode: {str(e)}")
        logging.error(f"Error setting channel mode: {str(e)}")

def unlock(pb, event, args):
    """Remove invite-only mode (-i) from the channel"""
    channel = event.target
    nick = event.source.nick
    
    # Check if the user has permission (is op or higher)
    if not pb.is_op_or_higher(channel, nick):
        pb.msg(channel, f"{nick}: You don't have permission to use this command.")
        return
    
    try:
        pb.connection.mode(channel, '-i')
        pb.msg(channel, f"Channel {channel} is now unlocked (removed invite-only mode).")
        logging.info(f"User {nick} removed invite-only mode from {channel}")
    except Exception as e:
        pb.msg(channel, f"Error setting channel mode: {str(e)}")
        logging.error(f"Error setting channel mode: {str(e)}")