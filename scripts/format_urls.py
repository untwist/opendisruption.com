#!/usr/bin/env python3
"""
URL Formatter for Open Disruption Weekly Links

This script automatically formats raw URLs into organized, professional markdown links
with descriptive titles, preserving the original order from your presentation.

Quick Usage:
    python format_urls.py --input-file weekly-links/2025-10-16-links.md
    python format_urls.py --urls "https://example.com https://twitter.com/user/status/123"
    python format_urls.py --help

For detailed documentation, see README.md in this directory.
"""

import argparse
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Tuple, Optional

# URL patterns for different types of content
URL_PATTERNS = {
    "twitter": r"https?://(?:www\.)?(?:twitter\.com|x\.com)/[^/]+/status/\d+",
    "arxiv": r"https?://arxiv\.org/(?:abs|pdf)/(\d+\.\d+)",
    "github": r"https?://github\.com/([^/]+/[^/]+)",
    "youtube": r"https?://(?:www\.)?youtube\.com/watch\?v=([^&]+)",
    "huggingface": r"https?://huggingface\.co/([^/]+)",
    "anthropic": r"https?://(?:www\.)?anthropic\.com/",
    "google": r"https?://(?:www\.)?google\.com/",
    "deepmind": r"https?://deepmind\.google/",
    "openai": r"https?://(?:www\.)?openai\.com/",
    "brookings": r"https?://(?:www\.)?brookings\.edu/",
    "fortune": r"https?://(?:www\.)?fortune\.com/",
    "arxiv_pdf": r"https?://arxiv\.org/pdf/(\d+\.\d+)",
}

# Domain-based title generators
DOMAIN_TITLES = {
    "stateof.ai": "State of AI 2025 Report",
    "anthropic.com": "Anthropic",
    "arxiv.org": "arXiv",
    "github.com": "GitHub",
    "huggingface.co": "Hugging Face",
    "google.com": "Google",
    "deepmind.google": "Google DeepMind",
    "openai.com": "OpenAI",
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
    "huixiang.baidu.com": "Baidu Huixiang",
    "runware.ai": "Runware.ai",
    "streamlake.ai": "StreamLake.ai",
    "scispace.com": "SciSpace",
    "exa.ai": "Exa.ai",
    "creativebloq.com": "Creative Bloq",
    "stable-diffusion-art.com": "Stable Diffusion Art",
    "video-zero-shot.github.io": "Video Zero-Shot",
    "kangliao929.github.io": "Puffin AI Project",
    "publish.obsidian.md": "Obsidian",
}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Format raw URLs into organized markdown links"
    )
    parser.add_argument(
        "--input-file", help="Path to file containing raw URLs to format", type=Path
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
        "--dry-run",
        action="store_true",
        help="Show what would be formatted without writing files",
    )
    parser.add_argument(
        "--preserve-order",
        action="store_true",
        default=True,
        help="Preserve the original order of URLs (default: True)",
    )
    return parser.parse_args()


def extract_urls_from_text(text: str) -> List[str]:
    """Extract URLs from text, preserving order."""
    # URL regex pattern
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return urls


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return ""


def generate_title_for_url(url: str) -> str:
    """Generate a descriptive title for a URL based on its content."""
    domain = get_domain(url)

    # Handle Twitter/X URLs
    if re.match(URL_PATTERNS["twitter"], url):
        # Extract username from URL
        match = re.search(r"/([^/]+)/status/", url)
        if match:
            username = match.group(1)
            return f"{username} — AI Discussion"
        return "Twitter Thread — AI Discussion"

    # Handle arXiv URLs
    if re.match(URL_PATTERNS["arxiv"], url):
        match = re.search(r"/(\d+\.\d+)", url)
        if match:
            paper_id = match.group(1)
            return f"arXiv: Research Paper {paper_id}"
        return "arXiv: Research Paper"

    # Handle arXiv PDF URLs
    if re.match(URL_PATTERNS["arxiv_pdf"], url):
        match = re.search(r"/(\d+\.\d+)", url)
        if match:
            paper_id = match.group(1)
            return f"arXiv PDF: Research Paper {paper_id}"
        return "arXiv PDF: Research Paper"

    # Handle GitHub URLs
    if re.match(URL_PATTERNS["github"], url):
        match = re.search(r"github\.com/([^/]+/[^/]+)", url)
        if match:
            repo = match.group(1)
            return f"GitHub: {repo}"
        return "GitHub Repository"

    # Handle YouTube URLs
    if re.match(URL_PATTERNS["youtube"], url):
        return "YouTube Video"

    # Handle Hugging Face URLs
    if re.match(URL_PATTERNS["huggingface"], url):
        match = re.search(r"huggingface\.co/([^/]+)", url)
        if match:
            model = match.group(1)
            return f"Hugging Face: {model}"
        return "Hugging Face Model"

    # Handle specific domains
    for domain_key, title in DOMAIN_TITLES.items():
        if domain_key in domain:
            # Add specific context based on URL path
            if "engineering" in url:
                return f"{title}: Engineering Blog"
            elif "research" in url:
                return f"{title}: Research"
            elif "blog" in url:
                return f"{title}: Blog Post"
            elif "discover" in url:
                return f"{title}: Discovery"
            elif "guidebook" in url:
                return f"{title}: Guidebook"
            elif "layoffs" in url:
                return f"{title}: Layoff Tracker"
            elif "ai-detector" in url:
                return f"{title}: AI Detector"
            elif "api" in url:
                return f"{title}: API"
            elif "models" in url:
                return f"{title}: AI Models"
            elif "product" in url:
                return f"{title}: Product"
            else:
                return title

    # Handle specific URL patterns
    if "stateof.ai" in url:
        return "State of AI 2025 Report"
    elif "equipping-agents" in url:
        return "Anthropic: Equipping Agents for the Real World with Agent Skills"
    elif "economic-policy-responses" in url:
        return "Anthropic: Economic Policy Responses Research"
    elif "introducing-codemender" in url:
        return "Google DeepMind: CodeMender AI Agent for Code Security"
    elif "video-overviews-nano-banana" in url:
        return "Google Labs: Video Overviews Nano Banana"
    elif "announcing-the-2025-dora-report" in url:
        return "Google Cloud: 2025 DORA Report Announcement"
    elif "comfyui-desktop" in url:
        return "Stable Diffusion Art: ComfyUI Desktop"
    elif "sora-2-prompt-guide" in url:
        return "Higgsfield.ai: Sora 2 Prompt Guide"
    elif "moondream-3-preview" in url:
        return "Moondream 3 Preview"
    elif "moondream3-preview" in url:
        return "Hugging Face: Moondream3 Preview Model"
    elif "exa-api-2-0" in url:
        return "Exa.ai: API 2.0 Launch"
    elif "kat-coder" in url:
        return "StreamLake.ai: Kat Coder Product"
    elif "nano-banana-camera" in url:
        return "Creative Bloq: iPhone Nano Banana Camera for AI Photography"
    elif "video-zero-shot" in url:
        return "Video Zero-Shot Research Project"
    elif "puffin" in url:
        return "Puffin AI Project"
    elif "vg-layoffs" in url:
        return "Obsidian: Layoffs Archive 2025"

    # Fallback: use domain name
    if domain:
        # Clean up domain name
        clean_domain = (
            domain.replace("www.", "")
            .replace(".com", "")
            .replace(".org", "")
            .replace(".edu", "")
        )
        return f"{clean_domain.title()}: AI Tool"

    return "AI Resource"


def format_urls_to_markdown(urls: List[str], preserve_order: bool = True) -> str:
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
    input_file: Path, output_file: Optional[Path] = None, dry_run: bool = False
) -> str:
    """Process a file containing raw URLs and format them."""
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Read the file
    content = input_file.read_text(encoding="utf-8")

    # Extract URLs
    urls = extract_urls_from_text(content)

    if not urls:
        print("No URLs found in the file.")
        return content

    print(f"Found {len(urls)} URLs to format")

    # Format URLs
    formatted_links = format_urls_to_markdown(urls)

    # Create the new section
    new_section = f"""## Links from Office Hours
*Presented in the order they were discussed during the episode*

{formatted_links}"""

    # Replace the old content with the new formatted section
    # Look for the section between the header and the archive section
    lines = content.split("\n")
    new_lines = []
    in_old_section = False
    skip_until_archive = False

    for line in lines:
        if line.startswith("## Links from Office Hours") or line.startswith(
            "## AI Industry News"
        ):
            in_old_section = True
            skip_until_archive = True
            # Add the new section
            new_lines.append(new_section)
            continue
        elif line.startswith("## Archive") and skip_until_archive:
            skip_until_archive = False
            new_lines.append(line)
            continue
        elif skip_until_archive:
            continue
        else:
            new_lines.append(line)

    result = "\n".join(new_lines)

    if dry_run:
        print("\n--- Formatted Content Preview ---\n")
        print(result)
        return result
    else:
        # Write to output file
        output_path = output_file or input_file
        output_path.write_text(result, encoding="utf-8")
        print(f"Formatted URLs written to: {output_path}")
        return result


def main():
    """Main function."""
    args = parse_args()

    if args.input_file:
        # Process file
        try:
            process_file(args.input_file, args.output_file, args.dry_run)
        except Exception as e:
            print(f"Error processing file: {e}")
            return 1
    elif args.urls:
        # Process URLs directly
        urls = args.urls.split()
        formatted = format_urls_to_markdown(urls, args.preserve_order)
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
