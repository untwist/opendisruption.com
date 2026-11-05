#!/usr/bin/env python3
"""
Open RAW_LINKS in Google Chrome

Parses RAW_LINKS format and opens each URL in a new Chrome tab.
Search terms (in double quotes) are opened as Google searches.
Section tags insert a matching SLIDES PNG before that section's links.

Usage:
    python open_links_in_chrome.py RAW_LINKS/2026-01-29
    python open_links_in_chrome.py RAW_LINKS/2026-01-29 --category HEADLINES
    python open_links_in_chrome.py RAW_LINKS/2026-01-29 --delay 3 8   # random 3-8 sec (reduces blocking risk)
    python open_links_in_chrome.py RAW_LINKS/2026-01-29 --dry-run
    python open_links_in_chrome.py RAW_LINKS/2026-01-29 --output-html
    python open_links_in_chrome.py RAW_LINKS/2026-01-29 --no-slides
"""

from __future__ import annotations

import argparse
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parent.parent
SLIDES_DIR = REPO_ROOT / "SLIDES"

# Colon-style headers recognized in older RAW_LINKS files (case-insensitive)
COLON_CATEGORIES = {
    "HEADLINES",
    "GRAPHICS",
    "LLMS",
    "AGENTS",
    "CODING",
    "OTHER",
    "LABOR",
    "PROMPT SHARE",
    "CLAW",
}

TAG_OPEN_RE = re.compile(r"^<([^/>][^>]*)>\s*$")
TAG_CLOSE_RE = re.compile(r"^</([^>]+)>\s*$")


def normalize_name(value: str) -> str:
    """Normalize tag/filename text for matching (case-insensitive, alnum only)."""
    return "".join(c for c in value.upper() if c.isalnum())


def categories_match(a: str | None, b: str | None) -> bool:
    if a is None or b is None:
        return False
    return normalize_name(a) == normalize_name(b)


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


def find_slide_for_category(category: str, slides_dir: Path) -> Path | None:
    """Return the PNG whose normalized stem starts with the normalized tag."""
    if not slides_dir.is_dir():
        return None

    needle = normalize_name(category)
    if not needle:
        return None

    matches: list[Path] = []
    for path in sorted(slides_dir.glob("*.png")):
        stem = normalize_name(path.stem)
        if stem.startswith(needle):
            matches.append(path)

    if not matches:
        return None

    # Prefer the shortest stem so "LLMs" prefers "LLMs and Models" over a longer
    # accidental prefix match if multiple files share a prefix.
    matches.sort(key=lambda p: (len(normalize_name(p.stem)), p.name.lower()))
    return matches[0]


def parse_category_line(line: str) -> tuple[str | None, bool]:
    """
    Parse a category header/footer line.
    Returns (category_name, is_closing). category_name is None if not a header.
    """
    open_match = TAG_OPEN_RE.match(line)
    if open_match:
        return open_match.group(1).strip(), False

    close_match = TAG_CLOSE_RE.match(line)
    if close_match:
        return close_match.group(1).strip(), True

    if line.endswith(":"):
        name = line[:-1].strip()
        if name.upper() in COLON_CATEGORIES or normalize_name(name) in {
            normalize_name(c) for c in COLON_CATEGORIES
        }:
            return name, False

    return None, False


def parse_raw_links_with_categories(
    content: str,
    category_filter: str | None = None,
    *,
    include_slides: bool = False,
    slides_dir: Path | None = None,
):
    """
    Parse RAW_LINKS with optional category filter.
    Returns (items, search_topics) - items are (url, type) tuples.
    Types: url, search, slide.
    """
    lines = content.splitlines()
    items: list[tuple[str, str]] = []
    search_topics: list[str] = []
    seen_urls: set[str] = set()
    current_category: str | None = None
    section_items: list[tuple[str, str]] = []
    section_search_topics: list[str] = []
    slides_dir = slides_dir or SLIDES_DIR

    def flush_section() -> None:
        nonlocal section_items, section_search_topics
        if not section_items:
            section_items = []
            section_search_topics = []
            return

        if category_filter and not categories_match(current_category, category_filter):
            section_items = []
            section_search_topics = []
            return

        if include_slides and current_category:
            slide_path = find_slide_for_category(current_category, slides_dir)
            if slide_path is not None:
                items.append((slide_path.resolve().as_uri(), "slide"))
            else:
                print(
                    f"  Warning: no slide found in {slides_dir.name}/ "
                    f"for section <{current_category}>",
                    file=sys.stderr,
                )

        items.extend(section_items)
        search_topics.extend(section_search_topics)
        section_items = []
        section_search_topics = []

    for line in lines:
        line = line.strip()

        category_name, is_closing = parse_category_line(line)
        if category_name is not None:
            if is_closing:
                # Only flush when the close tag matches the open section
                if categories_match(current_category, category_name):
                    flush_section()
                    current_category = None
                continue

            flush_section()
            current_category = category_name
            continue

        if not line or line.lower() in ("xx", "---"):
            continue

        # Search terms in double quotes
        if line.startswith('"') and line.endswith('"') and len(line) > 2:
            term = line[1:-1].strip()
            if term:
                section_search_topics.append(term)
                url = f"https://www.google.com/search?q={quote(term)}"
                section_items.append((url, "search"))
            continue

        # Direct URLs
        if line.startswith("http://") or line.startswith("https://"):
            url = line.strip()
            if url not in seen_urls:
                seen_urls.add(url)
                section_items.append((url, "url"))
            continue

    flush_section()
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


def item_label(typ: str) -> str:
    if typ == "search":
        return "search"
    if typ == "slide":
        return "slide"
    return "url"


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
        "--no-slides",
        action="store_true",
        help="Skip section title slides from SLIDES/",
    )
    parser.add_argument(
        "--delay",
        nargs="+",
        type=float,
        default=[5.0],
        metavar="SEC",
        help="Seconds between tabs: one value (fixed) or two values MIN MAX (random range). Default: 5. Example: --delay 3 8",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    content = args.input.read_text(encoding="utf-8")
    items, search_topics = parse_raw_links_with_categories(
        content,
        category_filter=args.category,
        include_slides=not args.no_slides,
        slides_dir=SLIDES_DIR,
    )

    if not items:
        print("No URLs or search terms found.")
        if args.category:
            print(f"  (Category filter: {args.category})")
        sys.exit(0)

    url_count = sum(1 for _, t in items if t == "url")
    search_count = sum(1 for _, t in items if t == "search")
    slide_count = sum(1 for _, t in items if t == "slide")
    parts = [f"{url_count} URLs", f"{search_count} searches"]
    if slide_count:
        parts.append(f"{slide_count} slides")
    print(f"Opening {len(items)} items ({', '.join(parts)})...")

    if args.output_html:
        out_path = args.input.parent / f"{args.input.name}-launcher.html"
        generate_html_launcher(items, out_path)

    if args.dry_run:
        for url, typ in items:
            label = item_label(typ)
            print(f"  [{label}] {url[:90]}{'...' if len(url) > 90 else ''}")
        if search_topics:
            print(f"\nSearch topics: {', '.join(search_topics)}")
        return

    # Parse delay: one value = fixed, two values = random range
    delays = args.delay
    if len(delays) == 1:
        delay_min = delay_max = delays[0]
    elif len(delays) == 2:
        delay_min, delay_max = min(delays), max(delays)
    else:
        print("Error: --delay accepts 1 (fixed) or 2 (min max) values.", file=sys.stderr)
        sys.exit(1)

    for i, (url, _) in enumerate(items):
        print(f"[{i + 1}/{len(items)}] Opening: {url}")
        open_in_chrome(url, dry_run=False)
        if i < len(items) - 1:
            delay = random.uniform(delay_min, delay_max)
            print(f"  Waiting {delay:.1f} sec...")
            time.sleep(delay)

    print("Done.")


if __name__ == "__main__":
    main()
