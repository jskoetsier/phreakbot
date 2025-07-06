#! /usr/bin/env python3

"""
Query IRRExplorer for routing information on an IP or prefix.

Written by Teun Vink <teun AT teun DOT tv>
"""

import requests
from netaddr import IPNetwork


def config(bot):
    return {
        "events": [],
        "commands": ["irr", "irrexplorer"],
        "permissions": ["user"],
        "help": ["Show IRRExplorer information for a prefix"],
    }


def _print_items(bot, results, status):
    """
    Fancy output for statuses.
    """
    STATUS = {
        "success": "\0039OK\003\002\002",
        "danger": "\0034ERROR\003\002\002",
        "warning": "\0038WARNING\003\002\002",
        "info": "\00312INFO\003\002\002",
    }

    for prefix in results.get(status, []):
        for msg in results[status][prefix]:
            bot.add_response(f"[{STATUS[status]}] {prefix}: {msg}")


def run(bot, event):
    net = event["command_args"]
    try:
        # typecast to IPNetwork so we know it's a valid IP or prefix
        IPNetwork(net)
    except Exception:
        bot.add_response(f"{net} is not a valid IP or prefix.")
        return

    req = requests.get(f"https://irrexplorer.nlnog.net/api/prefixes/prefix/{net}")
    # check results
    if req.status_code != 200:
        bot.add_response(f"Failed to query IRRExplorer: {req.text}")
        return
    try:
        data = req.json()
    except Exception:
        bot.add_response("Failed to parse IRRExplorer answer.")
        return

    # sort the results by category and prefix
    results = {}
    for item in data:
        pfx = f"{item['prefix']}"
        if len(item.get("bgpOrigins", [])) > 0:
            origins = ", ".join([f"AS{asn}" for asn in item["bgpOrigins"]])
            pfx = f"{pfx} ({origins})"
        for message in item["messages"]:
            cat = message["category"]
            if cat not in results:
                results[cat] = {pfx: []}
            if pfx not in results[cat]:
                results[cat][pfx] = []
            results[cat][pfx].append(message["text"])

    # always print these categories
    for status in ["success", "danger", "warning"]:
        _print_items(bot, results, status)

    # some prefixes have MANY info items, only print them if there are 3 or less
    infoitems = results.get("info", {})
    infocount = sum([len(infoitems[p]) for p in infoitems])
    if infocount <= 3:
        _print_items(bot, results, "info")
    else:
        bot.add_response("Too many 'info' items found, not showing them here.")

    # print some details
    bot.add_response(f"More details: https://irrexplorer.nlnog.net/prefix/{net}")
