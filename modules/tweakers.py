#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Tweakers.net module for PhreakBot

# Use minimal imports to reduce chances of issues during reload
import requests

# Global cache to store articles between calls
# This will be reset when the module is reloaded
_article_cache = []
_last_fetch_time = 0


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
        bot.add_response("Fetching latest articles from tweakers.net...")
        
        # Get articles (either from cache or fresh)
        articles = get_articles()
        
        # Display results
        if articles:
            bot.add_response("📰 Latest articles from tweakers.net:")
            for i, (title, url) in enumerate(articles[:5], 1):
                bot.add_response(f"{i}. {title} - {url}")
        else:
            bot.add_response("No articles found on tweakers.net")
            
    except Exception as e:
        bot.add_response(f"Error processing request: {str(e)[:50]}")


def get_articles():
    """Get articles from tweakers.net"""
    global _article_cache, _last_fetch_time
    
    # Use cached results if less than 5 minutes old
    import time
    current_time = time.time()
    if _article_cache and current_time - _last_fetch_time < 300:
        return _article_cache
    
    try:
        # Set a timeout and user agent
        headers = {"User-Agent": "PhreakBot/1.0 Tweakers News Fetcher"}
        
        # Get the RSS feed
        response = requests.get(
            "https://feeds.tweakers.net/nieuws",
            headers=headers,
            timeout=3
        )
        response.raise_for_status()
        
        # Simple string parsing
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
        
        # Update cache
        _article_cache = articles
        _last_fetch_time = current_time
        
        return articles
        
    except Exception:
        # Return cached results if available, otherwise empty list
        return _article_cache if _article_cache else []