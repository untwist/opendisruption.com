#!/usr/bin/env python3
"""
Enhanced URL Formatter with Metadata Extraction

This script extends the original format_urls.py to extract additional metadata
from URLs using lightweight HTTP requests and meta tag parsing.

Usage:
    python enhanced_url_formatter.py --input-file weekly-links/2025-01-29-links.md
    python enhanced_url_formatter.py --urls "https://example.com https://twitter.com/user/status/123"
"""

import argparse
import re
import requests
from pathlib import Path
from typing import List, Optional, Dict
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup

# Import the original formatting functions
from format_urls import (
    CURATED_PATTERNS,
    DOMAIN_FALLBACKS,
    extract_urls_from_text,
    extract_urls_from_section,
    get_domain,
    format_urls_to_markdown,
)

# Enhanced patterns for better title extraction
ENHANCED_PATTERNS = {
    # Add more specific patterns for common AI sites
    "openai.com": "OpenAI",
    "anthropic.com": "Anthropic",
    "deepmind.google": "Google DeepMind",
    "huggingface.co": "Hugging Face",
    "arxiv.org": "arXiv",
    "github.com": "GitHub",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
}


def extract_metadata_from_url(url: str, timeout: int = 5) -> Dict[str, str]:
    """
    Extract metadata from a URL using lightweight HTTP requests.
    Returns a dictionary with title, description, and other metadata.
    """
    metadata = {"title": "", "description": "", "domain": "", "status": "unknown"}

    try:
        # Parse the domain
        parsed = urlparse(url)
        metadata["domain"] = parsed.netloc.lower()

        # Set a reasonable timeout and user agent
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; OpenDisruptionBot/1.0; +https://opendisruption.com)"
        }

        # Make a HEAD request first to check if the page exists
        head_response = requests.head(
            url, timeout=timeout, headers=headers, allow_redirects=True
        )

        if head_response.status_code == 200:
            # If HEAD request works, make a GET request for the first 8KB
            response = requests.get(
                url, timeout=timeout, headers=headers, stream=True, allow_redirects=True
            )

            if response.status_code == 200:
                # Read only the first 8KB to get meta tags
                content = ""
                for chunk in response.iter_content(
                    chunk_size=1024, decode_unicode=True
                ):
                    content += chunk
                    if len(content) > 8192:  # Stop after 8KB
                        break

                # Parse HTML to extract title and meta description
                soup = BeautifulSoup(content, "html.parser")

                # Extract title
                title_tag = soup.find("title")
                if title_tag and title_tag.string:
                    metadata["title"] = title_tag.string.strip()

                # Extract meta description
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc and meta_desc.get("content"):
                    metadata["description"] = meta_desc.get("content").strip()

                metadata["status"] = "success"
            else:
                metadata["status"] = f"http_error_{response.status_code}"
        else:
            metadata["status"] = f"head_error_{head_response.status_code}"

    except requests.exceptions.Timeout:
        metadata["status"] = "timeout"
    except requests.exceptions.ConnectionError:
        metadata["status"] = "connection_error"
    except Exception as e:
        metadata["status"] = f"error: {str(e)}"

    return metadata


def generate_enhanced_title_for_url(url: str, use_metadata: bool = True) -> str:
    """
    Generate an enhanced title for a URL using metadata extraction.
    Falls back to the original method if metadata extraction fails.
    """
    # First, try the original method for known patterns
    original_title = generate_title_for_url_original(url)

    # If we have a good curated title, use it
    if any(pattern in url for pattern in CURATED_PATTERNS.keys()):
        return original_title

    # If we should use metadata and it's not a social media URL
    if use_metadata and not any(
        social in url for social in ["twitter.com", "x.com", "youtube.com", "youtu.be"]
    ):
        print(f"🔍 Extracting metadata from: {url}")
        metadata = extract_metadata_from_url(url)

        if metadata["status"] == "success" and metadata["title"]:
            # Clean up the title
            title = metadata["title"]

            # Remove common suffixes
            title = re.sub(
                r"\s*[-|]\s*(Home|Welcome|Official).*$", "", title, flags=re.IGNORECASE
            )
            title = re.sub(
                r"\s*[-|]\s*.*\.(com|org|edu|ai).*$", "", title, flags=re.IGNORECASE
            )

            # Truncate if too long
            if len(title) > 80:
                title = title[:77] + "..."

            # Add domain context if helpful
            domain = metadata["domain"]
            if domain and domain not in title.lower():
                if domain.startswith("www."):
                    domain = domain[4:]
                return f"{title} ({domain})"
            else:
                return title
        else:
            print(f"⚠️  Metadata extraction failed for {url}: {metadata['status']}")

    # Fall back to original method
    return original_title


def generate_title_for_url_original(url: str) -> str:
    """Original title generation method from format_urls.py"""
    domain = get_domain(url)

    # Handle Twitter/X URLs
    if "twitter.com" in url or "x.com" in url:
        match = re.search(r"/([^/]+)/status/", url)
        if match:
            username = match.group(1)
            # Use more descriptive labels based on username
            if username in ["karpathy", "sundarpichai", "elonmusk", "raydalio"]:
                return f"{username} — AI Industry Insight"
            elif username in ["emollick", "cryps1s", "mhdfaran"]:
                return f"{username} — AI Research & Analysis"
            elif username in ["claudeai", "GoogleAIStudio", "brave"]:
                return f"{username} — AI Product Update"
            elif username in ["krea_ai", "wavespeed_ai"]:
                return f"{username} — AI Tool Launch"
            else:
                return f"{username} — AI Discussion"
        return "Twitter Thread — AI Discussion"

    # Handle arXiv URLs
    if "arxiv.org" in url:
        match = re.search(r"/(\d+\.\d+)", url)
        if match:
            paper_id = match.group(1)
            return f"arXiv: Research Paper {paper_id}"
        return "arXiv: Research Paper"

    # Handle GitHub URLs
    if "github.com" in url:
        match = re.search(r"github\.com/([^/]+/[^/]+)", url)
        if match:
            repo = match.group(1)
            return f"GitHub: {repo}"
        return "GitHub Repository"

    # Handle YouTube URLs
    if "youtube.com" in url or "youtu.be" in url:
        video_id_match = re.search(r"(?:v=|/)([a-zA-Z0-9_-]{11})", url)
        if video_id_match:
            return "YouTube: AI Video Content"
        return "YouTube: AI Video Content"

    # Check curated patterns first
    for pattern, title in CURATED_PATTERNS.items():
        if pattern in url:
            return title

    # Fallback to domain-based title
    for domain_key, fallback_title in DOMAIN_FALLBACKS.items():
        if domain_key in domain:
            return fallback_title

    # Final fallback: clean domain name with more specific labels
    if domain:
        clean_domain = (
            domain.replace("www.", "")
            .replace(".com", "")
            .replace(".org", "")
            .replace(".edu", "")
            .replace(".ai", "")
        )

        # More specific labels based on domain type
        if domain.endswith(".ai"):
            return f"{clean_domain.title()}: AI Platform"
        elif domain.endswith(".edu"):
            return f"{clean_domain.title()}: Academic Research"
        elif domain.endswith(".org"):
            return f"{clean_domain.title()}: Research Organization"
        elif "research" in domain or "lab" in domain:
            return f"{clean_domain.title()}: Research Publication"
        else:
            return f"{clean_domain.title()}: AI Resource"

    return "AI Resource"


def format_urls_to_markdown_enhanced(urls: List[str], use_metadata: bool = True) -> str:
    """Format URLs with enhanced metadata extraction."""
    if not urls:
        return ""

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Generate markdown links with enhanced titles
    markdown_links = []
    for i, url in enumerate(unique_urls, 1):
        print(f"🔄 Processing URL {i}/{len(unique_urls)}: {url[:50]}...")
        title = generate_enhanced_title_for_url(url, use_metadata)
        markdown_link = (
            f'- <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>'
        )
        markdown_links.append(markdown_link)

        # Add a small delay to be respectful to servers
        if use_metadata and i < len(unique_urls):
            time.sleep(0.5)

    return "\n".join(markdown_links)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Enhanced URL formatter with metadata extraction"
    )
    parser.add_argument(
        "--input-file", type=Path, help="Input markdown file to process"
    )
    parser.add_argument("--urls", help="Space-separated list of URLs to format")
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Disable metadata extraction (use original method only)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Timeout for HTTP requests in seconds (default: 5)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be formatted without making changes",
    )
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()

    if args.input_file:
        # Process file
        print(f"📁 Processing file: {args.input_file}")
        content = args.input_file.read_text(encoding="utf-8")
        urls = extract_urls_from_section(content)

        if not urls:
            print("❌ No URLs found in the Links section.")
            return

        print(f"📊 Found {len(urls)} URLs to format")

        if args.dry_run:
            print("🔍 DRY RUN - Showing enhanced titles:")
            for i, url in enumerate(urls[:5], 1):  # Show first 5 as example
                title = generate_enhanced_title_for_url(url, not args.no_metadata)
                print(f"   {i}. {title}")
            if len(urls) > 5:
                print(f"   ... and {len(urls) - 5} more")
        else:
            formatted_links = format_urls_to_markdown_enhanced(
                urls, not args.no_metadata
            )
            print("\n📝 Formatted links:")
            print(formatted_links)

    elif args.urls:
        # Process individual URLs
        urls = args.urls.split()
        print(f"📊 Processing {len(urls)} URLs")

        for url in urls:
            title = generate_enhanced_title_for_url(url, not args.no_metadata)
            print(f"🔗 {url} -> {title}")

    else:
        print("Please provide either --input-file or --urls")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
