#!/usr/bin/env python3
"""
Open RAW_LINKS in Google Chrome

Parses RAW_LINKS format and opens each URL in a new Chrome tab.
Search terms (in double quotes) are opened as Google searches.

Usage:
    python open_links_in_chrome.py RAW_LINKS/2026-01-29
    python open_links_in_chrome.py RAW_LINKS/2026-01-29 --category HEADLINES
    python open_links_in_chrome.py RAW_LINKS/2026-01-29 --delay 1.0   # slower (1 sec between tabs)
    python open_links_in_chrome.py RAW_LINKS/2026-01-29 --dry-run
    python open_links_in_chrome.py RAW_LINKS/2026-01-29 --output-html
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

# Categories recognized in RAW_LINKS (case-insensitive)
CATEGORIES = {"HEADLINES", "GRAPHICS", "LLMS", "AGENTS", "CODING", "OTHER", "LABOR"}


def open_in_chrome(url: str, dry_run: bool = False) -> bool:
    """Open a URL in Google Chrome (macOS)."""
    if dry_run:
        print(f"  [would open] {url[:80]}{'...' if len(url) > 80 else ''}")
        return True
    try:
        subprocess.run(
            ["open", "-a", "Google Chrome", url],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error opening {url[:60]}...: {e}", file=sys.stderr)
        return False


def parse_raw_links_with_categories(content: str, category_filter: str | None = None):
    """
    Parse RAW_LINKS with optional category filter.
    Returns (items, search_topics) - items are (url, type) tuples.
    """
    lines = content.splitlines()
    items = []
    search_topics = []
    seen_urls = set()
    current_category = None

    for line in lines:
        raw_line = line
        line = line.strip()

        # Category headers
        if line.rstrip(":").upper() in CATEGORIES and line.endswith(":"):
            current_category = line.rstrip(":").upper()
            continue

        if not line or line.lower() in ("xx", "---"):
            continue

        # If filtering by category, skip items not in that category
        if category_filter and current_category != category_filter.upper():
            continue

        # Search terms in double quotes
        if line.startswith('"') and line.endswith('"') and len(line) > 2:
            term = line[1:-1].strip()
            if term:
                search_topics.append(term)
                url = f"https://www.google.com/search?q={quote(term)}"
                items.append((url, "search"))
            continue

        # Direct URLs
        if line.startswith("http://") or line.startswith("https://"):
            url = line.strip()
            if url not in seen_urls:
                seen_urls.add(url)
                items.append((url, "url"))
            continue

    return items, search_topics


def generate_html_launcher(items: list[tuple[str, str]], output_path: Path) -> None:
    """Generate an HTML file with an Open All button."""
    urls = [url for url, _ in items]
    urls_js = ", ".join(repr(u) for u in urls)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Office Hours Links — Open All</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 600px; margin: 2rem auto; padding: 1rem; }}
        h1 {{ font-size: 1.25rem; }}
        button {{ font-size: 1rem; padding: 0.75rem 1.5rem; cursor: pointer; background: #1a73e8; color: white; border: none; border-radius: 6px; }}
        button:hover {{ background: #1557b0; }}
        .count {{ color: #666; margin: 0.5rem 0; }}
    </style>
</head>
<body>
    <h1>Office Hours Links</h1>
    <p class="count">{len(urls)} links</p>
    <button onclick="openAll()">Open All in New Tabs</button>
    <p style="margin-top: 1rem; font-size: 0.875rem; color: #666;">Note: Popup blockers may block multiple tabs. Allow popups for this page if needed.</p>
    <script>
        const urls = [{urls_js}];
        function openAll() {{
            urls.forEach(url => window.open(url, '_blank'));
        }}
    </script>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    print(f"  Saved HTML launcher: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Open RAW_LINKS URLs in Google Chrome")
    parser.add_argument(
        "input",
        type=Path,
        help="Path to RAW_LINKS file (e.g. RAW_LINKS/2026-01-29)",
    )
    parser.add_argument(
        "--category",
        type=str,
        help="Only open links from this category (e.g. HEADLINES, GRAPHICS, LLMs)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be opened without opening",
    )
    parser.add_argument(
        "--output-html",
        action="store_true",
        help="Also save an HTML launcher file with Open All button",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="Seconds to wait between opening each tab (default: 5). Use --delay 1.0 for faster opening.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    content = args.input.read_text(encoding="utf-8")
    items, search_topics = parse_raw_links_with_categories(
        content, category_filter=args.category
    )

    if not items:
        print("No URLs or search terms found.")
        if args.category:
            print(f"  (Category filter: {args.category})")
        sys.exit(0)

    url_count = sum(1 for _, t in items if t == "url")
    search_count = sum(1 for _, t in items if t == "search")
    print(f"Opening {len(items)} items ({url_count} URLs, {search_count} searches)...")

    if args.output_html:
        out_path = args.input.parent / f"{args.input.name}-launcher.html"
        generate_html_launcher(items, out_path)

    if args.dry_run:
        for url, typ in items:
            label = "search" if typ == "search" else "url"
            print(f"  [{label}] {url[:90]}{'...' if len(url) > 90 else ''}")
        if search_topics:
            print(f"\nSearch topics: {', '.join(search_topics)}")
        return

    for i, (url, _) in enumerate(items):
        open_in_chrome(url, dry_run=False)
        if i < len(items) - 1:
            time.sleep(args.delay)

    print("Done.")


if __name__ == "__main__":
    main()
