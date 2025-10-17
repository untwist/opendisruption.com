#!/usr/bin/env python3
"""
URL Formatter for Open Disruption Weekly Links

A simple, reliable script that takes raw URLs and formats them into clean markdown links
with descriptive titles using curated patterns. No web scraping - fast and reliable.

Quick Usage:
    python format_urls.py --input-file weekly-links/2025-01-29-links.md
    python format_urls.py --urls "https://example.com https://twitter.com/user/status/123"
    python format_urls.py --help
"""

import argparse
import re
from pathlib import Path
from typing import List

# Curated patterns for sites that have consistent, good titles
CURATED_PATTERNS = {
    # State of AI
    "stateof.ai": "State of AI 2025 Report",
    # Anthropic
    "anthropic.com/engineering/equipping-agents": "Anthropic: Equipping Agents for the Real World with Agent Skills",
    "anthropic.com/research/economic-policy-responses": "Anthropic: Economic Policy Responses Research",
    # Google/DeepMind
    "deepmind.google/discover/blog/introducing-codemender": "Google DeepMind: CodeMender AI Agent for Code Security",
    "blog.google/technology/google-labs/video-overviews-nano-banana": "Google Labs: Video Overviews Nano Banana",
    "cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report": "Google Cloud: 2025 DORA Report Announcement",
    "pair.withgoogle.com/guidebook": "Google PAIR Guidebook",
    # Research & Academic
    "brookings.edu/articles/new-data-show-no-ai-jobs-apocalypse-for-now": "Brookings: New Data Show No AI Jobs Apocalypse (For Now)",
    "budgetlab.yale.edu/research/evaluating-impact-ai-labor-market": "Yale Budget Lab: Evaluating Impact of AI on Labor Market",
    "dallasfed.org/research/economics/2025/0624": "Dallas Fed: AI and Economic Research",
    "fortune.com/2025/10/10/ai-cheating-on-homework-chatbots-students-education": "Fortune: AI Cheating on Homework - Students and Education",
    # AI Tools & Startups
    "wavespeed.ai": "WaveSpeed.ai - AI Tool",
    "moondream.ai/blog/moondream-3-preview": "Moondream 3 Preview",
    "huggingface.co/moondream/moondream3-preview": "Hugging Face: Moondream3 Preview Model",
    "higgsfield.ai/sora-2-prompt-guide": "Higgsfield.ai: Sora 2 Prompt Guide",
    "huixiang.baidu.com": "Baidu Huixiang AI Tool",
    "runware.ai/models": "Runware.ai: AI Models",
    "streamlake.ai/product/kat-coder": "StreamLake.ai: Kat Coder Product",
    "scispace.com/ai-detector": "SciSpace AI Detector",
    "exa.ai/blog/exa-api-2-0": "Exa.ai: API 2.0 Launch",
    "creativebloq.com/ai/ai-art/could-this-iphone-nano-banana-camera": "Creative Bloq: iPhone Nano Banana Camera for AI Photography",
    "video-zero-shot.github.io": "Video Zero-Shot Research Project",
    "kangliao929.github.io/projects/puffin": "Puffin AI Project",
    # Layoff Trackers
    "layoffs.fyi": "Layoffs.fyi - Tech Layoff Tracker",
    "trueup.io/layoffs": "TrueUp.io - Layoff Tracking",
    "warntracker.com": "WarnTracker - Layoff Warnings",
    "publish.obsidian.md/vg-layoffs/Archive/2025": "Obsidian: Layoffs Archive 2025",
    # Stable Diffusion
    "stable-diffusion-art.com/comfyui-desktop": "Stable Diffusion Art - ComfyUI Desktop",
}

# Simple domain fallbacks for major sites
DOMAIN_FALLBACKS = {
    "anthropic.com": "Anthropic",
    "openai.com": "OpenAI",
    "deepmind.google": "Google DeepMind",
    "google.com": "Google",
    "brookings.edu": "Brookings",
    "fortune.com": "Fortune",
    "yale.edu": "Yale",
    "dallasfed.org": "Dallas Fed",
    "cloud.google.com": "Google Cloud",
    "pair.withgoogle.com": "Google PAIR",
    "layoffs.fyi": "Layoffs.fyi",
    "trueup.io": "TrueUp.io",
    "warntracker.com": "WarnTracker",
    "wavespeed.ai": "WaveSpeed.ai",
    "moondream.ai": "Moondream",
    "higgsfield.ai": "Higgsfield.ai",
    "runware.ai": "Runware.ai",
    "streamlake.ai": "StreamLake.ai",
    "scispace.com": "SciSpace",
    "exa.ai": "Exa.ai",
    "creativebloq.com": "Creative Bloq",
    "stable-diffusion-art.com": "Stable Diffusion Art",
    "publish.obsidian.md": "Obsidian",
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Format raw URLs into organized markdown links with curated patterns"
    )
    parser.add_argument(
        "--input-file", help="Path to file containing URLs to format", type=Path
    )
    parser.add_argument(
        "--urls", help="Raw URLs as a string (space-separated)", type=str
    )
    parser.add_argument(
        "--output-file",
        help="Output file path (default: overwrites input file)",
        type=Path,
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be formatted"
    )
    return parser.parse_args()


def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text, preserving order."""
    # More precise URL pattern that doesn't include trailing punctuation
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]()]+'
    urls = re.findall(url_pattern, text)
    return urls


def extract_urls_from_section(content: str) -> List[str]:
    """Extract URLs only from the 'Links from Office Hours' section."""
    lines = content.split("\n")
    urls = []
    in_links_section = False

    for line in lines:
        if line.startswith("## Links from Office Hours"):
            in_links_section = True
            continue
        elif line.startswith("## Archive") and in_links_section:
            break
        elif in_links_section:
            # Extract URLs from this line
            line_urls = extract_urls_from_text(line)
            urls.extend(line_urls)

    return urls


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def generate_title_for_url(url: str) -> str:
    """Generate a title for a URL using curated patterns and fallbacks."""
    domain = get_domain(url)

    # Handle Twitter/X URLs
    if "twitter.com" in url or "x.com" in url:
        match = re.search(r"/([^/]+)/status/", url)
        if match:
            username = match.group(1)
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
        return "YouTube Video"

    # Check curated patterns first
    for pattern, title in CURATED_PATTERNS.items():
        if pattern in url:
            return title

    # Fallback to domain-based title
    for domain_key, fallback_title in DOMAIN_FALLBACKS.items():
        if domain_key in domain:
            return fallback_title

    # Final fallback: clean domain name
    if domain:
        clean_domain = (
            domain.replace("www.", "")
            .replace(".com", "")
            .replace(".org", "")
            .replace(".edu", "")
            .replace(".ai", "")
        )
        return f"{clean_domain.title()}: AI Resource"

    return "AI Resource"


def format_urls_to_markdown(urls: List[str]) -> str:
    """Format a list of URLs into organized markdown."""
    if not urls:
        return ""

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    # Generate markdown links
    markdown_links = []
    for url in unique_urls:
        title = generate_title_for_url(url)
        markdown_link = (
            f'- <a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>'
        )
        markdown_links.append(markdown_link)

    return "\n".join(markdown_links)


def process_file(
    input_file: Path, output_file: Path = None, dry_run: bool = False
) -> str:
    """Process a file containing raw URLs and format them."""
    print(f"📁 Reading file: {input_file}")
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Read the file
    content = input_file.read_text(encoding="utf-8")
    print(f"📄 File size: {len(content)} characters")

    # Extract URLs only from the Links section
    print("🔍 Extracting URLs from 'Links from Office Hours' section...")
    urls = extract_urls_from_section(content)

    if not urls:
        print("❌ No URLs found in the Links section.")
        return content

    print(f"📊 Found {len(urls)} URLs to format")
    print("📝 Sample URLs:")
    for i, url in enumerate(urls[:3], 1):
        print(f"   {i}. {url}")
    if len(urls) > 3:
        print(f"   ... and {len(urls) - 3} more")

    # Format URLs
    print("\n🚀 Formatting URLs...")
    formatted_links = format_urls_to_markdown(urls)

    # Create the new section
    new_section = f"""## Links from Office Hours
*Presented in the order they were discussed during the episode*

{formatted_links}"""

    # Replace the old content with the new formatted section
    print("🔄 Replacing content...")
    lines = content.split("\n")
    new_lines = []
    skip_until_archive = False
    replaced_section = False

    for line in lines:
        if line.startswith("## Links from Office Hours") or line.startswith(
            "## AI Industry News"
        ):
            skip_until_archive = True
            replaced_section = True
            print(f"   🔄 Replacing section: '{line}'")
            new_lines.append(new_section)
            continue
        elif line.startswith("## Archive") and skip_until_archive:
            skip_until_archive = False
            print(f"   📁 Found Archive section: '{line}'")
            new_lines.append(line)
            continue
        elif skip_until_archive:
            continue
        else:
            new_lines.append(line)

    result = "\n".join(new_lines)

    if not replaced_section:
        print("⚠️  Warning: No 'Links from Office Hours' section found to replace")

    if dry_run:
        print("\n" + "=" * 50)
        print("📋 FORMATTED CONTENT PREVIEW")
        print("=" * 50)
        print(result)
        print("=" * 50)
        return result
    else:
        # Write to output file
        output_path = output_file or input_file
        print(f"💾 Writing to: {output_path}")
        output_path.write_text(result, encoding="utf-8")
        print(f"✅ Successfully formatted URLs written to: {output_path}")
        return result


def main():
    """Main function."""
    args = parse_args()

    if args.input_file:
        try:
            process_file(args.input_file, args.output_file, args.dry_run)
        except Exception as e:
            print(f"Error processing file: {e}")
            return 1
    elif args.urls:
        # Process URLs directly
        urls = args.urls.split()
        formatted = format_urls_to_markdown(urls)
        if args.dry_run:
            print("\n--- Formatted URLs ---\n")
            print(formatted)
        else:
            print(formatted)
    else:
        print("Please provide either --input-file or --urls")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
