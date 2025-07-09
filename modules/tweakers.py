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

        # Try multiple RSS feed URLs
        urls = [
            "https://feeds.tweakers.net/nieuws",
            "https://tweakers.net/feeds/nieuws.xml",
            "https://tweakers.net/rss",
            "https://feeds.feedburner.com/tweakers/mixed"
        ]
        
        content = None
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=3)
                if response.status_code == 200:
                    content = response.text
                    break
            except Exception:
                continue
                
        if not content:
            return []
            
        # Find article titles and URLs
        articles = []
        
        # Try different parsing approaches
        # First try: Look for <item> tags
        if "<item>" in content:
            item_blocks = content.split("<item>")[1:6]  # Get first 5 items
            
            for block in item_blocks:
                # Extract title
                title_start = block.find("<title>") + 7
                title_end = block.find("</title>")
                title = block[title_start:title_end] if title_start > 6 and title_end > 0 else "No title"
                
                # Clean up title (remove CDATA if present)
                if "CDATA[" in title:
                    title = title.split("CDATA[")[1].split("]]")[0]
                
                # Extract link
                link_start = block.find("<link>") + 6
                link_end = block.find("</link>")
                link = block[link_start:link_end] if link_start > 5 and link_end > 0 else ""
                
                # Add to articles list if we have both title and link
                if title and link:
                    articles.append((title, link))
        
        # Second try: If no articles found, try scraping the website directly
        if not articles:
            try:
                response = requests.get("https://tweakers.net", headers=headers, timeout=3)
                if response.status_code == 200:
                    content = response.text
                    
                    # Look for article links
                    article_sections = content.split('<h1><a href="')
                    for section in article_sections[1:6]:  # Skip first (header) and get next 5
                        link_end = section.find('"')
                        link = section[:link_end] if link_end > 0 else ""
                        
                        # Get title
                        title_start = section.find('">') + 2
                        title_end = section.find('</a>')
                        title = section[title_start:title_end] if title_start > 1 and title_end > 0 else "No title"
                        
                        # Clean up title
                        title = title.replace("&quot;", '"').replace("&amp;", "&")
                        
                        # Add to articles list if we have both title and link
                        if title and link:
                            if not link.startswith("http"):
                                link = f"https://tweakers.net{link}"
                            articles.append((title, link))
            except Exception:
                pass

        # Update cache
        _article_cache = articles
        _last_fetch_time = current_time

        return articles

    except Exception:
        # Return cached results if available, otherwise empty list
        return _article_cache if _article_cache else []
