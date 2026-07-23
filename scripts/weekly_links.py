#!/usr/bin/env python3
"""
Weekly Links Generator for Open Disruption

This script creates weekly AI news link collections and updates the archive index.

Quick Usage:
    python weekly_links.py --date 2025-01-29 --video-url "https://youtube.com/watch?v=your-video"
    python weekly_links.py --dry-run  # Preview changes
    python weekly_links.py --help     # See all options

For detailed documentation, see README.md in this directory.
"""

import argparse

# import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

WEEKLY_DIR = Path("weekly-links")
TEMPLATE_FILE = WEEKLY_DIR / "template.md"
INDEX_FILE = WEEKLY_DIR / "index.md"
INDEX_HTML_FILE = WEEKLY_DIR / "index.html"
FILENAME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-links\.md$")
DATE_FMT_FILE = "%Y-%m-%d"
DATE_FMT_DISPLAY = "%B %d, %Y"
GA_ID = "G-W5RHK6N572"

ARCHIVE_HEADER = """# 🧭 Open Disruption — Link Archive

Welcome to the **Open Disruption Link Archive**, a weekly collection of curated AI news, research papers, product launches, and X (Twitter) threads from our live Office Hours sessions.

> 📺 Watch the weekly show on [YouTube](https://www.youtube.com/@toddbrous)
> 🌐 Learn more at [opendisruption.com](https://opendisruption.com/)

---

## 🗓️ Archive
"""

ARCHIVE_FOOTER = """
---

*This archive is open-source and updated weekly.*
"""

DEFAULT_TEMPLATE = """# 🧠 Open Disruption — Weekly AI News Links
**Date:** {DISPLAY_DATE}  
**Episode:** Weekly Office Hours

Welcome to this week’s curated list of the most important stories, research papers, threads, and tools in AI.

> 📺 Watch the full episode on YouTube: [{YOUTUBE_TEXT}]({YOUTUBE_URL})

---

## 📰 AI Industry News
- [Title of Article or Launch](https://example.com)

## 🧪 Research & Papers
- [arXiv: Paper Title](https://arxiv.org/abs/abc123)

## 🧰 Tools, Startups & Launches
- [Cool new AI tool](https://example.com)

## 🗣️ Great Threads
- [Author — Thread Topic](https://twitter.com/example/status/12345)

---

## 🗃️ Archive
You can find **all previous weeks** of curated AI news here:  
👉 [Open Disruption Link Archive](https://opendisruption.com/weekly-links/)

---

*Curated by Todd Brous for [Open Disruption](https://opendisruption.com/)*  
*Follow for weekly deep dives into the future of AI.*
"""


def parse_args():
    p = argparse.ArgumentParser(
        description="Create weekly links file from template and update index.md + index.html"
    )
    p.add_argument(
        "--date",
        help="Week date in YYYY-MM-DD (default: today)",
        default=datetime.now().strftime(DATE_FMT_FILE),
    )
    p.add_argument(
        "--video-url",
        help="YouTube URL to insert into the new weekly file (optional)",
        default="https://youtube.com/your-video-link",
    )
    p.add_argument(
        "--youtube-text",
        help="Anchor text for the YouTube link",
        default="YouTube Link Here",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the weekly file if it already exists",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change but do not write files",
    )
    p.add_argument(
        "--update-index",
        action="store_true",
        help="Only regenerate weekly-links/index.md and index.html from existing *-links.md files (no new file created)",
    )
    return p.parse_args()


def ensure_dirs():
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)


def load_template():
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    # Fallback to default template if no template.md is found
    return DEFAULT_TEMPLATE


def is_external_url(url: str) -> bool:
    """Check if a URL is external (not relative or same domain)"""
    if not url or url.startswith("#") or url.startswith("./") or url.startswith("/"):
        return False
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc)  # Has a domain
    except Exception:
        return False


def convert_markdown_links_to_html_with_target(markdown_text: str) -> str:
    """
    Convert Markdown links to HTML with target="_blank" for external links.
    Pattern: [text](url) -> <a href="url" target="_blank" rel="noopener noreferrer">text</a>
    """
    # Pattern to match Markdown links: [text](url)
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    def replace_link(match):
        text = match.group(1)
        url = match.group(2)

        if is_external_url(url):
            return (
                f'<a href="{url}" target="_blank" rel="noopener noreferrer">{text}</a>'
            )
        else:
            return f'<a href="{url}">{text}</a>'

    return re.sub(link_pattern, replace_link, markdown_text)


def fill_template(
    tpl: str, display_date: str, video_url: str, youtube_text: str
) -> str:
    """
    Replaces common placeholders gracefully.
    - Replaces {DISPLAY_DATE}, {YOUTUBE_URL}, {YOUTUBE_TEXT} tokens
    - Also replaces bracket-style placeholders if the user kept the original template:
      [Month Day, Year] and [YouTube Link Here]
    """
    out = tpl
    out = out.replace("{DISPLAY_DATE}", display_date)
    out = out.replace("{YOUTUBE_URL}", video_url)
    out = out.replace("{YOUTUBE_TEXT}", youtube_text)

    # Backward-friendly replacements for the earlier template format
    out = out.replace("[Month Day, Year]", display_date)
    out = out.replace(
        "[YouTube Link Here](https://youtube.com/your-video-link)",
        f"[{youtube_text}]({video_url})",
    )

    # Convert Markdown links to HTML with target="_blank" for external links
    out = convert_markdown_links_to_html_with_target(out)

    return out


def weekly_filename(date_obj: datetime) -> Path:
    return WEEKLY_DIR / f"{date_obj.strftime(DATE_FMT_FILE)}-links.md"


def find_weeklies():
    files = []
    for p in WEEKLY_DIR.glob("*.md"):
        m = FILENAME_RE.match(p.name)
        if m:
            d = datetime.strptime(m.group(1), DATE_FMT_FILE)
            files.append((d, p))
    files.sort(key=lambda x: x[0], reverse=True)
    return files


def write_index_md(files, dry_run=False):
    lines = [ARCHIVE_HEADER, ""]
    for d, path in files:
        display = d.strftime(DATE_FMT_DISPLAY)
        lines.append(f"- [{display}](./{path.name})")
    lines.append(ARCHIVE_FOOTER)
    content = "\n".join(lines).strip() + "\n"
    if dry_run:
        print("\n--- index.md (preview) ---\n")
        print(content)
    else:
        INDEX_FILE.write_text(content, encoding="utf-8")


def write_index_html(files, dry_run=False):
    """Write static archive index.html (required for GitHub Pages with .nojekyll)."""
    items = []
    for d, path in files:
        display = d.strftime(DATE_FMT_DISPLAY)
        html_name = path.name.replace("-links.md", "-links.html")
        items.append(f'        <li><a href="./{html_name}">{display}</a></li>')
    list_html = "\n".join(items)
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Open Disruption — Link Archive</title>

    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{GA_ID}');
    </script>

    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }}

        h1, h2 {{
            color: #C04A3B;
        }}

        h1 {{
            font-size: 2.5em;
            margin-bottom: 0.5em;
        }}

        h2 {{
            font-size: 1.8em;
            margin-top: 2em;
            margin-bottom: 1em;
            border-bottom: 2px solid #C04A3B;
            padding-bottom: 0.5em;
        }}

        a {{
            color: #C04A3B;
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
        }}

        .back-link {{
            display: inline-block;
            margin-bottom: 20px;
            color: #666;
            font-size: 0.9em;
        }}

        .intro {{
            margin-bottom: 1.5em;
        }}

        .note {{
            color: #666;
            border-left: 3px solid #C04A3B;
            padding-left: 1em;
            margin: 1.5em 0;
        }}

        ul {{
            padding-left: 0;
        }}

        li {{
            margin-bottom: 0.5em;
            list-style: none;
        }}

        .footer {{
            margin-top: 3em;
            padding-top: 1em;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <a href="/" class="back-link">← Back to Open Disruption</a>

    <h1>🧭 Open Disruption — Link Archive</h1>

    <p class="intro">
        Welcome to the <strong>Open Disruption Link Archive</strong>, a weekly collection of curated AI news,
        research papers, product launches, and X (Twitter) threads from our live Office Hours sessions.
    </p>

    <p class="note">
        📺 Watch the weekly show on <a href="https://www.youtube.com/@toddbrous" target="_blank" rel="noopener noreferrer">YouTube</a><br>
        🌐 Learn more at <a href="https://opendisruption.com/">opendisruption.com</a>
    </p>

    <h2>🗓️ Archive</h2>

    <ul>
{list_html}
    </ul>

    <p class="footer"><em>This archive is open-source and updated weekly.</em></p>
</body>
</html>
"""
    if dry_run:
        print("\n--- index.html (preview) ---\n")
        print(content)
    else:
        INDEX_HTML_FILE.write_text(content, encoding="utf-8")


def write_index(files, dry_run=False):
    write_index_md(files, dry_run=dry_run)
    write_index_html(files, dry_run=dry_run)


def main():
    args = parse_args()
    ensure_dirs()

    if args.update_index:
        # Only regenerate archive indexes from existing *-links.md files
        files = find_weeklies()
        write_index(files, dry_run=args.dry_run)
        if not args.dry_run:
            print(
                f"✅ Updated: {INDEX_FILE} and {INDEX_HTML_FILE} with {len(files)} entries."
            )
        return

    # Parse/validate date
    try:
        date_obj = datetime.strptime(args.date, DATE_FMT_FILE)
    except ValueError:
        raise SystemExit("❌ --date must be in YYYY-MM-DD format (e.g., 2025-10-17)")

    # Generate weekly file path
    out_file = weekly_filename(date_obj)
    display_date = date_obj.strftime(DATE_FMT_DISPLAY)

    # Create weekly file
    if out_file.exists() and not args.force:
        print(f"⚠️  {out_file} already exists. Use --force to overwrite.")
    else:
        tpl = load_template()
        rendered = fill_template(tpl, display_date, args.video_url, args.youtube_text)
        if args.dry_run:
            print(f"\n--- {out_file} (preview) ---\n")
            print(rendered)
        else:
            out_file.write_text(rendered, encoding="utf-8")
            print(f"✅ Created: {out_file}")

    # Update indexes (markdown + HTML for static GitHub Pages)
    files = find_weeklies()
    write_index(files, dry_run=args.dry_run)
    if not args.dry_run:
        print(
            f"✅ Updated: {INDEX_FILE} and {INDEX_HTML_FILE} with {len(files)} entries."
        )


if __name__ == "__main__":
    main()
