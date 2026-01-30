# Open Disruption Scripts Documentation

This directory contains automation scripts for creating and managing weekly AI news link collections for Open Disruption, including **Google Analytics tracking**, **HTML generation**, and **smart metadata extraction**.

## 🚀 Quick Start

> **📹 Important Reminder**: Upload your video to YouTube first and get the YouTube URL before running the pipeline. This ensures the weekly links template is created with the correct video link from the start.

### 🧠 Smart Hybrid Workflow (Recommended)
```bash
# 1. Upload your video to YouTube and get the URL
# 2. Generate template for this week with your YouTube URL
python scripts/weekly_links.py --date 2026-01-29 --video-url "https://youtube.com/watch?v=your-video"

python scripts/weekly_links.py --date

# 3. Add your raw URLs to the generated file
# (Open weekly-links/2025-01-29-links.md and paste URLs in the "Links from Office Hours" section)

# 4. Smart formatting with metadata extraction + HTML generation
python scripts/hybrid_workflow.py --input weekly-links/2025-01-29-links.md

python scripts/hybrid_workflow.py --input weekly-links/

# 5. Review and commit (both .md and .html files)
git add . && git commit -m "Add weekly links with smart titles and GA tracking" && git push
```

### 📋 RAW_LINKS Workflow (If you compile links in RAW_LINKS/)
```bash
# 1. Open all links in Chrome for office hours
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29

# 2. Convert RAW_LINKS to weekly-links and run pipeline
python scripts/raw_links_to_weekly.py --input RAW_LINKS/2026-01-29
# Edit weekly-links/2026-01-29-links.md to add YouTube URL
python scripts/hybrid_workflow.py --input weekly-links/2026-01-29-links.md

# 3. Review and commit
git add . && git commit -m "Add weekly links for January 29" && git push
```

### ⚡ Fast One-Command Solutions
```bash
# Smart processing for most recent file
python scripts/hybrid_workflow.py --latest

# Process all files with smart extraction
python scripts/hybrid_workflow.py --all

# Easy wrapper (same as above)
python scripts/smart_workflow.py --latest
```

### 🔧 Advanced Options
```bash
# Smart extraction for ALL URLs (slower but most informative)
python scripts/hybrid_workflow.py --input weekly-links/2025-01-29-links.md --smart-only

# Fast formatting only (no metadata extraction)
python scripts/hybrid_workflow.py --input weekly-links/2025-01-29-links.md --fast-only

# Original workflow (backward compatible)
python scripts/workflow.py --input weekly-links/2025-01-29-links.md
```

## Available Scripts

### 🧠 Smart Processing (New!)
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `hybrid_workflow.py` | **Smart hybrid processing** - metadata extraction + fast formatting | **Recommended for best results** |
| `smart_workflow.py` | Easy wrapper for hybrid workflow | Quick access to smart processing |
| `smart_url_formatter.py` | Smart metadata extraction for individual URLs | Testing or specific URL processing |
| `enhanced_url_formatter.py` | Full metadata extraction (slower but comprehensive) | When you need maximum information |

### 📋 RAW_LINKS Workflow (Office Hours)
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `open_links_in_chrome.py` | Open all RAW_LINKS URLs in Chrome tabs; search terms open as Google searches | Before office hours — open links for presentation |
| `raw_links_to_weekly.py` | Convert RAW_LINKS to weekly-links markdown format | After compiling links — feed into website pipeline |

### ⚡ Original Scripts
| Script | Purpose | When to Use |
|--------|---------|-------------|
| `weekly_links.py` | Creates template structure | Starting a new week |
| `format_urls.py` | Formats raw URLs into professional links | After pasting URLs |
| `markdown_to_html.py` | Converts markdown to HTML with Google Analytics | Generate HTML versions |
| `format_urls_with_html.py` | Formats URLs AND generates HTML with GA | One-step solution |
| `workflow.py` | **Complete automation** - formats URLs + generates HTML | **Backward compatible** |

## 🧠 Smart Metadata Extraction

The new hybrid workflow includes intelligent metadata extraction that dramatically improves link titles:

### ✨ What It Does
- **Extracts real page titles** from research papers, news articles, and AI company blogs
- **Uses smart categorization** to determine which URLs benefit from metadata extraction
- **Respects rate limits** and terms of service
- **Falls back gracefully** to original formatting when extraction fails

### 🎯 Smart vs Fast Processing
| URL Type | Processing Method | Example Result |
|----------|------------------|---------------|
| **Research Papers** (arXiv, academic sites) | Smart extraction | `"[2509.25140] ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory"` |
| **AI Company Blogs** (OpenAI, Anthropic, Google) | Smart extraction | `"Netflix goes 'all in' on generative AI as entertainment industry remains divided \| TechCrunch"` |
| **News Articles** (TechCrunch, Wired, etc.) | Smart extraction | `"State of Generative Media Survey Report 2025 \| Artificial Analysis"` |
| **Social Media** (Twitter/X, YouTube) | Fast formatting | `"karpathy — AI Industry Insight"` |
| **Video Platforms** | Fast formatting | `"YouTube: AI Video Content"` |

### 🔧 Processing Modes
```bash
# Hybrid approach (recommended) - smart for beneficial URLs, fast for others
python scripts/hybrid_workflow.py --input weekly-links/2025-01-29-links.md

# Smart-only mode - metadata extraction for ALL URLs (slower)
python scripts/hybrid_workflow.py --input weekly-links/2025-01-29-links.md --smart-only

# Fast-only mode - original formatting only (fastest)
python scripts/hybrid_workflow.py --input weekly-links/2025-01-29-links.md --fast-only
```

### 🛡️ Safe Domains (80+ domains)
The system intelligently extracts metadata from safe, beneficial domains:
- **Academic**: arXiv, NeurIPS, ICML, universities, research institutions
- **AI Companies**: OpenAI, Anthropic, Google DeepMind, Hugging Face, Stability AI
- **Tech Platforms**: GitHub, GitLab, Stack Overflow, Medium, Substack
- **News & Media**: TechCrunch, The Verge, Wired, Reuters, Bloomberg

### ⚠️ Avoided Domains
- **Social Media**: Twitter/X, YouTube, LinkedIn, Facebook, Instagram
- **Video Platforms**: YouTube, TikTok, Vimeo
- **Other**: Reddit, Discord, Slack

## 📋 RAW_LINKS Workflow (Office Hours)

If you compile links in `RAW_LINKS/YYYY-MM-DD` during the week, use these scripts to open them in Chrome for your office hours and feed them into the website pipeline.

### RAW_LINKS Format
- **Category headers**: `HEADLINES:`, `GRAPHICS:`, `LLMs:`, `AGENTS:`, `CODING:`, `OTHER:`, `LABOR:`
- **Direct URLs**: `https://x.com/...`, `https://arxiv.org/...`, etc.
- **Search topics** (in double quotes): `"Qwen3 max thinking"` — opens as Google search

### Open All Links in Chrome
```bash
# Open all URLs and search terms in separate Chrome tabs
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29

# Open only HEADLINES category
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29 --category HEADLINES

# Preview without opening
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29 --dry-run

# Also save HTML launcher (fallback if popup blockers block script)
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29 --output-html

# Faster opening (1 second between tabs; default is 5 seconds)
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29 --delay 1.0
```

### Feed RAW_LINKS into Website Pipeline
```bash
# 1. Convert RAW_LINKS to weekly-links markdown (URLs only; search terms excluded)
python scripts/raw_links_to_weekly.py --input RAW_LINKS/2026-01-29

# 2. Add YouTube URL to the generated file (edit weekly-links/2026-01-29-links.md)

# 3. Run hybrid workflow to format URLs and generate HTML
python scripts/hybrid_workflow.py --input weekly-links/2026-01-29-links.md

# 4. Review and commit
git add . && git commit -m "Add weekly links for January 29" && git push
```

### Notes
- **Search terms** (in double quotes) are opened as Google searches in Chrome but excluded from the website output. Topics to research are printed when running `raw_links_to_weekly.py`.
- **Date inference**: If `--date` is omitted, the date is inferred from the filename (e.g. `RAW_LINKS/2026-01-29` → `2026-01-29`).

## 🎯 Google Analytics Integration

All HTML files automatically include Google Analytics tracking (ID: `G-W5RHK6N572`):

- **Page views** on individual weekly link pages
- **User behavior** and engagement metrics
- **Traffic sources** to your content
- **Real-time visitor data**

### HTML Generation Options

**Option 1: Complete Workflow (Recommended)**
```bash
python scripts/workflow.py --latest  # Process most recent file
python scripts/workflow.py --all      # Process all files
```

**Option 2: Step by Step**
```bash
# 1. Format URLs in markdown
python format_urls.py --input-file weekly-links/2025-01-29-links.md

# 2. Generate HTML with Google Analytics
python scripts/markdown_to_html.py --input weekly-links/2025-01-29-links.md
```

**Option 3: Combined Script**
```bash
# Format URLs AND generate HTML in one command
python scripts/format_urls_with_html.py --input-file weekly-links/2025-01-29-links.md --generate-html
```

## 📁 Files Created

When you run the conversion, you'll get:

1. **Original markdown file** (unchanged)
2. **HTML file** with the same name but `.html` extension
3. **Google Analytics tracking** automatically included

Example:
- `weekly-links/2025-10-16-links.md` → `weekly-links/2025-10-16-links.html`

## 🎨 HTML Features

The HTML files include:
- **Google Analytics tracking** automatically included
- **Responsive design** that matches your main site
- **Navigation** back to main site
- **Mobile-friendly** styling
- **Professional typography** and layout
- **Clean, readable typography**
- **Archive navigation**

## 📚 Usage Examples

### 🧠 Smart Hybrid Workflow Examples
```bash
# Process most recent file with smart extraction
python scripts/hybrid_workflow.py --latest

# Process specific file with hybrid approach
python scripts/hybrid_workflow.py --input weekly-links/2025-10-23-links.md

# Process all files with smart extraction
python scripts/hybrid_workflow.py --all

# Smart extraction for ALL URLs (slower but most informative)
python scripts/hybrid_workflow.py --input weekly-links/2025-10-23-links.md --smart-only

# Fast formatting only (no metadata extraction)
python scripts/hybrid_workflow.py --input weekly-links/2025-10-23-links.md --fast-only

# Dry run to see what would be processed
python scripts/hybrid_workflow.py --input weekly-links/2025-10-23-links.md --dry-run
```

### 🔧 Individual Tool Examples
```bash
# Test smart formatter on specific URLs
python scripts/smart_url_formatter.py --urls "https://arxiv.org/abs/2509.25140 https://openai.com/index/introducing-chatgpt-atlas/"

# Test enhanced formatter (full metadata extraction)
python scripts/enhanced_url_formatter.py --urls "https://techcrunch.com/2025/10/21/netflix-goes-all-in-on-generative-ai/"

# Easy wrapper for hybrid workflow
python scripts/smart_workflow.py --latest
python scripts/smart_workflow.py --all
```

### ⚡ Original Workflow Examples
```bash
# Original workflow (backward compatible)
python scripts/workflow.py --input weekly-links/2025-10-23-links.md
python scripts/workflow.py --latest
python scripts/workflow.py --all

# Individual components
python scripts/format_urls.py --input-file weekly-links/2025-10-23-links.md
python scripts/markdown_to_html.py --input weekly-links/2025-10-23-links.md
```

## Script Details

### open_links_in_chrome.py
Opens RAW_LINKS URLs in Google Chrome. Search terms (in double quotes) open as Google searches.

**Basic Usage:**
```bash
# Open all links in Chrome
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29

# Open only HEADLINES category
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29 --category HEADLINES

# Preview without opening
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29 --dry-run

# Save HTML launcher
python scripts/open_links_in_chrome.py RAW_LINKS/2026-01-29 --output-html
```

**All Options:**
| Option | Description | Example |
|--------|-------------|---------|
| `input` | Path to RAW_LINKS file | `RAW_LINKS/2026-01-29` |
| `--category` | Only open links from this category | `--category HEADLINES` |
| `--dry-run` | Preview without opening | `--dry-run` |
| `--output-html` | Save HTML launcher with Open All button | `--output-html` |
| `--delay` | Seconds between opening each tab (default: 5) | `--delay 1.0` |

### raw_links_to_weekly.py
Converts RAW_LINKS format to weekly-links markdown. URLs only (search terms excluded). Run `hybrid_workflow.py` afterward.

**Basic Usage:**
```bash
# Convert RAW_LINKS to weekly-links (date inferred from filename)
python scripts/raw_links_to_weekly.py --input RAW_LINKS/2026-01-29

# Specify date explicitly
python scripts/raw_links_to_weekly.py --input RAW_LINKS/2026-01-29 --date 2026-01-29

# Preview without writing
python scripts/raw_links_to_weekly.py --input RAW_LINKS/2026-01-29 --dry-run
```

**All Options:**
| Option | Description | Example |
|--------|-------------|---------|
| `--input` | Path to RAW_LINKS file | `--input RAW_LINKS/2026-01-29` |
| `--date` | Date in YYYY-MM-DD (default: inferred from filename) | `--date 2026-01-29` |
| `--dry-run` | Preview output without writing | `--dry-run` |

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
| `--youtube-text` | Link text for YouTube video | `YouTube Link Here` | `--youtube-text "Watch This Week's Office Hours"` |
| `--force` | Overwrite existing file | False | `--force` |
| `--dry-run` | Preview changes without creating files | False | `--dry-run` |

### format_urls.py
Automatically formats raw URLs into organized, professional markdown links with descriptive titles using curated patterns. **No web scraping** - fast and reliable.

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

### markdown_to_html.py
Converts markdown files to HTML with Google Analytics tracking and responsive styling.

**Basic Usage:**
```bash
# Convert single file
python scripts/markdown_to_html.py --input weekly-links/2025-01-29-links.md

# Convert all markdown files
python scripts/markdown_to_html.py --all

# Custom Google Analytics ID
python scripts/markdown_to_html.py --input weekly-links/2025-01-29-links.md --ga-id G-XXXXXXXXXX
```

### format_urls_with_html.py
Enhanced version of `format_urls.py` that also generates HTML with Google Analytics.

**Basic Usage:**
```bash
# Format URLs AND generate HTML with Google Analytics
python scripts/format_urls_with_html.py --input-file weekly-links/2025-01-29-links.md --generate-html

# Preview before making changes
python scripts/format_urls_with_html.py --input-file weekly-links/2025-01-29-links.md --generate-html --dry-run
```

### workflow.py
**Complete automation script** - the recommended way to process your weekly links.

**Basic Usage:**
```bash
# Process most recent file (recommended)
python scripts/workflow.py --latest

# Process all files at once
python scripts/workflow.py --all

# Process specific file
python scripts/workflow.py --input weekly-links/2025-01-29-links.md

# Preview without making changes
python scripts/workflow.py --latest --dry-run
```

## Smart URL Formatting

The `format_urls.py` script automatically recognizes and formats:

- **Twitter/X threads** → "Username — AI Discussion"
- **arXiv papers** → "arXiv: Research Paper 2510.04871"
- **GitHub repos** → "GitHub: username/repo"
- **YouTube videos** → "YouTube Video"
- **AI tools** → "ToolName: Description"
- **Research papers** → "Institution: Paper Title"
- **News articles** → "Source: Article Title"

### Curated Patterns
The script uses carefully curated patterns for consistent, high-quality titles:
- **State of AI** → "State of AI 2025 Report"
- **Anthropic** → "Anthropic: Equipping Agents for the Real World with Agent Skills"
- **Google/DeepMind** → "Google DeepMind: CodeMender AI Agent for Code Security"
- **Brookings** → "Brookings: New Data Show No AI Jobs Apocalypse (For Now)"
- **And many more...**

## Generated Files

### Weekly Files
- **Markdown**: `weekly-links/YYYY-MM-DD-links.md`
- **HTML**: `weekly-links/YYYY-MM-DD-links.html` (with Google Analytics)
- **Example**: `weekly-links/2025-01-29-links.md` + `weekly-links/2025-01-29-links.html`
- **Content**: Curated AI news, research papers, tools, and threads

### Archive Index
- **Location**: `weekly-links/index.md`
- **Content**: Automatically updated list of all weekly collections
- **Features**: Sorted by date (newest first)

## 🔧 Your New Workflow

### Option 1: Simple (Recommended)
1. Paste your URLs into a markdown file
2. Run: `python scripts/workflow.py --latest`
3. Both markdown and HTML versions are ready!

### Option 2: Step by Step
1. Format URLs: `python scripts/format_urls.py --input-file weekly-links/2025-10-16-links.md`
2. Generate HTML: `python scripts/markdown_to_html.py --input weekly-links/2025-10-16-links.md`

### Option 3: Combined Script
1. Format URLs AND generate HTML: `python scripts/format_urls_with_html.py --input-file weekly-links/2025-10-16-links.md --generate-html`

## Complete Workflow Examples

### Scenario 1: Starting Fresh (New Week) - With Google Analytics
```bash
# 1. Generate template
python weekly_links.py --date 2025-01-29 --video-url "https://youtube.com/watch?v=abc123" --youtube-text "January 29 Office Hours"

# 2. Edit the file and paste your raw URLs in the "Links from Office Hours" section
# (Open weekly-links/2025-01-29-links.md and paste URLs)

# 3. Format URLs AND generate HTML with Google Analytics (one command!)
python scripts/workflow.py --input weekly-links/2025-01-29-links.md

# 4. Review and commit (both .md and .html files)
git add . && git commit -m "Add weekly links with GA tracking for January 29" && git push
```

### Scenario 2: You Already Have Raw URLs - With Google Analytics
```bash
# Format URLs AND generate HTML with Google Analytics
python scripts/workflow.py --input weekly-links/2025-01-29-links.md

# Or use the combined script
python scripts/format_urls_with_html.py --input-file weekly-links/2025-01-29-links.md --generate-html
```

### Scenario 3: Process All Files at Once
```bash
# Generate HTML with Google Analytics for all weekly files
python scripts/workflow.py --all
```

### Scenario 4: Preview Before Making Changes
```bash
# Preview template generation
python weekly_links.py --date 2025-01-29 --dry-run

# Preview URL formatting
python format_urls.py --input-file weekly-links/2025-01-29-links.md --dry-run

# Preview complete workflow (formats URLs + generates HTML)
python scripts/workflow.py --input weekly-links/2025-01-29-links.md --dry-run
```

## Output Format

The scripts create professionally formatted content like this:

```markdown
## Links from Office Hours
*Presented in the order they were discussed during the episode*

- <a href="https://www.stateof.ai/" target="_blank" rel="noopener noreferrer">State of AI 2025 Report</a>
- <a href="https://x.com/openai/status/1978655285406302398" target="_blank" rel="noopener noreferrer">OpenAI — Latest Updates</a>
- <a href="https://arxiv.org/abs/2510.04871v1" target="_blank" rel="noopener noreferrer">arXiv: TinyRecursiveModels Paper</a>
```

## Advanced Features

### Section-Aware Processing
The `format_urls.py` script only processes URLs from the "Links from Office Hours" section, ignoring:
- Footer links
- Archive links
- Other markdown links in the file

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

## Troubleshooting

### Common Issues

**File already exists error:**
```bash
# Use --force to overwrite
python weekly_links.py --date 2025-01-29 --force
```

**Invalid date format:**
```bash
# Use YYYY-MM-DD format
python weekly_links.py --date 2025-01-29  # Correct
python weekly_links.py --date 01/29/2025  # Wrong format
```

**No URLs found:**
```bash
# Make sure your file contains URLs in the "Links from Office Hours" section
python format_urls.py --input-file weekly-links/2025-01-29-links.md --dry-run
```

**Footer URLs being processed:**
```bash
# The script only processes URLs from the "Links from Office Hours" section
# Footer links are automatically ignored
```

### Debug Mode
Use `--dry-run` to preview changes without creating files:
```bash
python weekly_links.py --date 2025-01-29 --dry-run
python format_urls.py --input-file weekly-links/2025-01-29-links.md --dry-run
```

## File Structure

```
scripts/
├── open_links_in_chrome.py      # Open RAW_LINKS in Chrome
├── raw_links_to_weekly.py       # Convert RAW_LINKS to weekly-links
├── weekly_links.py              # Template generator
├── format_urls.py               # URL formatter (original)
├── markdown_to_html.py          # Markdown to HTML converter with GA
├── format_urls_with_html.py     # Enhanced formatter with HTML generation
├── workflow.py                  # Complete automation workflow
├── requirements.txt             # Python dependencies
└── README.md                    # Complete documentation

weekly-links/
├── template.md                  # Custom template (optional)
├── template_with_ga.html       # HTML template with Google Analytics
├── index.md                     # Archive index (auto-generated)
├── 2025-01-15-links.md          # Individual weekly files (markdown)
├── 2025-01-15-links.html        # Individual weekly files (HTML with GA)
├── 2025-01-22-links.md
├── 2025-01-22-links.html
└── ...
```

## Integration with GitHub Pages

The generated files work seamlessly with GitHub Pages:

### Markdown Files (Original)
- **Archive**: `https://opendisruption.com/weekly-links/`
- **Individual weeks**: `https://opendisruption.com/weekly-links/2025-01-29-links.html`

### HTML Files (With Google Analytics)
- **Individual weeks**: `https://opendisruption.com/weekly-links/2025-01-29-links.html`
- **Features**: Full Google Analytics tracking, responsive design, professional styling

### Recommended Setup
1. **Keep both formats**: Commit both `.md` and `.html` files
2. **Link to HTML**: Update your main site to link to `.html` versions for tracking
3. **Analytics data**: All HTML pages will send data to Google Analytics

## 🚨 Troubleshooting

### Common Issues
```bash
# If you get "ModuleNotFoundError: No module named 'markdown'"
uv add markdown

# If you get "ModuleNotFoundError: No module named 'requests'"
uv add requests beautifulsoup4

# If HTML generation fails
python scripts/markdown_to_html.py --input weekly-links/2025-10-23-links.md

# If smart extraction is too slow
python scripts/hybrid_workflow.py --input weekly-links/2025-10-23-links.md --fast-only

# If you want to test without making changes
python scripts/hybrid_workflow.py --input weekly-links/2025-10-23-links.md --dry-run
```

### Performance Tips
- **Hybrid approach** (default) balances speed and quality
- **Smart-only mode** is slower but gives best titles
- **Fast-only mode** is fastest but uses generic labels
- **Dry run** shows what would be processed without making changes

### 🧠 Smart Processing Benefits
- **Dramatically improved titles** for research papers and news articles
- **Intelligent categorization** of URLs for optimal processing
- **Respectful rate limiting** to avoid overwhelming servers
- **Graceful fallbacks** when metadata extraction fails

## Support

For issues or questions:
1. Check this documentation first
2. Use `--dry-run` to preview changes
3. Verify date format is YYYY-MM-DD
4. Ensure you have write permissions in the `weekly-links/` directory

---

*This script is part of the Open Disruption project. For more information, visit [opendisruption.com](https://opendisruption.com/).*