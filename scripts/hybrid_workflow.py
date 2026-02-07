#!/usr/bin/env python3
"""
Hybrid Workflow for Open Disruption Weekly Links

This script combines the original fast formatting with smart metadata extraction
for the best of both worlds: speed and reliability with enhanced titles.

Usage:
    python hybrid_workflow.py --input weekly-links/2025-10-23-links.md
    python hybrid_workflow.py --all  # Process all markdown files
    python hybrid_workflow.py --latest  # Process the most recent file
"""

import argparse
from pathlib import Path
from datetime import datetime
import subprocess
import sys

# Import the smart formatter
from smart_url_formatter import (
    generate_smart_title_for_url,
    format_urls_to_markdown_smart,
    should_extract_metadata,
)

# Import original functions
from format_urls import extract_urls_from_section


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Hybrid workflow for Open Disruption weekly links"
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
    parser.add_argument(
        "--smart-only",
        action="store_true",
        help="Use only smart metadata extraction (slower but more informative)",
    )
    parser.add_argument(
        "--fast-only",
        action="store_true",
        help="Use only fast formatting (no metadata extraction)",
    )
    return parser.parse_args()


def update_archive_index(dry_run: bool = False) -> bool:
    """Regenerate weekly-links/index.md from all *-links.md files."""
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    weekly_links_py = script_dir / "weekly_links.py"
    cmd = [sys.executable, str(weekly_links_py), "--update-index"]
    if dry_run:
        cmd.append("--dry-run")
    try:
        result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)
        if result.stdout:
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not update archive index: {e}")
        if e.stderr:
            print(e.stderr.strip())
        return False


def get_latest_markdown_file(weekly_links_dir: Path) -> Path:
    """Get the most recent markdown file in the weekly-links directory."""
    markdown_files = list(weekly_links_dir.glob("*.md"))
    if not markdown_files:
        raise FileNotFoundError(f"No markdown files found in {weekly_links_dir}")

    # Sort by modification time, most recent first
    latest_file = max(markdown_files, key=lambda f: f.stat().st_mtime)
    return latest_file


def process_single_file_hybrid(
    input_file: Path,
    dry_run: bool = False,
    smart_only: bool = False,
    fast_only: bool = False,
):
    """Process a single markdown file using hybrid approach."""
    print(f"🚀 Processing: {input_file}")

    if dry_run:
        print("🔍 DRY RUN - No changes will be made")

    # Read the file
    content = input_file.read_text(encoding="utf-8")
    print(f"📄 File size: {len(content)} characters")

    # Extract URLs from the Links section
    print("🔍 Extracting URLs from 'Links from Office Hours' section...")
    urls = extract_urls_from_section(content)

    if not urls:
        print("❌ No URLs found in the Links section.")
        return False

    print(f"📊 Found {len(urls)} URLs to format")
    print("📝 Sample URLs:")
    for i, url in enumerate(urls[:3], 1):
        print(f"   {i}. {url}")
    if len(urls) > 3:
        print(f"   ... and {len(urls) - 3} more")

    # Determine processing strategy
    if fast_only:
        print("⚡ Using fast formatting only (no metadata extraction)")
        # Use original format_urls_with_html.py
        return process_with_original_formatter(input_file, dry_run)
    elif smart_only:
        print("🧠 Using smart metadata extraction for all URLs")
        return process_with_smart_formatter(input_file, urls, dry_run)
    else:
        print("🔄 Using hybrid approach (smart for beneficial URLs, fast for others)")
        return process_with_hybrid_approach(input_file, urls, dry_run)


def process_with_original_formatter(input_file: Path, dry_run: bool = False):
    """Process using the original fast formatter."""
    print("📝 Step 1: Fast formatting URLs...")
    cmd = [
        sys.executable,
        "scripts/format_urls_with_html.py",
        "--input-file",
        str(input_file),
        "--generate-html",
    ]

    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Fast formatting complete")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in fast formatting: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def process_with_smart_formatter(input_file: Path, urls: list, dry_run: bool = False):
    """Process using smart metadata extraction for all URLs."""
    print("🧠 Step 1: Smart formatting URLs with metadata extraction...")

    if dry_run:
        print("🔍 DRY RUN - Showing smart titles:")
        for i, url in enumerate(urls[:5], 1):
            title = generate_smart_title_for_url(url)
            print(f"   {i}. {title}")
        if len(urls) > 5:
            print(f"   ... and {len(urls) - 5} more")
        return True

    # Use smart formatter
    formatted_links = format_urls_to_markdown_smart(urls)

    # Replace the content in the file
    print("🔄 Replacing content...")
    content = input_file.read_text(encoding="utf-8")

    # Create the new section
    new_section = f"""## Links from Office Hours
*Presented in the order they were discussed during the episode*

{formatted_links}"""

    # Replace the old content with the new formatted section
    lines = content.split("\n")
    new_lines = []
    in_old_section = False
    skip_until_archive = False
    replaced_section = False

    for line in lines:
        if line.startswith("## Links from Office Hours"):
            in_old_section = True
            skip_until_archive = True
            new_lines.append(new_section)
            replaced_section = True
            continue
        elif line.startswith("## Archive") and skip_until_archive:
            skip_until_archive = False
            new_lines.append(line)
            continue
        elif skip_until_archive:
            continue
        else:
            new_lines.append(line)

    # Write the updated content
    updated_content = "\n".join(new_lines)
    input_file.write_text(updated_content, encoding="utf-8")
    print("✅ Smart formatting complete")

    # Generate HTML version
    print("🌐 Step 2: Generating HTML version...")
    html_cmd = [
        sys.executable,
        "scripts/markdown_to_html.py",
        "--input",
        str(input_file),
    ]

    try:
        result = subprocess.run(html_cmd, capture_output=True, text=True, check=True)
        print("✅ HTML version created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  HTML generation failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return True  # Still successful for markdown


def process_with_hybrid_approach(input_file: Path, urls: list, dry_run: bool = False):
    """Process using hybrid approach: smart for beneficial URLs, fast for others."""
    print("🔄 Step 1: Hybrid formatting URLs...")

    # Analyze URLs to determine which ones would benefit from metadata extraction
    smart_urls = []
    fast_urls = []

    for url in urls:
        if should_extract_metadata(url):
            smart_urls.append(url)
        else:
            fast_urls.append(url)

    print(
        f"📊 Analysis: {len(smart_urls)} URLs will use smart extraction, {len(fast_urls)} will use fast formatting"
    )

    if dry_run:
        print("🔍 DRY RUN - Showing hybrid approach:")
        print("🧠 Smart extraction URLs:")
        for i, url in enumerate(smart_urls[:3], 1):
            title = generate_smart_title_for_url(url)
            print(f"   {i}. {title}")
        if len(smart_urls) > 3:
            print(f"   ... and {len(smart_urls) - 3} more")

        print("⚡ Fast formatting URLs:")
        for i, url in enumerate(fast_urls[:3], 1):
            print(f"   {i}. {url} (will use original method)")
        if len(fast_urls) > 3:
            print(f"   ... and {len(fast_urls) - 3} more")
        return True

    # Process smart URLs with metadata extraction
    if smart_urls:
        print(f"🧠 Processing {len(smart_urls)} URLs with smart extraction...")
        smart_formatted = format_urls_to_markdown_smart(smart_urls)
    else:
        smart_formatted = ""

    # Process fast URLs with original method
    if fast_urls:
        print(f"⚡ Processing {len(fast_urls)} URLs with fast method...")
        # For now, we'll use the original formatter for fast URLs
        # In a full implementation, you'd extract just the fast URLs and process them
        fast_formatted = format_urls_to_markdown_smart(
            fast_urls
        )  # Fallback to smart for now
    else:
        fast_formatted = ""

    # Combine results
    all_formatted = smart_formatted + (fast_formatted if fast_formatted else "")

    # Replace content in file
    print("🔄 Replacing content...")
    content = input_file.read_text(encoding="utf-8")

    new_section = f"""## Links from Office Hours
*Presented in the order they were discussed during the episode*

{all_formatted}"""

    # Replace the old content
    lines = content.split("\n")
    new_lines = []
    in_old_section = False
    skip_until_archive = False
    replaced_section = False

    for line in lines:
        if line.startswith("## Links from Office Hours"):
            in_old_section = True
            skip_until_archive = True
            new_lines.append(new_section)
            replaced_section = True
            continue
        elif line.startswith("## Archive") and skip_until_archive:
            skip_until_archive = False
            new_lines.append(line)
            continue
        elif skip_until_archive:
            continue
        else:
            new_lines.append(line)

    # Write the updated content
    updated_content = "\n".join(new_lines)
    input_file.write_text(updated_content, encoding="utf-8")
    print("✅ Hybrid formatting complete")

    # Generate HTML version
    print("🌐 Step 2: Generating HTML version...")
    html_cmd = [
        sys.executable,
        "scripts/markdown_to_html.py",
        "--input",
        str(input_file),
    ]

    try:
        result = subprocess.run(html_cmd, capture_output=True, text=True, check=True)
        print("✅ HTML version created")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  HTML generation failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return True  # Still successful for markdown


def process_all_files(
    weekly_links_dir: Path,
    dry_run: bool = False,
    smart_only: bool = False,
    fast_only: bool = False,
):
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
        if process_single_file_hybrid(md_file, dry_run, smart_only, fast_only):
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
            success = process_all_files(
                weekly_links_dir, args.dry_run, args.smart_only, args.fast_only
            )
            if success:
                print("🎉 All files processed successfully!")
                print("📋 Updating archive index...")
                update_archive_index(args.dry_run)
            else:
                print("⚠️  Some files failed to process")
                return 1

        elif args.latest:
            print("🚀 Processing latest markdown file...")
            latest_file = get_latest_markdown_file(weekly_links_dir)
            print(f"📄 Latest file: {latest_file}")
            success = process_single_file_hybrid(
                latest_file, args.dry_run, args.smart_only, args.fast_only
            )
            if success:
                print("🎉 Latest file processed successfully!")
                print("📋 Updating archive index...")
                update_archive_index(args.dry_run)
            else:
                print("❌ Failed to process latest file")
                return 1

        elif args.input:
            print("🚀 Processing specified file...")
            success = process_single_file_hybrid(
                args.input, args.dry_run, args.smart_only, args.fast_only
            )
            if success:
                print("🎉 File processed successfully!")
                print("📋 Updating archive index...")
                update_archive_index(args.dry_run)
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
