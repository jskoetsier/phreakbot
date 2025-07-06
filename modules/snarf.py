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
        "events": [],
        "commands": ["@", "snarf"],
        "permissions": ["user"],
        "help": "Fetch the description of a URL.\n"
                "Usage: !@ <url> - Fetch the description of the given URL\n"
                "       !snarf <url> - Same as !@",
    }


def run(pb, event):
    """Handle snarf commands"""
    # Get the URL from the command arguments
    url = event["command_args"].strip()

    if not url:
        pb.add_response("Please provide a URL to fetch the description.")
        return

    # Add http:// prefix if missing
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    try:
        # Fetch the description
        title, description = get_url_info(url)

        # Display the results
        if title:
            pb.add_response(f"Title: {title}")

        if description:
            pb.add_response(f"Description: {description}")
        else:
            pb.add_response("No description found for this URL.")

    except Exception as e:
        pb.logger.error(f"Error fetching URL info: {e}")
        pb.add_response(f"Error fetching information from URL: {str(e)}")


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
    title = title_tag.string.strip() if title_tag else None

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
