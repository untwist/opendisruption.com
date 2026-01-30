#!/usr/bin/env python3
"""
Convert RAW_LINKS to weekly-links markdown format

Parses RAW_LINKS format and outputs weekly-links/YYYY-MM-DD-links.md
with raw URLs in the "Links from Office Hours" section. Run hybrid_workflow.py
afterward to format URLs and generate HTML.

Usage:
    python raw_links_to_weekly.py --input RAW_LINKS/2026-01-29 --date 2026-01-29
    python raw_links_to_weekly.py --input RAW_LINKS/2026-01-29  # date from filename
"""

import argparse
from datetime import datetime
from pathlib import Path

# Import parsing from open_links_in_chrome
from open_links_in_chrome import parse_raw_links_with_categories

WEEKLY_DIR = Path("weekly-links")
TEMPLATE_FILE = WEEKLY_DIR / "template.md"
DATE_FMT_FILE = "%Y-%m-%d"
DATE_FMT_DISPLAY = "%B %d, %Y"

DEFAULT_TEMPLATE = """#  Open Disruption — Weekly AI News Links
**Date:** {DISPLAY_DATE}  
**Episode:** Weekly Office Hours

Welcome to this week's curated list of the most important stories, research papers, threads, and tools in AI.

> Watch the full episode on YouTube: [YouTube Link Here](https://youtube.com/your-video-link)

---

## Links from Office Hours
*Presented in the order they were discussed during the episode*

{LINKS_PLACEHOLDER}

---

## Archive
You can find **all previous weeks** of curated AI news here:  
[Open Disruption Link Archive](https://opendisruption.com/weekly-links/)

---

*Curated by Todd Brous for [Open Disruption](https://opendisruption.com/)*  
*Follow for weekly deep dives into the future of AI.*
"""


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert RAW_LINKS to weekly-links markdown"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to RAW_LINKS file (e.g. RAW_LINKS/2026-01-29)",
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date in YYYY-MM-DD (default: inferred from input filename)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview output without writing",
    )
    return parser.parse_args()


def extract_urls_only(content: str) -> list[str]:
    """Parse RAW_LINKS and return URLs only (no search terms)."""
    items, search_topics = parse_raw_links_with_categories(content)
    urls = [url for url, typ in items if typ == "url"]
    if search_topics:
        print(f"Topics to research (excluded from output): {', '.join(search_topics)}")
    return urls


def build_links_section(urls: list[str]) -> str:
    """Build the Links from Office Hours section with raw URLs."""
    header = """## Links from Office Hours
*Presented in the order they were discussed during the episode*

"""
    bullets = "\n".join("- " + url for url in urls)
    return header + bullets


def load_template() -> str:
    """Load template from file or use default."""
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    return DEFAULT_TEMPLATE


def replace_links_section(content: str, urls: list[str]) -> str:
    """Replace the Links from Office Hours section with our URLs."""
    new_section = build_links_section(urls)

    lines = content.split("\n")
    new_lines = []
    skip_until_next_section = False
    replaced = False

    for line in lines:
        if (
            line.strip().startswith("## Links from Office Hours")
            or line.strip().startswith("## AI Industry News")
            or "## 📰" in line
        ):
            skip_until_next_section = True
            replaced = True
            new_lines.append(new_section)
            continue
        if skip_until_next_section:
            stripped = line.strip()
            if (
                stripped.startswith("## ")
                and "Links" not in stripped
                and "AI Industry" not in stripped
            ):
                skip_until_next_section = False
                new_lines.append(line)
            continue
        new_lines.append(line)

    if not replaced:
        raise ValueError("Could not find 'Links from Office Hours' section to replace")

    return "\n".join(new_lines)


def main():
    args = parse_args()

    if not args.input.exists():
        print(f"Error: File not found: {args.input}")
        return 1

    # Determine date
    if args.date:
        try:
            date_obj = datetime.strptime(args.date, DATE_FMT_FILE)
        except ValueError:
            print(f"Error: --date must be YYYY-MM-DD (e.g. 2026-01-29)")
            return 1
    else:
        # Infer from filename (e.g. 2026-01-29 or RAW_LINKS/2026-01-29)
        name = args.input.name
        try:
            date_obj = datetime.strptime(name, DATE_FMT_FILE)
        except ValueError:
            print(
                f"Error: Could not infer date from filename '{name}'. Use --date YYYY-MM-DD"
            )
            return 1

    content = args.input.read_text(encoding="utf-8")
    urls = extract_urls_only(content)

    if not urls:
        print("No URLs found in RAW_LINKS.")
        return 1

    display_date = date_obj.strftime(DATE_FMT_DISPLAY)
    out_file = WEEKLY_DIR / f"{date_obj.strftime(DATE_FMT_FILE)}-links.md"

    if out_file.exists():
        existing = out_file.read_text(encoding="utf-8")
        result = replace_links_section(existing, urls)
    else:
        WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
        tpl = load_template()
        tpl = tpl.replace("[Month Day, Year]", display_date).replace(
            "{DISPLAY_DATE}", display_date
        )
        result = replace_links_section(tpl, urls)

    if args.dry_run:
        print(f"\n--- {out_file} (preview) ---\n")
        print(result[:2000] + "..." if len(result) > 2000 else result)
        return 0

    out_file.write_text(result, encoding="utf-8")
    print(f"Created/updated: {out_file} ({len(urls)} URLs)")
    print("Next: python scripts/hybrid_workflow.py --input", str(out_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
