import json
import re
from datetime import datetime

import requests


def config(bot):
    return {
        "commands": ["hassver", "haver"],
        "permissions": ["user"],
        "events": [],
        "help": "Fetches latest HomeAssistant release info.",
    }


def run(bot, event):
    # Only run in a specific channel :)
    if event["channel"] not in ["#nlhomeautomation", "#fdi-status"]:
        return bot.signal_cont

    req = requests.get("https://www.home-assistant.io/version.json")
    jsontxt = req.text
    try:
        obj = json.loads(jsontxt)
    except Exception as e:
        bot.add_response(f"Parsing content failed: {e}")
        return bot.signal_cont
    release_date_obj = datetime.fromisoformat(obj["release_date"])

    bot.add_response(
        f"Latest Home Assistant version is {obj['current_version']} released {release_date_obj.strftime('%Y-%m-%d')}, see https://github.com/home-assistant/core/releases/tag/{obj['current_version']} !"
    )

    # Update the topic for the channel if bot has permission
    # Note: This functionality requires the bot to have channel operator privileges
    try:
        if event["bot_is_op"]:
            # Get current topic
            current_topic = ""
            if hasattr(event, "raw_event") and hasattr(event["raw_event"], "target"):
                # Try to get topic from IRC library
                channel = event["connection"].channels.get(event["channel"])
                if channel and hasattr(channel, "topic"):
                    current_topic = channel.topic

            if current_topic:
                topic_parts = current_topic.split("|")
                new_topic_parts = []
                set_topic = True
                found = False

                for part in topic_parts:
                    topic_part = part.strip()
                    if not topic_part:
                        set_topic = True
                        continue

                    new_part = topic_part
                    match = re.match(r"^\s*LastHass: ([^\s]+) released", topic_part)
                    if match:
                        found = True
                        if obj["current_version"] == match.group(1):
                            set_topic = False
                        else:
                            new_part = f"LastHass: {obj['current_version']} released {release_date_obj.strftime('%Y-%m-%d')}"
                    new_topic_parts.append(new_part)

                if not found:
                    new_topic_parts.append(
                        f"LastHass: {obj['current_version']} released {release_date_obj.strftime('%Y-%m-%d')}"
                    )

                if set_topic:
                    new_topic = " | ".join(new_topic_parts)
                    event["connection"].topic(event["channel"], new_topic)
    except Exception as e:
        bot.add_response(f"Failed to update topic: {e}")

    return bot.signal_stop
