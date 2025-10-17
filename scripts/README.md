# Open Disruption Scripts Documentation

This directory contains automation scripts for creating and managing weekly AI news link collections for Open Disruption.

## 🚀 Quick Start

### Complete Workflow (Recommended)
```bash
# 1. Generate template for this week
python weekly_links.py --date 2025-01-29 --video-url "https://youtube.com/watch?v=your-video"

# 2. Add your raw URLs to the generated file
# (Open weekly-links/2025-01-29-links.md and paste URLs)

# 3. Format the URLs automatically
python format_urls.py --input-file weekly-links/2025-01-29-links.md

# 4. Review and commit
git add . && git commit -m "Add weekly links" && git push
```

### If You Already Have Raw URLs
```bash
# Just format the existing file
python format_urls.py --input-file weekly-links/2025-01-29-links.md
```

## 📋 Available Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `weekly_links.py` | Creates template structure | Starting a new week |
| `format_urls.py` | Formats raw URLs into professional links | After pasting URLs |

## 🔧 Script Details

### weekly_links.py
Creates weekly AI news link collections and updates the archive index.

**Basic Usage:**
```bash
# Create for today
python weekly_links.py

# Create for specific date
python weekly_links.py --date 2025-01-29

# Add YouTube video
python weekly_links.py --date 2025-01-29 --video-url "https://youtube.com/watch?v=abc123" --youtube-text "This Week's Office Hours"
```

**All Options:**
| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--date` | Date in YYYY-MM-DD format | Today's date | `--date 2025-01-29` |
| `--video-url` | YouTube URL for the episode | `https://youtube.com/your-video-link` | `--video-url "https://youtube.com/watch?v=abc123"` |
| `--youtube-text` | Link text for YouTube video | `YouTube Link Here` | `--youtube-text "Watch This Week's Office Hours"` |
| `--force` | Overwrite existing file | False | `--force` |
| `--dry-run` | Preview changes without creating files | False | `--dry-run` |

### format_urls.py
Automatically formats raw URLs into organized, professional markdown links with descriptive titles.

**Basic Usage:**
```bash
# Format URLs in a file
python format_urls.py --input-file weekly-links/2025-01-29-links.md

# Format URLs from command line
python format_urls.py --urls "https://www.stateof.ai/ https://x.com/openai/status/123"

# Preview before formatting
python format_urls.py --input-file weekly-links/2025-01-29-links.md --dry-run
```

**All Options:**
| Option | Description | Example |
|--------|-------------|---------|
| `--input-file` | File containing raw URLs to format | `--input-file weekly-links/2025-01-29-links.md` |
| `--urls` | Raw URLs as space-separated string | `--urls "https://example.com https://twitter.com/user/status/123"` |
| `--output-file` | Output file path (default: overwrites input) | `--output-file formatted-links.md` |
| `--dry-run` | Preview without writing files | `--dry-run` |
| `--preserve-order` | Keep original URL order (default: True) | `--preserve-order` |

## 🎯 Smart URL Formatting

The `format_urls.py` script automatically recognizes and formats:

- **Twitter/X threads** → "Username — AI Discussion"
- **arXiv papers** → "arXiv: Research Paper 2510.04871"
- **GitHub repos** → "GitHub: username/repo"
- **YouTube videos** → "YouTube Video"
- **AI tools** → "ToolName: Description"
- **Research papers** → "Institution: Paper Title"
- **News articles** → "Source: Article Title"

## 📁 Generated Files

### Weekly Files
- **Location**: `weekly-links/YYYY-MM-DD-links.md`
- **Example**: `weekly-links/2025-01-29-links.md`
- **Content**: Curated AI news, research papers, tools, and threads

### Archive Index
- **Location**: `weekly-links/index.md`
- **Content**: Automatically updated list of all weekly collections
- **Features**: Sorted by date (newest first)

## 🔄 Complete Workflow Examples

### Scenario 1: Starting Fresh (New Week)
```bash
# 1. Generate template
python weekly_links.py --date 2025-01-29 --video-url "https://youtube.com/watch?v=abc123" --youtube-text "January 29 Office Hours"

# 2. Edit the file and paste your raw URLs
# (Open weekly-links/2025-01-29-links.md and paste URLs anywhere)

# 3. Format the URLs
python format_urls.py --input-file weekly-links/2025-01-29-links.md

# 4. Review and commit
git add . && git commit -m "Add weekly links for January 29" && git push
```

### Scenario 2: You Already Have Raw URLs
```bash
# Just format the existing file
python format_urls.py --input-file weekly-links/2025-01-29-links.md
```

### Scenario 3: Preview Before Making Changes
```bash
# Preview template generation
python weekly_links.py --date 2025-01-29 --dry-run

# Preview URL formatting
python format_urls.py --input-file weekly-links/2025-01-29-links.md --dry-run
```

## 🎨 Output Format

The scripts create professionally formatted content like this:

```markdown
## 🔗 Links from Office Hours
*Presented in the order they were discussed during the episode*

- <a href="https://www.stateof.ai/" target="_blank" rel="noopener noreferrer">State of AI 2025 Report</a>
- <a href="https://x.com/openai/status/1978655285406302398" target="_blank" rel="noopener noreferrer">OpenAI — Latest Updates</a>
- <a href="https://arxiv.org/abs/2510.04871v1" target="_blank" rel="noopener noreferrer">arXiv: TinyRecursiveModels Paper</a>
```

## 🔧 Advanced Features

### External Link Handling
Both scripts automatically convert external links to HTML with `target="_blank"` for better user experience:
- External links: `<a href="url" target="_blank" rel="noopener noreferrer">text</a>`
- Internal links: `<a href="url">text</a>`

### Template System
- **Primary**: Uses `weekly-links/template.md` if it exists
- **Fallback**: Uses built-in template if no custom template found
- **Customization**: Edit `template.md` to change the format

### Archive Management
- Automatically sorts weekly files by date (newest first)
- Updates archive index with all available weeks
- Maintains consistent formatting across all entries

## 🐛 Troubleshooting

### Common Issues

**File already exists error:**
```bash
# Use --force to overwrite
python weekly_links.py --date 2025-01-29 --force
```

**Invalid date format:**
```bash
# Use YYYY-MM-DD format
python weekly_links.py --date 2025-01-29  # ✅ Correct
python weekly_links.py --date 01/29/2025  # ❌ Wrong format
```

**No URLs found:**
```bash
# Make sure your file contains URLs
python format_urls.py --input-file weekly-links/2025-01-29-links.md --dry-run
```

### Debug Mode
Use `--dry-run` to preview changes without creating files:
```bash
python weekly_links.py --date 2025-01-29 --dry-run
python format_urls.py --input-file weekly-links/2025-01-29-links.md --dry-run
```

## 📊 File Structure

```
scripts/
├── weekly_links.py          # Template generator
├── format_urls.py           # URL formatter
└── README.md               # This documentation

weekly-links/
├── template.md             # Custom template (optional)
├── index.md                # Archive index (auto-generated)
├── 2025-01-15-links.md     # Individual weekly files
├── 2025-01-22-links.md
└── ...
```

## 🔗 Integration with GitHub Pages

The generated markdown files work seamlessly with GitHub Pages:
- **Archive**: `https://opendisruption.com/weekly-links/`
- **Individual weeks**: `https://opendisruption.com/weekly-links/2025-01-29-links.html`

## 📞 Support

For issues or questions:
1. Check this documentation first
2. Use `--dry-run` to preview changes
3. Verify date format is YYYY-MM-DD
4. Ensure you have write permissions in the `weekly-links/` directory

---

*This script is part of the Open Disruption project. For more information, visit [opendisruption.com](https://opendisruption.com/).*