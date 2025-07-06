#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Choice module for PhreakBot

import random


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["choose", "choice"],
        "permissions": ["user"],
        "help": "Helps decide between multiple options.\n"
        "Usage: !choice option1 option2 option3 ... - Randomly selects one of the provided options",
    }


def run(bot, event):
    """Handle choice commands"""
    # Clean up the input by replacing multiple spaces with a single space
    valstr = bot.re.sub(r"\s+", " ", event["command_args"]).strip()

    if not valstr:
        bot.add_response("Please provide your options!")
        return

    # Split the input into an array of options
    valarr = valstr.split(" ")

    # Randomly select one of the options
    val = random.choice(valarr)

    bot.add_response(val)
