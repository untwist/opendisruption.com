#!/usr/bin/env python3
"""
Markdown to HTML Converter with Google Analytics

Converts markdown files to HTML with Google Analytics tracking included.
Extends the existing format_urls.py workflow to generate HTML versions.

Usage:
    python markdown_to_html.py --input weekly-links/2025-10-16-links.md
    python markdown_to_html.py --input weekly-links/2025-10-16-links.md --output weekly-links/2025-10-16-links.html
    python markdown_to_html.py --all  # Convert all markdown files in weekly-links/
"""

import argparse
import re
from pathlib import Path
from typing import List, Optional
import markdown
from datetime import datetime

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
        description="Convert markdown files to HTML with Google Analytics tracking"
    )
    parser.add_argument(
        "--input", help="Input markdown file path", type=Path, required=False
    )
    parser.add_argument(
        "--output",
        help="Output HTML file path (default: same name as input with .html extension)",
        type=Path,
        required=False,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Convert all markdown files in weekly-links/ directory",
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
    markdown_file: Path, output_file: Path = None, ga_id: str = GA_MEASUREMENT_ID
) -> Path:
    """Convert a markdown file to HTML with Google Analytics."""
    print(f"📁 Reading markdown file: {markdown_file}")

    if not markdown_file.exists():
        raise FileNotFoundError(f"Input file not found: {markdown_file}")

    # Read markdown content
    content = markdown_file.read_text(encoding="utf-8")
    print(f"📄 File size: {len(content)} characters")

    # Extract title
    title = extract_title_from_markdown(content)
    print(f"📝 Title: {title}")

    # Enhance content
    enhanced_content = enhance_markdown_content(content)

    # Convert markdown to HTML
    print("🔄 Converting markdown to HTML...")
    md = markdown.Markdown(extensions=["extra", "codehilite"])
    html_content = md.convert(enhanced_content)

    # Generate output filename if not provided
    if output_file is None:
        output_file = markdown_file.with_suffix(".html")

    # Create full HTML document
    full_html = HTML_TEMPLATE.format(title=title, ga_id=ga_id, content=html_content)

    # Write HTML file
    print(f"💾 Writing HTML file: {output_file}")
    output_file.write_text(full_html, encoding="utf-8")
    print(f"✅ Successfully created: {output_file}")

    return output_file


def convert_all_markdown_files(
    weekly_links_dir: Path = None, ga_id: str = GA_MEASUREMENT_ID
) -> List[Path]:
    """Convert all markdown files in the weekly-links directory."""
    if weekly_links_dir is None:
        weekly_links_dir = Path("weekly-links")

    if not weekly_links_dir.exists():
        raise FileNotFoundError(f"Weekly links directory not found: {weekly_links_dir}")

    markdown_files = list(weekly_links_dir.glob("*.md"))
    if not markdown_files:
        print(f"❌ No markdown files found in {weekly_links_dir}")
        return []

    print(f"📁 Found {len(markdown_files)} markdown files to convert")

    converted_files = []
    for md_file in markdown_files:
        if md_file.name == "index.md":
            continue  # Skip index file

        try:
            html_file = convert_markdown_to_html(md_file, ga_id=ga_id)
            converted_files.append(html_file)
        except Exception as e:
            print(f"❌ Error converting {md_file}: {e}")

    return converted_files


def main():
    """Main function."""
    args = parse_args()

    try:
        if args.all:
            print("🚀 Converting all markdown files...")
            converted_files = convert_all_markdown_files(ga_id=args.ga_id)
            print(f"✅ Converted {len(converted_files)} files")
            for file in converted_files:
                print(f"   📄 {file}")

        elif args.input:
            output_file = convert_markdown_to_html(args.input, args.output, args.ga_id)
            print(f"🎉 Conversion complete: {output_file}")

        else:
            print("Please provide either --input or --all")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
