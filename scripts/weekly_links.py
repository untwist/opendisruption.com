#!/usr/bin/env python3
import argparse
import os
import re
from datetime import datetime
from pathlib import Path

WEEKLY_DIR = Path("weekly-links")
TEMPLATE_FILE = WEEKLY_DIR / "template.md"
INDEX_FILE = WEEKLY_DIR / "index.md"
FILENAME_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-links\.md$")
DATE_FMT_FILE = "%Y-%m-%d"
DATE_FMT_DISPLAY = "%B %d, %Y"

ARCHIVE_HEADER = """# 🧭 Open Disruption — Link Archive

Welcome to the **Open Disruption Link Archive**, a weekly collection of curated AI news, research papers, product launches, and X (Twitter) threads from our live Office Hours sessions.

> 📺 Watch the weekly show on [YouTube](https://youtube.com/@OpenDisruption)
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
👉 [Open Disruption Link Archive](./index.md)

---

*Curated by Todd Brous for [Open Disruption](https://opendisruption.com/)*  
*Follow for weekly deep dives into the future of AI.*
"""

def parse_args():
    p = argparse.ArgumentParser(
        description="Create weekly links file from template and update index.md"
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
    return p.parse_args()

def ensure_dirs():
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)

def load_template():
    if TEMPLATE_FILE.exists():
        return TEMPLATE_FILE.read_text(encoding="utf-8")
    # Fallback to default template if no template.md is found
    return DEFAULT_TEMPLATE

def fill_template(tpl: str, display_date: str, video_url: str, youtube_text: str) -> str:
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
    out = out.replace("(https://youtube.com/your-video-link)", f"({video_url})")
    out = out.replace("[YouTube Link Here]", youtube_text)

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

def write_index(files, dry_run=False):
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

def main():
    args = parse_args()
    ensure_dirs()

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

    # Update index
    files = find_weeklies()
    write_index(files, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"✅ Updated: {INDEX_FILE} with {len(files)} entries.")

if __name__ == "__main__":
    main()
