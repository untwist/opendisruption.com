#!/usr/bin/env python3
"""
Twitter/X Scraper for Link Title Generation

This module scrapes Twitter/X tweets to extract actual tweet content
for use in link titles, avoiding generic "AI Discussion" labels.

Usage:
    from twitter_scraper import scrape_tweet_content, generate_twitter_title
    
    tweet_text = scrape_tweet_content("https://x.com/sama/status/123")
    title = generate_twitter_title("https://x.com/sama/status/123", tweet_text)
"""

import re
import time
import requests
from typing import Optional
from bs4 import BeautifulSoup


def scrape_tweet_content(url: str, timeout: int = 10) -> Optional[str]:
    """
    Scrape tweet content from a Twitter/X URL.
    
    Args:
        url: Twitter/X URL to scrape
        timeout: Request timeout in seconds
    
    Returns:
        Tweet text content or None if scraping fails
    """
    if not url or ("twitter.com" not in url and "x.com" not in url):
        return None
    
    try:
        # Set up headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }
        
        # Make request
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        if response.status_code != 200:
            return None
        
        # Parse HTML
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Try multiple strategies to find tweet text
        tweet_text = None
        
        # Strategy 1: Look for meta tags (Open Graph, Twitter Card)
        meta_tags = soup.find_all("meta")
        for meta in meta_tags:
            # Try Open Graph description
            if meta.get("property") == "og:description":
                tweet_text = meta.get("content", "").strip()
                if tweet_text:
                    break
            # Try Twitter Card description
            if meta.get("name") == "twitter:description":
                tweet_text = meta.get("content", "").strip()
                if tweet_text:
                    break
        
        # Strategy 2: Look for specific div/span classes that contain tweet text
        # X.com uses various class names, try common ones
        if not tweet_text:
            # Try data-testid="tweetText" or similar
            tweet_elements = soup.find_all(attrs={"data-testid": re.compile(r"tweetText|tweet.*text", re.I)})
            if tweet_elements:
                tweet_text = tweet_elements[0].get_text(strip=True)
        
        # Strategy 3: Look for article or main content areas
        if not tweet_text:
            article = soup.find("article")
            if article:
                # Try to find text content in article
                text_elements = article.find_all(["span", "div", "p"], string=True)
                if text_elements:
                    # Get the longest text element (likely the tweet)
                    tweet_text = max([elem.get_text(strip=True) for elem in text_elements], key=len)
        
        # Strategy 4: Extract from script tags (JSON-LD or embedded data)
        if not tweet_text:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Look for text in various fields
                        for key in ["text", "description", "headline", "name"]:
                            if key in data and data[key]:
                                tweet_text = str(data[key]).strip()
                                break
                except:
                    continue
        
        # Clean up the tweet text
        if tweet_text:
            # Remove extra whitespace
            tweet_text = re.sub(r'\s+', ' ', tweet_text).strip()
            # Remove URLs if they're at the end
            tweet_text = re.sub(r'\s+https?://\S+$', '', tweet_text)
            # Limit length
            if len(tweet_text) > 200:
                tweet_text = tweet_text[:197] + "..."
            
            return tweet_text if len(tweet_text) > 10 else None
        
        return None
        
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException:
        return None
    except Exception as e:
        # Silently fail - we'll use fallback behavior
        return None


# Mapping of Twitter/X usernames to proper display names
USERNAME_TO_DISPLAY_NAME = {
    # Companies & Organizations
    "openai": "OpenAI",
    "openaidevs": "OpenAI",
    "anthropic": "Anthropic",
    "googlelabs": "Google Labs",
    "googleai": "Google AI",
    "deepmind": "DeepMind",
    "baidu_inc": "Baidu",
    "huggingface": "Hugging Face",
    "runwayml": "Runway",
    "stabilityai": "Stability AI",
    "midjourney": "Midjourney",
    "replicate": "Replicate",
    "together_ai": "Together AI",
    "cohere": "Cohere",
    "mistralai": "Mistral AI",
    "perplexity_ai": "Perplexity",
    "claudeai": "Claude AI",
    "character_ai": "Character.AI",
    "krea_ai": "Krea AI",
    "wavespeed_ai": "WaveSpeed AI",
    "higgsfield_ai": "Higgsfield AI",
    "heydin_ai": "HeyDin AI",
    "wildmindai": "WildMind AI",
    "minimax__ai": "MiniMax AI",
    "hailuo_ai": "Hailuo AI",
    "extropic_ai": "Extropic AI",
    "artificialanlys": "Artificial Analysis",
    "theworldlabs": "The World Labs",
    "googleanalytics": "Google Analytics",
    "erniefordevs": "Ernie for Developers",
    # Individuals (keep as @username for clarity)
    "sama": "@sama",
    "karpathy": "@karpathy",
    "sundarpichai": "@sundarpichai",
    "elonmusk": "@elonmusk",
    "raydalio": "@raydalio",
    "emollick": "@emollick",
    "drfeifei": "@drfeifei",
}


def format_username(username: str) -> str:
    """
    Format username to proper display name.
    Returns proper name if known, otherwise returns @username format.
    """
    username_lower = username.lower()
    
    # Check exact match first
    if username_lower in USERNAME_TO_DISPLAY_NAME:
        return USERNAME_TO_DISPLAY_NAME[username_lower]
    
    # Check case-insensitive match
    for key, display_name in USERNAME_TO_DISPLAY_NAME.items():
        if username_lower == key.lower():
            return display_name
    
    # For unknown usernames, use @username format
    return f"@{username}"


def generate_twitter_title(url: str, tweet_text: Optional[str] = None, enable_scraping: bool = True) -> str:
    """
    Generate a title for a Twitter/X URL.
    
    Args:
        url: Twitter/X URL
        tweet_text: Optional pre-scraped tweet text (if None and enable_scraping=True, will scrape)
        enable_scraping: Whether to attempt scraping if tweet_text is None
    
    Returns:
        Formatted title like "OpenAI — tweet text..." or "@username — tweet text..."
        If scraping fails, returns just the display name or "@username"
    """
    # Extract username from URL
    match = re.search(r"/([^/]+)/status/", url)
    if not match:
        return "Twitter Thread"
    
    username = match.group(1)
    display_name = format_username(username)
    
    # Try to get tweet text if not provided
    if tweet_text is None and enable_scraping:
        tweet_text = scrape_tweet_content(url)
    
    # If we have tweet text, format it nicely
    if tweet_text:
        # Truncate tweet text to reasonable length for title
        max_tweet_length = 60
        if len(tweet_text) > max_tweet_length:
            truncated = tweet_text[:max_tweet_length].rsplit(' ', 1)[0] + "..."
        else:
            truncated = tweet_text
        
        return f"{display_name} — {truncated}"
    
    # Fallback: Just return the display name (no generic labels)
    return display_name

