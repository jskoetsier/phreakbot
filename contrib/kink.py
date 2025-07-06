import json

import requests


def config(bot):
    return {
        "events": [],
        "commands": ["kink"],
        "permissions": ["user"],
        "help": "K!NK Now Playing",
    }


def run(bot, event):
    # Only run in a specific channel :)
    if event["channel"] not in ["#cistron", "#fdi-status"]:
        return bot.signal_cont

    try:
        res = requests.get("https://api.kink.nl/static/now-playing.json")
    except Exception as err:
        return bot.reply(f"i failed: '{err}'")

    try:
        obj = json.loads(res.text)
        cur = obj["playing"]
    except Exception as err:
        return bot.reply(f"i failed: '{err}'")

    return bot.reply(f"ꓘINK is currently playing: '{cur}'")
