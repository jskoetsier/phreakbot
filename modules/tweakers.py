#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Tweakers.net module for PhreakBot

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime


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
        articles = get_latest_articles()
        
        if not articles:
            bot.add_response("Failed to fetch articles from tweakers.net.")
            return
            
        bot.add_response("📰 Latest articles from tweakers.net:")
        for i, article in enumerate(articles[:5], 1):
            title = article.get('title', 'No title')
            url = article.get('url', '')
            timestamp = article.get('timestamp', '')
            
            # Format the output
            time_str = f" ({timestamp})" if timestamp else ""
            bot.add_response(f"{i}. {title}{time_str} - {url}")
            
    except Exception as e:
        bot.add_response(f"Error fetching articles: {str(e)[:50]}")


def get_latest_articles():
    """Get the latest articles from tweakers.net"""
    articles = []
    
    try:
        # First try the RSS feed
        articles = get_articles_from_rss()
        if articles:
            return articles
    except:
        # If RSS fails, fall back to web scraping
        pass
        
    try:
        # Fall back to web scraping
        articles = get_articles_from_website()
    except:
        pass
        
    return articles


def get_articles_from_rss():
    """Get articles from the RSS feed"""
    articles = []
    
    headers = {"User-Agent": "PhreakBot/1.0 Tweakers News Fetcher"}
    response = requests.get("https://feeds.feedburner.com/tweakers/mixed", 
                           headers=headers, timeout=5)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "xml")
    items = soup.find_all("item")
    
    for item in items[:5]:
        title = item.find("title").text if item.find("title") else "No title"
        link = item.find("link").text if item.find("link") else ""
        pub_date = item.find("pubDate").text if item.find("pubDate") else ""
        
        # Parse and format the date
        timestamp = ""
        if pub_date:
            try:
                dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
                timestamp = dt.strftime("%d-%m %H:%M")
            except:
                pass
                
        articles.append({
            "title": title,
            "url": link,
            "timestamp": timestamp
        })
        
    return articles


def get_articles_from_website():
    """Get articles by scraping the website"""
    articles = []
    
    headers = {"User-Agent": "PhreakBot/1.0 Tweakers News Fetcher"}
    response = requests.get("https://tweakers.net", headers=headers, timeout=5)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the news articles on the homepage
    article_elements = soup.select(".headline")
    
    for article in article_elements[:5]:
        title_element = article.select_one("h1, h2, h3, h4")
        link_element = article.select_one("a")
        time_element = article.select_one("time")
        
        title = title_element.text.strip() if title_element else "No title"
        url = ""
        if link_element and link_element.has_attr("href"):
            url = link_element["href"]
            if not url.startswith("http"):
                url = f"https://tweakers.net{url}"
                
        timestamp = ""
        if time_element and time_element.has_attr("datetime"):
            try:
                dt = datetime.fromisoformat(time_element["datetime"].replace("Z", "+00:00"))
                timestamp = dt.strftime("%d-%m %H:%M")
            except:
                pass
                
        articles.append({
            "title": title,
            "url": url,
            "timestamp": timestamp
        })
        
    return articles