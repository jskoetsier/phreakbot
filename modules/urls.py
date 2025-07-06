#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# URLs module for PhreakBot

import re

import requests
from bs4 import BeautifulSoup


def config(bot):
    """Return module configuration"""
    return {
        "events": ["pubmsg"],
        "commands": [],
        "permissions": ["user"],
        "help": "Automatically detects URLs in chat messages and displays their titles.",
    }


def run(bot, event):
    """Handle URL detection in messages"""
    # Only process event messages, not commands
    if event["trigger"] != "event" or event["signal"] != "pubmsg":
        return

    # Extract URLs from the message
    urls = extract_urls(event["text"])

    if not urls:
        return

    # Process only the first URL to avoid spam
    url = urls[0]

    try:
        title = get_url_title(url)
        if title:
            bot.add_response(f"Title: {title}")
    except Exception as e:
        bot.logger.error(f"Error fetching URL title: {e}")


def extract_urls(text):
    """Extract URLs from text"""
    url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    return url_pattern.findall(text)


def get_url_title(url):
    """Get the title of a webpage"""
    # Add http:// prefix if missing
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    # Set a timeout and user agent
    headers = {"User-Agent": "PhreakBot/1.0 URL Title Fetcher"}

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()

        # Parse the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Get the title
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.string.strip()
            # Limit title length
            if len(title) > 200:
                title = title[:197] + "..."
            return title
    except:
        # Silently fail on any error
        pass

    return None
