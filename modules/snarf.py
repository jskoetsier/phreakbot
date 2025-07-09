#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Snarf module for PhreakBot
#
# This module implements the snarf/!@ function that fetches the description
# of a URL of a website.

import re
import requests
from bs4 import BeautifulSoup


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg"],  # Listen for public messages for !@ command
        "commands": ["url", "snarf", "at"],
        "permissions": ["user"],
        "help": "Fetch the description of a URL. Usage: !url <url>, !snarf <url>, !at <url>, or !@ <url>",
    }


def run(bot, event):
    """Handle snarf commands and events"""
    try:
        # Handle !@ command through event processing
        if event["trigger"] == "event" and event["signal"] in ["pubmsg", "privmsg"]:
            message = event["text"]
            bot.logger.info(f"Checking message for !@ command: {message}")

            # Check if message starts with !@
            if message.startswith("!@"):
                bot.logger.info("Found !@ command in message")
                # Extract URL (everything after !@)
                url = message[2:].strip()
                if url:
                    bot.logger.info(f"Processing URL from !@ command: {url}")
                    process_url(bot, event, url)
                    # Add a debug response to confirm the command was processed
                    bot.add_response("DEBUG: !@ command processed")
                else:
                    bot.add_response("Please provide a URL after !@")
                return

        # Handle regular commands
        if event["trigger"] == "command":
            bot.logger.info(f"Snarf module called with command: {event['command']}")

            # Get the URL from the command arguments
            url = event["command_args"].strip()

            bot.logger.info(f"URL argument: '{url}'")

            if not url:
                bot.logger.info("No URL provided")
                bot.add_response("Please provide a URL to fetch the description.")
                return

            process_url(bot, event, url)

    except Exception as e:
        # Catch-all exception handler to prevent the bot from crashing
        bot.logger.error(f"Critical error in snarf module: {e}")
        import traceback
        bot.logger.error(f"Critical traceback: {traceback.format_exc()}")
        try:
            bot.add_response("An error occurred while processing the URL.")
        except:
            pass


def process_url(bot, event, url):
    """Process a URL and display its title and description"""
    try:
        # Add http:// prefix if missing
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        bot.logger.info(f"Processing URL: {url}")

        # Fetch the description
        bot.logger.info(f"Fetching info for URL: {url}")
        title, description = get_url_info(url)

        bot.logger.info(f"Retrieved title: {title}")
        bot.logger.info(f"Retrieved description: {description}")

        # Display the results
        if title:
            bot.add_response(f"Title: {title}")
            bot.logger.info(f"Added title response: {title}")

        if description:
            bot.add_response(f"Description: {description}")
            bot.logger.info(f"Added description response: {description}")
        else:
            bot.add_response("No description found for this URL.")
            bot.logger.info("No description found")

    except Exception as e:
        bot.logger.error(f"Error fetching URL info: {e}")
        bot.add_response(f"Error fetching information from URL: {str(e)}")
        import traceback
        bot.logger.error(f"Traceback: {traceback.format_exc()}")


def get_url_info(url):
    """Get the title and description of a webpage"""
    # Set a timeout and user agent
    headers = {"User-Agent": "PhreakBot/1.0 URL Description Fetcher"}

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    # Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Get the title
    title_tag = soup.find("title")
    title = title_tag.string.strip() if title_tag and title_tag.string else None

    # Limit title length
    if title and len(title) > 200:
        title = title[:197] + "..."

    # Get the description from meta tags
    description = None

    # Try Open Graph description first
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        description = og_desc["content"].strip()

    # Try Twitter description next
    if not description:
        twitter_desc = soup.find("meta", attrs={"name": "twitter:description"})
        if twitter_desc and twitter_desc.get("content"):
            description = twitter_desc["content"].strip()

    # Try standard meta description as fallback
    if not description:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"].strip()

    # Limit description length
    if description and len(description) > 300:
        description = description[:297] + "..."

    return title, description
