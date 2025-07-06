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


def config(pb):
    """Return module configuration"""
    return {
        "events": ["pubmsg"],  # Listen for public messages for !@ command
        "commands": ["url", "snarf", "at"],
        "permissions": ["user"],
        "help": "Fetch the description of a URL. Usage: !url <url>, !snarf <url>, !at <url>, or !@ <url>",
    }


def run(pb, event):
    """Handle snarf commands and events"""
    try:
        # Handle !@ command through event processing
        if event["trigger"] == "event" and event["signal"] == "pubmsg":
            message = event["text"]
            pb.logger.info(f"Checking message for !@ command: {message}")

            # Check if message starts with !@
            if message.startswith("!@"):
                pb.logger.info("Found !@ command in message")
                # Extract URL (everything after !@)
                url = message[2:].strip()
                if url:
                    pb.logger.info(f"Processing URL from !@ command: {url}")
                    process_url(pb, event, url)
                return

        # Handle regular commands
        if event["trigger"] == "command":
            pb.logger.info(f"Snarf module called with command: {event['command']}")

            # Get the URL from the command arguments
            url = event["command_args"].strip()

            pb.logger.info(f"URL argument: '{url}'")

            if not url:
                pb.logger.info("No URL provided")
                pb.add_response("Please provide a URL to fetch the description.")
                return

            process_url(pb, event, url)

    except Exception as e:
        # Catch-all exception handler to prevent the bot from crashing
        pb.logger.error(f"Critical error in snarf module: {e}")
        import traceback
        pb.logger.error(f"Critical traceback: {traceback.format_exc()}")
        try:
            pb.add_response("An error occurred while processing the URL.")
        except:
            pass


def process_url(pb, event, url):
    """Process a URL and display its title and description"""
    try:
        # Add http:// prefix if missing
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        pb.logger.info(f"Processing URL: {url}")

        # Fetch the description
        pb.logger.info(f"Fetching info for URL: {url}")
        title, description = get_url_info(url)

        pb.logger.info(f"Retrieved title: {title}")
        pb.logger.info(f"Retrieved description: {description}")

        # Display the results
        if title:
            pb.add_response(f"Title: {title}")
            pb.logger.info(f"Added title response: {title}")

        if description:
            pb.add_response(f"Description: {description}")
            pb.logger.info(f"Added description response: {description}")
        else:
            pb.add_response("No description found for this URL.")
            pb.logger.info("No description found")

    except Exception as e:
        pb.logger.error(f"Error fetching URL info: {e}")
        pb.add_response(f"Error fetching information from URL: {str(e)}")
        import traceback
        pb.logger.error(f"Traceback: {traceback.format_exc()}")


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
