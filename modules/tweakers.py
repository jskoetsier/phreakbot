#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Tweakers.net module for PhreakBot

import requests
import time
import sys

# Check if this module is being reloaded
if 'tweakers' in sys.modules:
    # This is a reload, not a fresh import
    print("Tweakers module is being reloaded")


def config(bot):
    """Return module configuration"""
    return {
        "events": [],
        "commands": ["tweakers", "tw"],
        "permissions": ["user"],
        "help": "Fetches the latest articles from tweakers.net.\n"
        "Usage: !tweakers - Show the 5 most recent articles\n"
        "       !tw - Alias for !tweakers",
    }


def run(bot, event):
    """Handle tweakers command"""
    if event["command"] not in ["tweakers", "tw"]:
        return

    try:
        # Use a simpler approach with just requests
        bot.add_response("Fetching latest articles from tweakers.net...")
        
        # Use a session for better performance
        session = requests.Session()
        
        # Set a timeout and user agent
        headers = {"User-Agent": "PhreakBot/1.0 Tweakers News Fetcher"}
        
        # Get the RSS feed
        try:
            response = session.get(
                "https://feeds.tweakers.net/nieuws",
                headers=headers,
                timeout=3
            )
            response.raise_for_status()
            
            # Simple string parsing instead of using BeautifulSoup
            content = response.text
            
            # Find article titles and URLs
            articles = []
            
            # Look for <item> tags
            item_blocks = content.split("<item>")[1:6]  # Get first 5 items
            
            for block in item_blocks:
                # Extract title
                title_start = block.find("<title>") + 7
                title_end = block.find("</title>")
                title = block[title_start:title_end] if title_start > 6 and title_end > 0 else "No title"
                
                # Extract link
                link_start = block.find("<link>") + 6
                link_end = block.find("</link>")
                link = block[link_start:link_end] if link_start > 5 and link_end > 0 else ""
                
                # Add to articles list
                articles.append((title, link))
            
            # Display results
            if articles:
                bot.add_response("📰 Latest articles from tweakers.net:")
                for i, (title, url) in enumerate(articles[:5], 1):
                    bot.add_response(f"{i}. {title} - {url}")
            else:
                bot.add_response("No articles found on tweakers.net")
                
        except Exception as e:
            bot.add_response(f"Error fetching articles: {str(e)[:50]}")
            
    except Exception as e:
        bot.add_response(f"Error processing request: {str(e)[:50]}")