#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# IRRExplorer module for PhreakBot
# Checks routing information for an IP or prefix

import requests
from netaddr import IPNetwork


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["irr", "irrexplorer", "roa"],
        "permissions": ["user"],
        "help": "Check routing information for an IP or prefix using IRRExplorer.\n"
        "Usage: !irr <ip_or_prefix> - Show IRRExplorer information\n"
        "       !roa <ip_or_prefix> - Alias for !irr (checks ROA status)\n"
        "       !irrexplorer <ip_or_prefix> - Alias for !irr",
    }


def _print_items(bot, results, status):
    """
    Fancy output for statuses.
    """
    STATUS = {
        "success": "✅",
        "danger": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
    }

    for prefix in results.get(status, []):
        for msg in results[status][prefix]:
            bot.add_response(f"{STATUS[status]} {prefix}: {msg}")


def run(bot, event):
    """Handle IRRExplorer commands"""
    net = event["command_args"]
    if not net:
        bot.add_response("Please specify an IP address or prefix to check.")
        return
        
    try:
        # typecast to IPNetwork so we know it's a valid IP or prefix
        IPNetwork(net)
    except Exception:
        bot.add_response(f"{net} is not a valid IP or prefix.")
        return

    try:
        bot.logger.info(f"Querying IRRExplorer for {net}")
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

        # Check if we have any results
        if not any(results.get(status, {}) for status in ["success", "danger", "warning", "info"]):
            bot.add_response(f"No routing information found for {net}")
            return

        # always print these categories
        for status in ["success", "danger", "warning"]:
            _print_items(bot, results, status)

        # some prefixes have MANY info items, only print them if there are 3 or less
        infoitems = results.get("info", {})
        infocount = sum([len(infoitems[p]) for p in infoitems])
        if infocount <= 3:
            _print_items(bot, results, "info")
        else:
            bot.add_response(f"ℹ️ {infocount} 'info' items found, not showing them here.")

        # print some details
        bot.add_response(f"More details: https://irrexplorer.nlnog.net/prefix/{net}")
        
    except Exception as e:
        bot.logger.error(f"Error checking routing information for {net}: {str(e)}")
        bot.add_response(f"Error checking routing information for {net}: {str(e)}")