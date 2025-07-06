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
        "commands": ["url", "snarf", "@"],
        "permissions": ["user"],
        "help": "Fetch the description of a URL.\n"
                "Usage: !@ <url> - Fetch the description of the given URL\n"
                "       !url <url> - Same as !@\n"
                "       !snarf <url> - Same as !@",
    }


def run(pb, event):
    """Handle snarf commands"""
    try:
        pb.logger.info(f"Snarf module called with command: {event['command']}")
        
        # Get the URL from the command arguments
        url = event["command_args"].strip()
        
        pb.logger.info(f"URL argument: '{url}'")
        
        if not url:
            pb.logger.info("No URL provided")
            pb.say(event["channel"], "Please provide a URL to fetch the description.")
            return

        # Add http:// prefix if missing
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        
        pb.logger.info(f"Processing URL: {url}")
        
        try:
            # Fetch the description
            pb.logger.info(f"Fetching info for URL: {url}")
            title, description = get_url_info(url)
            
            pb.logger.info(f"Retrieved title: {title}")
            pb.logger.info(f"Retrieved description: {description}")

            # Display the results
            if title:
                pb.say(event["channel"], f"Title: {title}")
                pb.logger.info(f"Added title response: {title}")

            if description:
                pb.say(event["channel"], f"Description: {description}")
                pb.logger.info(f"Added description response: {description}")
            else:
                pb.say(event["channel"], "No description found for this URL.")
                pb.logger.info("No description found")

        except Exception as e:
            pb.logger.error(f"Error fetching URL info: {e}")
            pb.say(event["channel"], f"Error fetching information from URL: {str(e)}")
            import traceback
            pb.logger.error(f"Traceback: {traceback.format_exc()}")
    
    except Exception as e:
        # Catch-all exception handler to prevent the bot from crashing
        pb.logger.error(f"Critical error in snarf module: {e}")
        import traceback
        pb.logger.error(f"Critical traceback: {traceback.format_exc()}")
        try:
            pb.say(event["channel"], "An error occurred while processing the URL.")
        except:
            pass


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
