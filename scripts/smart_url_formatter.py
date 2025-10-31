#!/usr/bin/env python3
"""
Smart URL Formatter with Selective Metadata Extraction

This script enhances URL titles by extracting metadata from specific types of URLs
that are most likely to benefit from it, while respecting rate limits and ToS.

Usage:
    python smart_url_formatter.py --input-file weekly-links/2025-01-29-links.md
    python smart_url_formatter.py --urls "https://example.com https://twitter.com/user/status/123"
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

# Enhanced curated patterns for better titles
ENHANCED_CURATED_PATTERNS = {
    # OpenAI Atlas
    "chatgpt.com/atlas": "OpenAI Atlas - AI Web Browser",
    "openai.com/index/introducing-chatgpt-atlas": "OpenAI: Introducing ChatGPT Atlas",
    # Anthropic
    "anthropic.com/news/skills": "Anthropic: Agent Skills Announcement",
    "anthropic.com/engineering/equipping-agents": "Anthropic: Equipping Agents for the Real World",
    "anthropic.com/news/statement-dario-amodei": "Anthropic: Dario Amodei on American AI Leadership",
    # GitHub repositories with better descriptions
    "github.com/antgroup/ditto-talkinghead": "GitHub: Ditto Talking Head (AI Video Generation)",
    "github.com/Tencent-Hunyuan/HunyuanWorld-Mirror": "GitHub: HunyuanWorld (Tencent AI World Model)",
    # Research and statements
    "superintelligence-statement.org": "Statement on Superintelligence",
    # AI Tools and Platforms
    "metaphysic.ai/studios": "Metaphysic Studios - AI VFX Innovation",
    "artificialanalysis.ai/media/survey-2025": "Artificial Analysis: 2025 Generative Media Survey",
    "deepseek.ai/blog/deepseek-ocr": "DeepSeek: OCR Context Compression",
    "learnyourway.withgoogle.com": "Google: Learn Your Way AI Learning Platform",
    # News articles with better context
    "techcrunch.com/2025/10/21/netflix-goes-all-in": "TechCrunch: Netflix Goes All-In on Generative AI",
    "zdnet.com/article/adobe-mightve-just-solved": "ZDNet: Adobe Solves Generative AI Legal Risks",
    "blog.google/technology/research/quantum-echoes": "Google Research: Quantum Echoes Willow Advantage",
}

# Domains that are safe and beneficial to extract metadata from
SAFE_DOMAINS = {
    # Academic & Research
    "arxiv.org",
    "scholar.google.com",
    "paperswithcode.com",
    "neurips.cc",
    "icml.cc",
    "iclr.cc",
    "aaai.org",
    "acm.org",
    "ieee.org",
    "nature.com",
    "science.org",
    "cell.com",
    "springer.com",
    "elsevier.com",
    # Universities & Research Institutions
    "mit.edu",
    "stanford.edu",
    "berkeley.edu",
    "cmu.edu",
    "yale.edu",
    "harvard.edu",
    "princeton.edu",
    "caltech.edu",
    "oxford.edu",
    "cambridge.edu",
    "brookings.edu",
    "rand.org",
    "nber.org",
    # AI Companies & Labs
    "openai.com",
    "anthropic.com",
    "deepmind.google",
    "google.com",
    "blog.google",
    "cloud.google.com",
    "pair.withgoogle.com",
    "research.google",
    "ai.google",
    "huggingface.co",
    "stability.ai",
    "midjourney.com",
    "runwayml.com",
    "replicate.com",
    "together.ai",
    "cohere.ai",
    "mistral.ai",
    "perplexity.ai",
    "claude.ai",
    "chatgpt.com",
    # Tech Platforms
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "stackoverflow.com",
    "stackexchange.com",
    "dev.to",
    "medium.com",
    "substack.com",
    # News & Media (Tech/AI focused)
    "techcrunch.com",
    "theverge.com",
    "wired.com",
    "reuters.com",
    "bloomberg.com",
    "wsj.com",
    "nytimes.com",
    "washingtonpost.com",
    "fortune.com",
    "forbes.com",
    "venturebeat.com",
    "artificialintelligence-news.com",
    "venturebeat.com",
    "zdnet.com",
    "cnet.com",
    "engadget.com",
    "arstechnica.com",
    "slashdot.org",
    # Research Organizations
    "openai.com",
    "ai.google",
    "research.google",
    "deepmind.com",
    "anthropic.com",
    "huggingface.co",
    "stability.ai",
    "runwayml.com",
    "replicate.com",
    "together.ai",
    "cohere.ai",
    "mistral.ai",
    "perplexity.ai",
    "claude.ai",
    "chatgpt.com",
}

# Domains to avoid (social media, video platforms, etc.)
AVOID_DOMAINS = {
    "twitter.com",
    "x.com",
    "youtube.com",
    "youtu.be",
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "reddit.com",
}


def should_extract_metadata(url: str) -> bool:
    """
    Determine if we should extract metadata from this URL.
    Returns True for safe domains that would benefit from metadata extraction.
    """
    domain = get_domain(url)

    # Don't extract from social media or video platforms
    if any(avoid in domain for avoid in AVOID_DOMAINS):
        return False

    # Extract from safe domains
    if any(safe in domain for safe in SAFE_DOMAINS):
        return True

    # Extract from academic/research domains
    if domain.endswith(".edu") or domain.endswith(".org"):
        return True

    # Extract from AI/tech domains
    if domain.endswith(".ai") or "research" in domain or "lab" in domain:
        return True

    # Extract from major AI company domains (even if not in safe list)
    ai_company_domains = [
        "openai.com",
        "anthropic.com",
        "chatgpt.com",
        "deepmind.google",
        "huggingface.co",
        "stability.ai",
        "runwayml.com",
        "replicate.com",
        "together.ai",
        "cohere.ai",
        "mistral.ai",
        "perplexity.ai",
        "claude.ai",
        "deepseek.ai",
        "metaphysic.ai",
        "artificialanalysis.ai",
    ]

    if any(ai_domain in domain for ai_domain in ai_company_domains):
        return True

    return False


def extract_title_from_url(url: str, timeout: int = 5) -> Optional[str]:
    """
    Extract page title from a URL with enhanced metadata extraction.
    Handles Open Graph tags, JSON-LD structured data, and meta descriptions.
    Uses a lightweight approach with minimal data transfer.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

        # Adjust timeout based on domain type (longer for company blogs)
        domain = get_domain(url)
        if any(company in domain for company in ["openai.com", "anthropic.com", "google.com", "deepmind.google"]):
            timeout = max(timeout, 8)  # Give company blogs more time

        # Make a request with retry logic
        max_retries = 2
        response = None
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout, headers=headers, stream=True, allow_redirects=True)
                if response.status_code == 200:
                    break
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(1)  # Brief delay before retry
                    continue
                return None
            except Exception:
                return None

        if not response or response.status_code != 200:
            return None

        # Read more content for better extraction (up to 16KB)
        content = ""
        max_size = 16384  # 16KB for better metadata extraction
        for chunk in response.iter_content(chunk_size=2048, decode_unicode=True):
            content += chunk
            if len(content) > max_size:
                break

        # Parse HTML to extract title
        soup = BeautifulSoup(content, "html.parser")
        title = None

        # Strategy 1: Try Open Graph title (often better than regular title)
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title.get("content").strip()
        
        # Strategy 2: Try Twitter Card title
        if not title:
            twitter_title = soup.find("meta", attrs={"name": "twitter:title"})
            if twitter_title and twitter_title.get("content"):
                title = twitter_title.get("content").strip()
        
        # Strategy 3: Try JSON-LD structured data
        if not title:
            scripts = soup.find_all("script", type="application/ld+json")
            for script in scripts:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        # Look for title in various fields
                        for key in ["headline", "name", "title"]:
                            if key in data and data[key]:
                                title = str(data[key]).strip()
                                break
                        if title:
                            break
                except:
                    continue
        
        # Strategy 4: Fall back to regular title tag
        if not title:
            title_tag = soup.find("title")
            if title_tag and title_tag.string:
                title = title_tag.string.strip()

        if not title:
            return None

        # Clean up common title patterns
        # Remove site name suffixes (e.g., "Title | OpenAI")
        title = re.sub(
            r"\s*[-|]\s*(Home|Welcome|Official).*$",
            "",
            title,
            flags=re.IGNORECASE,
        )
        # Remove domain suffixes (e.g., "Title - example.com")
        title = re.sub(
            r"\s*[-|]\s*.*\.(com|org|edu|ai).*$", "", title, flags=re.IGNORECASE
        )
        # Remove common separators and clean up
        title = re.sub(r"\s*[-|]\s*", " — ", title)
        title = re.sub(r"\s+", " ", title).strip()

        # If title is too generic (just site name), try meta description
        domain_clean = domain.replace("www.", "").replace(".com", "").replace(".org", "").replace(".edu", "").replace(".ai", "")
        if title.lower() == domain_clean.lower() or len(title) < 10:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if not meta_desc:
                meta_desc = soup.find("meta", property="og:description")
            if meta_desc and meta_desc.get("content"):
                desc = meta_desc.get("content").strip()
                if len(desc) > 20:  # Use description if it's substantial
                    title = desc[:80] + "..." if len(desc) > 80 else desc

        # Truncate if too long
        if len(title) > 100:
            title = title[:97] + "..."

        return title if title and len(title) > 5 else None

    except Exception as e:
        print(f"⚠️  Could not extract title from {url}: {e}")

    return None


def generate_smart_title_for_url(url: str, enable_twitter_scraping: bool = True) -> str:
    """
    Generate a smart title for a URL using selective metadata extraction.
    """
    domain = get_domain(url)
    
    # Handle Twitter/X URLs with scraping
    if "twitter.com" in url or "x.com" in url:
        try:
            from twitter_scraper import generate_twitter_title
            return generate_twitter_title(url, enable_scraping=enable_twitter_scraping)
        except ImportError:
            pass  # Fall through to original method
    
    # First, check enhanced curated patterns
    for pattern, title in ENHANCED_CURATED_PATTERNS.items():
        if pattern in url:
            return title

    # Then check original curated patterns
    for pattern, title in CURATED_PATTERNS.items():
        if pattern in url:
            return title

    # If this URL would benefit from metadata extraction, try it
    if should_extract_metadata(url):
        print(f"🔍 Extracting title from: {url}")
        extracted_title = extract_title_from_url(url)

        if extracted_title:
            # Use the extracted title
            return extracted_title
        else:
            print(f"⚠️  Metadata extraction failed, using fallback")

    # Try URL path parsing before final fallback
    try:
        try:
            from format_urls import parse_url_path_to_title
        except ImportError:
            # Try importing from scripts directory
            import sys
            from pathlib import Path
            scripts_dir = Path(__file__).parent
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
            from format_urls import parse_url_path_to_title
        path_title = parse_url_path_to_title(url, domain)
        if path_title:
            # Combine with domain context
            domain_fallback = None
            for domain_key, fallback_title in DOMAIN_FALLBACKS.items():
                if domain_key in domain:
                    domain_fallback = fallback_title
                    break
            
            if domain_fallback:
                return f"{domain_fallback}: {path_title}"
            else:
                clean_domain = (
                    domain.replace("www.", "")
                    .replace(".com", "")
                    .replace(".org", "")
                    .replace(".edu", "")
                    .replace(".ai", "")
                    .title()
                )
                if clean_domain:
                    return f"{clean_domain}: {path_title}"
                else:
                    return path_title
    except ImportError:
        pass  # Continue to fallback

    # Fall back to original method
    return generate_title_for_url_original(url)


def generate_title_for_url_original(url: str) -> str:
    """Original title generation method from format_urls.py"""
    domain = get_domain(url)

    # Handle Twitter/X URLs
    if "twitter.com" in url or "x.com" in url:
        match = re.search(r"/([^/]+)/status/", url)
        if match:
            username = match.group(1)
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


def format_urls_to_markdown_smart(urls: List[str]) -> str:
    """Format URLs with smart metadata extraction."""
    if not urls:
        return ""

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Generate markdown links with smart titles
    markdown_links = []
    for i, url in enumerate(unique_urls, 1):
        print(f"🔄 Processing URL {i}/{len(unique_urls)}: {url[:50]}...")
        title = generate_smart_title_for_url(url)
        markdown_link = (
            f'- <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>'
        )
        markdown_links.append(markdown_link)

        # Add a small delay to be respectful to servers
        if should_extract_metadata(url) and i < len(unique_urls):
            time.sleep(1)  # 1 second delay for metadata extraction

    return "\n".join(markdown_links)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Smart URL formatter with selective metadata extraction"
    )
    parser.add_argument(
        "--input-file", type=Path, help="Input markdown file to process"
    )
    parser.add_argument("--urls", help="Space-separated list of URLs to format")
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
            print("🔍 DRY RUN - Showing smart titles:")
            for i, url in enumerate(urls[:5], 1):  # Show first 5 as example
                title = generate_smart_title_for_url(url)
                print(f"   {i}. {title}")
            if len(urls) > 5:
                print(f"   ... and {len(urls) - 5} more")
        else:
            formatted_links = format_urls_to_markdown_smart(urls)
            print("\n📝 Formatted links:")
            print(formatted_links)

    elif args.urls:
        # Process individual URLs
        urls = args.urls.split()
        print(f"📊 Processing {len(urls)} URLs")

        for url in urls:
            title = generate_smart_title_for_url(url)
            print(f"🔗 {url} -> {title}")

    else:
        print("Please provide either --input-file or --urls")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
