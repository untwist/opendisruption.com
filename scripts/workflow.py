#!/usr/bin/env python3
"""
Complete Workflow for Open Disruption Weekly Links

This script automates the entire process:
1. Format URLs in markdown files
2. Generate HTML versions with Google Analytics
3. Update the archive index

Usage:
    python workflow.py --input weekly-links/2025-10-16-links.md
    python workflow.py --all  # Process all markdown files
    python workflow.py --latest  # Process the most recent file
"""

import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import sys


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Complete workflow for Open Disruption weekly links"
    )
    parser.add_argument("--input", help="Input markdown file to process", type=Path)
    parser.add_argument(
        "--all", action="store_true", help="Process all markdown files in weekly-links/"
    )
    parser.add_argument(
        "--latest", action="store_true", help="Process the most recent markdown file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without making changes",
    )
    return parser.parse_args()


def get_latest_markdown_file(weekly_links_dir: Path) -> Path:
    """Get the most recent markdown file in the weekly-links directory."""
    markdown_files = list(weekly_links_dir.glob("*.md"))
    if not markdown_files:
        raise FileNotFoundError(f"No markdown files found in {weekly_links_dir}")

    # Sort by modification time, most recent first
    latest_file = max(markdown_files, key=lambda f: f.stat().st_mtime)
    return latest_file


def process_single_file(input_file: Path, dry_run: bool = False):
    """Process a single markdown file."""
    print(f"🚀 Processing: {input_file}")

    if dry_run:
        print("🔍 DRY RUN - No changes will be made")

    # Step 1: Format URLs in markdown
    print("📝 Step 1: Formatting URLs in markdown...")
    cmd = [
        sys.executable,
        "format_urls_with_html.py",
        "--input-file",
        str(input_file),
        "--generate-html",
    ]

    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Markdown formatting complete")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error formatting markdown: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

    # Step 2: Generate HTML version
    print("🌐 Step 2: Generating HTML version...")
    html_file = input_file.with_suffix(".html")

    if not dry_run and html_file.exists():
        print(f"✅ HTML file created: {html_file}")
    elif dry_run:
        print(f"🔍 Would create HTML file: {html_file}")

    return True


def process_all_files(weekly_links_dir: Path, dry_run: bool = False):
    """Process all markdown files in the weekly-links directory."""
    markdown_files = list(weekly_links_dir.glob("*.md"))
    if not markdown_files:
        print(f"❌ No markdown files found in {weekly_links_dir}")
        return False

    # Filter out index.md
    markdown_files = [f for f in markdown_files if f.name != "index.md"]

    if not markdown_files:
        print("❌ No markdown files to process (excluding index.md)")
        return False

    print(f"📁 Found {len(markdown_files)} markdown files to process")

    success_count = 0
    for md_file in markdown_files:
        if process_single_file(md_file, dry_run):
            success_count += 1
        print()  # Add spacing between files

    print(f"✅ Successfully processed {success_count}/{len(markdown_files)} files")
    return success_count == len(markdown_files)


def main():
    """Main function."""
    args = parse_args()

    weekly_links_dir = Path("weekly-links")
    if not weekly_links_dir.exists():
        print(f"❌ Weekly links directory not found: {weekly_links_dir}")
        return 1

    try:
        if args.all:
            print("🚀 Processing all markdown files...")
            success = process_all_files(weekly_links_dir, args.dry_run)
            if success:
                print("🎉 All files processed successfully!")
            else:
                print("⚠️  Some files failed to process")
                return 1

        elif args.latest:
            print("🚀 Processing latest markdown file...")
            latest_file = get_latest_markdown_file(weekly_links_dir)
            print(f"📄 Latest file: {latest_file}")
            success = process_single_file(latest_file, args.dry_run)
            if success:
                print("🎉 Latest file processed successfully!")
            else:
                print("❌ Failed to process latest file")
                return 1

        elif args.input:
            print("🚀 Processing specified file...")
            success = process_single_file(args.input, args.dry_run)
            if success:
                print("🎉 File processed successfully!")
            else:
                print("❌ Failed to process file")
                return 1

        else:
            print("Please specify --input, --all, or --latest")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
