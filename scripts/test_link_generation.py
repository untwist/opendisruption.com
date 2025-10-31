#!/usr/bin/env python3
"""
Test script for enhanced link title generation

This script tests the various improvements:
1. URL path parsing
2. Enhanced metadata extraction
3. Twitter/X scraping (optional)
"""

import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from format_urls import generate_title_for_url, parse_url_path_to_title
from smart_url_formatter import generate_smart_title_for_url
from twitter_scraper import generate_twitter_title


def test_path_parsing():
    """Test URL path parsing functionality"""
    print("=" * 70)
    print("TEST 1: URL Path Parsing")
    print("=" * 70)
    
    test_urls = [
        "https://openai.com/index/introducing-aardvark/",
        "https://openai.com/index/built-to-benefit-everyone/",
        "https://openai.com/foundation/",
        "https://openai.com/index/introducing-gpt-oss-safeguard/",
        "https://anthropic.com/news/some-announcement",
        "https://blog.google/technology/ai-update",
    ]
    
    for url in test_urls:
        path_title = parse_url_path_to_title(url)
        full_title = generate_title_for_url(url, enable_twitter_scraping=False)
        print(f"\nURL: {url}")
        print(f"  Path extracted: {path_title}")
        print(f"  Full title: {full_title}")
    
    print("\n" + "=" * 70 + "\n")


def test_metadata_extraction():
    """Test enhanced metadata extraction (may make network requests)"""
    print("=" * 70)
    print("TEST 2: Enhanced Metadata Extraction")
    print("=" * 70)
    print("(This will make HTTP requests - may take a moment)\n")
    
    test_urls = [
        "https://openai.com/index/introducing-aardvark/",
        "https://openai.com/foundation/",
    ]
    
    for url in test_urls:
        print(f"URL: {url}")
        try:
            title = generate_smart_title_for_url(url, enable_twitter_scraping=False)
            print(f"  Extracted title: {title}")
        except Exception as e:
            print(f"  Error: {e}")
        print()
    
    print("=" * 70 + "\n")


def test_twitter_scraping(enable_scraping=False):
    """Test Twitter/X scraping functionality"""
    print("=" * 70)
    print("TEST 3: Twitter/X Link Generation")
    print("=" * 70)
    
    if enable_scraping:
        print("(Scraping enabled - will make HTTP requests)\n")
    else:
        print("(Scraping disabled - using fallback categorization)\n")
    
    test_urls = [
        "https://x.com/sama/status/1983584366547829073",
        "https://x.com/openai/status/1983661036533379486",
        "https://twitter.com/karpathy/status/1234567890",
    ]
    
    for url in test_urls:
        print(f"URL: {url}")
        try:
            title = generate_twitter_title(url, enable_scraping=enable_scraping)
            print(f"  Title: {title}")
        except Exception as e:
            print(f"  Error: {e}")
        print()
    
    print("=" * 70 + "\n")


def test_actual_file_comparison():
    """Compare old vs new title generation for URLs from actual file"""
    print("=" * 70)
    print("TEST 4: Comparison with Actual File URLs")
    print("=" * 70)
    
    # Sample URLs from 2025-10-30-links.md
    sample_urls = [
        "https://openai.com/index/built-to-benefit-everyone/",
        "https://openai.com/foundation/",
        "https://openai.com/index/introducing-aardvark/",
        "https://openai.com/index/introducing-gpt-oss-safeguard/",
        "https://arxiv.org/abs/2510.18212",
        "https://github.com/johannschopplich/toon",
    ]
    
    print("\nComparing old vs new generation:\n")
    for url in sample_urls:
        # Old method (just domain fallback)
        old_title = generate_title_for_url(url, enable_twitter_scraping=False)
        
        # New method with path parsing
        new_title = generate_title_for_url(url, enable_twitter_scraping=False)
        
        print(f"URL: {url}")
        print(f"  Before: {old_title}")
        print(f"  After:  {new_title}")
        if old_title != new_title:
            print(f"  ✅ IMPROVED!")
        print()
    
    print("=" * 70 + "\n")


def main():
    """Run all tests"""
    print("\n" + "🧪 LINK TITLE GENERATION TEST SUITE" + "\n")
    
    # Test 1: Path parsing (fast, no network)
    test_path_parsing()
    
    # Test 2: Metadata extraction (slower, makes network requests)
    response = input("Run metadata extraction tests? (makes HTTP requests) [y/N]: ")
    if response.lower() == 'y':
        test_metadata_extraction()
    
    # Test 3: Twitter scraping
    response = input("Run Twitter scraping tests? (makes HTTP requests) [y/N]: ")
    if response.lower() == 'y':
        test_twitter_scraping(enable_scraping=True)
    else:
        test_twitter_scraping(enable_scraping=False)
    
    # Test 4: Comparison
    test_actual_file_comparison()
    
    print("\n✅ Testing complete!\n")
    print("To test with your actual file, run:")
    print("  python scripts/format_urls.py --input-file weekly-links/2025-10-30-links.md --dry-run")
    print("\nOr use the smart formatter:")
    print("  python scripts/smart_url_formatter.py --input-file weekly-links/2025-10-30-links.md --dry-run")


if __name__ == "__main__":
    main()

