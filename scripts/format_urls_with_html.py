#!/usr/bin/env python3
"""
Enhanced URL Formatter with HTML Generation

Extends the original format_urls.py to also generate HTML versions with Google Analytics.
This gives you both markdown and HTML versions of your weekly links.

Usage:
    python format_urls_with_html.py --input-file weekly-links/2025-01-29-links.md
    python format_urls_with_html.py --input-file weekly-links/2025-01-29-links.md --generate-html
    python format_urls_with_html.py --urls "https://example.com https://twitter.com/user/status/123" --generate-html
"""

import argparse
import re
from pathlib import Path
from typing import List
import markdown
from datetime import datetime

# Import the original formatting functions
from format_urls import (
    CURATED_PATTERNS,
    DOMAIN_FALLBACKS,
    extract_urls_from_text,
    extract_urls_from_section,
    get_domain,
    generate_title_for_url,
    format_urls_to_markdown,
)

# Google Analytics Measurement ID
GA_MEASUREMENT_ID = "G-W5RHK6N572"

# HTML template with Google Analytics
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{ga_id}');
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
        
        h1, h2, h3 {{
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
        
        h3 {{
            font-size: 1.3em;
            margin-top: 1.5em;
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
        
        .date-info {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 2em;
        }}
        
        ul {{
            padding-left: 0;
        }}
        
        li {{
            margin-bottom: 0.5em;
            list-style: none;
        }}
        
        blockquote {{
            border-left: 4px solid #C04A3B;
            margin: 1em 0;
            padding-left: 1em;
            color: #666;
            font-style: italic;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #eee;
            margin: 2em 0;
        }}
        
        .archive-link {{
            background: #C04A3B;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            text-decoration: none;
            display: inline-block;
            margin: 1em 0;
        }}
        
        .archive-link:hover {{
            background: #A03A2B;
            text-decoration: none;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}
            
            h1 {{
                font-size: 2em;
            }}
            
            h2 {{
                font-size: 1.5em;
            }}
        }}
    </style>
</head>
<body>
    <a href="/" class="back-link">← Back to Open Disruption</a>
    
    {content}
</body>
</html>"""


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Format raw URLs into organized markdown links with optional HTML generation"
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
        "--generate-html",
        action="store_true",
        help="Also generate HTML version with Google Analytics",
    )
    parser.add_argument(
        "--html-output",
        help="HTML output file path (default: same as input with .html extension)",
        type=Path,
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be formatted"
    )
    parser.add_argument(
        "--ga-id",
        help=f"Google Analytics Measurement ID (default: {GA_MEASUREMENT_ID})",
        default=GA_MEASUREMENT_ID,
    )
    return parser.parse_args()


def extract_title_from_markdown(content: str) -> str:
    """Extract title from markdown content."""
    lines = content.split("\n")
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
        if line.startswith("**Date:**"):
            # Extract date and create title
            date_match = re.search(r"\*\*Date:\*\*\s*(.+)", line)
            if date_match:
                date_str = date_match.group(1).strip()
                return f"Open Disruption — Weekly AI News Links ({date_str})"
    return "Open Disruption — Weekly AI News Links"


def enhance_markdown_content(content: str) -> str:
    """Enhance markdown content with additional styling and links."""
    # Add archive link if not present
    if "Archive" not in content:
        archive_section = """
---

## 🗃️ Archive
You can find **all previous weeks** of curated AI news here:  
👉 [Open Disruption Link Archive](https://opendisruption.com/weekly-links/)

---

*Curated by Todd Brous for [Open Disruption](https://opendisruption.com/)*  
*Follow for weekly deep dives into the future of AI.*"""
        content += archive_section

    return content


def convert_markdown_to_html(
    content: str, title: str, ga_id: str = GA_MEASUREMENT_ID
) -> str:
    """Convert markdown content to HTML with Google Analytics."""
    # Enhance content
    enhanced_content = enhance_markdown_content(content)

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=["extra", "codehilite"])
    html_content = md.convert(enhanced_content)

    # Create full HTML document
    full_html = HTML_TEMPLATE.format(title=title, ga_id=ga_id, content=html_content)

    return full_html


def process_file_with_html(
    input_file: Path,
    output_file: Path = None,
    html_output: Path = None,
    dry_run: bool = False,
    ga_id: str = GA_MEASUREMENT_ID,
) -> tuple[str, str]:
    """Process a file and optionally generate HTML version."""
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
        return content, ""

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
    in_old_section = False
    skip_until_archive = False
    replaced_section = False

    for line in lines:
        if line.startswith("## Links from Office Hours") or line.startswith(
            "## AI Industry News"
        ):
            in_old_section = True
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

    # Generate HTML version if requested
    html_content = ""
    if not dry_run:
        # Write markdown file
        output_path = output_file or input_file
        print(f"💾 Writing markdown to: {output_path}")
        output_path.write_text(result, encoding="utf-8")
        print(f"✅ Successfully formatted URLs written to: {output_path}")

        # Generate HTML if requested
        title = extract_title_from_markdown(result)
        html_content = convert_markdown_to_html(result, title, ga_id)

        if html_output is None:
            html_output = input_file.with_suffix(".html")

        print(f"🌐 Writing HTML to: {html_output}")
        html_output.write_text(html_content, encoding="utf-8")
        print(f"✅ HTML version created: {html_output}")

    if dry_run:
        print("\n" + "=" * 50)
        print("📋 FORMATTED CONTENT PREVIEW")
        print("=" * 50)
        print(result)
        print("=" * 50)
        if html_content:
            print("\n" + "=" * 50)
            print("🌐 HTML CONTENT PREVIEW")
            print("=" * 50)
            print(
                html_content[:500] + "..." if len(html_content) > 500 else html_content
            )
            print("=" * 50)

    return result, html_content


def main():
    """Main function."""
    args = parse_args()

    if args.input_file:
        try:
            process_file_with_html(
                args.input_file,
                args.output_file,
                args.html_output,
                args.dry_run,
                args.ga_id,
            )
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
